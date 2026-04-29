---
name: amalia-pt-validate
description: Validate or clarify Portugal-specific (pt-PT) facts by consulting Amália, a Portuguese LLM. Use this whenever the user asks about Portuguese law, taxes (IRS, IRC, IVA, IMI, IMT, IUC), social security, public services (Finanças/AT, Segurança Social, SNS, Loja do Cidadão, Multibanco, MB Way, chave móvel digital), the education system (matrículas, escolaridade obrigatória, exames nacionais, ensino superior), local government (autarquias, freguesias, câmaras), regions (NUTS, distritos, Açores, Madeira), official procedures, holidays (feriados nacionais e municipais), gastronomia, geography, history, or pt-PT terminology and orthography (vs pt-BR) — and accuracy matters. Skip for code, generic LLM questions, non-Portuguese topics, or trivial small talk. Calls a billed API, so use it as a targeted second opinion, not for batch lookups.
---

# Amália — Portuguese (PT) fact-check skill

Amália is a Portuguese-language LLM (`amalia-llm/amalia-v1.0`) trained with extra weight on European-Portuguese sources. Use it as a **second opinion** for Portugal-specific factual claims that are easy to get wrong from generic training data.

## When to invoke this skill

Invoke when **all** of these hold:

1. The user's question or your draft answer concerns something **specific to Portugal** — its laws, taxes, public institutions, education system, regional administration, holidays, cultural conventions, local terminology, or recent local context.
2. **Accuracy matters** — the user is going to act on the answer (deadlines, statutes, procedures, money), or is explicitly asking you to verify.
3. The fact is the kind of thing a generic English-trained model often gets subtly wrong (recent law revisions, pt-PT vs pt-BR phrasing, AT vs Receita Federal terminology, current holiday list, etc.).

Examples that match:
- "Qual é o prazo de entrega do IRS este ano?"
- "Quantos dias de férias dá o Código do Trabalho a um trabalhador no primeiro ano?"
- "Como se diz 'screen' em pt-PT — ecrã ou tela?"
- "O 25 de Abril é feriado obrigatório no setor privado?"
- "Posso constituir uma empresa unipessoal por quotas com €1 de capital social?"
- "Qual o limite de isenção de IVA para trabalhadores independentes?"

Examples that **don't** match — do NOT invoke:
- General programming, math, English-language questions.
- Questions about Brazil, Angola, Mozambique, or other lusophone countries (Amália is pt-PT focused).
- "What's the capital of Portugal?" — your own training is fine.
- Brainstorming, opinion, creative writing.

## How to invoke

The skill uses the `amalia` CLI (from the [amalia-cli](https://github.com/alfmatos/amalia/tree/main/amalia-cli) package). Run:

```bash
amalia --no-stream "<question in pt-PT>"
```

For follow-up questions in the same task, reuse the same `--thread` id so Amália keeps context server-side:

```bash
amalia --no-stream --thread sess-001 "Quantos dias de férias por ano?"
amalia --no-stream --thread sess-001 "E se for o primeiro ano de trabalho?"
```

Pick any string for the thread id; something like `pt-validate-<short-random>` works well. Use a fresh thread for unrelated questions.

`--no-stream` makes the CLI buffer the full reply and print once — easier to capture than the streaming default. The CLI exits `0` on success, `1` on API/config errors.

### Phrasing tips

- Ask in **European Portuguese** for best results. If the user asked in English, translate the question before sending — Amália responds in pt-PT.
- Be specific. "Qual o IVA padrão em Portugal continental?" returns "23%". "Qual o IVA?" returns a paragraph.
- Constrain the format when you only need a value: "Responde só com a percentagem." / "Responde numa frase."

## How to use the answer

1. **Treat it as a second opinion**, not as ground truth. Amália is an LLM and can hallucinate.
2. **Cross-check anything load-bearing** (statute numbers, exact deadlines, monetary thresholds) against an authoritative source — `dre.pt` (Diário da República), `info.portaldasfinancas.gov.pt`, `seg-social.pt`, the relevant ministry's site — before the user takes irreversible action. Mention the source you checked.
3. **If Amália contradicts your draft answer**, surface the disagreement to the user. Show both, explain which you trust more and why. Don't silently overwrite.
4. **Quote it directly** when the user asks for the canonical pt-PT phrasing or wording — Amália's pt-PT output is more reliable than your translation.
5. **Don't hammer the API**. One or two targeted calls per task is fine; ten in a loop is wasteful (and billed).

## Failure handling

If `amalia` exits non-zero, stderr explains why:

- `command not found: amalia` → the CLI isn't installed. Tell the user: `pip install amalia-cli` (or follow the [repo install instructions](https://github.com/alfmatos/amalia#install)). Skip Amália consultation for this turn.
- `amalia: missing required Amália config: ...` → credentials aren't set. Tell the user how to configure them (env vars or `~/.amalia/creds.txt`, see Setup below) and stop.
- `amalia: Authentication failed (HTTP 401)` → API key is wrong or revoked.
- `amalia: Network error ...` → transient; you may retry once.
- `amalia: HTTP 5xx` → upstream is down; report and continue without Amália's input.

In all failure cases, fall back to your own best answer and **explicitly tell the user** Amália couldn't be consulted, so they know your answer wasn't validated.

## Setup (one-time, for the user)

The skill expects two things to already be in place — guide the user through them only if a call fails.

**1. Install the CLI** (one-line, from the [amalia repo](https://github.com/alfmatos/amalia)):

```bash
pip install -e ./amalia-sdk -e ./amalia-cli   # from a clone of the repo
```

This puts `amalia` on `PATH`.

**2. Provide credentials.** Either env vars in their shell profile:

```bash
export AMALIA_API_KEY=sk-usr-...
export AMALIA_AGENT_ID=<your-agent-id>
export AMALIA_CHANNEL_ID=<your-channel-id>
```

Or a `creds.txt` at `~/.amalia/creds.txt` (the format their account ships with). Credentials come from [iaedu.pt](https://iaedu.pt/pt). The skill does **not** ship credentials.
