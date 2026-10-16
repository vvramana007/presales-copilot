"""Tiny provider layer so the app can use Google Gemini or Anthropic Claude.

Picks a provider automatically:
  - if GEMINI_API_KEY is set  -> Google Gemini   (recommended: free tier)
  - elif ANTHROPIC_API_KEY set -> Anthropic Claude
Demo mode never calls this file, so demos work with no key at all.

Gemini model names change over time and some are restricted on the free tier,
so we build an ordered list of candidate models and TRY EACH until one works,
caching the winner. This survives model renames and access limits automatically.
"""
import json
import os
import time

# Ordered candidates per tier; the code tries each until one works, so a renamed
# or unavailable model simply falls through to the next. Sonnet leads the "pro"
# tier (strong but far cheaper than Opus); Haiku leads "flash" (cheapest).
_ANTHROPIC_PREF = {
    "pro": ["claude-sonnet-5", "claude-opus-5", "claude-haiku-4-5-20251001"],
    "flash": ["claude-haiku-4-5-20251001", "claude-sonnet-5", "claude-opus-5"],
}
_anthropic_working = {}   # tier -> model name that actually worked

# Preference order, best-and-most-available first. Flash models are free-tier
# friendly, so they lead; pro models are tried too but often need a paid tier.
_GEMINI_PREF = [
    "gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest",
    "gemini-2.5-flash-lite", "gemini-2.0-flash-lite",
    "gemini-2.5-pro", "gemini-pro-latest",
    "gemini-1.5-flash", "gemini-1.5-pro",
]

_gemini_working = {}   # tier -> model name that actually worked

# Groq: free tier (console.groq.com), runs open models. 70B leads "pro"
# (strongest), 8B leads "flash" (fastest). Tried in order, skips unavailable.
_GROQ_PREF = {
    "pro": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
    "flash": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"],
}
_groq_working = {}   # tier -> model name that actually worked

_NOT_AVAIL = ("not found", "no longer available", "not supported",
              "permission", "403", "404", "decommission", "does not exist")

_override = None       # set by set_provider() to force a specific provider


# Which env var holds each provider's key, and a friendly label.
_KEY_ENV = {"gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
            "groq": "GROQ_API_KEY"}
_KEY_HINT = {"gemini": "aistudio.google.com", "anthropic": "console.anthropic.com",
             "groq": "console.groq.com (free, no card)"}


def available_providers():
    """Which providers have an API key set right now (in priority order)."""
    return [p for p in ("gemini", "groq", "anthropic") if os.environ.get(_KEY_ENV[p])]


def set_provider(name):
    """Force a provider ('gemini'/'groq'/'anthropic'), or None to auto-detect."""
    global _override
    _override = name if name in _KEY_ENV else None


def provider():
    """Return which provider to use: the forced one, else by available keys."""
    if _override:
        if not os.environ.get(_KEY_ENV[_override]):
            raise RuntimeError(f"{_override} selected but {_KEY_ENV[_override]} is not set.")
        return _override
    for p in available_providers():
        return p
    raise RuntimeError(
        "No API key found. Set GEMINI_API_KEY (free: aistudio.google.com), "
        "GROQ_API_KEY (free: console.groq.com), or ANTHROPIC_API_KEY. "
        "Or run any command with --demo for offline mode."
    )


def _gemini_candidates(tier):
    """Ordered list of Gemini model names to try for this tier."""
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    try:
        available = [m.name.replace("models/", "")
                     for m in genai.list_models()
                     if "generateContent" in getattr(m, "supported_generation_methods", [])]
    except Exception:
        available = []
    avail = set(available)
    # Start with our preference list (only those the key lists), then any other
    # available models as extra fallbacks, then the raw preference list as a
    # last resort in case list_models() was empty.
    ordered = [m for m in _GEMINI_PREF if m in avail]
    ordered += [m for m in available if m not in ordered
                and not any(b in m for b in ("exp", "preview", "thinking",
                                             "vision", "tts", "image", "embedding"))]
    ordered += [m for m in _GEMINI_PREF if m not in ordered]
    # For the "pro" tier, move pro models a bit earlier if present.
    if tier == "pro":
        ordered.sort(key=lambda m: (0 if "pro" in m else 1))
    return ordered


def _gemini_call(system, user, tier, gen_config, tools=None):
    """Try candidate models until one succeeds; cache and reuse the winner."""
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    cached = _gemini_working.get(tier)
    candidates = [cached] + _gemini_candidates(tier) if cached else _gemini_candidates(tier)
    last = None
    for name in candidates:
        try:
            gm = genai.GenerativeModel(name, system_instruction=system, tools=tools)
            r = gm.generate_content(user, generation_config=gen_config)
            _gemini_working[tier] = name
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e).lower()
            if any(s in msg for s in _NOT_AVAIL):
                continue          # model blocked/renamed -> try the next one
            raise                 # a real error (bad key, network) -> surface it
    raise RuntimeError(f"No usable Gemini model found. Last error: {last}")


