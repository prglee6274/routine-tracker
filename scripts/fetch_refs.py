#!/usr/bin/env python3
"""
Fetch references for an arxiv paper from its ar5iv HTML and cache them.

Strategy:
  1. Try https://arxiv.org/html/{id}v1 (latest version uses suffix from arxiv).
  2. Fall back to /html/{id} (no version).
  3. Parse <li class="ltx_bibitem"> elements, extracting tag, authors, title, venue, year,
     and any arxiv links found inside.
  4. Save to papers/refs/{id}.json with shape:
        {
          "arxiv_id": "...",
          "source": "arxiv-html v1",
          "fetched_at": "YYYY-MM-DD",
          "references": [
            {"idx": 1, "label": "Angrist et al. [1996]",
             "text": "Joshua D. Angrist ... Identification of causal effects ... JASA, 91(434):444-455, 1996.",
             "year": 1996, "arxiv_id": null, "url": null},
            ...
          ]
        }

If references cannot be parsed (no HTML build), write a stub with "references": [] and reason.

Usage:
  python3 fetch_refs.py <arxiv_id> [<arxiv_id> ...]
  python3 fetch_refs.py --backfill              # fetch any base_id in INDEX.json without refs file
"""
import argparse, json, os, re, sys, time, datetime, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(os.environ.get("PAPERS_ROOT", "/sessions/jolly-inspiring-goldberg/mnt/routine 생성/papers"))
INDEX = ROOT / "INDEX.json"
REFS_DIR = ROOT / "refs"
REFS_DIR.mkdir(parents=True, exist_ok=True)

UA = "paper-tracker/1.0 (research notebook; contact gwangyeal@gmail.com)"
TIMEOUT = 30

def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace"), r.status

def strip_html(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#x2013;","-").replace("&#x2014;","-")
    return s

ARXIV_RE = re.compile(r"(?:arxiv\.org/abs/|arxiv:)\s*(\d{4}\.\d{4,5})", re.I)

def parse_bibitems(html):
    """Return list of dicts."""
    # The reference list is a <ul class="ltx_biblist"> ... </ul>
    # ar5iv-rendered pages have either <ul class="ltx_biblist"> or <ul id="bib.L1" class="ltx_biblist">.
    # Find the opening tag containing ltx_biblist, then take body until the matching </ul>.
    m = re.search(r'<ul[^>]*\bclass="[^"]*ltx_biblist[^"]*"[^>]*>', html)
    if not m: return []
    body = html[m.end():]
    # Each top-level bibitem <li> may contain nested <ul>; we look for them directly rather than
    # trying to balance the outer <ul>.
    items = re.findall(r'<li id="bib\.bib(\d+)"[^>]*class="[^"]*ltx_bibitem[^"]*"[^>]*>(.*?)</li>', body, flags=re.S)
    refs = []
    for idx, raw in items:
        # Extract the label tag (e.g. "Angrist et al. [1996]")
        m_label = re.search(r'<span class="ltx_tag ltx_role_refnum ltx_tag_bibitem"[^>]*>(.*?)</span>', raw, flags=re.S)
        label = strip_html(m_label.group(1)) if m_label else ""
        # Concat all ltx_bibblock contents into one text
        blocks = re.findall(r'<span class="ltx_bibblock"[^>]*>(.*?)</span>', raw, flags=re.S)
        text = strip_html(" ".join(blocks))
        # year (4-digit, last one wins)
        years = re.findall(r"\b(19|20|21|22|23|24|25|26|27|28)(\d{2})\b", text)
        year = None
        for prefix, suffix in years:
            try:
                year = int(prefix + suffix)
            except: pass
        # arxiv id inside text or raw
        m_ax = ARXIV_RE.search(text) or ARXIV_RE.search(raw)
        arxiv_id = m_ax.group(1) if m_ax else None
        # Any URL inside <a href="...">
        m_url = re.search(r'<a[^>]+href="(https?://[^"]+)"', raw)
        url = m_url.group(1) if m_url else None
        refs.append({
            "idx": int(idx),
            "label": label,
            "text": text,
            "year": year,
            "arxiv_id": arxiv_id,
            "url": url,
        })
    return refs

def fetch_one(aid, sleep=1.0, force=False):
    out_path = REFS_DIR / f"{aid}.json"
    if out_path.exists() and not force:
        return {"arxiv_id": aid, "status": "cached", "n": json.loads(out_path.read_text()).get("count", 0)}
    last_err = None
    for url in (f"https://arxiv.org/html/{aid}v1", f"https://arxiv.org/html/{aid}"):
        try:
            html, status = http_get(url)
            if status != 200 or "ltx_biblist" not in html:
                last_err = f"no_biblist({status})"
                continue
            refs = parse_bibitems(html)
            payload = {
                "arxiv_id": aid,
                "source": url,
                "fetched_at": datetime.date.today().isoformat(),
                "count": len(refs),
                "references": refs,
            }
            out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            time.sleep(sleep)
            return {"arxiv_id": aid, "status": "ok", "n": len(refs)}
        except urllib.error.HTTPError as e:
            last_err = f"http_{e.code}"
        except Exception as e:
            last_err = f"err_{type(e).__name__}"
        time.sleep(sleep)
    # Write a stub so we don't retry forever in backfill
    payload = {
        "arxiv_id": aid,
        "source": None,
        "fetched_at": datetime.date.today().isoformat(),
        "count": 0,
        "references": [],
        "note": f"unavailable: {last_err}",
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return {"arxiv_id": aid, "status": "miss", "reason": last_err}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="arxiv base IDs (e.g. 2605.08012)")
    ap.add_argument("--backfill", action="store_true", help="fetch refs for every INDEX entry without a cache file")
    ap.add_argument("--force", action="store_true", help="re-fetch even if cached")
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args()

    targets = list(args.ids)
    if args.backfill:
        idx = json.loads(INDEX.read_text())
        for aid in idx["entries"]:
            if args.force or not (REFS_DIR / f"{aid}.json").exists():
                targets.append(aid)
    if not targets:
        print("nothing to do; pass IDs or --backfill")
        return

    ok = miss = 0
    for aid in targets:
        res = fetch_one(aid, sleep=args.sleep, force=args.force)
        line = f"{aid:15s} {res['status']:7s} n={res.get('n', '-')}"
        if res["status"] == "miss":
            line += f" ({res.get('reason')})"
            miss += 1
        else:
            ok += 1
        print(line, flush=True)
    print(f"\nsummary: ok={ok} miss={miss} total={len(targets)}")

if __name__ == "__main__":
    main()
