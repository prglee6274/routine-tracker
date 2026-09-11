# Favocado: Fuzzing the Binding Code of JavaScript Engines Using Semantically Correct Test Cases

**Authors:** Sung Ta Dinh, Haehyun Cho, Kyle Zeng, Gail-Joon Ahn, Tiffany Bao, Ruoyu Wang, Adam Doupé, Yan Shoshitaishvili (Arizona State University); Kyle Martin, Alexandros Kapravelos (North Carolina State University); Adam Oest (PayPal, Inc.); Gail-Joon Ahn (also Samsung Research)
**Venue / Year:** Network and Distributed Systems Security Symposium (NDSS) 2021, 21–25 February 2021, Virtual · ISBN 1-891562-66-5
**Links:** [paper](https://www.ndss-symposium.org/ndss-paper/favocado-fuzzing-the-binding-code-of-javascript-engines-using-semantically-correct-test-cases/) · [PDF](https://www.ndss-symposium.org/wp-content/uploads/ndss2021_6A-2_24224_paper.pdf) · [DOI 10.14722/ndss.2021.24224](https://dx.doi.org/10.14722/ndss.2021.24224) · [code](https://github.com/favocado/Favocado)
**Scope tag:** PRIMARY

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Favocado is the origin paper of the "binding layer is the neglected attack surface" line that this thesis sits in — it establishes that when a desktop application embeds a JavaScript engine, the C/C++ *binding code* that exposes host functionality to scripts is systematically under-tested relative to the engine core, which is the exact structural claim a thesis makes about Electron's preload/`contextBridge`/native-addon surface.

> **한 줄 요약 (KO):** JavaScript 엔진을 내장한 데스크톱 애플리케이션(Adobe Acrobat, Foxit, Chromium, WebKit)에서 JS↔C/C++ 사이를 잇는 **바인딩 레이어**만을 겨냥해, IDL·API 레퍼런스에서 추출한 시맨틱 정보로 "런타임 예외를 내지 않는" 테스트케이스를 생성하고, DOM 객체를 **동치류(equivalence class)** 로 쪼개 입력 공간을 줄이는 퍼저. 2주~4일 캠페인으로 신규 버그 61개(보안 취약점 33개, CVE 13개)를 찾아냄. Electron의 preload/contextBridge/native addon도 정확히 같은 "바인딩 레이어"이므로, 본 논문은 그 공격면이 왜 별도 기법을 필요로 하는지에 대한 최초 근거.

## 1. Problem, Gap & Hypothesis

JavaScript escaped the browser: engines are now embedded in general-purpose commercial software (the paper names Adobe Acrobat and Node.js explicitly). Those embedders expose host capability to scripts through a **binding layer** — native C/C++ code that creates and maps data types between JavaScript and the host, declared through Interface Definition Language (IDL) files. Because the translation happens in an unsafe language and JavaScript's type- and memory-safety cannot be carried across, binding code is a dense source of memory-corruption bugs.

**The gap, stated plainly by the authors:** "While the JavaScript engines are being heavily studied, fuzzed, and hardened, their binding layers are frequently overlooked" — and none of the JS fuzzers of that era could fuzz binding code in *non-browser* environments. Two concrete obstacles explain why:

1. **Semantic correctness.** Triggering binding code takes at minimum two dependent steps — create the object, then set a property or call a method on it (the paper's Listing 1: `var cb = this.getField("CheckBox"); cb.checkThisBox(0,true);`). Syntax-only generators produce statements that die on reference/type errors before reaching native code. Even CodeAlchemist, the semantics-*aware* state of the art, got <20% of >5-statement test cases to run exception-free.
2. **Input-space size.** Chromium alone exposes **more than 1,000 DOM binding objects**, each with many methods and properties, some requiring other DOM objects as arguments. Enumerating the cross-product is infeasible.

**Hypothesis (two parts):** (a) semantic information can be *extracted mechanically* from IDL files and vendor API references, and combined with execution-state tracking to emit test cases that essentially never raise unintended exceptions; (b) binding objects are **relatively isolated** — separate native modules that do not interact unless one object can be passed to another — so the input space can be partitioned into equivalence classes and fuzzed class by class.

*(KO) 이 "상대적 격리(relative isolation)" 가정이 논문의 핵심 통찰. Acrobat의 `spell.check()`와 `Net.HTTP.request()`는 서로 다른 네이티브 모듈이라 호출 순서를 바꿔도 동치 → 동치류 안에서만 변이하면 탐색 공간이 급감. Electron으로 옮기면 "preload에서 노출한 API 묶음별로 동치류를 만든다"는 설계로 그대로 번역된다.*

## 2. Methodology

Favocado has two components (paper's Fig. 3):

**(A) Semantic information construction.** Parse IDL files where available (Chromium, WebKit) or vendor API reference documents where the target is closed-source (Adobe Acrobat; Foxit has *no* public API reference, so Adobe's was reused). The output is a JavaScript file describing every binding object: its properties, its methods, and for each argument the exact type and the set of admissible values. The paper's Listing 2 example is `HTMLDialogElement` with its two properties and methods. Building relations: if object A can appear as a property value or method argument of object B, A and B are related; the transitive closure of that relation defines the **equivalence classes**.

**(B) Test case generator (`fuzz.js`).** Runs inside the target. It picks an equivalence class, selects a small group of objects from it (configured to **fewer than 6 objects**, excluding related objects), and emits statements. State is tracked during mutation so that generated statements only touch objects/properties/methods currently live — notably, it will not reference an object that a previous statement deallocated. Deliberate error injection: because type-confusion and range bugs need *wrong* values, Favocado intentionally emits erroneous statements (wrong types, out-of-range values) with a default probability of **20%**.

**Honest limitation the authors record:** semantic-information construction is *not* fully automated. Some argument constraints cannot be recovered from IDL/API references and were supplied manually — the paper notes Domato has the same problem (its hand-written DOM grammar is 5.6K+ LoC) and leaves full automation to future work.

*(KO) 방법론에서 논문에 쓸 교훈 두 가지: (i) "명세(IDL/API 레퍼런스)를 시드로 삼는다"는 발상 — Electron에는 IDL이 없지만 `contextBridge`로 노출된 API 표면을 preload 소스에서 정적으로 추출하면 같은 역할을 한다. (ii) 의도적 오류 주입 20% — 시맨틱하게 완벽한 입력만 만들면 type confusion을 못 찾는다는 균형점.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**Targets (4 JavaScript runtime systems, 3 kinds of binding object):**

| Target | Binding objects | Source | Campaign length |
|---|---|---|---|
| Adobe Acrobat Reader v2019.012.20040 | PDF | closed-source; Adobe API reference | **2 weeks**, 8 VMs (2 cores / 4 GB each, 1 fuzzing process per VM) |
| Foxit Reader v9.5 | PDF | closed-source; **reused Adobe's** API reference | **3 days**, same settings |
| Chromium (v84.0.4110.0 for the DOM result) | Mojo and DOM | IDL files | not stated per-campaign in the read text |
| WebKit | DOM | IDL files | **4 days** |

**Configuration:** target objects rotate if no crash is found within 100K generated JavaScript statements.

**Baseline comparison 1 — CodeAlchemist (semantics-aware generative fuzzer) as a binding fuzzer.** Seeded with 4,450 valid snippets harvested for PDF binding objects plus 4,197 V8 regression-suite samples = **8,647 seeds**; its dynamic type-analysis module was *modified in CodeAlchemist's favour* (a proxy tarpit per PDF binding object so the objects are recognised as generic JS objects). **100K** test cases generated, each embedded in a PDF, loaded into Acrobat.

**Baseline comparison 2 — Domato** (Google's grammar-based DOM/binding fuzzer, the prior state of the art). To make the comparison fair-to-favourable for Domato, the authors wrote a grammar file covering only the `Field` and `Doc` objects — i.e. exactly the objects where Favocado's bugs had clustered — and ran Domato **1 week** on the newest Acrobat version (after the vendor had fixed the previously reported bugs). Favocado was restricted to the same two objects and already-found bugs were not counted.

**Runtime-error measurement:** 100,000 statements generated for each of Chromium and WebKit, execution outcomes monitored (Table II).

**Bug counting:** because targets were at latest versions, all crashes were new; crashes were manually de-duplicated by root cause and all distinct bugs reported to vendors.

*(KO) 평가 설계에서 눈여겨볼 점: 경쟁 도구(Domato)에게 "가장 유리한 조건"(버그가 몰린 두 객체만 대상으로 문법 파일 작성)을 주고도 이겼다는 서술 구조 — 방어적 비교 설계의 좋은 예. 반대로 캠페인 길이가 타깃마다 제각각(2주/3일/4일)이라 타깃 간 비교는 불가능하다는 점은 약점.*

## 4. Results / Key Findings — concrete numbers

**Headline: 61 previously unknown distinct bugs across 4 runtime systems; 33 are exploitable security vulnerabilities; 13 had been assigned CVEs by the time of writing.**

Per target (from §V and Table III):

| Target | Distinct bugs | Of which exploitable | CVEs |
|---|---|---|---|
| Adobe Acrobat Reader | **39** (in 2 weeks) | **18** | **11** at time of writing; vendor rated impact "critical" |
| Foxit Reader | **3** (in 3 days) | 3 use-after-free | — |
| Chromium — DOM | **6** | 2 security vulnerabilities | incl. CVE-2020-6524 (heap overflow) |
| Chromium — Mojo | **2** | incl. an exploitable use-after-free | — |
| WebKit — DOM | **3** (in 4 days) | **all 3** exploitable | — |

Named CVEs visible in Table III include CVE-2019-8211/8212/8213/8214/8215/8220 and CVE-2019-16448, CVE-2020-3792 (Acrobat use-after-free), CVE-2019-16446 (untrusted pointer dereference), CVE-2020-9594 (heap out-of-bounds write), CVE-2019-8221 (type confusion), CVE-2020-9722 (Acrobat v2020.009.20067 UAF), CVE-2020-6524 (Chromium DOM heap overflow).

**vs. CodeAlchemist:** only **28.24%** of its 100K test cases executed without a runtime error, and none produced a crash; ~71% failed to execute completely, **98.24%** of those failures being reference errors and type errors — i.e. the state-of-the-art semantics-aware fuzzer is effectively blind to binding code.

**vs. Domato (1 week, restricted to `Field`/`Doc`):** Domato found **1** use-after-free; Favocado found **6** distinct bugs *including* the one Domato found. Domato's test cases executed successfully **65.36%** of the time.

**Favocado's own error rate:** about **10%** of generated statements raised runtime errors (mostly type errors) — and that figure is inflated on purpose by the 20% deliberate-error setting.

**Case study shape (CVE-2019-8211, Acrobat UAF):** Favocado assigns a custom function to an object's `toString` method; that function calls `flattenPages(0)`, which deallocates every `Field` object on page 0; `toString` then returns a valid string, so from the generator's point of view the statement is perfectly well-typed — the bug comes from the *callback re-entering the host during type coercion*. CVE-2020-9594 is a heap out-of-bounds write found the same way.

*(KO) 숫자 중에 논문에 인용할 가치가 가장 큰 것: (1) CodeAlchemist의 28.24% 실행 성공률 — "일반 JS 퍼저는 바인딩 코드에 도달조차 못한다"는 정량적 증거. (2) `toString` 콜백으로 호스트를 재진입시켜 UAF를 만드는 패턴 — Electron의 IPC 직렬화 경계에서 동일한 재진입 문제가 발생할 수 있다는 논지의 직접 근거.*

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Prior work has established that the *binding layer* — the native code that translates values between an embedded JavaScript engine and its C/C++ host — is a distinct and systematically under-tested attack surface, separate from the engine core. Dinh et al. showed that general-purpose JavaScript fuzzers cannot reach this layer at all: the state-of-the-art semantics-aware fuzzer CodeAlchemist executed only 28.24% of its test cases without a runtime error and produced no crashes when retargeted at PDF binding objects [Favocado, NDSS'21]. By extracting binding semantics from IDL files and vendor API references and partitioning binding objects into equivalence classes, Favocado found 61 previously unknown bugs — 33 of them exploitable, 13 assigned CVEs — in Adobe Acrobat Reader, Foxit Reader, Chromium and WebKit. This line of work, however, treats the host application as a *single* trust domain and asks only whether the native binding code is memory-safe; it does not consider the case where the script itself is attacker-supplied and the binding layer is the intended privilege boundary. That is precisely the setting of an Electron application, where `contextBridge` is deliberately designed to expose host capability to web content of uncertain provenance.

*(KO) 포지셔닝: 이 논문은 **동기(motivation)** 이자 **기법의 조상**이지, 경쟁자가 아니다. 세 가지로 쓰면 좋다. (i) "바인딩 레이어는 별도의 공격면이다"라는 명제의 1차 출처 — Electron의 preload/contextBridge/native addon이 모두 같은 레이어임을 지적하며 인용. (ii) **남긴 gap**: Favocado의 위협 모델은 "악성 PDF가 앱을 공격"이며 스크립트는 신뢰 경계의 *바깥*에 있다. Electron은 정반대로, 스크립트(렌더러의 웹 콘텐츠)가 신뢰 경계의 *안쪽 가까이* 있고 바인딩이 곧 권한 경계다 — 즉 Favocado의 기법은 있어도 Electron의 위협 모델은 다루어진 적이 없다는 논지가 성립. (iii) 기법적 gap: Favocado는 IDL이 있는 세계를 전제한다. Electron 앱에는 IDL이 없고 `contextBridge.exposeInMainWorld` 호출을 정적으로 파싱해 API 표면을 복원해야 하므로, "명세 추출" 단계 자체가 새 기여 지점이 된다. 계보상 후속 연구인 COOPER(NDSS'22), Bilingual Problems(USENIX'23), Best of Both Worlds(S&P'26), From Documentation to Zero-day(CCS'26)와 한 문단으로 묶어 서술할 것.*

## 6. Caveats / what I could not confirm from the text

- The full NDSS PDF was fetched and read, but **selectively**: §I–§III fully, then §V (evaluation), Table I–III rows, §V-F/G/H and §VI–§VII by targeted grep. §IV (design internals) was read only through its grepped fragments, so fine detail of the test-case generation algorithm is summarised at a coarser level than the rest.
- **Campaign durations for the Chromium Mojo and DOM experiments were not recovered** from the portions read; only Acrobat (2 weeks), Foxit (3 days) and WebKit (4 days) are stated above. Do not cite a Chromium campaign length.
- Table III was read as fragmentary rows (the PDF-to-text conversion interleaved the table), so the per-target exploitable/moderate/low breakdown above is assembled from the prose in §V plus visible rows; the 61 / 33 totals and the named CVEs are directly attested, but **the exact count of "moderate" vs "low" impact bugs is not**.
- The paper says 13 bugs had CVEs "by the time of writing" overall, while §V-C says 11 of the Acrobat vulnerabilities had CVEs. Both figures are quoted as the paper states them; the remaining 2 are presumably Chromium/WebKit, but that attribution is **inference, not text**.
- No artifact-evaluation badge information was recovered, and the GitHub repository was not opened.
