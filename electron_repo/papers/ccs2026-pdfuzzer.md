# From Documentation to Zero-day Vulnerabilities: LLM-Driven Fuzzing of JavaScript Engines in PDF Readers

> **⚠️ GROUNDING WARNING — read before quoting anything below.**
> This note is written from the **arXiv abstract page (arXiv:2608.06641v1) and its metadata only**, plus the paper's row on the official ACM CCS 2026 accepted-papers page. **The full text was NOT read.** A `web_fetch` of `https://arxiv.org/pdf/2608.06641` was attempted on 2026-08-22 and returned **HTTP 429 (Cowork web_fetch rate limit exceeded)**; per the runbook it was not retried in a loop. arXiv offers **no HTML (experimental) rendering** for this submission — only `View PDF` and `TeX Source` — so the cheap HTML channel that worked for other papers is not available here.
> Every number below traces to the abstract. **Section structure, dataset construction, per-reader breakdowns, the CVE list, the ablation table and the coverage methodology are all unread and must not be cited.**

**Authors:** Suyue Guo, Stijn Pletinckx, Tianle Yu, Yigitcan Kaya, Saad Ullah, Wenbo Guo, Christopher Kruegel, Giovanni Vigna (UC Santa Barbara; author affiliations inferred from the CCS listing entry "Suyue Guo (UC Santa Barbara)" — the arXiv page lists no affiliations)
**Venue / Year:** ACM CCS 2026 (First Cycle) — The Hague, 15–19 November 2026
**Links:** [CCS 2026 accepted papers](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html) · [arXiv:2608.06641](https://arxiv.org/abs/2608.06641) · PDF: `https://arxiv.org/pdf/2608.06641` (CC-BY 4.0, 16 pages, 2 figures; arXiv DOI `10.48550/arXiv.2608.06641`, pending registration) · DOI (ACM): not yet assigned
**Tool name:** PDFuzzer
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** it is the same structural target as Electron — a **native desktop application that embeds a JavaScript engine and exposes a large, documented, privileged host API surface to script** — and it demonstrates that the *vendor's own API documentation* can be turned into the grammar that drives vulnerability discovery against that surface.

> **한 줄 요약 (KO):** PDF 뷰어에 내장된 JavaScript 엔진을, **공식 API 매뉴얼에서 LLM으로 추출한 문법과 API 간 관계**를 이용해 시퀀스 단위로 퍼징하여 3개 상용 리더에서 zero-day 31개를 찾아낸 연구. Electron이 아니지만 "데스크톱 앱 + 내장 JS 런타임 + 문서화된 특권 API"라는 구조가 동일하다.

---

## 1. Problem, Gap & Hypothesis

**Problem.** Mainstream PDF readers ship a full JavaScript engine plus a large host-object API (the Acrobat JS API and its Foxit / PDF-XChange equivalents) that script inside a document can call. That API reaches well past the document into the host process, so a bug in it is a bug in a desktop application, reachable by merely opening a file.

**Gap the authors claim.** Existing PDF-reader fuzzers "rely on simple test cases that involve only individual API calls, leading to limited coverage and potentially missing vulnerabilities that require **sequences** of API calls." The named prior art is **TypeOracle, Favocado and Cooper** on the PDF-fuzzing side and **Fuzz4All** plus a naive-LLM baseline on the LLM-fuzzing side.

**Hypothesis.** If the relationships *between* API calls — which call must precede which, what object each returns, what state each requires — can be recovered automatically, a fuzzer can synthesize semantically valid multi-call sequences and reach engine states that single-call fuzzing cannot.

> **(KO)** 핵심 갭은 "단일 API 호출 테스트케이스"의 한계다. 실제 취약점은 **여러 API 호출이 순서대로 이어져야** 도달하는 상태에 숨어 있다는 것. 이 문제 설정은 Electron의 IPC 채널을 하나씩 때리는 방식 vs. 여러 채널을 연쇄시키는 방식의 차이와 정확히 같은 형태다.

## 2. Methodology

Two stages, per the abstract:

1. **LLM-based specification mining.** An LLM constructs **context-free grammars** and infers **relationships between individual API calls**, working from two inputs: (a) specifications extracted from the readers' **JavaScript API manuals**, and (b) **execution traces**.
2. **Constraint-solver-driven sequence generation.** Given the grammars and the inferred inter-call relationships, PDFuzzer uses a **constraint solver** to emit *concrete* API call sequences, which become the fuzzing inputs.

> **(KO)** 방법론의 새로움은 LLM을 "입력 생성기"가 아니라 **명세 추출기**로 쓴 데 있다. 매뉴얼 → CFG + API 관계 그래프 → 제약 해결기 → 구체적 호출 시퀀스. LLM이 직접 페이로드를 뱉는 naive 방식(Fuzz4All 등)과 대비된다. **주의: 파이프라인 세부 단계 수, 사용한 LLM 모델, 제약 해결기 종류는 초록에 없어 확인 불가.**

## 3. Experiments / Evaluation Setup

Grounded from the abstract only:

- **Targets — 3 mainstream PDF readers:** Adobe Acrobat Reader, Foxit PDF Reader, PDF-XChange Editor.
- **Baselines — 5:** TypeOracle, Favocado, Cooper (state-of-the-art PDF fuzzers); Fuzz4All and a naive-LLM fuzzer (LLM-based fuzzers).
- **Measured:** code coverage; number of zero-day vulnerabilities found; per-stage LLM accuracy (ablation).
- **Ablation:** the authors report an ablation "validat[ing] the necessity of each component, including LLMs."

**Not recoverable from the abstract:** fuzzing budget (hours/CPU), number of trials, coverage instrumentation used, seed corpus, reader version numbers, hardware. **Do not invent these.**

> **(KO)** 타깃 3종·베이스라인 5종은 확실하다. 반면 **퍼징 시간, 시도 횟수, 커버리지 측정 도구, 리더 버전**은 초록에 없다. 인용 시 이 수치들을 추정해 쓰면 안 된다.

## 4. Results / Key Findings

Every number here is from the abstract:

| Claim | Value |
|---|---|
| Coverage vs. existing tools | **up to 48% higher** |
| Zero-day vulnerabilities found | **31**, across the three readers |
| Severity range | **information leakage → arbitrary code execution** |
| LLM accuracy across pipeline stages | **93–98%** |
| Disclosure | coordinated vulnerability disclosure to vendors; **bug bounties received** |

**Not stated in the abstract:** how the 31 split across Acrobat / Foxit / PDF-XChange, how many reached ACE specifically, how many CVEs were assigned, or which of the three readers "up to 48%" refers to.

> **(KO)** 31개 zero-day, 최대 48% 커버리지 향상, LLM 단계별 정확도 93–98%. **리더별 분포·CVE 개수·ACE 도달 개수는 초록에 없다.**

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Beyond the browser, native desktop applications increasingly embed a JavaScript engine and expose a large privileged host API to document-supplied script. Guo et al. show that this surface is a productive target: their PDFuzzer synthesizes multi-call API sequences from grammars and inter-call relationships that an LLM mines directly from vendor JavaScript API manuals and execution traces, and a constraint solver then instantiates them into concrete inputs [CCS'26]. Evaluated on Adobe Acrobat Reader, Foxit PDF Reader and PDF-XChange Editor, PDFuzzer attains up to 48% higher coverage than TypeOracle, Favocado, Cooper, Fuzz4All and a naive-LLM baseline, and uncovers 31 zero-day vulnerabilities ranging from information leakage to arbitrary code execution. Their result underlines a point that applies equally to Electron: the *documented* host API surface, not just its undocumented internals, is where reachable desktop-privilege bugs live.

> **(KO) 취약점 발견 논문 관점에서의 포지셔닝:**
> - **동기(motivation)로 쓰기 좋다.** "데스크톱 앱에 내장된 스크립트 런타임 + 특권 호스트 API"라는 문제 구조가 Electron과 동형이라는 점을 근거로, Electron에서 같은 질문을 던지는 것의 정당성을 확보할 수 있다.
> - **방법론을 빌려올 수 있다.** PDF 리더의 "JavaScript API 매뉴얼"에 해당하는 것이 Electron에는 **공식 API 문서(`ipcMain`/`ipcRenderer`/`contextBridge`/`shell`/`BrowserWindow` 등)와 각 앱의 preload 스크립트**다. 문서에서 CFG + API 관계를 뽑아 시퀀스를 합성하는 파이프라인은 그대로 이식 가능한 아이디어다.
> - **남겨둔 갭(이 논문이 열어두는 공간).** ① 이들은 **단일 프로세스 내부의 엔진 메모리 안전성**을 본다 — 프로세스 경계를 넘는 전파(Electron의 renderer→main IPC)는 다루지 않는다. ② 타깃이 **클로즈드소스 상용 리더**라 블랙박스 퍼징이지만, Electron 앱은 대부분 소스가 asar 안에 그대로 있어 정적 분석과 결합할 여지가 훨씬 크다. ③ 소스(source)가 **문서 파일 하나**로 고정돼 있다 — Electron의 custom URI / 원격 응답 / 로컬 파일 등 다중 소스 문제는 다루지 않는다.
> - **대비군으로 쓸 때:** "LLM으로 명세를 뽑아 시퀀스를 만든다"는 축에서 본 논문과 비교하면, Electron 쪽 기여는 **크로스-프로세스 연쇄**와 **다중 페이로드 소스**에 있다고 주장할 수 있다.

## 6. Caveats / what I could not confirm from the text

1. **The full text was not read** — HTTP 429 on the PDF, no arXiv HTML rendering. Everything above is abstract-grounded. Re-fetch `https://arxiv.org/pdf/2608.06641` on a later run and rewrite §§2–4 from the real sections.
2. **Affiliations are partly inferred.** The arXiv page lists no affiliations; "UC Santa Barbara" comes from the CCS accepted-papers row for the first author. Kruegel and Vigna are UCSB, which is consistent, but the middle authors' affiliations are **unverified**.
3. **"up to 48%"** is an upper bound over an unspecified set of comparisons — it is *not* the average improvement, and the abstract does not say against which baseline or on which reader it was achieved.
4. **No CVE identifiers are stated** in the abstract. "31 zero-day vulnerabilities" and "received bug bounties" are the only disclosure facts available. Do not write "31 CVEs".
5. **The word "Electron" does not appear anywhere in the abstract**, and there is no evidence the authors make any Electron claim. The Electron mapping in §5 is this watch's analysis, not theirs.
6. **ACM DOI not yet assigned** — CCS 2026 is in November 2026, so the proceedings entry does not exist yet. Cite the arXiv version, and re-check for the ACM DOI after mid-November 2026.
7. **Cycle placement:** the paper appears under **"First Cycle"** on the CCS 2026 accepted-papers page. The Second Cycle list was not yet published as of 2026-08-22.
