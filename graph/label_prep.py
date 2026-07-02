#!/usr/bin/env python3
"""Prepare semantic-labeling input: for each intra-corpus citation edge A->B,
extract the in-text context in A where B is referenced, so a classifier can
decide extends / baseline / compares / rebuts / background.

Writes graph/cache/edges_to_label.json = [{key, from, to, context}, ...]
Only re-parses the distinct CITING papers (cheap).
"""
import json, glob, os, re, subprocess
from collections import defaultdict

ROOT = os.environ.get("RT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "graph", "cache")
idx = json.load(open(os.path.join(ROOT, "papers", "INDEX.json"), encoding="utf-8"))["entries"]
authors = json.load(open(os.path.join(CACHE, "authors.json"), encoding="utf-8"))

def load(fn):
    p = os.path.join(CACHE, fn)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

merged = defaultdict(set)
for fn in ("citations.json", "citations_title.json"):
    for a, refs in load(fn).items():
        for b in refs:
            if a != b:
                merged[a].add(b)

pdfs = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(ROOT, "papers", "*", "pdfs", "*.pdf"))}
existing = load("semantic_edges.json")

out = []
for a in sorted(merged):
    if a not in pdfs or a not in idx:
        continue
    try:
        text = subprocess.run(["pdftotext", "-q", pdfs[a], "-"],
                              capture_output=True, text=True, timeout=120).stdout
    except Exception:
        text = ""
    m = re.search(r"\n\s*(references|bibliography)\s*\n", text, re.I)
    body = text[:m.start()] if m else text
    bodyn = re.sub(r"\s+", " ", body)
    low = bodyn.lower()
    for b in sorted(merged[a]):
        if b not in idx:
            continue
        key = f"{a}->{b}"
        if key in existing:
            continue
        cues = [b]
        au = authors.get(b, [])
        if au:
            cues.append(au[0].split()[-1])
        cues += [w for w in re.findall(r"[A-Za-z]{7,}", idx[b]["title"])][:3]
        ctx = ""
        for cue in cues:
            i = low.find(cue.lower())
            if i >= 0:
                ctx = bodyn[max(0, i - 220): i + 220].strip()
                break
        out.append({
            "key": key,
            "from": idx[a]["title"],
            "to": idx[b]["title"],
            "context": ctx or "(appears only in reference list; no in-text context found)"
        })

json.dump(out, open(os.path.join(CACHE, "edges_to_label.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"edges needing labels: {len(out)}  (already labeled: {len(existing)})")
print(f"distinct citing papers parsed: {sum(1 for a in merged if a in pdfs)}")
