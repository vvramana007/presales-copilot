"""Client Research: pre-meeting brief. Uses web-search grounding when the
provider supports it (Gemini google_search_retrieval / Claude web_search)."""
import os
import re

from . import llm

# "flash" = the fast model (Gemini 1.5 Flash or Claude Sonnet). See copilot/llm.py.
SONNET_MODEL = "flash"

BRIEF_SYSTEM = """You are a presales research analyst. Produce a concise, factual
pre-meeting client brief in markdown. Use web search to gather current information.
Cite sources inline as markdown links. Structure:
# Client Brief: <company>
## Snapshot  (what they do, size, HQ, leadership)
## Recent news  (last 6 months, dated)
## Financial signals  (revenue/funding/results if public)
## Technology stack signals  (from job posts, engineering blogs, public docs)
## Industry trends relevant to this meeting
## Suggested talking points  (tie their situation to our services)
Be specific; no filler. If information is unavailable, say so rather than guessing."""


def research(company, context="", out_dir="out", model=SONNET_MODEL, demo=False):
    os.makedirs(out_dir, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9]+", "_", company).strip("_")
    out_path = os.path.join(out_dir, f"client_brief_{safe}.md")

    if demo:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "sample_data", "demo_client_brief.md"), encoding="utf-8") as f:
            brief = f.read()
    else:
        print(f"Researching {company} ...")
        user = (f"Prepare a pre-meeting brief on {company}."
                + (f" Meeting context: {context}" if context else ""))
        try:
            brief = llm.ask_text(BRIEF_SYSTEM, user, tier=model, web_search=True)
        except Exception:
            # Web-search grounding not available on this provider/version -
            # fall back to the model's own knowledge (still useful for a brief).
            brief = llm.ask_text(BRIEF_SYSTEM, user, tier=model, web_search=False)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(brief)
    print(f"Client brief -> {out_path}")
