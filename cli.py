#!/usr/bin/env python3
"""Presales Copilot prototype CLI."""
import argparse
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from copilot import rfp_analyzer, client_research, knowledge_search, proposal_generator, parsers  # noqa: E402


def main():
    ap = argparse.ArgumentParser(prog="presales-copilot",
                                 description="Presales Copilot prototype")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rfp = sub.add_parser("rfp", help="Analyze an RFP -> compliance matrix + gap report")
    rfp.add_argument("rfp_file", help="RFP file (.pdf, .docx, or .txt)")
    rfp.add_argument("--catalog", default="sample_data/capability_catalog.json")
    rfp.add_argument("--model", default=rfp_analyzer.OPUS_MODEL)
    rfp.add_argument("--out", default="out")
    rfp.add_argument("--demo", action="store_true", help="Offline demo (no API key)")

    res = sub.add_parser("research", help="Generate a pre-meeting client brief")
    res.add_argument("company")
    res.add_argument("--context", default="")
    res.add_argument("--model", default=client_research.SONNET_MODEL)
    res.add_argument("--out", default="out")
    res.add_argument("--demo", action="store_true")

    srch = sub.add_parser("search", help="Search the internal asset library")
    srch.add_argument("query")
    srch.add_argument("--industry", default=None)
    srch.add_argument("--type", dest="asset_type", default=None,
                      help="proposal | case_study | reference_architecture | boilerplate")
    srch.add_argument("--outcome", default=None, help="won | lost | n/a")
    srch.add_argument("--top", dest="top_k", type=int, default=5)
    srch.add_argument("--out", default="out")

    prop = sub.add_parser("propose", help="Draft a grounded proposal from the compliance matrix")
    prop.add_argument("--matrix", default="out/compliance_matrix.csv")
    prop.add_argument("--client", dest="client_name", default="the client")
    prop.add_argument("--model", default=proposal_generator.OPUS_MODEL)
    prop.add_argument("--out", default="out")
    prop.add_argument("--demo", action="store_true")

    ui = sub.add_parser("ui", help="Launch the demo web app (http://localhost:8765)")
    ui.add_argument("--port", type=int, default=8765)
    ui.add_argument("--live", action="store_true", help="Use live API instead of demo mode")

    for pcmd in (rfp, res, prop):
        pcmd.add_argument("--provider", choices=["gemini", "groq", "anthropic"], default=None,
                          help="Force an AI provider (default: auto-detect by key)")

    args = ap.parse_args()
    needs_key = args.cmd in ("rfp", "research", "propose") and not getattr(args, "demo", False)
    has_key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GROQ_API_KEY")
               or os.environ.get("ANTHROPIC_API_KEY"))
    if needs_key and not has_key:
        sys.exit("No API key set. Set GEMINI_API_KEY (free: aistudio.google.com), "
                 "GROQ_API_KEY (free: console.groq.com), or ANTHROPIC_API_KEY, "
                 "or use --demo for offline mode.")
    if getattr(args, "provider", None):
        from copilot import llm
        llm.set_provider(args.provider)

    if args.cmd == "rfp":
        path = args.rfp_file
        if not args.demo and os.path.splitext(path)[1].lower() in (".pdf", ".docx"):
            text = parsers.extract_text(path)
            tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                              encoding="utf-8")
            tmp.write(text); tmp.close()
            path = tmp.name
            print(f"Parsed {args.rfp_file} -> {len(text)} chars of text")
        rfp_analyzer.analyze(path, args.catalog, out_dir=args.out,
                             model=args.model, demo=args.demo)
    elif args.cmd == "research":
        client_research.research(args.company, context=args.context,
                                 out_dir=args.out, model=args.model, demo=args.demo)
    elif args.cmd == "search":
        knowledge_search.run_search(args.query, out_dir=args.out, top_k=args.top_k,
                                    industry=args.industry, asset_type=args.asset_type,
                                    outcome=args.outcome)
    elif args.cmd == "propose":
        proposal_generator.generate(matrix_path=args.matrix, out_dir=args.out,
                                    client_name=args.client_name, model=args.model,
                                    demo=args.demo)
    elif args.cmd == "ui":
        from webapp import serve
        serve(port=args.port, demo=not args.live)


if __name__ == "__main__":
    main()
