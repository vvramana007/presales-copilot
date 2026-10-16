#!/usr/bin/env python3
"""Presales Copilot demo web app - Python stdlib only, no frameworks.

Run:  python cli.py ui          (demo mode, no API key needed)
      python cli.py ui --live   (live AI, needs GEMINI_API_KEY or ANTHROPIC_API_KEY)
Then open http://localhost:8765
"""
import csv
import html
import io
import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from copilot import rfp_analyzer, client_research, knowledge_search, proposal_generator, parsers, llm  # noqa: E402

DEMO = True
OUT = "out"
PROVIDER = None  # None = auto; or "gemini" / "anthropic" chosen via the UI

_PROVIDER_LABEL = {"gemini": "Google Gemini", "groq": "Groq (Llama, free)",
                   "anthropic": "Anthropic Claude"}

STYLE = """<style>
body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#f4f7fd;color:#222840}
header{background:#1e2761;color:#fff;padding:18px 32px}
header h1{margin:0;font-size:20px} header p{margin:4px 0 0;color:#cadcfc;font-size:13px}
nav{background:#fff;border-bottom:1px solid #dde;padding:0 32px}
nav a{display:inline-block;padding:12px 16px;text-decoration:none;color:#1e2761;font-size:14px;font-weight:bold}
nav a.on{border-bottom:3px solid #4a6cf7}
main{max-width:960px;margin:24px auto;padding:0 24px}
.card{background:#fff;border-radius:10px;padding:20px 24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(30,39,97,.08)}
h2{color:#1e2761;font-size:18px;margin:0 0 12px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{background:#1e2761;color:#fff;text-align:left;padding:7px 9px}
td{border-bottom:1px solid #e6eaf4;padding:7px 9px;vertical-align:top}
tr.gap td{background:#fdeaea} tr.partial td{background:#fdf6e3}
.pill{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;font-weight:bold}
.full{background:#e1f5ee;color:#0f6e56}.part{background:#faeeda;color:#854f0b}.gapp{background:#fcebeb;color:#a32d2d}
input[type=text],select{padding:8px 10px;border:1px solid #ccd;border-radius:6px;font-size:14px;width:280px}
button{background:#4a6cf7;color:#fff;border:0;border-radius:6px;padding:9px 18px;font-size:14px;font-weight:bold;cursor:pointer}
button:hover{background:#3a57d4}
.stat{display:inline-block;background:#f4f7fd;border-radius:8px;padding:10px 18px;margin:0 10px 10px 0;text-align:center}
.stat b{display:block;font-size:26px;color:#1e2761}.stat span{font-size:12px;color:#5a6482}
pre,.md{white-space:pre-wrap;font-size:13.5px;line-height:1.55}
.note{font-size:12px;color:#5a6482;font-style:italic}
.asset{border-left:4px solid #4a6cf7;padding:8px 14px;margin:10px 0;background:#f8faff}
.asset b{color:#1e2761}.asset .meta{font-size:12px;color:#5a6482}
.modelbar{background:#eef2fb;border-bottom:1px solid #dde;padding:8px 32px;font-size:13px;color:#5a6482}
.modelbar .lbl{font-weight:bold;color:#1e2761;margin-right:8px}
.modelbar a{display:inline-block;padding:5px 14px;margin-right:8px;border-radius:16px;
  text-decoration:none;font-weight:bold;font-size:13px;border:1px solid #c3cfe8;color:#1e2761;background:#fff}
.modelbar a.sel{background:#4a6cf7;color:#fff;border-color:#4a6cf7}
.modelbar a.off{opacity:.45;cursor:not-allowed}
</style>"""


def model_bar(active):
    """Row of buttons to pick which AI model runs live requests."""
    if DEMO:
        return ('<div class="modelbar"><span class="lbl">AI model:</span>'
                '<span>demo mode uses canned outputs — start with --live to pick a model</span></div>')
    have = llm.available_providers()
    btns = ""
    for key in ("gemini", "groq", "anthropic"):
        label = _PROVIDER_LABEL[key]
        if key in have:
            cls = "sel" if PROVIDER == key or (PROVIDER is None and have and have[0] == key) else ""
            btns += f'<a class="{cls}" href="/model?p={key}&next={active}">{label}</a>'
        else:
            btns += f'<a class="off" title="Set the API key to enable">{label} (no key)</a>'
    return f'<div class="modelbar"><span class="lbl">AI model:</span>{btns}</div>'


