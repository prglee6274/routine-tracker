# Daily watch — how the routine works

This file documents what the scheduled "daily watch" does each run. It is the human-readable spec; the actual run is driven by the scheduled task of the same project.

## What it does, each run

1. **Load state.** Read `config/sources.json` (venues, keywords, scope) and `ledger/seen_papers.json` (everything already triaged).
2. **Collect candidates.** For each of the 9 venues, gather recent paper titles:
   - Run the `standing_queries` from the config via web search (most reliable for this niche).
   - Fetch each venue's accepted-papers page where one exists.
   - Optionally scan the DBLP TOC for the current year.
3. **Filter.** Keep only titles/abstracts matching the `keywords` and the in-scope rules; drop the out-of-scope categories.
4. **Diff.** Normalize each surviving title (lowercase, alphanumerics + single spaces) and drop any already present in `in_scope` or `excluded`.
5. **Triage what's left.**
   - If clearly in scope → fetch the paper, write a note in `papers/<id>.md` using the 6-part template, and append an `in_scope` entry to the ledger.
   - If considered but out of scope → append to `excluded` with a one-line reason (so it is never re-surfaced).
6. **Record.** Update `last_updated`/`last_run` in the ledger, add a line to `CHANGELOG.md`, and `git add -A && git commit`.
7. **Report.** If anything new was added, surface a short summary; if nothing new, say so (this will be the common case — see cadence).

## Cadence reality

Security venues do **not** publish daily — accepted-paper lists drop a few times a year. So most daily runs will legitimately find nothing new, and that is fine: the cost is negligible and it guarantees you catch a new paper within a day of it appearing. (A weekly cadence would catch essentially the same papers; daily is just lower-latency.)

## The 6-part note template

```
# <Title>
**Authors:** … **Venue / Year:** … **Links:** paper · PDF · DOI
**Scope tag:** PRIMARY | ADJACENT
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** …
> **한 줄 요약 (KO):** …
## 1. Problem, Gap & Hypothesis        (+ KO comment)
## 2. Methodology                      (+ KO)
## 3. Experiments / Evaluation Setup   (+ KO)
## 4. Results / Key Findings           (+ KO)
## 5. How to cite in Related Work      (2–4 draft EN sentences + KO positioning note)
## 6. Caveats / what I could not confirm from the text
```

English body, short Korean `(KO)` comments. Ground every number in the actual paper; if the full text is unreachable (e.g., ACM paywall), write from the abstract + reachable secondary sources and **say so at the top of the note**.

## Tooling notes (so a fresh run doesn't relearn them)

- Use **web search** + **web_fetch on HTML pages**. JSON APIs (DBLP `/search/api`, `api.semanticscholar.org`) return **empty** via web_fetch, and the sandbox shell has **no outbound network**, so don't try `curl`/`wget`.
- Large HTML pages are saved to a file by web_fetch — read that file in chunks or grep it for keywords.
- USENIX PDFs are open; IEEE/NDSS usually have author or arXiv PDFs; **ACM is paywalled** — look for an author-hosted copy.

## A note on persistence & GitHub

For the daily watch to work, this repo must live at a **stable path** the scheduled task can reopen across sessions (a connected folder on your machine, ideally inside your thesis git project). Automated `git push` to GitHub is **not** available from this environment (no GitHub connector, no outbound network in the sandbox): each run commits **locally**, and you push to GitHub from your own machine — or set up a tiny local auto-push (a `post-commit` hook or your own cron running `git push`).
