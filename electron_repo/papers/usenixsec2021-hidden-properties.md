# Abusing Hidden Properties to Attack the Node.js Ecosystem

**Authors:** Feng Xiao (Georgia Tech), Jianwei Huang (Texas A&M), Yichang Xiong (Independent), Guangliang Yang (Georgia Tech), Hong Hu (Penn State), Guofei Gu (Texas A&M), Wenke Lee (Georgia Tech)
**Venue / Year:** 30th USENIX Security Symposium (USENIX Security '21), Vancouver B.C. (virtual), August 2021 — Fall cycle
**Links:** [paper](https://www.usenix.org/conference/usenixsecurity21/presentation/xiao) · [PDF](https://www.usenix.org/system/files/sec21fall-xiao.pdf) · [slides](https://www.usenix.org/system/files/sec21_slides_xiao.pdf) · [artifact](https://github.com/xiaofen9/Lynx)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the paper that first named and systematised *hidden property abusing* (HPA) — an attacker-controlled property riding a deserialized input object into an internal object and silently overwriting program state without ever touching `__proto__` — which is precisely the primitive an Electron renderer→main IPC message provides for free, since IPC payloads are structured-clone/JSON objects merged into main-process state by exactly the `Object.assign`-style code HPA targets.

> **한 줄 요약 (KO):** 원격 공격자가 JSON/query-string 직렬화로 넘긴 "숨은 프로퍼티"가 내부 객체로 전파되어 프로토타입을 건드리지 않고도 내부 상태(검증 로직, 타입 체크, DB 쿼리 조건)를 덮어쓸 수 있음을 최초로 체계화하고, 이를 자동 탐지·익스플로잇 합성하는 하이브리드 분석 도구 LYNX를 제시. Node.js 102개 프로그램에서 451개 후보 → 15개 0-day(CVE 10건, Critical/High 8건). Electron의 renderer→main IPC 페이로드가 동일한 구조의 공격면이므로 **prototype pollution과 구별되는 별도 공격 클래스**의 표준 인용원.

## 1. Problem, Gap & Hypothesis

Node.js is framed by the authors from the first sentence as a runtime for **"server-side and desktop programs (e.g., Skype)"**, and the introduction names **Skype, Slack and WhatsApp** as Node.js-built desktop applications — i.e. the paper's own framing already spans the desktop case even though every experiment is server-side.

The gap: CWE-915 ("improperly controlled modification of dynamically-determined object attributes") had been studied in **PHP** (object injection) and **Ruby** (mass assignment), but the authors claim to be the first to study it systematically in JavaScript/Node.js. They also argue it is *not* the same thing as prototype pollution, which by 2021 was the only recognised JS instance of the class.

Hypothesis: because Node.js programs routinely **share objects** across the client/server boundary via JSON or query-string deserialization and then merge them into internal objects (`Object.assign(internal, input)`), an attacker can inject an *extra, undocumented* property whose name collides with an internal one, and reach program states that were assumed unreachable — **without** the prototype write that prototype pollution requires.

Two attack vectors are defined:
- **App-specific attribute manipulation** — overwrite a developer-defined internal field (e.g. an access-right or order-status flag).
- **Prototype inheritance hijacking** — plant an own-property (e.g. `constructor`, or nested `constructor.name`) that *shadows* the inherited one, so code that trusts a prototype-inherited property reads the attacker's value. The paper is explicit that this **does not modify the prototype**, and gives the discriminating pair: `obj[__proto__] = input` is vulnerable to PP but `Object.assign(obj, input)` is not — yet the latter *is* vulnerable to HPA.

*(KO) 이 논문의 핵심 gap 주장: prototype pollution(PP)과 HPA는 다르다. PP는 프로토타입에 직접 쓰기가 필요하지만, HPA는 `Object.assign` 같은 병합만으로 성립한다. 즉 PP 스캐너가 잡지 못하는 별도 공격면이 존재한다는 것. Electron IPC handler가 `Object.assign(state, event.args)` 류로 작성되면 정확히 이 조건에 해당.*

## 2. Methodology

**LYNX** — a hybrid static/dynamic pipeline in two phases.

Phase 1 — *Identifying hidden properties*
1. **Dynamic label propagation.** Instrument the target program (built on **Jalangi**) and inject a unique `key:value` **label property** into the input object, recursively into every child property. Run, intercept all variable read/write operations, and mark any internal object that ends up carrying the label as a **property carrier**, recorded as `⟨O, L, S⟩` = object name, containing JS file, visibility scope (function names concatenated with `.`, `_fun` suffix for function scopes).
   - Deliberate design choice: labelling **mutates the input** rather than tracking it transparently, because that better emulates the real HPA attack — if the added property changes the input's type, the program takes the branch a real payload would take. Cost: a sanitizer may reject the labelled input, so LYNX uses a **one-label-at-a-time** strategy and repeats.
2. **Static complement.** Dynamic tracking misses properties on unexecuted branches (their Listing 1 example: `conf.propertyB` inside an `if (condition)`). LYNX runs an **intraprocedural static syntactic analysis** over the AST within each carrier's scope, recognising three indexing forms: static (`obj.k`, `obj['k']`), function (`obj.hasOwnProperty('k')`), and dynamic (`obj[kvar]` — resolved only from concrete values seen in the earlier traces, so coverage is not guaranteed).
3. **Pruning.** A context-based analyzer removes *documented* optional parameters, on the observation that documented params are handled together by the same dispatcher (an if-else chain) as the used params.

Phase 2 — *Generating exploits*
4. **Exploit template** — insert the candidate property name at the input position that the label→carrier map says reaches the carrier, with a **symbolic** value.
5. **Symbolic execution** to explore paths and reach **sensitive sinks**, categorised C/I/A: C1 sensitive DB query methods, C2 sensitive filesystem operations, I1 critical built-in properties + code-execution APIs, I2 final results of module invocation, A1 (availability).

**Input channels supported:** JSON serialization and query-string serialization (the paper singles out `qs`, ~100M monthly npm downloads). Explicitly *not* exhaustive — other channels (HTTP headers, cookies, user-agent) are acknowledged and left out.

*(KO) 방법론적으로 배울 점 두 가지. (1) "입력을 변형해서 추적한다"는 라벨링은 정적 taint보다 실제 공격 경로를 더 정확히 밟는다 — Electron IPC fuzzing에 그대로 옮길 수 있는 아이디어. (2) 동적으로 carrier를 먼저 찾고, 그 scope 안에서만 정적 분석을 돌리는 2단 구성이 false positive를 억제한다.*

## 3. Experiments / Evaluation Setup

- **Dataset: 102 Node.js programs** = **91 npm modules** + **11 web-based programs** (of the 11: 4 minimal frameworks/middlewares, 7 complete web applications). Selection criteria: (a) the program interacts with external input and its APIs accept objects via JSON or query-string; (b) it is widely used or actively maintained — from known vendors (e.g. MongoDB), or ≥1000 GitHub stars, or ≥500 monthly npm downloads.
- **Four categories** (tested / of which contain hidden properties): Database 9 (8), Input Validation 48 (30), User Functionalities 34 (26), Web 11 (7).
- **Test drivers:** for the 91 modules, the npm-homepage use cases are reused directly (justified by the observation that **45 of the 50 most depended-upon npm packages** ship directly usable test cases). For the 11 web programs, manual interaction feeds a profiling-based record-and-replay pipeline; **7 of the 11** support both query-string and JSON serialization on different APIs.
- **Hardware:** Ubuntu 18.04, Intel Core i5-9600K (3.70 GHz), 32 GB RAM.
- **Measured:** number of property carriers (#PC), hidden-property candidates (#HP), documented arguments correctly filtered (#DA); reported vs. manually-confirmed-exploitable vs. missed sinks; code coverage (via **ExpoSE**'s monitor, LoC executed / total LoC in executed files, dependencies excluded); per-API analysis time.

## 4. Results / Key Findings

**Prevalence (RQ1).** **69% (70/102)** of tested programs contain hidden properties. **3,175 property carriers** analysed → **451 hidden-property candidates**. Per-category #PC/#HP/#DA: Database 323/78/0, Input Validation 999/122/0, User Functionalities 584/156/24, Web 1269/95/0. The documented-argument filter was checked against official docs and **correctly recognised all documented arguments** (i.e. the 24 in User Functionalities were the only ones, and none were misclassified).

**Exploitation (RQ2).** Reported / exploitable / missed by category: Database 2/2/1, Input Validation 7/4/2, User Functionalities 5/4/0, Web 1/1/1. Overall **11 of 15 reported sinks were confirmed genuinely exploitable**; the other 4 reach a sensitive sink but are constrained by program semantics (e.g. an exception that the program then handles, so no validation bypass). Three causes of the **4 missed** cases: (i) constraints that live in memory rather than in code (taffyDB's internal index `T000002R000001`, guessable but not derivable by the symbolic executor); (ii) multi-constraint payloads needing several input fields set at once; (iii) Jalangi's incompatibility with post-ES6 grammar, worked around by down-compiling with Babel.

**Impact (RQ3).** **15 previously unknown vulnerabilities**, **10 CVEs assigned**, **8 rated Critical or High** by NVD, **10 vendors confirmed**, **7 patched** at time of writing. **2** of the 15 are in complete web applications; the other **13 are in modules, transitively impacting 20,402 dependent applications/modules.** Impact split: **4 confidentiality** (HP-1, 2, 3, 14), **10 integrity** (HP-4…13), **1 availability** (HP-15).

Named victims from Table 5, with monthly downloads / dependents:
- `mongoose` `findOne()` — SQL injection — 2,740,341 / 9,211 — Fixed, **Critical**
- `mongoDB driver` `find()` — SQL injection — 6,165,075 / 8,435 — Fixed
- `taffyDB` query APIs — universal SQL injection via forged internal index — 1,628,860 / 108 — Confirmed, High
- `class-validator` `validate()` — validation bypass (the running example) — 1,077,954 / 1,639 — Confirmed, **Critical**
- `schema-inspector` `validate()` + `sanitize()` — validation bypass — 35,783 / 104 — Fixed, High
- `bson-objectid` `ObjectID()` — ID forging — 142,562 / 298 — Fixed, High
- `kind-of` `kindOf()` — type manipulation — **196,448,574** / 458 — Fixed, High
- `cezerin` (eCommerce app) — order/payment-status (`ispaid`) manipulation — Confirmed, High
- `mongo-express` `addDocument()` — infinite-loop DoS — Fixed, Medium

Two mechanisms worth carrying into a thesis: (a) `kind-of` type-confusion cascades — `clone-deep` (1,822,028 dependent projects per GitHub) calls `kind-of`, so a forged `length` on an object masquerading as an array freezes the **whole** application, because Node.js is single-threaded; (b) `mongoDB`'s `_bsontype` property, which selects the query type and is never meant to come from input, is overwritable via HPA.

**Coverage / performance.** Modules: **10–80%** code coverage (most >40%); the authors argue coverage understates effectiveness because they deliberately test only object-accepting APIs. Web programs: **21% average**. Timing: hidden-property detection **<10 s per API in 90% of cases**, **>200 s per API for very large web apps (≤10 cases)**; exploitation ~**50 s per hidden property**.

**Community outcome.** Snyk's vulnerability database accepted the authors' proposal and **created a new notion** to track this class.

*(KO) 숫자 중 논문에서 가장 인용가치 높은 것: 69% (70/102) 유병률, 451개 후보 중 15개 실제 취약점, kind-of 한 모듈이 월 1.96억 다운로드. "널리 쓰이는 검증 모듈 자체가 우회 가능하다"는 결과가 특히 강력 — 즉 입력 검증은 HPA의 방어책이 되지 못한다.*

## 5. How to cite in Related Work

> Xiao et al. introduced *hidden property abusing* (HPA), showing that a Node.js program which merges a deserialized input object into an internal one exposes internal program state to a remote attacker without any write to `Object.prototype`, and thereby distinguished HPA from the prototype-pollution class that dominated prior JavaScript work. Their tool LYNX combines dynamic label propagation with scope-limited static AST analysis to enumerate hidden-property candidates, then uses symbolic execution to synthesise concrete exploits; over 102 widely used Node.js programs it found hidden properties in 69% of them and confirmed 15 previously unknown vulnerabilities, 10 of which received CVEs. Notably, four of the affected packages were themselves *input-validation* libraries, demonstrating that sanitisation at the application boundary is not a mitigation for this class. Their evaluation, however, covers only server-side JSON and query-string channels, leaving the equivalent object-sharing surface in Electron-style desktop applications — where structured-clone IPC messages cross the renderer→main privilege boundary — unexamined.

*(KO) 포지셔닝. 이 논문은 (a) **동기 부여**이자 (b) **방법론 차용원**이자 (c) **명확한 gap 제공자**의 세 역할을 동시에 한다. Gap이 특히 깔끔하다: 저자들이 직접 "Node.js는 Skype·Slack·WhatsApp 같은 데스크톱 앱에 쓰인다"고 서두에 써놓고, 실험은 전부 server-side HTTP/JSON 채널로만 했다. Electron의 `ipcRenderer.send`/`ipcMain.handle` 페이로드는 structured clone으로 전달되는 객체이고 main process는 Node 전권을 가지므로, HPA의 전제조건(객체 공유 + 내부 객체 병합)이 그대로 성립하면서 결과는 정보유출이 아니라 **로컬 RCE**로 격상된다. 즉 "HPA를 renderer→main 경계로 옮기면 어떻게 되는가"는 이 논문이 직접 열어둔 미탐색 영역이고, 학위논문의 연구질문으로 바로 쓸 수 있다. 또한 LYNX의 라벨링 기법은 Inspectron(블랙박스 감사)이나 COINDEF(방어)와 달리 **익스플로잇 합성까지** 가는 몇 안 되는 파이프라인이므로, NodeMedic-FINE·Bullseye와 함께 "PoC 자동 생성" 계보로 묶어 인용하면 좋다.*

## 6. Caveats / what I could not confirm from the text

- I read the **full USENIX open-access PDF** (`sec21fall-xiao.pdf`) but **selectively**: §1–§3 and §5 (evaluation) in full, §4 (LYNX design) in full, §6–§8 in full; **Appendix §A.1–§A.3 and Table 7 (the complete 102-program detection table) were not read**, so the three proposed countermeasures and the per-program timing breakdown are described only as far as the main text states them.
- **Table 5's numbering is internally inconsistent in the PDF text**: the prose says confidentiality covers "HP-1, HP-2, HP-3, and HP-14" and then discusses "HP-12" as the cezerin case, while the table lists cezerin as row 14 and integrity as HP-4…HP-13. I have reported the *table rows* (product names) rather than trying to reconcile the HP-numbers, and the C/I/A counts (4 / 10 / 1) are quoted as the prose states them.
- Table 5's "Downloads" column is not labelled with a period in the extracted text; I have assumed **monthly** downloads by analogy with the rest of the paper, but this is an inference.
- The two Table 5 rows for `component-type` (HP-11, HP-12) and the two for `jpv` (HP-5, HP-6) are separate API-level findings, not separate packages — the count of 15 is *vulnerabilities*, not distinct projects.
- The exact **CVE identifiers** are anonymised in the paper as "CVE1"…"CVE10"; I did not resolve them to real CVE numbers.
- No claim is made or verified here about HPA on **Electron IPC specifically** — the paper never tests Electron. Every desktop-relevance statement in §5 above is my own extrapolation from the paper's own framing sentence, and is flagged as a gap, not a finding.
