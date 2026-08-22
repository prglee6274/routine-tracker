# From Documentation to Zero-day Vulnerabilities: LLM-Driven Fuzzing of JavaScript Engines in PDF Readers

> **GROUNDING — updated 2026-08-23.** This note is now written from the **full text** of `arXiv:2608.06641v2` (18 Aug 2026), the CCS '26 camera-ready version (CC-BY 4.0, 16 pages). Sections 1–10, Tables 1–4 and Listings 1–5 were read. The previous abstract-only version of this note (2026-08-22) has been replaced.
> **Still unread / unreadable:** Figure 2 is a set of six coverage curves — only its axis ranges survive PDF-to-text flattening, so no per-hour coverage value may be quoted. **Table 1 is elided in the source text**: rows for IDs 10–14 and 26–28 are collapsed into `...` lines, so the per-ID type/impact/status for those eight vulnerabilities is unavailable. The reference list was read only far enough to resolve `[3,4] = Adobe JS API manuals`, `[24] = TypeOracle`, `[16] = Favocado`, `[63] = Cooper`, `[41] = Z3`, `[10] = SMT-LIB2`, `[17] = DynamoRIO`, `[44] = RAG`.

**Authors:** Suyue Guo, Stijn Pletinckx, Tianle Yu, Yigitcan Kaya, Wenbo Guo, Christopher Kruegel, Giovanni Vigna (all **UC Santa Barbara**); Saad Ullah (**Boston University**)
**Venue / Year:** ACM CCS 2026 (First Cycle) — The Hague, Netherlands, 15–19 November 2026
**Links:** [CCS 2026 accepted papers](https://www.sigsac.org/ccs/CCS2026/program/accepted-papers.html) · [arXiv:2608.06641](https://arxiv.org/abs/2608.06641) · PDF: `https://arxiv.org/pdf/2608.06641` · **ACM DOI: `10.1145/3830454.3832609`** (printed in the camera-ready; ISBN 979-8-4007-2871-6/2026/11) · arXiv DOI `10.48550/arXiv.2608.06641`
**Tool name:** PDFuzzer
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** it is the same structural target as Electron — a **native desktop application that embeds a JavaScript engine and exposes a large, documented, privileged host API to attacker-supplied script** — and it shows that the *vendor's own API manual* can be mechanically turned into the grammar **and the inter-call constraint system** that drives vulnerability discovery against that surface.

> **한 줄 요약 (KO):** PDF 뷰어에 내장된 JavaScript 엔진을, **공식 API 매뉴얼에서 LLM으로 추출한 파라미터 단위 CFG + API 간 심볼릭 제약(SMT)** 으로 시퀀스 퍼징하여 상용 리더 3종에서 zero-day 31개(그중 ACE 11개, CVE 10건)를 찾아낸 연구. Electron이 아니지만 "데스크톱 앱 + 내장 JS 런타임 + 문서화된 특권 API"라는 구조가 동일하며, **문서 → 문법 → 제약 → 호출 시퀀스** 파이프라인은 Electron IPC 표면에 그대로 이식 가능한 형태다.

---

## 1. Problem, Gap & Hypothesis

**Problem.** PDF documents may embed JavaScript, executed by a scripting engine inside the reader. Beyond standard JavaScript, that engine exposes **specialized APIs that invoke native code within the reader** (§2.1). A bug there is a bug in a desktop application reachable by merely opening a file — the paper's threat model (§2.2) is exactly that: a victim opens an attacker-crafted PDF, and the embedded script triggers memory corruption, information leakage, DoS or arbitrary code execution. The authors cite real precedents: Adobe `util.printf` buffer overflow (CVE-2008-2992), Foxit `app.launchURL` RCE (CVE-2017-10951), and in-the-wild JS-based PDF exploitation CVE-2024-28888 / CVE-2024-34099.

**Gap the authors claim (§2.3), stated as three numbered limitations.**

1. **Missing undocumented API specifications.** Favocado and Cooper rely solely on official manuals. TypeOracle can *detect* undocumented functions via differential analysis but cannot recover their semantics. The paper cites TypeOracle for the figure that **over 30% of PDF reader functions are undocumented**.
2. **Failure to capture complex inter-API relationships.** TypeOracle matches by **name similarity**; Favocado and RESTler-style approaches model only **producer-consumer** (return value → parameter). Neither can express a dependency that holds only when two *input* parameters carry the same value, or when two calls interact through shared reader state.
3. **Lack of automated specification extraction.** Adobe's official JS API manual **exceeds 700 pages** of natural-language prose; prior tools still need human experts to fill parser gaps, correct extraction errors, and hand-write binding-object initialization code.

**Hypothesis.** If (a) undocumented APIs can be given documented-quality specifications automatically, and (b) inter-API dependencies can be expressed as **symbolic constraints over parameter values and shared state** rather than type matches, then a fuzzer can synthesize semantically valid multi-call sequences and reach engine states single-call fuzzing cannot.

> **(KO)** 갭이 세 개로 명시돼 있다는 점이 중요하다. ①문서화되지 않은 API(전체의 30% 이상)의 명세 부재, ②API 간 관계를 producer-consumer / 이름 유사도로만 모델링하는 한계, ③700쪽 넘는 자연어 매뉴얼을 사람이 기계 규칙으로 옮겨야 하는 수작업 부담. 이 셋은 Electron에도 그대로 대응된다 — ①앱마다 다른 **비문서화 preload/IPC 채널**, ②채널 간 상태 의존(예: 세션 등록 → 호출) 미모델링, ③`ipcMain.handle` 핸들러 명세를 사람이 읽어야 하는 문제.

## 2. Methodology

### 2.1 The relationship taxonomy (§3) — the paper's conceptual core

Two **strength tiers**:

- **Candidate relationship** — coarse co-occurrence hypothesis: two APIs *may* meaningfully appear together. No order, no argument mapping, no constraint.
- **Strong symbolic relationship** — confirmed, and additionally carries symbolic variables, an **SMT-LIB2 constraint**, an optional **ordering requirement**, and one of three semantic types.

Three **semantic types** of strong symbolic relationship:

| Type | Definition | Paper's example (Listings 1–3) |
|---|---|---|
| **Producer-Consumer** | API1's return value flows into API2's argument; type-based | `Doc.getIcon()` → `Field.buttonSetIcon({oIcon: …})` |
| **Value-Constraint** | Constraint (equality, range, set-membership) over *input* parameters of two calls, plus ordering | `Doc.addField({cName:"myField"})` then `Doc.getField({cName:"myField"})` — same `cName`, addField first |
| **Implicit** | Interaction via **shared state**, no argument-to-argument or return-to-argument flow | `Field.setAction({cTrigger:"OnFocus", cScript:…})` then `Field.setFocus()` |

### 2.2 The four-component pipeline (§4)

1. **API Specification Extraction (§4.3).**
   - *Documented path:* an **API Manual Parser** applies regular expressions over the HTML manual, capturing owning object, function name, method-vs-property, description, parameters, parameter descriptions, return value → JSON.
   - *Undocumented path — three stages:* **Stage 1** applies TypeOracle's differential analysis to recover raw signatures `<object>.<method>(<param>:<type>,…)` (types inferred from how instruction operands vary across runs — e.g. a length operand going 2→4 for `"YY"` vs `"zzzz"` indicates `String`). **Stage 2** collects context: the parent object's description, sibling APIs on the same object, and Stage-1 names/types. **Stage 3** prompts an LLM to produce a documented-quality spec (functional description, parameter constraints and valid ranges, return-value semantics, behavioral side effects) in the same JSON schema. Worked example in the paper: `Subscriptions.addFeed(cURL: String, cType: String)` — the LLM infers `cURL` is a feed URL and `cType` a MIME string with concrete values such as `"application/rss+xml"`, purely from names and parent-object context, because `Subscriptions` has **no entry at all** in Adobe's manual.
   - Error handling: JSON-format verification with bounded retries, feeding the parse error back into the next prompt.
   - **Note the readers' asymmetry (§4.3):** Foxit and PDF-XChange publish no comprehensive manual, so **Adobe's manual is used as the reference specification for all three**, on the ground (from TypeOracle) that Adobe's JS API is the de facto standard both implement.

2. **Grammar Generation (§4.4) — two-phase, parameter-level.** Feeding a whole API spec to an LLM overgeneralizes: the paper's example is `Doc.submitForm` with **23 parameters**, whose `cSubmitAs` is typed `String` but admits only six values (`FDF`, `XML`, `XDF`, …). *Phase 1* decomposes an *n*-parameter API into *n* independent specification units; *Phase 2* generates a BNF-style CFG per unit. A Python normalization layer then fixes four recurring LLM formatting faults: missing string quotes, leading zeros (`007` → `7`), unescaped inner quotes, embedded newlines — with type-specific string/number/array/object rules. Extended Unicode syntax `\u{XXXX}` is avoided because Adobe Acrobat does not support it (Foxit and PDF-XChange do).

3. **Relationship Inference (§4.5) — two-stage, RAG-backed.** The brute-force cost is stated explicitly: with **n = 666 APIs**, C(666,2) = **221,445 pairs** at ~30 s of LLM analysis each = **over 1,845 hours**, intractable. The two-stage design turns O(n²) into O(n) + O(k²), k ≪ n. **Stage 1** iterates over each API and uses fast **RAG** queries against a vector store of the specification database to surface *candidate* pairs. **Stage 2** runs one comprehensive zero-shot prompt per candidate pair doing three things at once: parameter symbolization (assign `x`, `y`), constraint generation as **SMT-LIB2** (e.g. `(= x y)`), and sequence analysis (must one precede the other?).

4. **Test Case Generator (§4.6) — four stages.** (1) instantiate individual calls from their CFGs; (2) relationship-aware sequencing — candidate pairs are concatenated with independent arguments, strong pairs are solved with **Z3** to bind the dependent parameter (**max sequence length configured to 2,000 API calls**, to keep hangs distinguishable from slow processing); (3) integrate **Cooper's cooperative mutation** to populate the PDF *native* objects (pages, form fields, actions, annotations) the calls need; (4) apply **targeted mutation to ~15% of test cases** — non-BMP Unicode, escape sequences, malformed encodings for strings; boundary values, `Infinity`, `NaN`, scientific notation, hex literals for numbers.

**Implementation scale (§4.6):** 435 documented API functions with 507 parameters, plus 231 undocumented functions with 379 parameters, yielding **CFG rules for 886 parameters across 666 API functions**.

> **(KO)** 방법론의 진짜 기여는 "LLM으로 퍼징 입력을 만든다"가 아니라 **자연어 명세를 SMT 제약으로 번역했다**는 점이다. LLM은 의미 추론만 담당하고, 실제 값 결정은 Z3가 한다 — 이 분업이 정확도(93~98%)와 처리량(초당 최대 20건)을 동시에 확보한 이유다. Electron으로 옮길 때의 대응: **API 매뉴얼 → `ipcMain.handle` 채널 목록 + preload `contextBridge.exposeInMainWorld` 표면**, **producer-consumer → 핸들러 반환 핸들/ID의 재사용**, **value-constraint → 같은 세션·창·경로 문자열을 공유해야 성립하는 채널 쌍**, **implicit → 앱 상태(로그인·창 생성·파일 열기)를 먼저 만들어야 도달하는 채널**. 특히 implicit 관계는 Electron IPC에서 가장 흔한 형태인데, 이 논문에서도 **가장 어려운 유형(인스턴스화 성공률 64.0%)** 으로 보고된다.

## 3. Experiments / Evaluation Setup (§5)

**Targets — 3 closed-source readers, exact versions given:**

| Reader | Version |
|---|---|
| Adobe Acrobat Reader | v24.005.20421 |
| Foxit PDF Reader | v2024.4.0.27683 |
| PDF-XChange Editor | v10.5.2.395 |

(All "the latest versions at the time of this study.")

**Baselines — three families.**

- *PDF fuzzers:* TypeOracle, Favocado, Cooper — plus the combinations **TypeOracle+Cooper** and **TypeOracle+Favocado**.
- *LLM-based general fuzzer:* **Fuzz4All**, fed the Adobe JS API manual, and modernized from the paper's defaults (GPT-4 → **GPT-4o** for distillation, StarCoder → **StarCoder2** for generation).
- *Naive vanilla-LLM* (inspired by TitanFuzz), run with three models: **GPT-4o**, **o3-mini**, **Claude-3.7-Sonnet**.

**Controlled variable — this matters for how the result is read (§5.2).** The evaluation deliberately does **not** compare online fuzzing loops. **TypeOracle's public fuzzing wrapper is used uniformly for all tools**; there is no AFL-style seed queue, power schedule, mutation scheduling or coverage-guided feedback. So every difference is attributed to **test-case generation quality alone**.

**Metrics and budgets.**

- *Coverage:* targets are closed-source, so **DynamoRIO** dynamic instrumentation collects **basic-block** coverage. **Five independent 24-hour runs per tool per target.**
- *Vulnerability discovery:* run **separately** from coverage (DynamoRIO's overhead and instability cause false-positive crashes). Each tool generates a corpus; each input is run through all three targets; crashes detected via Windows `werfault.exe`; every crash **manually analyzed**. **Two weeks per tool across all targets.**
- *Environment:* VMware Workstation VM (4 cores, 8 GB RAM, **Windows 8.1** — chosen for low resource use) on an 8-core Intel Core i7-7700 @3.60 GHz / 64 GB host. Every crash found was **re-verified on Windows 10 22H2 and Windows 11 24H2**.

> **(KO)** 실험 설계에서 가져올 만한 두 가지. ①**커버리지 실험과 취약점 발견 실험을 분리**했다 — 계측 오버헤드가 거짓 크래시를 만들기 때문. ②**퍼징 루프를 통일**(TypeOracle 래퍼)해 "생성기 품질"만 비교했다. Electron 논문을 쓸 때도 동일한 통제가 필요하다: 채널 탐색 전략과 페이로드 생성기를 섞어 비교하면 어느 쪽 기여인지 분리되지 않는다.

## 4. Results / Key Findings

### 4.1 Coverage (§6.1)

PDFuzzer is highest on all three targets. Improvement **upper bounds**, as stated:

| Compared against | PDFuzzer improvement (up to) |
|---|---|
| Cooper | **48%** ← this is the source of the abstract's "up to 48%" |
| TypeOracle | 37% |
| TypeOracle + Cooper | 19% |
| TypeOracle + Favocado | 17% |
| Favocado | 15% |
| Claude-3.7-Sonnet (best naive LLM) | **16–49%** |

Fuzz4All is the **worst** performer on Foxit and PDF-XChange because most of its generated test cases "were invalid JavaScript code, mostly containing C code or Java code, or even just plain text." It is not worst on Adobe, which the authors attribute to Adobe's more extensive error handling.

### 4.2 Vulnerabilities (§6.2, Table 1)

- **57 crashing test cases** across the three readers: **23 Adobe, 24 Foxit, 10 PDF-XChange**.
- Triage: statement-level reduction (iteratively delete JS statements, keep the minimal reproducer), then dedup by **normalized call-stack signature** (following TypeOracle and Cooper).
- → **31 unique crash signatures = 31 distinct zero-day vulnerabilities.**
- **11 of 31 are high-severity, potentially arbitrary code execution.**
- **26 of 31 fixed** by vendors; **10 assigned CVE entries**; **$2,450** total bounty, on **two** vulnerabilities.
- **No other tool found a vulnerability PDFuzzer did not.**

Confirmed CVE identifiers visible in Table 1: **CVE-2025-43575** (Adobe, out-of-bounds write, ACE), **CVE-2026-3777** (Foxit, use-after-free, ACE — the running-example bug), **CVE-2025-55308**, **CVE-2025-55314**, **CVE-2025-55312**, **CVE-2025-55307**, **CVE-2026-3778**, **CVE-2025-55313**, **CVE-2026-3776** (all Foxit), **CVE-2025-6661** (PDF-XChange, memory corruption, ACE). *(Table 1 rows 10–14 and 26–28 are elided in the source text; the remaining CVE assignments, if any, are among those.)*

**Table 1 aggregated row — vulnerabilities found per configuration:**

| Config | TypeOracle | Favocado | Naive LLM | Fuzz4All | Cooper | Fav+TO | Coop+TO | PDFuzzer fn-level grammar | PDFuzzer param-level | PDFuzzer candidate rel. | PDFuzzer strong rel. | **PDFuzzer-full** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Vulns | 5 | 4 | 1 | 0 | 2 | 6 | 6 | 4 | 7 | 12 | 28 | **31** |

The jump from **12 (candidate relationships only) → 28 (strong symbolic relationships)** is the single largest effect in the paper, and it is the effect that carries the thesis-relevant claim.

**Case study (§6.2, Listing 4):** `app.popUpMenuEx({cName:"popup", …})` allocates a region; `search.query({cQuery:"popup"})` frees it; calling a popup-menu API again touches the freed address → use-after-free in Foxit (CVE-2026-3777). The bug requires `cName == cQuery`. TypeOracle's name similarity links `popUpMenuEx` only to `popUpMenu` (shared prefix) and never to `search.query`; producer-consumer matching cannot connect them either, since neither returns a value the other consumes. **It was triggered only in the P_s / P_f configurations.**

### 4.3 Relationship distribution (§6.3, Table 2)

Of **1,019** inferred strong symbolic relationships:

| Type | Count | Share |
|---|---|---|
| Value-Constraint | 887 | **87.0%** |
| Producer-Consumer | 69 | 6.8% |
| Implicit | 63 | 6.2% |

Value-constraint subtypes: direct equality 667 (75.2%), relational comparisons 69 (7.8%), set memberships 59 (6.7%), range constraints 26 (2.9%), string constraints 8 (0.9%), complex 58 (6.5%).

**A producer-consumer-only model would miss ~93% of the strong relationships PDFuzzer instantiates.**

### 4.4 Instantiation success (§6.4, Table 3)

Over 1,000 generated PDFs, **71,586** selected strong symbolic relationship invocations, **65,508 (91.5%)** successfully solved:

| Type | Invocations | Success | Failure | Rate |
|---|---|---|---|---|
| Producer-Consumer | 4,704 | 3,832 | 872 | 81.5% |
| Value-Constraint | 60,675 | 57,706 | 2,969 | **95.1%** |
| Implicit | 6,207 | 3,970 | 2,237 | **64.0%** |
| **Total** | 71,586 | 65,508 | 6,078 | 91.5% |

Implicit is hardest because it needs both a parameter constraint (a specific event name) *and* a state precondition (the field must be focusable). Most residual failures are attributed to the deliberate Stage-4 mutation pass and to values being assembled before Z3 can re-bind them; genuinely unsatisfiable constraint sets are "rare."

### 4.5 Cost (§6.5)

| Method | GPT-4o | o3-mini | Claude-3.7-Sonnet |
|---|---|---|---|
| PDFuzzer, end-to-end | **$60.77** | $73.38 | $92.36 |
| Naive LLM | $76.14 | $156.76 | $174.83 |

Naive LLM generation: **>60 s per test case** (OpenAI models), **up to 90 s** (Claude). PDFuzzer: **~3 test cases/s** for strong symbolic relationships, **up to 20/s** for regular ones.

### 4.6 LLM accuracy (§6.6) — 60 sampled outputs per stage, manually annotated

| Stage | Sample | Accuracy |
|---|---|---|
| Specification inference (undocumented APIs) | 60 APIs / 87 parameters | **94%** (82/87 parameter types), errors clustered in 4 APIs |
| Grammar generation | 60 APIs (30 doc + 30 undoc) / 103 parameters | **97%** APIs (58/60), **98%** parameters (101/103) |
| Relationship inference | 60 relation pairs | **93%** (56/60) — 3 sequence-order errors, 1 constraint error |

Named failure mode worth remembering: the LLM systematically mistypes parameters whose names *sound* Boolean — `dcSignup`'s `cEmailPerm` / `cConnectPerm` were called Boolean because of the "Perm" suffix, when they take permission-level **strings**. Conversely it *corrected* TypeOracle, e.g. reclassifying `browseForMultipleDocs`'s `cFileFilter` from Boolean to String on the strength of the "Filter" naming convention.

### 4.7 Ablation (§7, Table 4)

| Dimension | Setting | Adobe | Foxit | PDF-XChange |
|---|---|---|---|---|
| **1. Undoc. spec inference** | PDFuzzer vs TypeOracle | 1,008,279 vs 725,776 (**↓28%**) | 349,635 vs 279,361 (**↓20%**) | 336,724 vs 333,408 (↓1%) |
| **2. Grammar granularity** | param- vs function-level | 1,121,910 vs 921,160 (**↓18%**) | 406,448 vs 371,901 (↓9%) | 440,480 vs 416,297 (↓5%) |
| **3. Relation tier** | Strong vs {Candidate, PC-Only, Favocado, None} | Strong 1,183,295 (others ↓4–5%) | Strong 459,634; PC-Only 397,916 → **max gain 15.5%** | Strong 500,579 (others ↓2–12%) |
| **4. PDF objects** | PDFuzzer-full vs -js | 1,283,296 vs 1,183,295 (↓8%) | 472,620 vs 459,634 (↓3%) | 524,782 vs 500,579 (↓5%) |

XChange's ↓1% on Dimension 1 has a stated cause: reverse engineering showed **PDF-XChange implements no undocumented APIs at all**, so there is nothing for specification inference to recover.

**LLM choice barely matters:** GPT-4o vs o3-mini vs Claude-3.7-Sonnet differ by **<10,000 basic blocks on Adobe, i.e. <1% of total**.

### 4.8 Generalization beyond PDF (§8) — a feasibility study, not a fuzzing result

The authors applied the specification-extraction and grammar-construction pipeline to **Microsoft Word VBA**: from **5,920 pages** of official documentation they extracted specs for **2,925 APIs covering 3,768 parameters** and generated CFGs for all of them, observing that all three relationship types recur in VBA. **They did not run the fuzzer** — the next step (emitting VBA macros into Word documents) is described as "straightforward" but is not executed or evaluated.

> **(KO)** 결과에서 논문 인용 시 반드시 붙잡아야 할 숫자는 **12 → 28**(candidate만 vs strong symbolic)이다. "API를 같이 호출하는 것"만으로는 부족하고 **파라미터 값 제약과 순서를 강제해야** 취약점이 나온다는 정량적 증거이기 때문. 그리고 **value-constraint가 전체 강한 관계의 87%** 라는 분포는, producer-consumer 중심으로 설계된 기존 API 퍼저 전제가 실제 분포와 크게 어긋난다는 뜻이다.

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Beyond the browser, native desktop applications increasingly embed a JavaScript engine and expose a large privileged host API to document-supplied script. Guo et al. show that this surface is a productive target: their PDFuzzer uses an LLM to mine parameter-level context-free grammars and inter-API dependencies from vendor JavaScript API manuals and execution traces, encodes those dependencies as SMT-LIB2 constraints, and uses Z3 to instantiate concrete multi-call sequences [CCS'26]. Crucially, they show that type-based producer-consumer modelling — the assumption behind most prior API fuzzers — accounts for only 6.8% of the dependencies that actually matter, while value-constraint relationships account for 87.0%; enforcing the stronger relationships raises the vulnerability count from 12 to 28 in an otherwise identical configuration. Evaluated on Adobe Acrobat Reader, Foxit PDF Reader and PDF-XChange Editor, PDFuzzer attains up to 48% higher basic-block coverage than Cooper (37% over TypeOracle, 15% over Favocado) and uncovers 31 zero-day vulnerabilities, 11 of them potentially yielding arbitrary code execution, with 10 CVEs assigned. Their result underlines a point that applies directly to Electron: the *documented* privileged API surface, and specifically the ordering and value coupling between its entry points, is where reachable desktop-privilege bugs live.

> **(KO) 취약점 발견 논문 관점에서의 포지셔닝:**
> - **동기(motivation)로 쓰기 좋다.** "데스크톱 앱 + 내장 스크립트 런타임 + 특권 호스트 API"가 Electron과 동형이라는 근거. 특히 이 논문은 **문서화된 API 표면 자체가 공격면**임을 31건의 zero-day로 실증한다.
> - **방법론을 빌려올 수 있다.** PDF 리더의 "API 매뉴얼"에 대응하는 Electron 자산은 ①Electron 공식 API 문서(`ipcMain`/`ipcRenderer`/`contextBridge`/`shell`/`BrowserWindow`), ②각 앱의 **preload 스크립트와 `ipcMain.handle` 등록부**(asar 안에 소스로 존재). 여기서 파라미터 단위 문법과 채널 간 제약을 뽑아 시퀀스를 합성하는 파이프라인은 거의 그대로 이식 가능하다.
> - **가장 강한 인용 포인트:** *implicit relationship의 인스턴스화 성공률이 64.0%로 가장 낮다*는 관측. Electron IPC에서 채널 간 의존은 대부분 **앱 상태를 매개로 한 implicit 형태**(로그인 → 세션 핸들 → 파일 접근)이므로, 이 논문이 가장 못 푼 유형이 Electron에서는 **지배적 유형**이 된다. 이것이 곧 기여 공간이다.
> - **남겨둔 갭(이 논문이 열어두는 공간):**
>   ① **단일 프로세스 내부의 엔진 메모리 안전성**만 본다 — 프로세스 경계를 넘는 전파(renderer → main IPC)는 범위 밖.
>   ② **클로즈드소스 상용 리더**라 블랙박스 퍼징에 갇힌다(DynamoRIO 기본블록 커버리지). Electron 앱은 소스가 읽히므로 **정적 분석 + 제약 합성** 결합 여지가 훨씬 크다.
>   ③ 입력 소스가 **문서 파일 하나**로 고정 — Electron의 custom URI / 원격 응답 / 로컬 파일 등 **다중 소스** 문제는 다루지 않는다.
>   ④ §8의 일반화는 **VBA 명세 추출까지만** 수행한 feasibility study다. "다른 도메인으로 일반화됨이 입증됐다"고 인용하면 과장이다.
> - **대비군으로 쓸 때:** "LLM으로 명세를 뽑아 시퀀스를 만든다"는 축에서 이 논문과 비교하면, Electron 쪽 기여는 **크로스-프로세스 연쇄**, **다중 페이로드 소스**, **소스 가용성을 활용한 화이트박스 제약 추출**에 있다고 주장할 수 있다.

## 6. Caveats / what I could not confirm from the text

1. **Figure 2 is unreadable as text.** Six coverage-vs-time curves; only axis ranges survive flattening (Adobe ~0.8–1.4×10⁶ bbks; Foxit ~340k–480k; XChange ~360k–540k). **No per-hour or per-tool curve value may be quoted from it** — the percentage claims in §4.1 above come from the §6.1 prose, not the figure.
2. **Table 1 is elided.** Rows for IDs 10–14 and 26–28 appear as `...` in the extracted text. The ten CVE identifiers listed in §4.2 are those visible in the un-elided rows; **there may be more among the eight hidden rows**, and the paper's own "10 have been assigned CVE entries" is the authoritative count.
3. **Two slightly different framings of the disclosure numbers.** §1 says "26 have been confirmed or fixed, yielding $2,450 in bug bounties"; §6.2 says "vendors have fixed 26 of the 31" and "**two** of the vulnerabilities have already received a bounty for a total of $2,450." Prefer §6.2's wording — the $2,450 is from two bounties, not from 26.
4. **"Up to 48%" is against Cooper specifically** (§6.1), not an average and not against the strongest baseline. The strongest baseline (TypeOracle+Cooper) is only 19% behind. Quoting "48% better than state of the art" would misrepresent the paper.
5. **Table 4, Dimension 3, Foxit is internally odd:** `PC-Only` (397,916) scores *below* `None` (406,448), i.e. producer-consumer-only modelling appears to *hurt* relative to no relationship modelling on that target. The paper does not comment on this. Do not build an argument on the Dim-3 sub-rows without re-reading them in the published version.
6. **The word "Electron" never appears in the paper** — grep-confirmed across the full retrieved text, along with "browser", "Chromium", "Node.js" and "desktop". The Electron mapping throughout this note is **this watch's analysis**, not an authors' claim.
7. **Adobe's manual is used as the reference spec for Foxit and PDF-XChange too.** Any Foxit/PDF-XChange-specific API not mirrored in Adobe's manual is outside the documented path by construction — a limitation the paper states but does not quantify.
8. **The evaluation deliberately removes the fuzzing loop as a variable** (uniform TypeOracle wrapper, no coverage-guided feedback). The coverage numbers therefore say nothing about how PDFuzzer would compare against a modern feedback-driven fuzzer; they compare *generators* only.
9. **arXiv v2 (18 Aug 2026) already carries the ACM DOI `10.1145/3830454.3832609`**, so this is the camera-ready. Still worth re-checking the ACM DL entry after CCS '26 (The Hague, 15–19 Nov 2026) for final pagination.
10. **Author affiliations** are now taken from the paper's own title block: seven UCSB, Saad Ullah at Boston University. (Tianle Yu's listed affiliation is UCSB although the contact email is `@stanford.edu` — noted, not resolved.)
