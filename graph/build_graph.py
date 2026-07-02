#!/usr/bin/env python3
"""Build the papers relationship graph.

Reads:  papers/INDEX.json  + graph/cache/{authors,citations,semantic_edges}.json
Writes: graph/graph_data.json  and  graph/index.html  (self-contained, embeds data)

Edge types:
  cite    directed  A->B  (A references B; B is the earlier/foundational work)
          subtyped by semantic_edges.json into extends / baseline / compares / rebuts / background
  author  undirected        (two papers share >=1 author)  weight = #shared authors
  topic   undirected        (two papers share >=3 specific keywords/subtopics)
"""
import json, os, re, itertools
from collections import defaultdict, Counter

ROOT = os.environ.get("RT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GRAPH = os.path.join(ROOT, "graph")
CACHE = os.path.join(GRAPH, "cache")

# ---- tunables ----
TOPIC_MIN_SHARED   = 3     # min shared keywords to consider a topic edge
TOPIC_GENERIC_MAX  = 40    # keywords appearing in more papers than this are too generic -> ignored
TOPIC_TOPK_PER_NODE = 6    # keep only the strongest topic edges per node (controls density)
AUTHOR_CLIQUE_MAX  = 15    # skip pairwise edges for an author with more papers than this

def load(fn, d):
    p = os.path.join(CACHE, fn)
    if os.path.exists(p):
        try: return json.load(open(p, encoding="utf-8"))
        except Exception: return d
    return d

idx = json.load(open(os.path.join(ROOT, "papers", "INDEX.json"), encoding="utf-8"))["entries"]
authors  = load("authors.json", {})
cites    = load("citations.json", {})          # arxiv-id matched
cites_t  = load("citations_title.json", {})    # title matched
semantic = load("semantic_edges.json", {})     # {"A->B": {"type":..,"evidence":..}}

# merge id + title citation sources
_merged = defaultdict(set)
for src in (cites, cites_t):
    for a, refs in src.items():
        for b in refs:
            _merged[a].add(b)
cites = {a: sorted(bs) for a, bs in _merged.items()}

# ---------------- category normalization / inference ----------------
CATMAP = {
    "interp": "interp", "interpretability": "interp", "LLM interpretability": "interp",
    "security": "security", "AI security": "security",
    "privacy": "privacy", "AI privacy": "privacy",
}
INFER = [
    ("privacy",  ["differential privacy", "membership inference", "unlearn", "memoriz", "federated",
                  "privacy", "pii", "canary", "data extraction", "leakage"]),
    ("security", ["jailbreak", "prompt injection", "backdoor", "adversarial", "red team", "red-team",
                  "poison", "watermark", "malicious", "safety", "misalign", "attack", "guardrail",
                  "robust", "agent security", "trojan", "defense", "refusal"]),
    ("interp",   ["mechanistic", "interpretab", "sparse autoencoder", "sae", "circuit", "probing",
                  "activation", "representation", "superposition", "steering", "feature attribution",
                  "monosemantic", "logit lens", "concept"]),
]
def norm_cat(entry):
    c = CATMAP.get(entry.get("category"))
    if c:
        return c
    blob = (entry.get("title", "") + " " + " ".join(entry.get("keywords", [])) + " " +
            " ".join(entry.get("subtopics", []))).lower()
    best, bestn = "other", 0
    for cat, kws in INFER:
        n = sum(1 for k in kws if k in blob)
        if n > bestn:
            best, bestn = cat, n
    return best

def short(title, n=52):
    t = title.strip()
    return t if len(t) <= n else t[:n - 1] + "…"

# ---------------- nodes ----------------
nodes = {}
for aid, e in idx.items():
    nodes[aid] = {
        "id": aid,
        "label": short(e.get("title", aid)),
        "title": e.get("title", aid),
        "cat": norm_cat(e),
        "date": e.get("first_seen", e.get("folder", "")),
        "folder": e.get("folder", ""),
        "keywords": e.get("keywords", []),
        "authors": authors.get(aid, []),
        "indeg": 0,   # in-corpus citation in-degree (filled below)
    }

# ---------------- citation edges ----------------
edges = []
seen_cite = set()
for a, refs in cites.items():
    if a not in nodes:
        continue
    for b in refs:
        if b not in nodes or a == b:
            continue
        key = a + "->" + b
        if key in seen_cite:
            continue
        seen_cite.add(key)
        sem = semantic.get(key, {})
        edges.append({
            "from": a, "to": b, "etype": "cite",
            "subtype": sem.get("type", "cite"),
            "evidence": sem.get("evidence", ""),
        })
        nodes[b]["indeg"] += 1

# ---------------- co-author edges ----------------
author_papers = defaultdict(set)
for aid, al in authors.items():
    if aid not in nodes:
        continue
    for name in al:
        author_papers[name.lower()].add(aid)

pair_authors = Counter()
for name, papers in author_papers.items():
    if len(papers) < 2 or len(papers) > AUTHOR_CLIQUE_MAX:
        continue
    for x, y in itertools.combinations(sorted(papers), 2):
        pair_authors[(x, y)] += 1
for (x, y), w in pair_authors.items():
    edges.append({"from": x, "to": y, "etype": "author", "weight": w})

# ---------------- topic-similarity edges (inverted index) ----------------
kw_index = defaultdict(set)
for aid, n in nodes.items():
    toks = set(k.strip().lower() for k in n["keywords"] if k.strip())
    toks |= set(s.strip().lower() for s in idx[aid].get("subtopics", []) if s.strip())
    for t in toks:
        kw_index[t].add(aid)

pair_topic = Counter()
for t, papers in kw_index.items():
    if len(papers) < 2 or len(papers) > TOPIC_GENERIC_MAX:
        continue
    for x, y in itertools.combinations(sorted(papers), 2):
        pair_topic[(x, y)] += 1

# keep only strong pairs, then cap per-node to top-K
strong = [(p, w) for p, w in pair_topic.items() if w >= TOPIC_MIN_SHARED]
per_node = defaultdict(list)
for (x, y), w in strong:
    per_node[x].append((w, y))
    per_node[y].append((w, x))
keep = set()
for node, lst in per_node.items():
    lst.sort(reverse=True)
    for w, other in lst[:TOPIC_TOPK_PER_NODE]:
        keep.add(tuple(sorted((node, other))))
for (x, y) in keep:
    edges.append({"from": x, "to": y, "etype": "topic", "weight": pair_topic[(x, y)]})

# ---------------- output ----------------
from collections import Counter as C
etype_counts = C(e["etype"] for e in edges)
sub_counts = C(e.get("subtype") for e in edges if e["etype"] == "cite")
cat_counts = C(n["cat"] for n in nodes.values())
meta = {
    "generated": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
    "n_nodes": len(nodes),
    "edge_counts": dict(etype_counts),
    "cite_subtypes": dict(sub_counts),
    "cat_counts": dict(cat_counts),
    "authors_cached": len(authors),
    "citations_cached": len(cites),
    "semantic_labeled": len(semantic),
}
data = {"nodes": list(nodes.values()), "edges": edges, "meta": meta}

os.makedirs(GRAPH, exist_ok=True)
json.dump(data, open(os.path.join(GRAPH, "graph_data.json"), "w", encoding="utf-8"),
          ensure_ascii=False)

tpl_path = os.path.join(GRAPH, "template.html")
if os.path.exists(tpl_path):
    tpl = open(tpl_path, encoding="utf-8").read()
    html = tpl.replace("/*__GRAPH_DATA__*/", "window.GRAPH = " +
                       json.dumps(data, ensure_ascii=False) + ";")
    open(os.path.join(GRAPH, "index.html"), "w", encoding="utf-8").write(html)

print("nodes:", meta["n_nodes"])
print("edges:", meta["edge_counts"])
print("cite subtypes:", meta["cite_subtypes"])
print("categories:", meta["cat_counts"])
