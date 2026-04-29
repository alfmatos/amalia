from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, IO, Iterable, Iterator, Mapping

import requests

from .config import AmaliaConfig
from .errors import AmaliaAuthError, AmaliaError, AmaliaHTTPError


@dataclass
class StreamEvent:
    type: str   # "start" | "token" | "message" | "done" | (anything new the server sends)
    content: Any
    run_id: str
    raw: dict


class AmaliaClient:
    def __init__(
        self,
        config: AmaliaConfig,
        *,
        session: requests.Session | None = None,
        timeout: float = 120.0,
    ):
        self.config = config
        self._session = session or requests.Session()
        self._timeout = timeout

    @staticmethod
    def new_thread_id() -> str:
        # Mirrors the style of the example ("fqYrRSqRshHXSCz0IvR-1"): short, URL-safe.
        return secrets.token_urlsafe(15)

    def stream(
        self,
        message: str,
        *,
        thread_id: str,
        user_info: Mapping[str, Any] | str | None = None,
        user_id: str | None = None,
        user_context: Mapping[str, Any] | str | None = None,
        image: str | Path | IO[bytes] | None = None,
    ) -> Iterator[StreamEvent]:
        """POST a message and yield StreamEvents as the server emits them."""
        files: list[tuple[str, Any]] = [
            ("channel_id", (None, self.config.channel_id)),
            ("thread_id", (None, thread_id)),
            ("user_info", (None, _as_json_field(user_info if user_info is not None else {}))),
            ("message", (None, message)),
        ]
        if user_id is not None:
            files.append(("user_id", (None, user_id)))
        if user_context is not None:
            files.append(("user_context", (None, _as_json_field(user_context))))

        image_handle = None
        try:
            if image is not None:
                image_handle, image_tuple = _open_image(image)
                files.append(("image", image_tuple))

            try:
                response = self._session.post(
                    self.config.stream_url(),
                    headers={"x-api-key": self.config.api_key},
                    files=files,
                    stream=True,
                    timeout=self._timeout,
                )
            except requests.RequestException as e:
                raise AmaliaError(f"Network error talking to Amália: {e}") from e

            with response:
                if response.status_code in (401, 403):
                    raise AmaliaAuthError(
                        f"Authentication failed (HTTP {response.status_code}). "
                        f"Check AMALIA_API_KEY."
                    )
                if not response.ok:
                    raise AmaliaHTTPError(response.status_code, response.text)

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        # Skip malformed lines instead of crashing the stream.
                        continue
                    yield StreamEvent(
                        type=obj.get("type", ""),
                        content=obj.get("content"),
                        run_id=obj.get("run_id", ""),
                        raw=obj,
                    )
        finally:
            if image_handle is not None:
                image_handle.close()

    def complete(self, message: str, **kwargs: Any) -> str:
        """Stream a turn and return the final reply as a single string.

        Prefers the canonical text from the `message` event; falls back to
        concatenated `token` chunks if the server doesn't send one.
        """
        tokens: list[str] = []
        final: str | None = None
        for ev in self.stream(message, **kwargs):
            if ev.type == "token" and isinstance(ev.content, str):
                tokens.append(ev.content)
            elif ev.type == "message" and isinstance(ev.content, dict):
                text = ev.content.get("content")
                if isinstance(text, str) and text:
                    final = text
        return final if final is not None else "".join(tokens)


def _as_json_field(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _open_image(image: str | Path | IO[bytes]) -> tuple[IO[bytes] | None, tuple]:
    if hasattr(image, "read"):
        # Caller-managed file-like object — don't close it.
        name = getattr(image, "name", "image")
        return None, (Path(str(name)).name, image)
    path = Path(image)  # type: ignore[arg-type]
    fh = path.open("rb")
    return fh, (path.name, fh)
