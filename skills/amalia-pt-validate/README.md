# amalia-pt-validate

A drop-in **Claude Code skill** (also adaptable to Codex / generic agents) that lets the assistant consult **Amália** — the Portuguese LLM — to validate Portugal-specific answers (law, taxes, public services, pt-PT terminology, etc.).

The skill is a thin wrapper: it tells the agent **when** to consult Amália and instructs it to call the [`amalia` CLI](../../amalia-cli) — no duplicated API logic, no separate script. Bug fixes in the SDK propagate automatically.

## What it gives the agent

A precise rule for **when** to consult Amália (Portugal-specific facts where accuracy matters), **how** to call `amalia --no-stream`, and **how to interpret** the answer (second opinion, cross-check load-bearing facts, surface disagreements). See [`SKILL.md`](./SKILL.md) for the full instructions Claude follows.

## Prerequisite: install the CLI

The skill calls `amalia` (the bundled CLI), so you need it on `PATH` first. From a clone of [the amalia repo](https://github.com/alfmatos/amalia):

```bash
pip install -e ./amalia-sdk -e ./amalia-cli
amalia --help    # sanity check
```

You also need credentials — either env vars (`AMALIA_API_KEY`, `AMALIA_AGENT_ID`, `AMALIA_CHANNEL_ID`) or `~/.amalia/creds.txt`. See the [main README](../../README.md#configure) for details. Credentials come from [iaedu.pt](https://iaedu.pt/pt) and are **never** stored in this skill.

## Install the skill

### Claude Code — user level (works in every project)

```bash
mkdir -p ~/.claude/skills
cp -r path/to/amalia/skills/amalia-pt-validate ~/.claude/skills/
```

### Claude Code — project level (only inside one repo)

```bash
mkdir -p .claude/skills
cp -r path/to/amalia/skills/amalia-pt-validate .claude/skills/
git add .claude/skills/amalia-pt-validate
```

Project-level skills travel with the repo, so collaborators get them automatically.

### Codex / OpenAI Agents

Codex doesn't have an identical `SKILL.md` primitive. Two equivalent patterns:

1. **Inline the rule in `AGENTS.md`** at the project root: copy the "When to invoke" and "How to invoke" sections of `SKILL.md` into a "## Portuguese (PT) fact-checking" section. Same `amalia` CLI does the work.
2. **Register `amalia` as a tool**: wrap the CLI as a function tool that takes `question: str` and returns the CLI's stdout. Then the model can call it explicitly.

The trigger rule and the answer-handling guidance are the same; only the host-specific instruction format changes.

## Verify the install

From any directory:

```bash
amalia --no-stream "Qual o IVA padrão em Portugal continental? Responde só com a percentagem."
# → 23%
```

If you get `23%` (or `23 %`), the toolchain is working end-to-end and Claude can use the skill. If `amalia: command not found`, finish the prerequisite step above. If `amalia: missing required Amália config`, fix credentials.

## When the agent will use it

After install, Claude will autonomously invoke this skill when its description matches the user's question — typically anything specific to Portuguese law, taxes, public services, education, regional administration, holidays, gastronomia, or pt-PT terminology. It will **not** invoke it for code, generic questions, or other lusophone countries (Brazil, Angola, etc.).

## Files

```
amalia-pt-validate/
├── SKILL.md       # The rule the agent follows (when/how/interpret)
└── README.md      # This file
```

That's it. No bundled script — the skill leans on `amalia-cli` so all API logic lives in one place.
