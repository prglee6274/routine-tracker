#!/usr/bin/env python3
"""Extract author lists (from per-day markdown) and intra-corpus citations
(from PDF reference lists) for the papers relationship graph.

Results are cached under graph/cache/ so daily runs only process NEW papers.

Usage:
  python3 extract.py authors   # fast, markdown only
  python3 extract.py cites     # slow, pdftotext over new PDFs
  python3 extract.py all
"""
import json, glob, os, re, subprocess, sys, time

ROOT = os.environ.get("RT_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE = os.path.join(ROOT, "graph", "cache")
os.makedirs(CACHE, exist_ok=True)

def load(fn, default):
    p = os.path.join(CACHE, fn)
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return default
    return default

def save(fn, obj):
    json.dump(obj, open(os.path.join(CACHE, fn), "w", encoding="utf-8"), ensure_ascii=False, indent=0)

idx = json.load(open(os.path.join(ROOT, "papers", "INDEX.json"), encoding="utf-8"))["entries"]
corpus = set(idx)

# ---------------- authors from markdown ----------------
def clean_authors(s):
    s = re.sub(r"\(.*?\)", "", s)            # drop parentheticals (often korean notes)
    s = re.sub(r"(?i)\bet\s*al\.?", "", s)   # drop 'et al.'
    s = s.replace("**", "").replace("`", "")
    parts = re.split(r"[,;·]", s)
    out = []
    for p in parts:
        p = p.strip().strip(".").strip()
        if not p or len(p) < 2 or len(p) > 40:
            continue
        if re.search(r"[가-힣]", p):          # drop korean tokens
            continue
        out.append(p)
    return out

def extract_authors():
    authors = load("authors.json", {})
    md_files = glob.glob(os.path.join(ROOT, "papers", "*", "*.md")) + \
               glob.glob(os.path.join(ROOT, "papers", "*.md"))
    for mf in md_files:
        txt = open(mf, encoding="utf-8", errors="ignore").read()
        for sec in re.split(r"\n##\s", txt):
            mid = re.search(r"arxiv\.org/abs/(\d{4}\.\d{4,5})", sec)
            if not mid:
                continue
            aid = mid.group(1)
            if aid in authors:
                continue
            ma = re.search(r"저자[^\n:：]*[:：]\s*([^\n]+)", sec)
            if not ma:
                continue
            al = clean_authors(ma.group(1))
            if al:
                authors[aid] = al
    save("authors.json", authors)
    return authors

# ---------------- citations from PDFs ----------------
def extract_citations(logf=None):
    cites = load("citations.json", {})
    pdfs = {}
    for p in glob.glob(os.path.join(ROOT, "papers", "*", "pdfs", "*.pdf")):
        pdfs[os.path.basename(p)[:-4]] = p
    todo = [pid for pid in pdfs if pid not in cites]
    for i, pid in enumerate(todo):
        try:
            txt = subprocess.run(["pdftotext", "-q", pdfs[pid], "-"],
                                 capture_output=True, text=True, timeout=120).stdout
        except Exception:
            txt = ""
        ids = set(re.findall(r"(\d{4}\.\d{4,5})", txt))
        cites[pid] = sorted(c for c in ids if c in corpus and c != pid)
        if i % 20 == 0:
            save("citations.json", cites)
            if logf:
                open(logf, "a").write(f"{time.strftime('%H:%M:%S')} cites {i}/{len(todo)}\n")
    save("citations.json", cites)
    if logf:
        open(logf, "a").write(f"DONE cites +{len(todo)} (total {len(cites)})\n")
    return cites

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("authors", "all"):
        a = extract_authors()
        print("authors cached:", len(a))
    if mode in ("cites", "all"):
        c = extract_citations(os.path.join(CACHE, "extract.log"))
        print("citations cached:", len(c))
