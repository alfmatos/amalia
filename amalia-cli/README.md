# amalia-cli

One-shot command-line client for **Amália** (Portuguese LLM).

## Install

Install the SDK first, then this:

```bash
pip install -e ../amalia-sdk
pip install -e .
```

## Use

```bash
# Direct prompt — streams to stdout as Amália responds:
amalia "Qual a capital de Portugal?"

# Read prompt from stdin (great for piping):
echo "Resume isto em 3 linhas: ..." | amalia --stdin

# Read prompt from a file:
amalia -f question.txt

# Buffered output (no streaming) — handy for scripts:
amalia --no-stream "Diz olá."

# Reuse a thread id across calls so Amália remembers context:
amalia --thread my-session "Como te chamas?"
amalia --thread my-session "Repete o teu nome."

# Attach an image:
amalia --image cat.jpg "O que vês?"

# Inspect raw stream events (debugging):
amalia --json "olá"
```

### Exit codes

- `0` — success
- `1` — API / config error
- `2` — argparse error
