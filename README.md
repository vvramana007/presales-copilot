# Presales Copilot — Prototype v2

Working prototype covering **4 of 7 modules** of the AI-Powered Presales Copilot:

1. **RFP Analyzer** — extracts every requirement (with clause refs), classifies mandatory vs. desirable, maps to the capability catalog, flags gaps and commercial red-lines. Outputs compliance matrix (CSV) + gap report. Accepts **PDF, DOCX, or TXT**.
2. **Client Research** — pre-meeting brief (news, financials, tech signals, talking points) via Claude's web search.
3. **Knowledge Search** — hybrid keyword + metadata search over the internal asset library (past proposals, case studies, reference architectures, boilerplate) with relevance ranking and citations. Fully offline.
4. **Proposal Generator** — drafts grounded proposal sections from the compliance matrix; every claim cites an asset ID `[AST-xxx]`; unsupported points become `[TO VERIFY]` instead of invented claims.

Plus a **web UI** (zero dependencies — Python stdlib only) for live demos.

## Setup

```bash
pip install anthropic          # only needed for live mode
export ANTHROPIC_API_KEY=...   # Windows: set ANTHROPIC_API_KEY=...
```

Demo mode needs **nothing** — no key, no network, no packages beyond Python 3.9+.

## Web UI (best for demos)

```bash
python cli.py ui               # demo mode -> http://localhost:8765
python cli.py ui --live        # live Claude API
```

Four tabs: RFP Analyzer (run analysis, see color-coded matrix + gap report), Knowledge Search (query + industry/type filters), Proposal Draft (generate grounded draft), Client Research (company brief).

## CLI

```bash
# 1. Analyze an RFP (pdf/docx/txt)
python cli.py rfp sample_data/sample_rfp.txt --demo
python cli.py rfp path/to/real_rfp.pdf                 # live mode parses PDF/DOCX

# 2. Search the asset library (always offline)
python cli.py search "claims migration guidewire" --industry Insurance
python cli.py search "fraud scoring" --type reference_architecture

# 3. Draft a proposal from the compliance matrix
python cli.py propose --demo
python cli.py propose --client "Acme Insurance Group"  # live

# 4. Client research brief
python cli.py research "Acme Insurance Group" --demo
```

Outputs land in `./out/`: `compliance_matrix.csv`, `gap_report.md`, `knowledge_search_results.md`, `proposal_draft.md`, `client_brief_<company>.md`.

## Suggested 5-minute demo script

1. Open `sample_data/sample_rfp.txt` — "someone reads these manually today; real ones are 200 pages"
2. `python cli.py ui` → RFP Analyzer tab → Run analysis → show 16 requirements, 13 mandatory, 3 gaps, red rows = bid risks (unlimited liability, IP transfer caught automatically)
3. Knowledge Search tab → search "claims guidewire migration" → instant ranked hits from past wins
4. Proposal Draft tab → Generate → point at the `[AST-xxx]` citations: "it is not allowed to claim anything it can't cite"
5. Client Research tab → "every AE walks into every meeting with this"
6. Close: "Four modules working. 8 weeks to run this on our real RFPs with a 95% accuracy gate."

## Design principles carried into the full product

- **Grounding**: coverage/claims only with a citable source; gaps declared honestly
- **Demo mode**: canned outputs so live demos can never fail on stage
- **Model tiering**: Opus for analysis/drafting, Sonnet for research (see `--model`)
- **Same interfaces as production**: Knowledge Search's `search() -> ranked assets with citations` is exactly what the pgvector-backed version will expose

## Not yet built (production scope)

Meeting Intelligence, Discovery Assistant, real vector embeddings, MCP connectors (CRM/SharePoint/Zoom), SSO/RBAC/permission trimming, approval workflow, eval suite, OCR for scanned PDFs. See the Solution Design document, Sections 5–8 and 11.
