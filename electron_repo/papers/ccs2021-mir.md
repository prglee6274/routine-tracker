# Preventing Dynamic Library Compromise on Node.js via RWX-Based Privilege Reduction (Mir)

**Authors:** Nikos Vasilakis (MIT CSAIL), Cristian-Alexandru Staicu (CISPA), Grigoris Ntousakis (TU Crete), Konstantinos Kallas (U. Pennsylvania), Ben Karel (Aarno Labs), André DeHon (U. Pennsylvania), Michael Pradel (U. Stuttgart)
**Venue / Year:** 28th **ACM SIGSAC Conference on Computer and Communications Security** (**CCS '21**), 15–19 November 2021, Virtual Event, Republic of Korea · 18 pages
**Links:** [ACM DL](https://dl.acm.org/doi/abs/10.1145/3460120.3484535) · [PDF (author-hosted, UPenn)](https://www.seas.upenn.edu/~andre/pdf/mir_ccs2021.pdf) · [CISPA publications record](https://publications.cispa.saarland/3478/) · DOI 10.1145/3460120.3484535 · Artifact: <https://github.com/andromeda/mir>
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Mir is the canonical statement of the problem an Electron main process inherits wholesale — *every* imported library runs with the full ambient authority of the JavaScript runtime (`require`, `child_process`, `fs`, globals, the module cache) — and its own §3 explicitly declares native `.node` add-ons a **non-threat**, which is precisely the door an Electron app leaves open.

> **한 줄 요약 (KO):** Node.js에서 서드파티 라이브러리는 필요 이상의 권한(모든 내장 API·전역·다른 라이브러리·`require` 자체)을 갖는다는 문제에서 출발해, **라이브러리 경계마다 자유변수 이름 단위의 RWX(+I) 권한 집합**을 정의하고 정적 분석으로 자동 추론·런타임 강제하는 시스템 Mir. 1,000개 이상 라이브러리에 적용해 **실제 공격 63건 중 61건 차단**, 공격면 평균 **143.48× 축소**, 오버헤드 **1.93%**, 호환성 **99.09%**.

**Grounding:** written from the **complete open-access author-hosted PDF** (`mir_ccs2021.pdf`, UPenn). Abstract, §1 Introduction, §3 Threat model, §4 Permission model, §8.1–8.5 Evaluation read directly; §5–§7 (inference algorithm, quantification, runtime enforcement) read in part. All numbers below are read off the paper text.

## 1. Problem, Gap & Hypothesis

Node.js applications import dozens to hundreds of third-party libraries, and **each one runs with every privilege the language and runtime offer**: any built-in API, any global, the APIs of every other imported library, and the ability to `require` further libraries. The authors name the resulting risk **dynamic compromise** — the runtime subversion of a *benign* library through the inputs passed to it.

Their running example is a deserialization library that legitimately calls `eval`. The library is not malicious and touches no other external API, but an attacker who controls the serialized input turns that single `eval` into file-system and network access. The bug is not in the library's code; the bug is that nothing stops the library from reaching APIs it never mentions.

Gap: existing answers are either too heavyweight for adoption (membranes, higher-order contracts, information-flow monitoring) or address a different problem (debloating removes *unreachable* code but leaves the reachable code's ambient authority intact).

**Key insight / hypothesis:** *if a library does not reference some functionality statically — as visible in its own source — then it should not be able to reach that functionality dynamically, even when subverted.* Deny by default; whitelist only what static analysis proves the library names.

> **(KO)** 이 문제 정의는 Electron 메인 프로세스에 **글자 그대로** 이식된다. 메인 프로세스는 Node 전체 권한을 갖고, 거기서 `require`된 npm 라이브러리 하나하나가 같은 앰비언트 권한을 상속한다. 즉 Electron 앱에서는 "렌더러 XSS → preload/IPC → 메인 프로세스"까지 도달한 공격자가 **메인 프로세스가 import한 모든 라이브러리의 권한 합집합**을 얻는다. Mir의 문제 정의를 그대로 인용하고 "Electron에서는 이 권한 합집합이 원격 웹 콘텐츠로부터 도달 가능해진다"는 한 문장을 덧붙이면 학위논문 문제 정의가 된다.

## 2. Methodology

Four coupled contributions:

**(a) Permission model + DSL (§4).** A **first-order** RWX permission model applied *at library boundaries*. Every **access path** — a free variable name and its fields in the library's top-level scope (e.g. `String.toUpperCase`, `fs.readFile`, `child_process.exec`) — is governed by a mode drawn from **R** (read), **W** (write), **X** (execute) and **I** (import). The deserialization library above receives only `X` on `eval`, and nothing else. Access-path roots are of two classes: a closed set of language-provided roots (globals, `process.env`, `process.args`, the module cache, `require`) and the exports of other libraries. The DSL supports wildcards (`*.f`, `f.*`).

The authors are explicit that this is **deliberately less powerful** than membranes, higher-order contracts, or information-flow monitoring — the design target is a tool with the operational weight of a *linter or minifier*, because that is what Node developers actually run.

**(b) Automated permission inference (§5).** A mostly-**static** dataflow analysis over the control-flow graph, tracking a permission set `C` and a `DefToAPI` map from local definitions to fully-qualified API paths, with transfer functions that add `(a,R)`, `(a,W)` or `(a,X)` when an API `a` is read, written or executed. Branches propagate along both paths and union at merges; **loops are unrolled once** (justified: loops rarely reassign third-party references). Critically, the static analysis is augmented by a short **dynamic, import-time phase** to catch the runtime meta-programming patterns endemic to npm — this turns out to matter enormously for compatibility (see §4 below). Deliberately scalable, conservative, and **assumes no test suite exists**.

**(c) Privilege-reduction quantification (§6).** A metric comparing the permissions Mir grants against the permissions the library would hold by default (statically counting all access paths in its lexical scope) — a proxy for the residual attack surface. The authors note it is **conservative by construction**: it does not track transitive calls across library boundaries (that would need heavyweight information-flow analysis), so the reported reduction is a *lower bound*.

**(d) Implementation.** Analysis mostly in **Java**; runtime enforcement in **JavaScript** (~2.8 KLoC, built on **Lya**), using lightweight wrapping rather than a stronger protection mechanism, matching the model's first-order nature.

**Threat model (§3) — and its two decisive exclusions.** In scope: an attacker who subverts a benign library at runtime through its inputs, reaching (1) language-level power such as stack inspection, reflection and **prototype pollution**; (2) ambient authority over `process.env`, `process.args`, globals, the module cache and `require`; (3) standard-library interfaces (file system, network); (4) other third-party libraries in the program. Assumptions: the static analysis runs before execution, and the runtime component loads before any other library; the language runtime and built-ins (`fs`) are trusted.

**Non-threats, quoted because they define the gap:** Mir "**does not consider native libraries written in lower-level languages, such as C/C++, or libraries available in binary form**" — for two stated reasons: they cannot be analysed by a source-level static analysis, and they can **bypass Mir's runtime protection, which depends on memory safety**. Also excluded: input-sanitization/command-injection attacks on APIs the library *does* legitimately use; and availability, DoS and side-channel attacks.

> **(KO)** 방법론에서 학위논문에 직접 쓸 부분은 **"정적으로 이름을 언급하지 않은 API는 동적으로도 못 쓴다"**는 원칙과, **import-time 동적 분석을 소량 섞어 호환성을 구제**한 설계다. 후자는 §4에서 수치로 정당화된다(70.59% → 99.09%). Electron에 옮기면 "preload 스크립트가 `contextBridge`로 노출한 이름의 집합"이 곧 권한 집합이 되므로, Mir의 access path 모델이 preload 노출면 정량화에 거의 그대로 대응한다.

## 3. Experiments / Evaluation Setup

Five research questions (Q1–Q5), evaluated on **over 1,000 npm libraries**.

**Q1 — Security.** Systematic, unbiased construction of the attack set from **all publicly known npm vulnerabilities in the Snyk database**, filtered to categories inside the threat model: **arbitrary code execution, remote code execution, sandbox escape** → **132** candidates. Then removed: **23** for other platforms/languages (Android, browser, PHP, Python), **33** misclassified, plus further "could not exploit" / "could not install" / "outside threat model" losses (per Fig. 5's funnel bars: 63, 7, 6, 33, 23 / 46, 15, 2 / 61, 2), leaving **63** working PoC attacks against real vulnerable packages.

**Q2 — Privilege reduction.** **81 libraries**: the 31 of the 63 Q1 libraries that could be set up (excluding 10 without tests, 7 duplicates, 7 whose test suites would not run, 2 where Mir crashes, 6 where Mir crashes on test cases), **plus 50 additional libraries with extensive test suites** deliberately chosen to include modules that do *not* use security-critical APIs.

**Q3 — Compatibility.** Same 81 libraries. Measured at three granularities: unique field-access **code locations** (3,431 total), **fully compatible packages** (out of 81), and **test cases** (2,557 total). Run twice — full Mir vs. **static-analysis-only Mir** — to isolate the contribution of the import-time dynamic phase.

**Q4 — Performance.** Static analysis time per library; runtime enforcement overhead.

**Q5 — Comparison with debloating.** Head-to-head against **Mininode** (RAID '20 — already `in_scope` in this ledger), latest version `v.f604d9e`, applied to the same corpus, with all 63 PoC attacks replayed against the debloated libraries.

> **(KO)** 평가 설계에서 가장 정직한 부분은 **Snyk 전수 → 카테고리 필터 → 재현 가능 여부 필터**로 이어지는 깔때기를 그림 한 장(Fig. 5)으로 공개한 점이다. "63개"라는 작아 보이는 숫자가 어디서 왔는지 완전히 추적 가능하다. Electron 앱 대상 평가셋을 만들 때 그대로 따라 할 만한 서술 방식.

## 4. Results / Key Findings

**Q1 — Security: 61 / 63 attacks mitigated.** The two failures are instructive and named: one package **applies its own complex runtime wrapping** that Mir's wrapping does not handle correctly; **`typed-function`** manipulates the `Function` prototype chain in a way Mir does not currently support. For many of the 61 successes Mir blocks **at multiple levels** — e.g. for `node-serialize`, even if the `child_process` import were permitted, Mir would still block `exec`.

**Q2 — Privilege reduction: average 143.48×, range 3.5×–706×.** Up to three orders of magnitude. Permissions per library range **2–658 (avg 42.2)**, unevenly split: **1–341 R (avg 22.1)**, **0–29 W (avg 3.3)**, **0–209 X (avg 12.5)**, **0–87 I (avg 4.1)**. Reduction is **inversely correlated with library size** — small libraries use a tiny fraction of available APIs and so shed the most privilege. Manual inspection of the inferred permission sets: after Mir, **only one** of the 81 libraries retains permissions to security-critical system-wide interfaces (defined as `X` on `child_process.*`, `X` on `fs.{read,write}File[Sync]`, `R` on a subset of `process.env`), and **only five** retain "security-concerning" library-specific permissions.

**Q3 — Compatibility: 99.09% of field-access locations.** Full Mir correctly allows **3,400 of 3,431** unique access locations; counting repeats, **226,497 of 226,553 (99.98%)**. **73 of 81 (90.12%)** packages fully compatible; **2,541 of 2,557 (99.37%)** test cases pass. The **static-only ablation is the headline**: without the import-time dynamic phase, compatible access locations collapse from 3,400 to **2,422 (70.59%)** and fully-compatible packages from 73 to **58 (71.60%)**, with average inferred permissions falling from **155.9 to 42.3**. The paper's example is `fs-promise`, which computes wrappers for all `fs` methods by traversing the object returned by `fs` rather than naming them — invisible to static analysis, captured by the import-time phase.

**Q4 — Performance: 2.1 s inference, 1.93% runtime overhead** (≈3.3 ms average). Accessed fields are few per library but hot — accessed on average **795 times each**.

**Q5 — Mir vs. Mininode: 63/63 attacks still succeed against Mininode.** Mininode's static-analysis debloating takes 0.82–4.013 s (comparable to Mir) and adds **no runtime overhead**, but it **fails on 7/88 libraries** (5 entry-point failures, 1 dynamic-import exit, 1 out-of-memory) and — decisively — **every one of the 63 PoC attacks still works**, because the debloated libraries retain access to the APIs the exploits use. Removing dead code is not the same as removing privilege.

> **(KO)** 학위논문에 가장 쓸모 있는 결과 세 개. **(1) 63/63 — Mininode 무력**: 이미 `in_scope`인 Mininode(RAID '20)에 대한 직접 반증이므로, 두 논문을 **한 문단에서 짝지어** 인용하면 "디블로팅 ≠ 권한 축소"라는 구분을 저자들의 실험으로 세울 수 있다. **(2) 70.59% → 99.09%**: 순수 정적 분석만으로는 Node/npm 생태계의 동적 메타프로그래밍을 감당 못 한다는 정량적 증거 — Electron 앱 정적 분석 도구를 만들 때 예상되는 한계를 미리 인용할 근거. **(3) 143.48×**: "권한 축소"를 숫자로 말하는 방법론 자체가 참고 대상.

## 5. How to cite in Related Work

> A parallel line of work attacks the same exposure from the runtime side, by reducing what an imported library is permitted to reach. Vasilakis et al. observe that every third-party library on Node.js executes with the full ambient authority of the runtime — built-in APIs, globals, `process.env`, the module cache, and `require` itself — so that a benign library subverted through its inputs (*dynamic compromise*) inherits privileges far beyond its function [Mir, CCS '21]. Mir attaches a first-order read-write-execute-import permission set to every free-variable access path at each library boundary, infers those permissions automatically by static analysis augmented with a short import-time dynamic phase, and enforces them at runtime: across more than 1,000 npm libraries it mitigates 61 of 63 real-world exploits, reduces residual privilege by an average of 143.48×, and costs 2.1 s of analysis and 1.93% runtime overhead while preserving 99.09% of field accesses. Notably, the authors show that debloating is not a substitute for privilege reduction — all 63 exploits still succeed against the same libraries processed by Mininode [RAID '20]. Mir's threat model, however, explicitly excludes native libraries written in C/C++ or shipped in binary form, since they can neither be analysed at source level nor contained by a runtime monitor that depends on memory safety.

> **(KO) 학위논문에서의 포지셔닝:** Mir은 **방어 쪽 계보의 중간 고리**이며, 이 저장소의 Mininode(RAID '20) → **Mir(CCS '21)** → HODOR(CCS '23) → NodeShield(CCS '25) 라인을 완성시킨다. 세 가지 활용. (1) **대조군**: "이미 Node.js 라이브러리 권한 축소는 잘 연구돼 있다"는 반론에 대해, Mir이 **자기 위협모델에서 네이티브 애드온을 명시적으로 배제**했다는 문장을 인용하면 곧바로 갭 서술이 된다 — 그 배제 이유("소스 정적 분석 불가 + 메모리 안전성에 의존하는 런타임 보호를 우회 가능")는 Electron 메인 프로세스가 `.node` 바이너리를 그대로 로드한다는 사실과 결합해 BinWrap(AsiaCCS '23)·Bilingual Problems(USENIX Sec '23)·NatiSand(RAID '23)로 이어지는 다음 문단의 도입부가 된다. (2) **경계 모델의 재사용**: access path 단위 권한 집합은 Electron의 preload `contextBridge` 노출면을 정량화하는 데 거의 그대로 대응하며, "노출된 이름의 개수 = 렌더러가 도달 가능한 권한의 크기"라는 측정 지표를 만들 수 있다. (3) **적용 범위의 갭**: 평가는 전부 **서버측 Node.js npm 라이브러리**이고, 패키징된 데스크톱 앱·렌더러 프로세스·IPC 채널은 한 번도 다루지 않는다. 특히 Mir의 공격 진입점은 "라이브러리에 전달되는 입력"이지 "원격 웹 콘텐츠"가 아니다.

## 6. Caveats / what I could not confirm from the text

- **Electron is not the subject.** I did not find Electron discussed as a target; all evaluation is server-side Node.js/npm. Every Electron connection in §5 is my extrapolation from the shared runtime, not the authors' claim.
- **§5 (inference algorithm), §6 (quantification) and §7 (runtime enforcement) were read only in part.** I have the transfer-function shape (updates to `C` and `DefToAPI`, branch union, single loop unrolling, `getAPIs` resolution) but **not** the full soundness discussion or the complete enforcement mechanics.
- **Tables 3, 7 and 8** (highlighted defended attacks; the full per-library attack results in Appendix B) and **Appendix C** (full privilege-reduction results for all 81 libraries) were **not** read. Per-library numbers should be re-grounded before citing individually.
- **Fig. 5's funnel is rendered as bare numbers in the extracted text** (`63 7 6 33 23 / 46 15 2 / 61 2`). I am confident about the endpoints — 132 candidates from Snyk, 23 dropped for platform/language, 33 misclassified, 63 working attacks, 61 mitigated — but I **cannot** reliably attribute each intermediate count to its specific funnel category.
- The **2021 evaluation predates** modern Node (and Electron's patched V8) by several major versions; the paper does not state the exact Node version used, and I did not locate it in the sections I read.
- **Privilege reduction is a proxy metric**, not an exploitability measure, and the authors say it is conservative because transitive cross-library calls are not tracked. It should not be quoted as "attack surface reduced 143×" without that qualification.
- The **Mininode comparison** is Mir's own framing of a competitor. I have not re-verified the 63/63 claim against the Mininode paper or artifact.
