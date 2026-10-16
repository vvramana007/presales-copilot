"""RFP Analyzer: extract requirements, build compliance matrix, flag gaps."""
import csv
import json
import os

from . import llm

# "pro" = the strong model (Gemini 1.5 Pro or Claude Opus). See copilot/llm.py.
OPUS_MODEL = "pro"

EXTRACTION_SYSTEM = """You are an RFP analyst for a technology services company.
Extract EVERY requirement from the RFP. Be exhaustive - missing a mandatory
requirement can disqualify a bid. For each requirement return:
- id: R-001, R-002, ...
- clause: the section/clause reference in the source document
- text: the requirement, quoted or tightly paraphrased
- type: "mandatory" (shall/must/required) or "desirable" (should/may/preferred)
Also list ambiguities (vague or contradictory clauses) and risky_terms
(unlimited liability, aggressive SLAs, IP transfer, unusual penalties).
Return ONLY valid JSON:
{"requirements": [...], "ambiguities": ["..."], "risky_terms": ["..."]}"""

MAPPING_SYSTEM = """You map RFP requirements to a company's capability catalog.
RULES (anti-hallucination):
1. Claim "full" or "partial" coverage ONLY if a specific catalog entry supports it;
   cite that entry's id as evidence.
2. If no catalog entry applies, coverage is "gap". Never invent capabilities.
For each requirement return: id, coverage ("full"|"partial"|"gap"),
capability_id (or null), evidence (one sentence citing the catalog entry, or null),
owner_suggestion (role best placed to respond).
Also draft clarification_questions for ambiguous requirements.
Return ONLY valid JSON:
{"mappings": [...], "clarification_questions": ["..."]}"""


def analyze(rfp_path, catalog_path, out_dir="out", model=OPUS_MODEL, demo=False):
    os.makedirs(out_dir, exist_ok=True)
    if demo:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "sample_data", "demo_rfp_analysis.json"), encoding="utf-8") as f:
            extraction, mapping = (lambda d: (d["extraction"], d["mapping"]))(json.load(f))
    else:
        with open(rfp_path, encoding="utf-8") as f:
            rfp_text = f.read()
        with open(catalog_path, encoding="utf-8") as f:
            catalog = f.read()
        print("Pass 1/2: extracting requirements ...")
        extraction = llm.ask_json(EXTRACTION_SYSTEM, f"<rfp>\n{rfp_text}\n</rfp>", tier=model)
        print(f"  {len(extraction['requirements'])} requirements found")
        print("Pass 2/2: mapping to capability catalog ...")
        mapping = llm.ask_json(
            MAPPING_SYSTEM,
            "<catalog>\n" + catalog + "\n</catalog>\n<requirements>\n"
            + json.dumps(extraction["requirements"], indent=1) + "\n</requirements>",
            tier=model,
        )

    by_id = {m["id"]: m for m in mapping["mappings"]}
    matrix_path = os.path.join(out_dir, "compliance_matrix.csv")
    with open(matrix_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Clause", "Requirement", "Type", "Coverage",
                    "Capability", "Evidence", "Suggested owner"])
        for r in extraction["requirements"]:
            m = by_id.get(r["id"], {})
            w.writerow([r["id"], r.get("clause", ""), r["text"], r["type"],
                        m.get("coverage", "unmapped"), m.get("capability_id") or "-",
                        m.get("evidence") or "-", m.get("owner_suggestion", "-")])

    reqs = extraction["requirements"]
    mandatory = [r for r in reqs if r["type"] == "mandatory"]
    gaps = [r for r in reqs if by_id.get(r["id"], {}).get("coverage") == "gap"]
    gap_path = os.path.join(out_dir, "gap_report.md")
    with open(gap_path, "w", encoding="utf-8") as f:
        f.write("# RFP Gap Report\n\n")
        f.write(f"Requirements: **{len(reqs)}** ({len(mandatory)} mandatory) | "
                f"Gaps: **{len(gaps)}**\n\n## Gaps\n\n")
        for r in gaps:
            flag = " **[MANDATORY - bid risk]**" if r["type"] == "mandatory" else ""
            f.write(f"- {r['id']} ({r.get('clause','?')}): {r['text']}{flag}\n")
        f.write("\n## Ambiguities\n\n")
        for a in extraction.get("ambiguities", []):
            f.write(f"- {a}\n")
        f.write("\n## Risky terms\n\n")
        for t in extraction.get("risky_terms", []):
            f.write(f"- {t}\n")
        f.write("\n## Suggested clarification questions\n\n")
        for i, q in enumerate(mapping.get("clarification_questions", []), 1):
            f.write(f"{i}. {q}\n")

    print(f"\nCompliance matrix -> {matrix_path}")
    print(f"Gap report        -> {gap_path}")
    print(f"Summary: {len(reqs)} requirements, {len(mandatory)} mandatory, "
          f"{len(gaps)} gaps ({sum(1 for r in gaps if r['type']=='mandatory')} mandatory gaps)")
