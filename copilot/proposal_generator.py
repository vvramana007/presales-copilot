"""Proposal Generator: draft grounded proposal sections from the compliance
matrix and the asset library. Every claim cites an asset ID."""
import csv
import json
import os

from . import knowledge_search
from . import llm

# "pro" = the strong model (Gemini 1.5 Pro or Claude Opus). See copilot/llm.py.
OPUS_MODEL = "pro"

DRAFT_SYSTEM = """You draft technology-services proposal sections.
GROUNDING RULES (strict):
1. Base every capability claim on the provided assets; cite as [AST-xxx].
2. If no asset supports a point, write "[TO VERIFY: ...]" instead of inventing.
3. Professional, confident, concise. No superlatives without evidence.
Write the requested section in markdown."""

SECTIONS = [
    ("Executive Summary", "Summarize why we are the right partner, referencing our directly relevant experience."),
    ("Understanding of Requirements", "Show we understand their needs, organized by theme, referencing requirement IDs."),
    ("Proposed Solution", "Describe the solution approach mapped to their requirements, citing reference architectures and accelerators."),
    ("Relevant Experience", "Present the most similar past engagements as proof points."),
    ("Delivery Approach and Team", "Phased delivery plan, governance, and knowledge transfer."),
]


def _load_matrix(matrix_path):
    with open(matrix_path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate(matrix_path="out/compliance_matrix.csv", out_dir="out",
             client_name="the client", model=OPUS_MODEL, demo=False):
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "proposal_draft.md")

    if demo:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "sample_data", "demo_proposal_draft.md"),
                  encoding="utf-8") as f:
            draft = f.read()
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(draft)
        print(f"Proposal draft -> {out_path}")
        return out_path

    rows = _load_matrix(matrix_path)
    ks = knowledge_search.KnowledgeSearch()
    # retrieve supporting assets per requirement theme
    themes = " ".join(r["Requirement"] for r in rows)
    assets = ks.search(themes, top_k=8)
    asset_block = json.dumps(assets, indent=1)
    matrix_block = json.dumps(rows, indent=1)

    parts = [f"# Proposal Draft — {client_name}\n\n"
             "*Generated draft. Every claim cites an asset ID; [TO VERIFY] items "
             "need human input. Requires review and approval before any client use.*\n"]
    for title, instruction in SECTIONS:
        print(f"Drafting: {title} ...")
        text = llm.ask_text(
            DRAFT_SYSTEM,
            f"Client: {client_name}\n\n<compliance_matrix>\n{matrix_block}\n"
            f"</compliance_matrix>\n\n<assets>\n{asset_block}\n</assets>\n\n"
            f"Write the section: {title}\nGuidance: {instruction}",
            tier=model, max_tokens=1500,
        )
        parts.append(f"\n## {title}\n\n{text.strip()}\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"Proposal draft -> {out_path}")
    return out_path
