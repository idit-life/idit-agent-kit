# idit-agent-kit

Drop-in library for AI agents to sign entries to a [Personal Idit](https://github.com/idit-life/personal-idit) chain.

**Status: alpha.** This is a thin HTTP client wrapper. It has not been independently security audited. Review the code before use.

## Install

```bash
pip install idit-agent-kit
```

## Quick start

```python
from idit_agent import IditAgent

agent = IditAgent(signer="my-agent", model="gpt-4o")
entry = agent.mint("Completed the quarterly report analysis.")
print(entry["entry_id"])  # id-a3f8b2c1d4e5f6a7
```

## Setup

Your Idit server needs a signing key for the agent:

```bash
idit init my-agent    # creates the keypair
idit serve            # starts the API
```

Then your agent can mint from anywhere that can reach the server.

## API

```python
agent = IditAgent(
    signer="my-agent",       # key name on the Idit server
    server="http://localhost:18793",  # server URL
    model="claude-opus-4-6",    # model identifier (stored in metadata)
    node="local",             # node identifier
    api_key="your-api-key",   # optional, for servers with IDIT_API_KEY set
)

# Mint entries by type
agent.note("Something worth recording.")
agent.memory("User prefers dark mode.")
agent.decision("Switched from REST to GraphQL.")
agent.milestone("Deployed v2.0 to production.")
agent.log("Morning report: all systems nominal.")

# Or use mint() directly for custom types
agent.mint("Battle plan drafted.", entry_type="battle_plan", description="Q2 strategy")

# Chain operations
agent.status()   # chain stats
agent.verify()   # verify all hashes
agent.health()   # server health check
```

## Works with any agent framework

```python
# OpenAI function calling
def record_decision(decision_text):
    agent.decision(decision_text)

# LangChain tool
from langchain.tools import tool

@tool
def mint_to_chain(content: str, entry_type: str = "note") -> str:
    """Record something to the permanent chain."""
    entry = agent.mint(content, entry_type=entry_type)
    return f"Minted: {entry['entry_id']}"

# CrewAI, AutoGen, or anything else — it's just HTTP
```

## Context manager

```python
with IditAgent(signer="my-agent", model="llama3.3:70b") as agent:
    agent.note("Session started.")
    # do work...
    agent.milestone("Task completed.")
```

## What gets recorded

Every entry includes:
- **Content** — whatever text you mint
- **SHA-256 hash** — linked to the previous entry
- **Ed25519 signature** — cryptographic proof of who signed it
- **Model name** — which AI model created the entry
- **Timestamp** — UTC, immutable
- **Entry type** — note, memory, decision, milestone, etc.

The chain is append-only. Nothing can be deleted or modified after signing.

## Requirements

- A running [Personal Idit](https://github.com/idit-life/personal-idit) server
- Python 3.10+
- httpx

## License

MIT