def page(active, body):
    tabs = [("/", "rfp", "RFP Analyzer"), ("/search", "search", "Knowledge Search"),
            ("/proposal", "proposal", "Proposal Draft"), ("/research", "research", "Client Research")]
    route_of = {"rfp": "/", "search": "/search", "proposal": "/proposal", "research": "/research"}
    nav = "".join(f'<a href="{u}" class="{"on" if k == active else ""}">{t}</a>' for u, k, t in tabs)
    mode = "DEMO MODE — canned outputs, no API key" if DEMO else "LIVE MODE — real AI"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Presales Copilot</title>{STYLE}</head><body>
<header><h1>Presales Copilot — Prototype</h1><p>{mode}</p></header>
<nav>{nav}</nav>{model_bar(route_of.get(active, "/"))}<main>{body}</main></body></html>"""


def esc(s):
    return html.escape(str(s))


def matrix_html():
    path = os.path.join(OUT, "compliance_matrix.csv")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    total = len(rows)
    mand = sum(1 for r in rows if r["Type"] == "mandatory")
    gaps = sum(1 for r in rows if r["Coverage"] == "gap")
    stats = (f'<div class="stat"><b>{total}</b><span>requirements</span></div>'
             f'<div class="stat"><b>{mand}</b><span>mandatory</span></div>'
             f'<div class="stat"><b>{gaps}</b><span>gaps flagged</span></div>')
    pills = {"full": "full", "partial": "part", "gap": "gapp"}
    body_rows = ""
    for r in rows:
        cls = "gap" if r["Coverage"] == "gap" else ("partial" if r["Coverage"] == "partial" else "")
        pill = f'<span class="pill {pills.get(r["Coverage"], "part")}">{esc(r["Coverage"])}</span>'
        body_rows += (f'<tr class="{cls}"><td>{esc(r["ID"])}</td><td>{esc(r["Clause"])}</td>'
                      f'<td>{esc(r["Requirement"])}</td><td>{esc(r["Type"])}</td>'
                      f'<td>{pill}</td><td>{esc(r["Evidence"])}</td></tr>')
    gap_md = ""
    gp = os.path.join(OUT, "gap_report.md")
    if os.path.exists(gp):
        with open(gp, encoding="utf-8") as f:
            gap_md = f'<div class="card"><h2>Gap report</h2><div class="md">{esc(f.read())}</div></div>'
    return (f'<div class="card"><h2>Compliance matrix</h2>{stats}'
            f'<table><tr><th>ID</th><th>Clause</th><th>Requirement</th><th>Type</th>'
            f'<th>Coverage</th><th>Evidence</th></tr>{body_rows}</table></div>{gap_md}')


class App(BaseHTTPRequestHandler):
    def _send(self, body, code=200):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        route = url.path

        if route == "/model":
            global PROVIDER
            PROVIDER = q.get("p", [None])[0]
            llm.set_provider(PROVIDER)
            self.send_response(303)
            self.send_header("Location", q.get("next", ["/"])[0])
            self.end_headers()
            return

        if route == "/":
            form = ('<div class="card"><h2>Analyze an RFP</h2>'
                    '<p class="note">Demo mode analyzes the bundled sample insurance RFP. '
                    'In live mode you can point the CLI at any PDF/DOCX/TXT.</p>'
                    '<form action="/run_rfp"><button>Run analysis on sample RFP</button></form></div>')
            self._send(page("rfp", form + matrix_html()))

        elif route == "/run_rfp":
            if not DEMO:
                llm.set_provider(PROVIDER)
            here = os.path.dirname(os.path.abspath(__file__))
            rfp_analyzer.analyze(os.path.join(here, "sample_data", "sample_rfp.txt"),
                                 os.path.join(here, "sample_data", "capability_catalog.json"),
                                 out_dir=OUT, demo=DEMO)
            self.send_response(303)
            self.send_header("Location", "/")
            self.end_headers()

        elif route == "/search":
            query = q.get("q", [""])[0]
            industry = q.get("industry", [""])[0] or None
            atype = q.get("type", [""])[0] or None
            results = ""
            if query:
                hits = knowledge_search.KnowledgeSearch().search(query, top_k=6,
                                                                 industry=industry,
                                                                 asset_type=atype)
                if not hits:
                    results = '<div class="card"><p>No matching assets.</p></div>'
                else:
                    items = "".join(
                        f'<div class="asset"><b>{esc(h["title"])}</b> '
                        f'<span class="pill part">{esc(h["id"])}</span>'
                        f'<div class="meta">{esc(h.get("type","-"))} · {esc(h.get("industry","-"))} · '
                        f'{esc(h.get("year","-"))} · outcome: {esc(h.get("outcome","-"))} · '
                        f'relevance {h["score"]}</div>{esc(h.get("summary",""))}</div>'
                        for h in hits)
                    results = f'<div class="card"><h2>{len(hits)} assets</h2>{items}</div>'
            form = (f'<div class="card"><h2>Search past proposals &amp; assets</h2>'
                    f'<form>'
                    f'<input type="text" name="q" value="{esc(query)}" placeholder="e.g. claims migration guidewire"> '
                    f'<select name="industry"><option value="">Any industry</option>'
                    f'<option{" selected" if industry=="Insurance" else ""}>Insurance</option>'
                    f'<option{" selected" if industry=="Banking" else ""}>Banking</option></select> '
                    f'<select name="type"><option value="">Any type</option>'
                    + "".join(f'<option value="{t}"{" selected" if atype==t else ""}>{t}</option>'
                              for t in ("proposal", "case_study", "reference_architecture", "boilerplate"))
                    + f'</select> <button>Search</button></form></div>')
            self._send(page("search", form + results))

        elif route == "/proposal":
            body = ('<div class="card"><h2>Draft a grounded proposal</h2>'
                    '<p class="note">Uses the compliance matrix (run the RFP Analyzer first) '
                    'and the asset library. Every claim cites an asset ID.</p>'
                    '<form action="/run_proposal"><button>Generate proposal draft</button></form></div>')
            pp = os.path.join(OUT, "proposal_draft.md")
            if os.path.exists(pp):
                with open(pp, encoding="utf-8") as f:
                    body += f'<div class="card"><h2>Draft</h2><div class="md">{esc(f.read())}</div></div>'
            self._send(page("proposal", body))

        elif route == "/run_proposal":
            if not DEMO:
                llm.set_provider(PROVIDER)
            proposal_generator.generate(matrix_path=os.path.join(OUT, "compliance_matrix.csv"),
                                        out_dir=OUT, client_name="Acme Insurance Group",
                                        demo=DEMO)
            self.send_response(303)
            self.send_header("Location", "/proposal")
            self.end_headers()

        elif route == "/research":
            company = q.get("company", [""])[0]
            body = (f'<div class="card"><h2>Pre-meeting client brief</h2><form>'
                    f'<input type="text" name="company" value="{esc(company)}" '
                    f'placeholder="Company name"> <button>Generate brief</button></form>'
                    f'<p class="note">Demo mode returns the canned Acme Insurance brief for any name.</p></div>')
            if company:
                if not DEMO:
                    llm.set_provider(PROVIDER)
                client_research.research(company, out_dir=OUT, demo=DEMO)
                import re as _re
                safe = _re.sub(r"[^A-Za-z0-9]+", "_", company).strip("_")
                bp = os.path.join(OUT, f"client_brief_{safe}.md")
                if os.path.exists(bp):
                    with open(bp, encoding="utf-8") as f:
                        body += f'<div class="card"><div class="md">{esc(f.read())}</div></div>'
            self._send(page("research", body))

        else:
            self._send(page("rfp", '<div class="card"><p>Not found.</p></div>'), 404)


def serve(port=8765, demo=True):
    global DEMO
    DEMO = demo
    os.makedirs(OUT, exist_ok=True)
    print(f"Presales Copilot UI -> http://localhost:{port}  "
          f"({'demo mode' if demo else 'LIVE mode'})  Ctrl+C to stop")
    HTTPServer(("127.0.0.1", port), App).serve_forever()


if __name__ == "__main__":
    serve()
