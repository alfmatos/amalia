# amalia-pt-validate

A drop-in **Claude Code skill** (also usable from Codex / generic agents) that lets the assistant consult **Amália** — the Portuguese LLM — to validate Portugal-specific answers (law, taxes, public services, pt-PT terminology, etc.).

The skill bundles a tiny pure-stdlib Python script (`scripts/ask_amalia.py`) that calls the Amália API and prints the answer. No `pip install` required.

## What it gives the agent

A precise rule for **when** to consult Amália (Portugal-specific facts where accuracy matters), **how** to call the script, and **how to interpret** the answer (second opinion, cross-check load-bearing facts, surface disagreements). See [`SKILL.md`](./SKILL.md) for the full instructions Claude follows.

## Install

### Claude Code — user level (works in every project)

```bash
mkdir -p ~/.claude/skills
cp -r path/to/this/repo/skills/amalia-pt-validate ~/.claude/skills/
```

### Claude Code — project level (only inside one repo)

```bash
mkdir -p .claude/skills
cp -r path/to/this/repo/skills/amalia-pt-validate .claude/skills/
git add .claude/skills/amalia-pt-validate
```

Project-level skills travel with the repo, so collaborators get them automatically.

### Codex / OpenAI Agents

Codex doesn't have an identical `SKILL.md` primitive. Two equivalent patterns:

1. **Inline the rule in `AGENTS.md`** at the project root: copy the "When to invoke" and "How to invoke" sections of `SKILL.md` into a "## Portuguese (PT) fact-checking" section, and add `~/.codex/skills/amalia-pt-validate/scripts/ask_amalia.py` to the project — same script works.
2. **Register as a tool**: wrap `ask_amalia.py` as a function tool that takes `question: str` and returns the script's stdout. Then the model can call it explicitly.

The script itself is the portable core; the instructions are the only thing whose format differs across hosts.

## Configure credentials

Either env vars in your shell profile:

```bash
export AMALIA_API_KEY=sk-usr-...
export AMALIA_AGENT_ID=<your-agent-id>
export AMALIA_CHANNEL_ID=<your-channel-id>
```

…or a `creds.txt` at `~/.amalia/creds.txt`:

```
Endpoint: https://api.iaedu.pt/agent-chat//api/v1/agent/<your-agent-id>/stream
API Key: sk-usr-...
ChannelID: <your-channel-id>
```

Credentials come from [iaedu.pt](https://iaedu.pt/pt). They are **never** stored in this skill.

## Verify the install

From any directory:

```bash
python3 ~/.claude/skills/amalia-pt-validate/scripts/ask_amalia.py "Qual o IVA padrão em Portugal continental? Responde só com a percentagem."
# → 23%
```

If you get `23%` (or `23 %`), it's working. If you get a `missing credentials` or `auth failed` message, fix that first.

## When the agent will use it

After install, Claude will autonomously invoke this skill when its description matches the user's question — typically anything specific to Portuguese law, taxes, public services, education, regional administration, holidays, gastronomia, or pt-PT terminology. It will **not** invoke it for code, generic questions, or other lusophone countries (Brazil, Angola, etc.).

## Files

```
amalia-pt-validate/
├── SKILL.md               # The rule the agent follows
├── README.md              # This file (human install/usage)
└── scripts/
    └── ask_amalia.py      # Self-contained API caller (stdlib only)
```
