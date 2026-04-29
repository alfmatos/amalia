#!/usr/bin/env python3
"""Ask Amália a Portugal-specific question. Pure stdlib — no pip install needed.

Reads credentials from environment variables first, then ~/.amalia/creds.txt or
./creds.txt. Prints Amália's answer to stdout. Exits non-zero with a clear
message if creds are missing or the request fails.

Usage:
    ask_amalia.py "Qual o prazo para entregar o IRS este ano?"
    ask_amalia.py --thread my-session "follow-up question"
    echo "question" | ask_amalia.py --stdin
"""
from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

DEFAULT_BASE_URL = "https://api.iaedu.pt/agent-chat"

_API_KEY_RE = re.compile(r"API\s*Key\s*:\s*(\S+)", re.IGNORECASE)
_CHANNEL_RE = re.compile(r"Channel\s*ID\s*:\s*(\S+)", re.IGNORECASE)
_AGENT_ID_RE = re.compile(r"/agent/([A-Za-z0-9_-]+)")


def _load_creds() -> dict[str, str]:
    creds = {
        "api_key": os.environ.get("AMALIA_API_KEY", ""),
        "agent_id": os.environ.get("AMALIA_AGENT_ID", ""),
        "channel_id": os.environ.get("AMALIA_CHANNEL_ID", ""),
        "base_url": os.environ.get("AMALIA_BASE_URL", DEFAULT_BASE_URL),
    }
    if not all(creds[k] for k in ("api_key", "agent_id", "channel_id")):
        for path in (Path.cwd() / "creds.txt", Path.home() / ".amalia" / "creds.txt"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if not creds["api_key"] and (m := _API_KEY_RE.search(text)):
                creds["api_key"] = m.group(1)
            if not creds["channel_id"] and (m := _CHANNEL_RE.search(text)):
                creds["channel_id"] = m.group(1)
            if not creds["agent_id"] and (m := _AGENT_ID_RE.search(text)):
                creds["agent_id"] = m.group(1)
            break

    missing = [
        f"AMALIA_{k.upper()}"
        for k in ("api_key", "agent_id", "channel_id")
        if not creds[k]
    ]
    if missing:
        sys.exit(
            f"ask_amalia: missing credentials: {', '.join(missing)}. "
            "Set the env vars, or place creds.txt at ~/.amalia/creds.txt."
        )
    return creds


def _build_multipart(fields: list[tuple[str, str]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts: list[bytes] = []
    for name, value in fields:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def ask(question: str, thread_id: str) -> str:
    creds = _load_creds()
    body, boundary = _build_multipart(
        [
            ("channel_id", creds["channel_id"]),
            ("thread_id", thread_id),
            ("user_info", "{}"),
            ("message", question),
        ]
    )
    url = f"{creds['base_url'].rstrip('/')}//api/v1/agent/{creds['agent_id']}/stream"
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "x-api-key": creds["api_key"],
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    tokens: list[str] = []
    final_text: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = ev.get("type")
                content = ev.get("content")
                if t == "token" and isinstance(content, str):
                    tokens.append(content)
                elif t == "message" and isinstance(content, dict):
                    txt = content.get("content")
                    if isinstance(txt, str) and txt:
                        final_text = txt
    except urllib.error.HTTPError as e:
        body_preview = e.read()[:500].decode("utf-8", "replace")
        if e.code in (401, 403):
            sys.exit(f"ask_amalia: auth failed (HTTP {e.code}). Check AMALIA_API_KEY.")
        sys.exit(f"ask_amalia: HTTP {e.code}: {body_preview}")
    except urllib.error.URLError as e:
        sys.exit(f"ask_amalia: network error: {e.reason}")

    return final_text if final_text is not None else "".join(tokens)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="ask_amalia",
        description="Ask Amália a Portugal-specific question and print the answer.",
    )
    p.add_argument("question", nargs="*", help="The question. Omit when using --stdin.")
    p.add_argument("--stdin", action="store_true", help="Read the question from stdin.")
    p.add_argument(
        "--thread",
        help="Reuse a thread id for follow-up questions (default: random).",
    )
    args = p.parse_args(argv)

    if args.stdin:
        question = sys.stdin.read().strip()
    else:
        question = " ".join(args.question).strip()
    if not question:
        p.error("no question given (provide POSITIONAL or --stdin)")

    thread_id = args.thread or secrets.token_urlsafe(15)
    answer = ask(question, thread_id)
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
