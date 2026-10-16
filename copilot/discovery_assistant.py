"""Discovery Assistant — YOUR FIRST MODULE TO BUILD.

Goal: given a client's industry, deal stage, and meeting context, produce a
ranked list of discovery questions to ask, each with a short rationale.

Work through the TODOs in order. Demo mode already works, so you can run this
file from day one and see the shape of the output before you write any AI code.

Run it:
    python cli.py discover --industry Insurance --stage discovery --demo
    python cli.py discover --industry Insurance --stage discovery      (live)

Pattern to copy from: copilot/rfp_analyzer.py — it does the same kind of thing
(build a prompt, call Claude, parse JSON, write a file).
"""
import json
import os

SONNET_MODEL = "claude-sonnet-5"

# ---------------------------------------------------------------------------
# TODO 1: Write the system prompt.
#
# This is just English instructions for the AI. Yours should tell it to:
#   - act as an experienced presales consultant
#   - generate discovery questions tailored to the industry and deal stage
#   - return between 8 and 12 questions
#   - for each question include: the question, why it matters, and which
#     qualification area it covers (budget / authority / need / timeline / risk)
#   - order them the way you'd actually ask them in a real meeting
#   - return ONLY valid JSON in this shape:
#       {"questions": [{"question": "...", "rationale": "...", "area": "..."}]}
#
# Tip: look at EXTRACTION_SYSTEM in rfp_analyzer.py for the style to copy.
# ---------------------------------------------------------------------------
DISCOVERY_SYSTEM = """TODO: write your system prompt here"""


def _client():
    """Lazy import so --demo works without the anthropic package installed."""
    import anthropic
    return anthropic.Anthropic()


def generate_questions(industry, stage, context="", model=SONNET_MODEL, demo=False):
    """Return a list of question dicts."""
    if demo:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "sample_data", "demo_discovery_questions.json"),
                  encoding="utf-8") as f:
            return json.load(f)["questions"]

    # -----------------------------------------------------------------------
    # TODO 2: Build the user message.
    #
    # Combine industry, stage and context into one clear string, e.g.:
    #   f"Industry: {industry}\nDeal stage: {stage}\nMeeting context: {context}"
    # -----------------------------------------------------------------------
    user_message = ""  # TODO

    # -----------------------------------------------------------------------
    # TODO 3: Call Claude.
    #
    # Copy the shape of _ask_json() in rfp_analyzer.py:
    #   client = _client()
    #   resp = client.messages.create(
    #       model=model, max_tokens=2000,
    #       system=DISCOVERY_SYSTEM,
    #       messages=[{"role": "user", "content": user_message}],
    #   )
    #   text = "".join(b.text for b in resp.content if b.type == "text")
    # -----------------------------------------------------------------------
    text = ""  # TODO

    # -----------------------------------------------------------------------
    # TODO 4: Parse the JSON out of the response.
    #
    # The model sometimes wraps JSON in prose, so slice from the first "{" to
    # the last "}" before json.loads() — same trick as rfp_analyzer._ask_json.
    # Then return data["questions"].
    # -----------------------------------------------------------------------
    return []  # TODO


def run(industry, stage, context="", out_dir="out", model=SONNET_MODEL, demo=False):
    """Generate questions and write them to out/discovery_questions.md."""
    os.makedirs(out_dir, exist_ok=True)
    questions = generate_questions(industry, stage, context, model=model, demo=demo)

    out_path = os.path.join(out_dir, "discovery_questions.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Discovery questions — {industry} / {stage}\n\n")
        if context:
            f.write(f"*Context: {context}*\n\n")
        # -------------------------------------------------------------------
        # TODO 5: Write each question to the file.
        #
        # Suggested format:
        #   1. **The question text**
        #      *Area: budget* — why this question matters
        #
        # Loop with: for i, q in enumerate(questions, 1):
        # -------------------------------------------------------------------
        for i, q in enumerate(questions, 1):
            f.write(f"{i}. **{q['question']}**\n")
            f.write(f"   *Area: {q.get('area', '-')}* — {q.get('rationale', '')}\n\n")

    print(f"{len(questions)} questions -> {out_path}")
    for q in questions[:5]:
        print(f"  [{q.get('area', '-')}] {q['question']}")
    return questions


# ---------------------------------------------------------------------------
# TODO 6 (in cli.py): add the "discover" subcommand.
#
#   disc = sub.add_parser("discover", help="Generate discovery questions")
#   disc.add_argument("--industry", required=True)
#   disc.add_argument("--stage", default="discovery")
#   disc.add_argument("--context", default="")
#   disc.add_argument("--out", default="out")
#   disc.add_argument("--demo", action="store_true")
#
# and in the dispatch section:
#
#   elif args.cmd == "discover":
#       discovery_assistant.run(args.industry, args.stage, args.context,
#                               out_dir=args.out, demo=args.demo)
#
# Don't forget to add discovery_assistant to the import line at the top.
#
# TODO 7 (in webapp.py): add a "Discovery" tab.
#   - add ("/discovery", "discovery", "Discovery") to the tabs list in page()
#   - add an elif route in do_GET() — copy the /search route as your template
# ---------------------------------------------------------------------------
