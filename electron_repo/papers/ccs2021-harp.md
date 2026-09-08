# Supply-Chain Vulnerability Elimination via Active Learning and Regeneration

**Authors:** Nikos Vasilakis (MIT CSAIL), Achilles Benetopoulos (UC Santa Cruz), Shivam Handa (MIT CSAIL), Alizee Schoen (MIT CSAIL), Jiasi Shen (MIT CSAIL), Martin C. Rinard (MIT CSAIL)
**Venue / Year:** ACM CCS 2021 (28th ACM SIGSAC Conference on Computer and Communications Security), 15–19 November 2021, Virtual Event, Republic of Korea. 16 pages.
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3460120.3484736) · [PDF (author-hosted)](http://nikos.vasilak.is/p/harp:ccs:2021.pdf) · DOI [10.1145/3460120.3484736](https://doi.org/10.1145/3460120.3484736)
**Scope tag:** ADJACENT
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It is the most radical point on the npm-defence spectrum — instead of detecting or confining a compromised dependency, it *deletes and re-synthesises* it from observed behaviour — and it explicitly covers native add-ons wrapped via Node's NaN / N-API, the same JS↔C++ boundary an Electron main process exposes.

> **한 줄 요약 (KO):** 손상된 npm 라이브러리를 고치거나 가두는 대신, 클라이언트가 관찰 가능한 동작만 능동 학습(active learning)으로 추론해 DSL 프로그램으로 **재생성**함으로써 파일시스템·네트워크 같은 부수효과를 표현 불가능하게 만들어 공급망 취약점을 원천 제거하는 CCS'21 논문.

**GROUNDING:** Written from the full author-hosted PDF (abstract, §1 Introduction, §3 Threat Model, §4 ALR, §7 Implementation & Evaluation incl. Table 1). All numbers below are read off that text. The extended version referenced for the Python results (cited as `[blind]` in the camera-ready) and Appendix B's per-library C/C++ table were **not** consulted — see §6.

---

## 1. Problem, Gap & Hypothesis

Software supply-chain attacks target the *supplier*, not the victim: an adversary inserts a payload into a widely-used open-source component that is then pulled — usually **transitively**, so the application developer may not even know it is present — into thousands of client applications. The paper's key observation is that to stay undetected such a component must keep delivering **correct client-observable behaviour**; the malicious part lives entirely in side effects the client never inspects — file-system writes, network sends, environment-variable reads, writes to global variables.

The gap: prior defences either *detect* malicious code (which fails against payloads that only fire in one specific production environment) or *confine* it at runtime (which still ships the attacker's code). Neither removes the code.

Hypothesis: for a well-delimited class of components — utility libraries whose functional behaviour is capturable by a domain-specific language — one can infer the client-observable behaviour by black-box exploration and **regenerate** a fresh implementation in that DSL. Because the DSL has no file-system, network, or global-state constructs, the malicious behaviour is not merely blocked but *inexpressible*.

> **(KO)** 핵심 통찰은 "은닉형 공급망 공격은 정상 기능을 반드시 보존해야 한다"는 점입니다. 그렇다면 정상 기능만 학습해 다시 만들면 악성 부분은 자동으로 사라집니다. 탐지(detection)나 격리(confinement)가 아니라 **제거(elimination)** 라는 제3의 축을 제시한 논문입니다.

## 2. Methodology

The technique is **Active Library Learning and Regeneration (ALR)**, instantiated as a system called **Harp** for string-processing components. Four cooperating pieces (§4):

1. **A DSL (§4.1)** whose grammar (Fig. 3) covers statements (`add`, `del`, `at`, `repeat`, `toggle`, `map`, `fold`, `split`), pipelines, locations/indices, predicates, character classes, and a restricted set of language built-ins (`+ − × %`, `Math.*`, `String.*`). Note what is *absent*: I/O, network, globals.
2. **An inference algorithm (§4.2)** that runs in increasingly sophisticated rounds of exploration.
3. **An input-generation component (§4.3)** that produces the probe inputs driving inference.
4. **Lightweight runtime interposition (§4.4)** to map the target library's interface.

Harp feeds generated inputs to the (potentially compromised) component, observes outputs, and infers a DSL program; a small Python compiler emits the regenerated library in the target language (JavaScript or Python), linked against a small runtime-support library `lib-harp.js`. §6 adds domain-specific **refinements** to make this tractable.

**Threat model (§3):** the adversary fully controls the target component and may modify it arbitrarily, but must preserve client-observable functionality. The library is exercised in a controlled isolated environment during learning so exploitation cannot occur mid-inference. The TCB is the language runtime, module-loading bindings, Harp's compiler, and `lib-harp.js`; Harp is assumed to load before other libraries, and libraries are assumed not to collude. Harp also defuses the *removal* case (an unpublished package) because the dependency itself is gone after regeneration.

**Deployment (§1):** before development (build a stock of safe regenerated libraries), during development (as new deps are added), or in production (hot-replace a suspect library).

> **(KO)** 방법론의 핵심은 "표현력의 의도적 축소"입니다. DSL에 파일·네트워크 연산이 아예 없기 때문에, 학습이 실패해도 악성 동작이 새어 나올 수 없습니다. 이는 방어를 정책(policy) 문제가 아니라 **언어 설계** 문제로 바꾼 접근입니다.

## 3. Experiments / Evaluation Setup

**Targets / datasets.**

- **Q1 (real attacks):** three widely-publicised JavaScript supply-chain incidents — `event-stream` (malicious `flatmap-stream` dependency harvesting Bitcoin credentials), `left-pad` (unpublished, replaced by a no-op, breaking a third of the Node.js ecosystem), and `string-compare` (two versions of one library in the same dependency tree, the later one touching the file system on the magic auth string `gbabWhaRQ`). Timeline-accurate replay used a **private `verdaccio` registry** reachable only from the experiment server.
- **Q2/Q3 (scale):** 14 further npm string-processing libraries selected by an experienced JS developer plus a senior undergraduate via npm keyword search ("padding", "strip", "change case"), sorted by popularity, first five pages, duplicates discarded (>10 `left-pad` clones dropped) → **17 unique string libraries**, plus **11 libraries misclassified as string-processing** (used as negative cases). §7.1 states Harp was applied to **all 28** libraries. Collective reach of the 17: **102M weekly downloads, 4.3K direct dependents, >15K total dependents**, transitively imported by **>100K applications**.
- **Q4 (cross-language):** **5 C/C++ string libraries** found by the same GitHub search terms, chosen specifically because they have JavaScript bindings so compatibility could be checked with JS tests. Harp expects native add-ons to be wrapped by a language-level interface such as **Node's NaN or N-API** (or Python's `ctypes`/`CFFI`).

**What was measured.** (a) whether the reproduced attack still fires after regeneration; (b) **privilege reduction** α/t — the fraction of otherwise-reachable built-in/third-party APIs the regenerated library can no longer invoke; (c) wall-clock ALR time from `npm install` to abort / timeout (12 h) / success; (d) source-code **coverage** achieved by the input generator; (e) runtime performance over 10K-iteration tight loops, each experiment repeated **100×** and averaged; (f) correctness via developer test suites **plus** the test suites of the **top 10 client libraries/applications** that import the original, plus manual inspection of the regenerated code.

**Setup.** Server with 512 GB RAM, 64 × 2.1 GHz Intel Xeon E5-2683, Debian 4.9.144-3.1. Node.js v12.19 (V8 v7.8.279.23, LibUV v1.39.0, npm v6.14.8); CPython 3.7.5.

> **(KO)** 평가 설계에서 눈여겨볼 점: ① 실제 사건 3건을 사설 레지스트리로 **시점까지 재현**했고, ② 정확성을 원 라이브러리 테스트뿐 아니라 **상위 10개 클라이언트 애플리케이션 테스트**로도 검증했으며, ③ "문자열 라이브러리가 아닌 11개"를 일부러 넣어 오탐/중단 동작까지 측정했습니다.

## 4. Results / Key Findings

**Attack elimination (Q1).** All three incidents eliminated; the authors state Harp is, to their knowledge, the first system that can eliminate these attacks.

| Incident | ALR time (avg) | Privilege reduction | Correctness | Overhead |
|---|---|---|---|---|
| `flatmap-stream` (event-stream) | 1.4 s | **332×** | 14/14 event-stream tests (100%) | ~107 µs/run |
| `left-pad` | 3.6 s | **332×** | 35/35 tests (100%) | ~20 µs/run |
| `string-compare` | 0.7 s | **332×** | 3/3 tests (100%) | ~41 µs/run |

For `event-stream`, ALR simply never infers a file-system access — there are none during learning, and the DSL cannot express them. For `string-compare`, the regenerated code is **identical for both the benign and the malicious version**, and the magic-string check is gone. For `left-pad`, the regenerated version keeps passing tests *after the original is unpublished from the local registry*.

**Learning cost (Q2).** Across the 17 string libraries: **0.7 s – 3059 s (50.9 min)**, average **204.83 s**; **14/17 under a minute**, **16/17 under 145 s**. The outlier is `camel-case` (8 computational statements, two of them `split`) at 50.9 min. Harp aborts within **5 s** on the 11 non-string libraries. The §6 refinements are worth **≥179.27×** — a conservative floor, because without them **7/17** libraries hit the **12-hour** timeout (average without refinements reported as `>10.2 h`). Five small libraries are actually penalised 1.1× by the refinements.

**Regenerated-library characteristics (Q3).** Runtime performance ranges from **−1.6% (a speedup, `repeat-string`) to +6.4% (`pascal-case`)**, average **+2.3%** — the overhead traced to Harp's pattern-matching primitives compiling to a non-regular regex language with back-references. **Correctness: 14/17 pass 100%** of developer and client tests; three are partial — `upper-case` 4/6 (66.7%, locale-dependent tests), `zero-fill` 11/16 (68.8%, partially-applied-function returns), `repeat-string` 28/30 (93.3%, exception-raising tests). The three failure causes are all *DSL inexpressibility*, not inference error. **Coverage** is 100% for 11/17, average **86.04%**, with misses concentrated in exception handlers (`decamelize` 80%, `flatmap-stream` 71.21%/62.2%, `trim` 33.3%, `upper-case` 44%, `zero-fill` 80%). Crucially, the regenerated libraries **import nothing** and use only basic language primitives, whereas the originals had access to the whole JavaScript ecosystem, the file system, the network, environment variables and process arguments.

**Cross-language (Q4).** Harp regenerates **JavaScript** versions of **5 native C/C++ string libraries**, with a maximum overhead of **1%**, and the regenerated versions gain memory- and type-safety properties the C/C++ originals lacked.

> **(KO)** 가장 인상적인 수치는 **332배 권한 감소**와 "악성 버전과 정상 버전의 재생성 결과가 동일"하다는 사실입니다. 실패한 3건도 추론 오류가 아니라 **DSL 표현력의 한계**라는 점이 방법론적으로 깔끔합니다. 또 C/C++ 네이티브 라이브러리를 JS로 재생성하면서 오버헤드 1% 이내라는 결과는 네이티브 애드온 제거 가능성을 시사합니다.

## 5. How to cite in Related Work

> Defences against compromised JavaScript dependencies span three strategies. Detection-based approaches flag malicious code before it ships, and confinement-based approaches such as Mir [Vasilakis et al., CCS '21], BinWrap [Christou et al., AsiaCCS '23] and NatiSand [Abbadini et al., RAID '23] restrict what a library may do at runtime; both, however, still execute attacker-supplied code. Harp [Vasilakis et al., CCS '21] takes a third route — *elimination* — by actively probing a component's black-box behaviour and regenerating it as a program in a domain-specific language that cannot express file-system, network, or global-state effects. Applied to seventeen npm string libraries with a combined 102M weekly downloads, Harp regenerated fourteen within a minute at an average 2.3% runtime overhead and a 332× privilege reduction, neutralising the `event-stream`, `left-pad` and `string-compare` incidents. Regeneration, however, is bounded by the DSL: it is demonstrated only for utility libraries whose semantics fit a string-processing grammar, and Harp explicitly excludes libraries that mutate built-in prototypes — precisely the class of behaviour that underpins prototype-pollution and gadget-chaining attacks in Electron's renderer and main processes.

> **(KO) 학위논문에서의 위치:** Harp는 **대조군(contrast)** 으로 쓰는 것이 가장 강력합니다. ① 동기 부여 측면: 공급망 라이브러리 하나가 Electron 앱의 main 프로세스 안에서 완전한 로컬 권한을 갖는다는 사실을 이 논문이 전제로 삼고 있으므로, "왜 Electron 앱에서 의존성 문제가 웹 앱보다 치명적인가"의 근거로 인용 가능. ② 방어 대조 측면: 탐지/격리/제거 3분류를 세우고, 본 학위논문은 **발견(discovery)** 이라는 네 번째 축임을 명확히 할 수 있음 — 제거는 "무엇을 제거해야 하는지 이미 안다"고 가정하지만, 발견 연구는 바로 그 전제를 만드는 작업. ③ **남겨진 공백**: (a) Harp는 문자열 유틸리티라는 좁은 도메인에만 적용되고 Electron 앱이 실제로 의존하는 복잡한 라이브러리(IPC 래퍼, 렌더러 브리지)에는 적용 불가; (b) **`String.prototype` 같은 내장 프로토타입을 변형하는 라이브러리를 명시적으로 배제** — 이는 본 코퍼스의 prototype pollution 계열(Silent Spring, GHunter, Bullseye, UOP)이 다루는 바로 그 표면이므로 정면으로 상보적; (c) 네이티브 애드온을 NaN/N-API 래핑 전제로만 다루므로, contextBridge·preload 경계는 전혀 건드리지 않음.

## 6. Caveats / what I could not confirm from the text

- **Internal inconsistency in the paper.** §7.5 opens "we apply Harp to 25 JavaScript libraries — 17 string-processing libraries and 11 other libraries", but 17 + 11 = 28, and §7.1 says "We applied Harp to all 28 libraries." I report **28** (17 + 11) as the figure the rest of the text supports; the "25" appears to be an editing slip. Do not cite "25" without re-checking.
- **Python results not verified.** §7 states Harp also works on Python libraries but that those results are "not shown here; reported in the extended version [blind]". The extended version was not located or read, so no Python numbers are recorded here.
- **Appendix B (the 5 C/C++ libraries) was not read** in full — only the summary claim in the Q4 bullet (max 1% overhead) and the §7.1 selection procedure. Per-library C/C++ timings/names are therefore not recorded.
- **No Electron, desktop-app, or contextBridge evaluation whatsoever.** The Electron relevance is entirely by inference from (i) the Node.js/npm runtime and (ii) the explicit NaN / N-API native-add-on wrapping assumption. The paper never mentions Electron.
- **The 332× privilege-reduction figure** is identical for all three incident libraries and derives from a metric defined in a cited prior work ([66] in the paper). I did not read that reference, so the exact API-counting denominator `t` is unverified.
- **`repeat-string` correctness** is given as 28/30 in Table 1 (93.3%) but the §7.5 prose says the three partial libraries pass "between 4/6 (66.7%) and 28/30 (99.3%)" — 28/30 is 93.3%, not 99.3%. Another apparent typo; the table value is the one used above.
