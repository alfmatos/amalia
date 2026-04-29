# amalia-sdk

Tiny synchronous Python client for **Amália**, the Portuguese LLM exposed via the IAEdu agent API.

## Install

```bash
pip install -e .
```

## Configure

Either set environment variables:

```bash
export AMALIA_API_KEY=sk-usr-...
export AMALIA_AGENT_ID=<your-agent-id>
export AMALIA_CHANNEL_ID=<your-channel-id>
# optional: export AMALIA_BASE_URL=https://api.iaedu.pt/agent-chat
```

…or drop a `creds.txt` (in the format provided with your account) in the current directory or `~/.amalia/creds.txt`. The SDK reads env first, then falls back to the file.

## Use

```python
from amalia_sdk import AmaliaClient, load_config

client = AmaliaClient(load_config())
thread = client.new_thread_id()

# One-shot:
print(client.complete("Olá, quem és?", thread_id=thread))

# Streaming:
for ev in client.stream("Conta-me uma piada curta.", thread_id=thread):
    if ev.type == "token":
        print(ev.content, end="", flush=True)
print()
```

Reusing the same `thread_id` across calls preserves conversation memory server-side.

### Image input

```python
client.complete("O que vês nesta imagem?", thread_id=thread, image="cat.jpg")
```

### Errors

- `AmaliaAuthError` — bad/missing API key (401/403).
- `AmaliaHTTPError` — other non-2xx responses; `.status_code` and `.body` are populated.
- `AmaliaError` — base class, also raised for missing config or network issues.
