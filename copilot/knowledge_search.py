"""Knowledge Search: hybrid keyword + metadata search over the internal asset library.

Works fully offline (pure-Python BM25-style scoring). In the full product this
becomes vector + keyword + metadata hybrid retrieval over a governed index;
the interface (search -> ranked assets with citations) stays the same.
"""
import json
import math
import os
import re

_WORD = re.compile(r"[a-z0-9]+")
_STOP = set("the a an and or of to in for on with by is are was were be as at "
            "this that it its from we our their they".split())


def _tokens(text):
    return [t for t in _WORD.findall(text.lower()) if t not in _STOP]


def load_assets(path=None):
    if path is None:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(here, "sample_data", "asset_library.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)["assets"]


class KnowledgeSearch:
    """BM25-lite scoring with optional metadata filters."""

    def __init__(self, assets=None, library_path=None):
        self.assets = assets if assets is not None else load_assets(library_path)
        self._docs = [_tokens(a["title"] + " " + a.get("summary", "") + " "
                              + " ".join(a.get("tags", []))) for a in self.assets]
        self._avg_len = sum(len(d) for d in self._docs) / max(len(self._docs), 1)
        self._df = {}
        for d in self._docs:
            for t in set(d):
                self._df[t] = self._df.get(t, 0) + 1

    def _score(self, query_tokens, doc):
        n = len(self.assets)
        score, k1, b = 0.0, 1.5, 0.75
        for q in query_tokens:
            tf = doc.count(q)
            if not tf:
                continue
            idf = math.log(1 + (n - self._df.get(q, 0) + 0.5) / (self._df.get(q, 0) + 0.5))
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(doc) / self._avg_len))
        return score

    def search(self, query, top_k=5, industry=None, asset_type=None, outcome=None):
        q = _tokens(query)
        results = []
        for asset, doc in zip(self.assets, self._docs):
            if industry and asset.get("industry", "").lower() != industry.lower():
                continue
            if asset_type and asset.get("type", "").lower() != asset_type.lower():
                continue
            if outcome and asset.get("outcome", "").lower() != outcome.lower():
                continue
            s = self._score(q, doc)
            if s > 0:
                results.append((s, asset))
        results.sort(key=lambda x: -x[0])
        return [{"score": round(s, 2), **a} for s, a in results[:top_k]]


def run_search(query, out_dir="out", **filters):
    os.makedirs(out_dir, exist_ok=True)
    ks = KnowledgeSearch()
    hits = ks.search(query, **filters)
    out_path = os.path.join(out_dir, "knowledge_search_results.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Knowledge Search: “{query}”\n\n")
        if not hits:
            f.write("No matching assets. Try fewer filters or different words.\n")
        for h in hits:
            f.write(f"## {h['title']}  `[{h['id']}]`\n\n")
            f.write(f"*{h.get('type','asset')} · {h.get('industry','-')} · "
                    f"{h.get('year','-')} · outcome: {h.get('outcome','-')} "
                    f"· relevance {h['score']}*\n\n")
            f.write(h.get("summary", "") + "\n\n")
    print(f"{len(hits)} assets found -> {out_path}")
    for h in hits:
        print(f"  [{h['id']}] ({h['score']}) {h['title']}")
    return hits
