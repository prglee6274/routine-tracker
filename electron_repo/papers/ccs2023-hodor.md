# HODOR: Shrinking Attack Surface on Node.js via System Call Limitation

**Authors:** Wenya Wang, Xingwei Lin, Jingyi Wang, Wang Gao, Dawu Gu, Wei Lv, Jiashui Wang (Shanghai Jiao Tong University; Ant Group; Zhejiang University / ZJU-Hangzhou Global Sci-Tech Innovation Center)
**Venue / Year:** ACM CCS 2023
**Links:** [paper/DOI](https://dl.acm.org/doi/10.1145/3576915.3616609) · [PDF (arXiv)](https://arxiv.org/pdf/2306.13984) · DOI: 10.1145/3576915.3616609
**Scope tag:** ADJACENT
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** HODOR is a runtime *defense* that caps the post-exploitation blast radius of Node.js arbitrary-code/command-execution — the same RCE endpoint an Electron XSS→RCE chain reaches once it touches the main process — making it the natural "defense to contrast" against a discovery thesis.
> **한 줄 요약 (KO):** HODOR는 Node.js 애플리케이션의 호출 그래프(JS+C/C++)를 분석해 꼭 필요한 시스템 콜만 화이트리스트로 남기고 seccomp로 제한함으로써, 공격 표면을 평균 19.42%로(=80.57% 감소) 줄이는 경량 런타임 방어 기법이다.

## 1. Problem, Gap & Hypothesis
Server-side Node.js apps inherit broad system-call access through the runtime, so a JavaScript arbitrary-code-execution (ACE) bug — reached via gadget-chaining (prototype pollution), injection, or supply-chain compromise — escalates straight to system-level damage. The authors identify a gap: existing protections operate at the **JavaScript level** (code debloating, or read-write-execute permission restriction) and cannot constrain arbitrary *command* execution once native capabilities are reached, while no targeted defense exists at the **system-call level** for Node.js. Hypothesis: if you can compute which syscalls a given Node.js application legitimately needs — across both its JS code and the JS+C/C++ of the Node.js framework itself — you can enforce a tight seccomp whitelist that neutralizes most ACE payloads with negligible overhead.
*(KO) 갭: 기존 방어는 JS 레벨(디블로팅·권한제한)에 머물러 시스템 콜 레벨의 명령 실행을 못 막음. HODOR는 syscall 레벨에서 정밀 화이트리스트로 방어.*

## 2. Methodology
HODOR builds **high-quality cross-language call graphs** for the whole stack: the Node.js application (JavaScript) plus the underlying Node.js framework (JavaScript and C/C++). For the JS side it proposes a combined static–dynamic analysis with context-sensitive refinement; for the C/C++ side it adds partial context-sensitive mechanisms — both presented as improvements over state-of-the-art call-graph builders. From the call-graph mappings it derives the set of necessary system calls and splits them into a **main-thread whitelist** and a **thread-pool whitelist** (Node.js offloads some work to a libuv thread pool, so the two execution contexts need distinct filters). It then enforces these whitelists at runtime with **seccomp BPF** in the Linux kernel, applied so that spawned threads inherit the appropriate filters. The design is integrated into the Node.js framework without disrupting normal application operation.
*(KO) 방법: JS+C/C++ 통합 콜그래프 → 필요한 syscall 추출 → 메인 스레드/스레드풀 화이트리스트 분리 → seccomp BPF로 강제. 콜그래프 정밀도 향상이 핵심 기여.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured
HODOR was applied to **168 real-world Node.js applications** that had been **compromised by arbitrary code/command-execution attacks**. The considered attack surface is defined as the sum of arbitrary-code-execution and arbitrary-command-execution reachable behavior; the evaluation measures (a) how much of that attack surface remains after enforcement and (b) the runtime overhead introduced by the seccomp filtering, alongside the call-graph precision optimizations that drive whitelist tightness.
*(KO) 평가 대상: ACE 공격으로 침해된 실제 Node.js 앱 168개. 측정: 잔여 공격 표면 비율, 런타임 오버헤드.*

## 4. Results / Key Findings — concrete numbers
- HODOR reduces the remaining attack surface to **19.42% on average** — i.e., an **80.57% average reduction** — across the 168 applications.
- Runtime overhead is **< 3%** ("negligible").
- The reduction is achieved through the precision gains in cross-language (JS + C/C++) call-graph construction that yield tighter main-thread / thread-pool syscall whitelists.
*(KO) 결과: 공격 표면 평균 19.42%로 축소(=80.57% 감소), 오버헤드 3% 미만.*

## 5. How to cite in Related Work
> Beyond detecting vulnerabilities, a complementary line of work hardens the Node.js runtime to limit post-exploitation impact. Wang et al. present HODOR, which constructs cross-language (JavaScript and C/C++) call graphs of a Node.js application and the runtime itself, derives the minimal set of required system calls, and enforces per-thread seccomp whitelists; across 168 real-world applications compromised by code/command-execution attacks it shrinks the residual attack surface to 19.42% on average with under 3% overhead. Such system-call-level confinement bounds the damage of an arbitrary-code-execution payload but does not prevent the initial compromise.

*(KO) 포지셔닝: HODOR는 Mininode(RAID'20)와 같은 "Node.js 공격 표면 축소" 계열의 방어 기법이지만 syscall 레벨로 한 단계 더 내려간다. Electron 논문 입장에서는 (1) Electron의 main 프로세스가 곧 풀권한 Node 런타임이라는 위협 동기, (2) "방어는 사후 피해를 제한할 뿐, 최초 침해(XSS→RCE 도달)는 막지 못한다"는 점에서 *발견(discovery)* 연구의 필요성을 부각하는 대조군으로 인용. 다만 HODOR는 서버사이드 Node를 가정하고 Electron의 renderer 샌드박스·IPC 경계는 다루지 않음 → 그 공백이 본 논문의 자리.*

## 6. Caveats / what I could not confirm from the text
- Grounding: built from the arXiv full-text PDF (abstract, introduction, contributions, background sections). I did not read every evaluation table, so per-application breakdowns, the exact set of 168 apps, and whether HODOR blocks each specific exploit end-to-end (vs. measuring attack-surface metrics) were not verified line-by-line beyond the headline 19.42% / <3% figures.
- HODOR assumes **server-side** Node.js and a Linux/seccomp deployment; applicability to an Electron main process (multi-process, cross-platform incl. Windows/macOS where seccomp is unavailable) is not addressed by the authors and would be my own extrapolation.
- "Attack surface = 19.42%" is a metric defined by the paper (reachable ACE/ACmdE behavior); confirm the precise definition before quoting it as a hard security guarantee.
