# ODBE-Forge

**Autonomous Hierarchical Multi-LLM Agent with Deception Detection**

ODBE-Forge coordinates specialized sub-agents in a hierarchy, cross-checks their outputs, and flags deception, contradiction, or low-trust signals before you act on them.

| | |
|---|---|
| **Python** | 3.10+ |
| **License** | MIT |
| **Mode** | Offline heuristics by default; optional OpenAI / Anthropic backends |

---

## Features

- **Hierarchical agents** — Planner → Researchers → Critic → Synthesizer
- **Deception detector** — contradiction scoring, confidence inflation, source-free claims, urgency pressure
- **Safety gate** — blocks high-risk tool-like actions unless explicitly allowed
- **Multi-backend** — offline mock, OpenAI-compatible, or Anthropic (env-driven)
- **CLI + library** — `python run.py "your task"` or import `odbe_forge_v3`
- **Tests** — `pytest` for detector and pipeline smoke tests

## Quick start

```bash
git clone https://github.com/Stijnman/ODBE-Forge.git
cd ODBE-Forge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Offline demo (no API keys)
python run.py "Summarize risks of shipping AI agents without audit logs"

# With OpenAI-compatible API
export OPENAI_API_KEY=sk-...
export ODBE_BACKEND=openai
python run.py "Draft a multi-step research plan for MCP security"
```

## Configuration

| Variable | Default | Meaning |
|----------|---------|---------|
| `ODBE_BACKEND` | `offline` | `offline` \| `openai` \| `anthropic` |
| `OPENAI_API_KEY` | — | OpenAI or compatible key |
| `OPENAI_BASE_URL` | OpenAI default | Optional proxy / local gateway |
| `ANTHROPIC_API_KEY` | — | Anthropic key |
| `ODBE_MAX_ROUNDS` | `3` | Hierarchy depth / critique rounds |
| `ODBE_DECEPTION_THRESHOLD` | `0.55` | Flag if score ≥ threshold |

Copy `.env.example` → `.env` if preferred.

## Architecture

```
User task
   │
   ▼
Planner (decompose)
   │
   ├─► Researcher A
   ├─► Researcher B
   │
   ▼
Critic (cross-check)
   │
   ▼
DeceptionDetector ──► SafetyGate
   │
   ▼
Synthesizer → final report + risk flags
```

## Library usage

```python
from odbe_forge_v3 import ODBEForge

forge = ODBEForge()
result = forge.run("Evaluate this claim: 'this coin will 100x tomorrow'")
print(result.report)
print(result.deception.score, result.deception.flags)
```

## Project layout

```
ODBE-Forge/
├── run.py                 # CLI entry
├── odbe_forge_v3.py       # orchestration
├── deception_detector.py  # trust / deception scoring
├── safety.py              # action policy gate
├── requirements.txt
├── tests/
└── LICENSE
```

## Ethics

This project is for **defensive analysis and research coordination**. It does not generate exploits, social-engineering scripts, or automated fraud tooling. Use on content you have a right to process.

## License

MIT © 2026 Stijnman
