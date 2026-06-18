# NodeShield: Runtime Enforcement of Security-Enhanced SBOMs for Node.js

**Authors:** Eric Cornelissen, Musard Balliu (KTH Royal Institute of Technology, Sweden)
**Venue / Year:** ACM CCS 2025
**Links:** [paper/DOI](https://dl.acm.org/doi/10.1145/3719027.3765136) · [PDF (arXiv)](https://arxiv.org/pdf/2508.13750) · [code](https://github.com/KTH-LangSec/nodeshield) · DOI: 10.1145/3719027.3765136
**Scope tag:** ADJACENT
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** NodeShield is a runtime supply-chain defense for the Node.js layer that Electron embeds — a "defense to contrast" that, like HODOR/Mininode, bounds what a compromised dependency can do but never detects the bug, leaving Electron-specific discovery as open space.
> **한 줄 요약 (KO):** NodeShield는 SBOM(의존성 계층) + 능력(capability) 확장(CBOM)을 런타임에 강제하여 Node.js 공급망 공격을 막는 방어 기법으로, 코드/런타임 수정 없이 67개 알려진 공급망 공격 중 98.51%를 차단하고 오버헤드는 요청당 1ms 미만이다.

## 1. Problem, Gap & Hypothesis
The Node.js/npm ecosystem is a prime software-supply-chain target: a single package transitively trusts (per cited prior work) ~79 third-party packages from ~40 maintainers, and Node.js apps run with full system access that every dependency inherits — an "invisible attack surface" where one malicious update has widespread reach. Existing defenses each miss at least one practical goal: lightweight permission systems have compatibility/policy/robustness limits, while finer-grained language-level sandboxing or taint analysis costs performance, automation, false positives, and policy conciseness. Gap/hypothesis: an SBOM — already being mandated for transparency — can be turned from a *reactive* inventory into a *proactive* runtime control if (a) it is enforced as the authoritative dependency hierarchy and (b) it is extended with per-component capabilities, all without modifying application code or the Node.js runtime.
*(KO) 문제: npm 공급망 공격 + Node 앱의 풀권한 상속. 갭: 기존 권한시스템/샌드박스/taint는 호환성·성능·오탐·정책 복잡도 중 하나 이상에서 실패. 가설: SBOM을 런타임 강제 + capability(CBOM)로 확장하면 사전 방어가 된다.*

## 2. Methodology
NodeShield enforces two policies at runtime: the **SBOM** dependency hierarchy (so a component cannot stealthily call undeclared components) and a new **Capability Bill of Materials (CBOM)** that records, per component, which of **seven** security-sensitive capabilities (sets of related system resources — files, network, processes, etc.) it may use. Enforcement is done via **code outlining** (package-level instrumentation that wraps access points *around* code rather than inlining into it), requiring **no changes to the original source or the Node.js runtime**. A novel **lexical-scoping-based** technique reduces the impact of enforcement bypasses and supports both **CommonJS and ESModules**. Coverage spans three system-access avenues: built-in modules, global variables, and native bindings. NodeShield also supports **automated policy generation** and presents CBOMs at multiple granularities to ease developer adoption.
*(KO) 방법: SBOM(의존성 계층) + CBOM(7개 capability)를 런타임에 강제. 코드 인라이닝이 아닌 'outlining'으로 원본/런타임 무수정. CommonJS·ESModules 모두 지원, built-in 모듈·전역변수·네이티브 바인딩 3경로 커버, 정책 자동 생성.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured
The authors contribute a **benchmark of 67 known supply-chain attacks** and measure prevention rate. They additionally test exploit-impact reduction using **SecBench.js** exploits, run a **performance** evaluation on long-lived server applications (response-time overhead and throughput), assess **maintainability** (how many capabilities a developer must review per dependency update / new dependency), evaluate **compatibility** with real Node.js software, run a **robustness** analysis against sandbox-bypass attempts within the threat model, and perform an **end-to-end case study** on the real-world Copay attack.
*(KO) 평가: 알려진 공급망 공격 67개 벤치마크 + SecBench.js 익스플로잇 + 성능/유지보수성/호환성/우회 견고성 + Copay 실사례 분석.*

## 4. Results / Key Findings — concrete numbers
- Prevents **98.51%** of the **67** known supply-chain attacks.
- Reduces ACE impact by detecting **87.50%** of exploits from SecBench.js.
- Performance: response-time overhead **< 1 ms**; throughput reduction **up to 360 requests/second**.
- Policy conciseness: **at most 7 entries per dependency**; maintenance burden of **< 1 capability per dependency update** on average, and **0–13 capabilities** for a new dependency.
- Robustness: prevents **all** attacks within the stated threat model; broadly compatible with vanilla Node.js despite some incompatible coding patterns in practice.
- Claimed first Node.js runtime protection tool to comprehensively cover **both CommonJS and ESModules** source.
*(KO) 결과: 공급망 공격 67개 중 98.51% 차단, SecBench.js 익스플로잇 87.50% 탐지, 오버헤드 <1ms(처리량 최대 360 req/s 감소), 의존성당 최대 7개 정책.*

## 5. How to cite in Related Work
> Complementary to vulnerability discovery, runtime supply-chain defenses aim to contain malicious or compromised dependencies in the Node.js ecosystem. Cornelissen and Balliu propose NodeShield, which enforces an application's SBOM dependency hierarchy together with a capability extension (CBOM) at runtime via non-intrusive code outlining, requiring no changes to source code or the runtime; on a benchmark of 67 known supply-chain attacks it prevents 98.51% while adding under 1 ms of response-time overhead. By binding each package to a concise set of declared capabilities, the approach shrinks the privileges an untrusted dependency inherits — yet, being a containment mechanism, it presupposes the vulnerable or malicious behavior rather than discovering it.

*(KO) 포지셔닝: NodeShield는 HODOR·Mininode와 함께 "Node.js 공격 표면/권한 축소" 방어군에 속하며, 특히 공급망 측면을 다룬다. 흥미롭게도 저자 Balliu는 Silent Spring(프로토타입 오염→RCE) 공동저자 → 본 ledger의 Node.js 인접 계열과 직접 연결. Electron 논문에서는 (1) Electron이 번들링하는 npm 의존성이 main 프로세스 권한을 그대로 상속한다는 위협 동기, (2) 컨테인먼트는 발견을 대체하지 못한다는 대조 논거로 인용. Electron 고유의 renderer↔main IPC/preload 경계는 범위 밖 → 갭.*

## 6. Caveats / what I could not confirm from the text
- Grounding: built from the arXiv full-text PDF (abstract, introduction, preliminaries, contribution list). I did not read the full evaluation tables, so per-attack breakdowns within the 67-attack benchmark and the precise SecBench.js subset were not verified line-by-line beyond the headline percentages.
- NodeShield targets **server-side** Node.js; it does not address Electron's multi-process model, renderer sandbox, or `contextBridge`/preload boundary — the Electron connection is the shared embedded Node.js runtime, my extrapolation, not an authors' claim.
- The 98.51% / 87.50% figures are tied to the authors' own 67-attack benchmark and SecBench.js respectively; generalization beyond those benchmarks is not established by the text.
- "Prevents all attacks within our threat model" is explicitly scoped to their threat model (e.g., specific bypass classes); the threat-model boundaries should be read before citing it as comprehensive.
