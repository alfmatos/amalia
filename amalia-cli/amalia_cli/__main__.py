from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from amalia_sdk import AmaliaClient, AmaliaError, load_config


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="amalia",
        description="Send a one-off prompt to Amália and print the reply.",
    )
    p.add_argument("prompt", nargs="?", help="The prompt text. Omit when using --stdin or -f.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--stdin", action="store_true", help="Read the prompt from stdin.")
    src.add_argument("-f", "--file", type=Path, help="Read the prompt from FILE.")
    p.add_argument("--image", type=Path, help="Attach an image to the message.")
    p.add_argument("--thread", help="Reuse a thread id (default: random per call).")
    p.add_argument("--no-stream", action="store_true", help="Buffer and print at end.")
    p.add_argument("--json", action="store_true", help="Emit raw NDJSON events (debugging).")
    p.add_argument("--user-id", help="Optional user_id for the request.")
    p.add_argument(
        "--user-context",
        action="append",
        default=[],
        metavar="KEY=VAL",
        help="Add a key/value to user_context (repeatable).",
    )
    return p


def _resolve_prompt(args: argparse.Namespace) -> str:
    if args.stdin:
        return sys.stdin.read()
    if args.file:
        return args.file.read_text(encoding="utf-8")
    if args.prompt is not None:
        return args.prompt
    raise SystemExit("amalia: no prompt given (provide POSITIONAL, --stdin, or -f FILE)")


def _parse_user_context(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"amalia: --user-context expects KEY=VAL, got {item!r}")
        k, v = item.split("=", 1)
        out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    prompt = _resolve_prompt(args)

    try:
        client = AmaliaClient(load_config())
    except AmaliaError as e:
        print(f"amalia: {e}", file=sys.stderr)
        return 1

    thread_id = args.thread or client.new_thread_id()
    user_context = _parse_user_context(args.user_context) or None

    try:
        if args.json:
            for ev in client.stream(
                prompt,
                thread_id=thread_id,
                image=args.image,
                user_id=args.user_id,
                user_context=user_context,
            ):
                print(json.dumps(ev.raw, ensure_ascii=False))
        elif args.no_stream:
            text = client.complete(
                prompt,
                thread_id=thread_id,
                image=args.image,
                user_id=args.user_id,
                user_context=user_context,
            )
            print(text)
        else:
            wrote_anything = False
            for ev in client.stream(
                prompt,
                thread_id=thread_id,
                image=args.image,
                user_id=args.user_id,
                user_context=user_context,
            ):
                if ev.type == "token" and isinstance(ev.content, str):
                    sys.stdout.write(ev.content)
                    sys.stdout.flush()
                    wrote_anything = True
            if wrote_anything:
                sys.stdout.write("\n")
    except AmaliaError as e:
        print(f"\namalia: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
