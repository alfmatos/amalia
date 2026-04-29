from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from amalia_sdk import AmaliaClient, AmaliaError, load_config
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

HISTORY_PATH = Path.home() / ".amalia" / "history"
console = Console()


class ChatSession:
    def __init__(self, client: AmaliaClient):
        self.client = client
        self.thread_id = client.new_thread_id()
        self.turns = 0
        self.transcript: list[tuple[str, str]] = []  # (role, text)
        self.pending_image: Optional[Path] = None

    # --- public command handlers ---

    def cmd_new(self, _arg: str) -> None:
        self.thread_id = self.client.new_thread_id()
        self.turns = 0
        self.transcript.clear()
        console.print(f"[dim]New thread: {self.thread_id}[/dim]")

    def cmd_thread(self, arg: str) -> None:
        if arg:
            self.thread_id = arg
            self.turns = 0
            self.transcript.clear()
            console.print(f"[dim]Switched to thread {self.thread_id} (history reset locally)[/dim]")
        else:
            console.print(f"[dim]thread_id: {self.thread_id}  ·  turns: {self.turns}[/dim]")

    def cmd_image(self, arg: str) -> None:
        if not arg:
            console.print("[yellow]usage: /image <path>[/yellow]")
            return
        path = Path(arg).expanduser()
        if not path.is_file():
            console.print(f"[red]not a file: {path}[/red]")
            return
        self.pending_image = path
        console.print(f"[dim]Will attach {path.name} to next message[/dim]")

    def cmd_save(self, arg: str) -> None:
        if not arg:
            console.print("[yellow]usage: /save <file>[/yellow]")
            return
        out = Path(arg).expanduser()
        out.write_text(_render_transcript(self.thread_id, self.transcript), encoding="utf-8")
        console.print(f"[dim]Wrote {out}[/dim]")

    def cmd_help(self, _arg: str) -> None:
        console.print(
            "[dim]Commands:\n"
            "  /new                  start a fresh thread\n"
            "  /thread [id]          show or switch thread id\n"
            "  /image <path>         attach an image to the next message\n"
            "  /save <file>          dump transcript to a file\n"
            "  /help                 show this help\n"
            "  /exit                 quit (or Ctrl-D)\n"
            "[/dim]"
        )

    # --- main turn ---

    def send(self, prompt: str) -> None:
        image = self.pending_image
        self.pending_image = None
        self.transcript.append(("user", prompt))

        chunks: list[str] = []
        final_text: Optional[str] = None

        try:
            with Live(console=console, refresh_per_second=20, transient=True) as live:
                live.update(_streaming_panel(""))
                for ev in self.client.stream(prompt, thread_id=self.thread_id, image=image):
                    if ev.type == "token" and isinstance(ev.content, str):
                        chunks.append(ev.content)
                        live.update(_streaming_panel("".join(chunks)))
                    elif ev.type == "message" and isinstance(ev.content, dict):
                        text = ev.content.get("content")
                        if isinstance(text, str) and text:
                            final_text = text
        except AmaliaError as e:
            console.print(f"[red]error:[/red] {e}")
            return

        reply = final_text if final_text is not None else "".join(chunks)
        self.transcript.append(("amalia", reply))
        self.turns += 1
        # Re-render the final reply as Markdown for nice formatting.
        console.print(Panel(Markdown(reply), title="Amália", border_style="cyan"))


def _streaming_panel(text: str) -> Panel:
    body = Text(text or "…", style="dim")
    return Panel(body, title="Amália (streaming)", border_style="grey50")


def _render_transcript(thread_id: str, turns: list[tuple[str, str]]) -> str:
    lines = [f"# Amália transcript", f"thread_id: {thread_id}", f"saved: {datetime.now().isoformat(timespec='seconds')}", ""]
    for role, text in turns:
        lines.append(f"## {role}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


COMMANDS = {
    "/new": "cmd_new",
    "/thread": "cmd_thread",
    "/image": "cmd_image",
    "/save": "cmd_save",
    "/help": "cmd_help",
}


def main(argv: list[str] | None = None) -> int:
    try:
        client = AmaliaClient(load_config())
    except AmaliaError as e:
        print(f"amalia-chat: {e}", file=sys.stderr)
        return 1

    session = ChatSession(client)
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    prompt_session: PromptSession = PromptSession(history=FileHistory(str(HISTORY_PATH)))

    console.print(
        Panel(
            Text.from_markup(
                "[bold]Amália[/bold] — Portuguese LLM\n"
                "Type your message and press Enter. [dim]/help[/dim] for commands, "
                "[dim]Ctrl-D[/dim] to exit."
            ),
            border_style="cyan",
        )
    )
    console.print(f"[dim]thread: {session.thread_id}[/dim]\n")

    while True:
        try:
            line = prompt_session.prompt(
                HTML(f"<ansigreen>amalia</ansigreen> <ansiwhite>›</ansiwhite> ")
            )
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]bye.[/dim]")
            return 0

        text = line.strip()
        if not text:
            continue

        if text in {"/exit", "/quit"}:
            return 0
        if text.startswith("/"):
            head, _, rest = text.partition(" ")
            handler = COMMANDS.get(head)
            if handler is None:
                console.print(f"[yellow]unknown command: {head}  (try /help)[/yellow]")
            else:
                getattr(session, handler)(rest.strip())
            continue

        session.send(text)

    # unreachable
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
