# On Measuring Vulnerable JavaScript Functions in the Wild

**Authors:** Maryna Kluban, Mohammad Mannan, Amr Youssef (Concordia University, Montreal)
**Venue / Year:** ACM AsiaCCS 2022 (ASIA CCS '22, May 30 – June 3 2022, Nagasaki, Japan), 14 pages
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3488932.3497769) · [author PDF](https://users.encs.concordia.ca/~mmannan/publications/JS-vulnerability-aisaccs2022.pdf) · DOI 10.1145/3488932.3497769 · extended journal version: ACM TOPS, "On Detecting and Measuring Exploitable JavaScript Functions in Real-world Applications"
**Scope tag:** ADJACENT
**Grounding:** full text read from the Concordia author-hosted PDF — abstract, Section 1, Sections 5.1–5.4 and Section 6 opening, including Tables 3 and 4. Sections 2–4 (related work, dataset construction, manual verification) were read in outline only; this is flagged again in §6 below.

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It makes and empirically defends the argument a vulnerability-discovery thesis needs when it triages an Electron app's dependency tree — that package-level CVE matching is the wrong granularity, because most projects flagged via a vulnerable dependency never call the vulnerable function at all.

> **한 줄 요약 (KO):** "이 프로젝트가 취약한 npm 패키지를 쓴다"는 패키지 단위 판정은 부정확하다(선행연구 기준 그렇게 표시된 프로젝트의 73.3%는 실제로 취약 함수를 호출하지 않음). 저자들은 Snyk + VulnCode-DB에서 검증된 취약 JS 함수 1,360개 데이터셋을 만들고, Semgrep 의미 기반 패턴 + Simhash/SHA-1 텍스트 유사도로 npm 패키지·Chrome 확장·인기 웹사이트에서 수집한 920만 개 함수를 훑어 **함수 단위로** 취약 코드 11,148개를 찾아냈다(평균 정밀도 약 94.5%).

## 1. Problem, Gap & Hypothesis

JavaScript runs in 97.5% of web applications and on both client and server, so its vulnerabilities are high-value. But the literature on JavaScript vulnerability measurement is almost entirely **package-level**: it tracks which projects depend on a package with a known CVE. The authors' central objection, stated in Section 1, is that this granularity is *imprecise in a specific, measurable direction*: a project that depends on a vulnerable package very often never invokes the vulnerable function, and even invoking it may not be a security problem if the function cannot be reached with exploitable inputs. They quote Zapata et al.: **73.3%** of projects flagged as vulnerable this way are not actually vulnerable.

The few code-level alternatives performed poorly. Ferenc et al. train ML on static code metrics and reach only F1 ≈ 0.7; Mosolygó et al. use generalised line representations and cosine distance and report **97.3% false positives**.

A second, compounding gap is **data**. Ferenc et al. published the first public dataset of JS functions with 1,496 marked vulnerable; Mosolygó et al. manually filtered it down to 443; the present authors report that even that filtered set still contains non-vulnerable functions.

Hypothesis: with a properly verified vulnerable-function corpus, a combination of *semantics-aware pattern matching* and *textual near-duplicate detection* can shift JavaScript vulnerability measurement from package granularity to **function granularity**, improving precision and enabling timely, targeted patching.

> **(KO)** 이 논쟁 구도가 본 학위논문에 직접 유용하다. Electron 앱은 수백~수천 개의 npm 의존성을 번들로 포함하므로 `npm audit` 류의 패키지 단위 경고가 대량으로 뜨지만 대부분 도달 불가능하다. "무엇이 실제로 도달 가능한 취약점인가"를 가려내는 근거 논문으로 쓸 수 있다.

## 2. Methodology

**(a) Building a verified vulnerable-function corpus.** Crawl the **Snyk** vulnerability database and the **VulnCode-DB** project for metadata (description, CVE number, affected project and version) *and* the corresponding code/functions. Then semi-automated verification: the authors wrote vulnerability patterns plus a purpose-built web tool for efficient manual review. The crawler is automated so the corpus can be refreshed as new vulnerabilities are reported. Final corpus: **1,360 verified vulnerable JavaScript functions.**

**(b) Detection framework — two complementary search strategies.**
1. *Vulnerable pattern search (semantics-based).* Hand-written **Semgrep** rule sets for two vulnerability classes: **prototype pollution** and **ReDoS**. Pipeline per function: run the prototype-pollution rule set and flag on match; extract regular expressions and run the `safe-regex` module to find "evil" regexes; run the ReDoS rule sets only on functions that carry an evil regex, and flag on match. The same rule sets were reused to semi-automate verification of the corpus in (a).
2. *Textual similarity search.* Tokenise every function in both the vulnerable corpus and the real-world corpus, then compute a content-sensitive **Simhash** and a **SHA-1** cryptographic hash. Simhash finds near-duplicates of known-vulnerable code; SHA-1 finds exact copies modulo variable names — and because exact matches are guaranteed identical, **SHA-1 hits need no manual verification and count automatically as true positives**.

**(c) Nested-function de-duplication.** Pattern search frequently matched several nested functions in one file against the same vulnerable equivalent. A post-filter keeps only the innermost (child) function, so "unique detections" are reported separately from raw matches.

> **(KO)** 두 검색 전략의 성질이 다르다는 점이 중요하다. Semgrep 패턴은 **알려지지 않은** 신규 취약 함수도 잡을 수 있고(패턴이 의미 기반이므로), 해시 유사도는 **알려진 취약 함수의 복붙 사본**만 잡는다. Electron 앱 감사에 옮긴다면 전자는 앱 자체 코드에, 후자는 번들된 vendored 라이브러리에 각각 유효하다.

## 3. Experiments / Evaluation Setup

**Real-world corpus — three environments (Table 3):**

| Dataset | Entries | Functions |
|---|---|---|
| NPM packages | 3,000 | 413,774 |
| Chrome extensions | 557 | 2,659,649 |
| Top websites | 1,893 | 5,739,271 |
| **Total** | **5,450** | **9,205,624** |

- **npm:** JavaScript files pulled from the GitHub repositories of the 3,000 most popular packages.
- **Chrome extensions:** source downloaded and unpacked for the 600 most popular Web Store extensions; 43 could not be retrieved via the Web Store API, leaving 557.
- **Websites:** the 20,000 most popular domains from the **Cisco Umbrella** list; inline `<script>` content and linked JS files were saved. **18,107** returned static HTML with no JavaScript, a non-HTML response, or an HTTP error — leaving JS for only **1,893** sites.
- Test files (`spec.js`, `test` in the path), empty-bodied functions, and one-statement functions were filtered out. Duplicate functions belonging to distinct sources are retained.

**Compute split (Section 5.3).** Textual-similarity search is cheap and ran on all 9,205,654 functions. Semgrep is expensive and ran on **795,912** functions only: **171,109** from npm (1,300 packages), **325,978** from Chrome extensions (31 extensions), **298,825** from websites (122 websites).

**Validation protocol.** 100 random prototype-pollution findings and 100 random ReDoS findings were manually checked on three criteria — pattern correctly matched, input genuinely originates outside the function, and no protection measure missed by the rules. For fuzzy hashing, 90 of 965 matches were diffed against the matching vulnerable function.

## 4. Results / Key Findings

**Detections (Table 4).**

| Method | NPM | Extensions | Websites | Total | Unique |
|---|---|---|---|---|---|
| Prototype pollution (patterns) | 4,592 | 7,080 | 6,690 | 18,362 | 9,858 |
| ReDoS (patterns) | 552 | 542 | 626 | 1,720 | 669 |
| **Pattern total** | **5,144** | **7,622** | **7,316** | **20,082** | **10,527** |
| Fuzzy (Simhash) | 56 | 201 | 1,063 | 1,320 | 965 |
| Crypto (SHA-1) | 30 | 85 | 16 | 131 | 131 |

- **Headline: 11,148 unique vulnerable functions** detected by at least one method, of which **10,527** are prototype pollution or ReDoS and **621** are other types carried in the corpus.
- **Simhash vulnerability-type breakdown** across the whole 9.2M-function corpus: XSS 307, ReDoS 306, prototype pollution 138, command injection 133, directory traversal 72, SQL injection 68, DoS 59, others 237.
- **SHA-1 breakdown** (131 exact copies, all also caught by Simhash): ReDoS 29, XSS 26, command injection 25, prototype pollution 14, timing attack 5, DoS 1, others 31.
- Every ReDoS and prototype-pollution finding from the textual methods was *also* caught by the Semgrep rules — expected, since the rules were derived from the same corpus the hashes match against.
- **Precision:** prototype pollution **92%** (8 false positives in 100), ReDoS **97%** (3 in 100), fuzzy hashing **98%** (2 in 90). Stated average precision **~94.5%**.
- **Why the false positives happen** — a genuinely useful diagnosis for anyone reusing these rules. For prototype pollution: (i) JavaScript's `obj[key] = value` is syntactically identical for object property assignment and array index assignment, and without explicit types the pattern cannot tell them apart — but only the object case pollutes; (ii) obfuscation left the vulnerable pattern intact while obscuring the *protection* code, so guards were missed. For ReDoS: the function held several regexes, and the user input flowed into a safe one rather than the evil one.
- **Case studies:** 15 findings across 10 popular/critical projects were examined in depth — eight prototype pollution, five ReDoS, and one project (**SailsJS**) with both. **All 15 were confirmed exploitable**, and after searching NVD, Snyk and project-specific sources the authors could find **no public report of any of them**, i.e. these were previously unknown. Disclosure was in progress at publication.

## 5. How to cite in Related Work

> Dependency-level vulnerability reporting systematically overstates exposure: a project flagged because it depends on a package with a known CVE frequently never calls the vulnerable function, and prior work found this to be the case for 73.3% of such projects. Kluban et al. therefore move the unit of measurement from the package to the function, assembling a semi-automatically verified corpus of 1,360 vulnerable JavaScript functions from Snyk and VulnCode-DB and combining semantics-aware Semgrep rules for prototype pollution and ReDoS with Simhash and cryptographic-hash near-duplicate detection [Kluban et al., AsiaCCS '22]. Across 9.2M functions drawn from 3,000 npm packages, 557 Chrome extensions and 1,893 popular websites they identify 11,148 vulnerable functions at an estimated 94.5% average precision, and confirm 15 previously unreported exploitable findings in ten widely used projects. This granularity argument applies directly to Electron applications, which bundle large npm dependency closures into the shipped artefact and consequently accumulate large volumes of dependency-level alerts whose reachability is unknown.

> **(KO) 논문 내 위치:** **트리아지 정당화**와 **방법론 차용** 두 용도.
> - **트리아지 정당화:** Electron 앱을 대상으로 취약점을 발굴할 때, `npm audit`이 뱉는 수백 개 경고를 전부 다루지 않고 골라내는 행위에 근거가 필요하다. 이 논문의 73.3% 수치와 함수 단위 접근이 그 근거다.
> - **방법론 차용:** Semgrep 의미 패턴 + 해시 유사도의 조합은 Electron 앱의 **번들된(asar에 패킹된) 자바스크립트**에 그대로 적용 가능하다 — 오히려 웹사이트보다 조건이 좋다(난독화가 덜하고 원본 모듈 경계가 보존됨).
> - **남긴 빈틈 (본 논문의 기여 공간):** 이 논문은 **함수가 존재하는가**까지만 측정하고, **그 함수에 공격자 입력이 실제로 도달하는가**는 15건 사례 연구에서 수동으로만 확인했다(§6에서 저자들도 한계로 인정). Electron에서는 도달 경로가 명확히 정의된다 — 렌더러의 DOM 입력 → preload/contextBridge → IPC → 메인 프로세스. 즉 Electron은 이 논문이 자동화하지 못한 "도달성" 부분을 **구조적으로 자동화할 수 있는 드문 환경**이며, 이것이 본 학위논문이 이 논문 위에 쌓을 수 있는 지점이다.
> - Chrome 확장 데이터셋이 포함되어 있어, 이미 in_scope인 UntrustIDE(VS Code 확장)와 함께 "확장 생태계의 취약 코드" 절을 구성할 때 나란히 인용하기 좋다.

## 6. Caveats / what I could not confirm from the text

- **Only two vulnerability classes are covered by the semantics-based rules** — prototype pollution and ReDoS. The other classes (XSS, command injection, SQL injection, directory traversal, timing) appear *only* through textual near-duplicate matching, i.e. only where someone copied known-vulnerable code nearly verbatim. The 11,148 headline is therefore heavily weighted toward two classes (10,527 of it).
- **Semgrep ran on only 795,912 of the 9,205,654 functions (~8.6%)**, and on a small number of entities — 31 extensions and 122 websites. The per-environment pattern counts in Table 4 are therefore not comparable across environments as prevalence rates; they are counts from unequal, compute-limited samples. This is easy to misquote and should not be reported as "npm is safer than extensions".
- **Precision is estimated from a 100+100+90 manual sample**, not a full audit; the authors themselves call it "based on manual verification of a small subset". No recall figure is given at all — there is no ground truth for how many vulnerable functions were missed.
- **Reachability is not automated.** The framework flags that a vulnerable pattern *exists*; whether attacker-controlled input reaches it was established by hand only for the 15 case studies.
- **Nothing desktop.** No Electron, CEF or WebView target appears anywhere; the paper is admitted as ADJACENT for the npm corpus, the prototype-pollution focus (a class already well represented in this ledger) and the granularity argument.
- Sections 2 (related work), 4.1–4.4 (corpus construction and verification protocol) and 7 (limitations/future work) were read in outline only. In particular I did not verify the internal composition of the 1,360-function corpus, nor read the authors' own limitations section in full — some of the caveats above are my own reading of Sections 5–6 rather than restatements of theirs.
- The extended ACM TOPS journal version ("On Detecting and Measuring Exploitable JavaScript Functions in Real-world Applications") was **not** read; its numbers likely supersede these and should be checked before citing figures in the final thesis.
