# Project: Presales Copilot

An AI copilot for the presales lifecycle. 4 of 7 modules built: RFP Analyzer,
Client Research, Knowledge Search, Proposal Generator. Plus a stdlib web UI.

## Who you're working with

The developer is a beginner. Explain every change in simple terms after making it.
Prefer clear, readable code over clever code.

## Architecture

- `cli.py` — command entry point; each subcommand calls one module
- `copilot/` — one file per module, each exposing a simple function
- `webapp.py` — stdlib HTTP server, four tabs, no frameworks
- `sample_data/` — sample RFP, capability catalog, asset library, canned demo outputs
- `out/` — generated artifacts (gitignored)

## Rules

- Every module must have a **demo mode** that works with no API key and no network.
  Canned outputs live in `sample_data/demo_*`.
- **Grounding is non-negotiable**: AI output may only claim a capability it can cite
  by asset/catalog ID. No evidence means "gap" or "[TO VERIFY]" — never an invented claim.
- **Model tiering**: Opus-class for analysis and drafting, Sonnet-class for research,
  Haiku-class for classification. Expose via a `--model` flag.
- Prefer the Python standard library. Ask before adding a dependency.
- Never hardcode API keys or secrets. Read from environment variables.
- Keep function signatures stable — `webapp.py` and other modules depend on them.
- Write a test for every new function.

## Commands

```bash
python cli.py rfp sample_data/sample_rfp.txt --demo
python cli.py search "claims migration guidewire" --industry Insurance
python cli.py propose --demo
python cli.py research "Acme Insurance Group" --demo
python cli.py ui
```

## Not yet built

Meeting Intelligence, Discovery Assistant, Solution Recommender, embeddings-based
retrieval, database persistence, MCP connectors, SSO/RBAC, approval workflow, eval suite.
