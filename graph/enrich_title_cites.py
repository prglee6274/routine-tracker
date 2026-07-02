#!/usr/bin/env python3
"""Enrich citation edges by matching corpus paper TITLES inside each PDF's
reference section (many papers cite each other by title, not arXiv id).

Strict to avoid false positives: only titles with >=6 words / >=40 chars,
matched verbatim (whitespace-normalized) within the References section.

Writes graph/cache/citations_title.json = {citing_id: [cited_id,...]}  (incremental)
"""
import json, glob, os, re, subprocess, sys, time

ROOT = os.environ.get("RT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "graph", "cache")
idx = json.load(open(os.path.join(ROOT, "papers", "INDEX.json"), encoding="utf-8"))["entries"]

def norm(s):
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

# title -> id, only distinctive titles
tmap = {}
for aid, e in idx.items():
    t = norm(e.get("title", ""))
    if len(t) >= 40 and len(t.split()) >= 6:
        tmap[t] = aid

out_f = os.path.join(CACHE, "citations_title.json")
out = json.load(open(out_f, encoding="utf-8")) if os.path.exists(out_f) else {}

pdfs = {os.path.basename(p)[:-4]: p for p in glob.glob(os.path.join(ROOT, "papers", "*", "pdfs", "*.pdf"))}
todo = [pid for pid in pdfs if pid not in out]
titles = list(tmap.items())

for i, pid in enumerate(todo):
    try:
        txt = subprocess.run(["pdftotext", "-q", pdfs[pid], "-"],
                             capture_output=True, text=True, timeout=120).stdout
    except Exception:
        out[pid] = []; continue
    # references section only (last occurrence of a references heading)
    m = list(re.finditer(r"\n\s*(references|bibliography)\s*\n", txt, re.I))
    ref = txt[m[-1].end():] if m else txt
    refn = norm(ref)
    found = []
    for t, cid in titles:
        if cid == pid:
            continue
        if t in refn:
            found.append(cid)
    out[pid] = sorted(set(found))
    if i % 20 == 0:
        json.dump(out, open(out_f, "w"), ensure_ascii=False)
        open(os.path.join(CACHE, "extract.log"), "a").write(
            f"{time.strftime('%H:%M:%S')} titlecite {i}/{len(todo)}\n")
json.dump(out, open(out_f, "w"), ensure_ascii=False)
tot = sum(len(v) for v in out.values())
print(f"title-cite parsed {len(out)} papers, {tot} title-matched edges (+{len(todo)} new)")
