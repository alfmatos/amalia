# amalia-chat

Interactive terminal chat client for **Amália** (Portuguese LLM). Streams replies live, then re-renders them as Markdown for nice formatting. One thread per session means Amália remembers context across turns.

## Install

```bash
pip install -e ../amalia-sdk
pip install -e .
```

## Run

```bash
amalia-chat
```

You'll get a REPL prompt. Type a message, press Enter, watch Amália reply. Ctrl-D to exit.

### Slash commands

| Command          | What it does                                   |
| ---------------- | ---------------------------------------------- |
| `/new`           | Start a fresh thread (clears server memory)    |
| `/thread [id]`   | Show current thread id, or switch to a given id |
| `/image <path>`  | Attach an image to the next message            |
| `/save <file>`   | Dump the transcript to a Markdown file         |
| `/help`          | Show command help                              |
| `/exit`          | Quit (or Ctrl-D)                               |

### History

Input history is persisted to `~/.amalia/history` so you can recall previous prompts with the up arrow.