def _groq_call(system, user, tier, max_tokens, json_mode=False):
    """Try Groq (Llama) model candidates until one works; cache the winner."""
    from groq import Groq
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    cached = _groq_working.get(tier)
    order = _GROQ_PREF.get(tier, list(_GROQ_PREF["pro"]))
    candidates = ([cached] + order) if cached else order
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    last = None
    for name in candidates:
        try:
            resp = client.chat.completions.create(
                model=name, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                **kwargs)
            _groq_working[tier] = name
            return resp.choices[0].message.content
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e).lower()
            if any(s in msg for s in _NOT_AVAIL):
                continue
            raise
    raise RuntimeError(f"No usable Groq model found. Last error: {last}")


def _anthropic_call(system, user, tier, max_tokens, tools=None):
    """Try Claude model candidates until one works; cache and reuse the winner."""
    import anthropic
    client = anthropic.Anthropic()
    cached = _anthropic_working.get(tier)
    order = _ANTHROPIC_PREF.get(tier, [tier])
    candidates = ([cached] + order) if cached else order
    kwargs = {"tools": tools} if tools else {}
    last = None
    for name in candidates:
        try:
            resp = client.messages.create(
                model=name, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}], **kwargs)
            _anthropic_working[tier] = name
            return "".join(b.text for b in resp.content if b.type == "text")
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e).lower()
            if any(s in msg for s in ("not_found", "not found", "model", "404")) \
                    and "overloaded" not in msg:
                continue
            raise
    raise RuntimeError(f"No usable Claude model found. Last error: {last}")


def _extract_json(text):
    """Parse a JSON object out of model text, tolerating common glitches."""
    import re
    start = text.find("{")
    if start == -1:
        raise RuntimeError("Model did not return JSON. Raw start: " + text[:200])
    s = text[start:]

    # 1) clean parse: first complete object, ignore trailing text
    try:
        return json.JSONDecoder().raw_decode(s)[0]
    except json.JSONDecodeError:
        pass

    # 2) remove trailing commas (",]" or ",}") then retry
    s2 = re.sub(r",\s*([}\]])", r"\1", s)
    try:
        return json.JSONDecoder().raw_decode(s2)[0]
    except json.JSONDecodeError:
        pass

    # 3) truncated output: walk back to the last balanced closing brace
    depth = 0
    for i, ch in enumerate(s2):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(s2[:i + 1])
                except json.JSONDecodeError:
                    continue
    raise json.JSONDecodeError("Could not parse model JSON", s, 0)


def _retry(fn, tries=3):
    last = None
    for i in range(tries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            msg = str(e).lower()
            if any(s in msg for s in _NOT_AVAIL):
                raise           # don't retry unavailable-model errors
            if i < tries - 1:
                time.sleep(2 * (i + 1))
    raise RuntimeError(f"AI call failed after {tries} tries: {last}")


def ask_json(system, user, tier="pro", max_tokens=8000):
    """Ask the model and parse its reply as a JSON object (dict).

    If the model returns malformed JSON, we repair what we can and, failing that,
    ask again (models are random, so a re-roll usually comes back clean).
    """
    prov = provider()
    last = None
    for _ in range(3):
        try:
            if prov == "gemini":
                cfg = {"response_mime_type": "application/json",
                       "max_output_tokens": max_tokens}
                return _extract_json(_gemini_call(system, user, tier, cfg))
            if prov == "groq":
                return _extract_json(_groq_call(system, user, tier, max_tokens,
                                                json_mode=True))
            return _extract_json(_anthropic_call(system, user, tier, max_tokens))
        except json.JSONDecodeError as e:
            last = e
    raise RuntimeError(f"Model kept returning invalid JSON: {last}")


def ask_text(system, user, tier="flash", max_tokens=4000, web_search=False):
    """Ask the model and return plain text (markdown)."""
    prov = provider()
    if prov == "gemini":
        cfg = {"max_output_tokens": max_tokens}
        tools = "google_search_retrieval" if web_search else None
        return _gemini_call(system, user, tier, cfg, tools=tools)

    if prov == "groq":
        # Groq has no built-in web search; answers from the model's knowledge.
        return _groq_call(system, user, tier, max_tokens, json_mode=False)

    tools = None
    if web_search:
        tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}]
    try:
        return _anthropic_call(system, user, tier, max_tokens, tools=tools)
    except Exception:
        if tools:  # web-search tool not available on this account -> plain call
            return _anthropic_call(system, user, tier, max_tokens, tools=None)
        raise
