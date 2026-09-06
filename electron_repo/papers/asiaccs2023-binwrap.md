# BinWrap: Hybrid Protection against Native Node.js Add-ons

**Authors:** George Christou (FORTH-ICS), Grigoris Ntousakis (Brown / TU Crete), Eric Lahtinen (Aarno Labs), Sotiris Ioannidis (TU Crete / FORTH-ICS), Vasileios P. Kemerlis (Brown), Nikos Vasilakis (Brown)
**Venue / Year:** ACM ASIA Conference on Computer and Communications Security (ASIA CCS '23), Melbourne, 10–14 July 2023 · **Distinguished Paper Award** · 14 pages
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3579856.3590330) · [PDF (author-hosted, Brown)](https://cs.brown.edu/people/vpk/papers/binwrap.asiaccs23.pdf) · [PDF (Vasilakis mirror)](http://nikos.vasilak.is/p/binwrap:asiaccs:2023.pdf) · DOI 10.1145/3579856.3590330
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Electron's main process *is* a Node.js runtime, and a packaged Electron app routinely ships `.node` native add-ons that load straight into it — BinWrap is the defense built precisely for that boundary, and its ecosystem study is the best public quantification of how large that boundary is.

> **한 줄 요약 (KO):** npm 생태계의 약 4.2%가 네이티브 애드온(NAN/N-API)에 의존하고 97,161개 패키지가 그것에 간접 의존한다는 실측을 근거로, 애드온의 **JS 래퍼와 바이너리 양쪽**에 동시에 권한 모델을 걸어(Intel MPK/PKU + seccomp-BPF) 메모리 안전성 붕괴를 막는 방어 프레임워크. 오버헤드 0.71%–10.40%.

**Grounding:** written from the complete open-access PDF (author-hosted copy at cs.brown.edu). All figures below are read off the paper text; nothing is inferred from secondary sources.

## 1. Problem, Gap & Hypothesis

Applications written in memory-safe, managed languages inherit that safety only as far as the managed runtime reaches. Node.js lets JS programs load **native add-ons** — C/C++ libraries exposed through a thin JS wrapper using NAN or Node-API (NAPI) — and a single memory-unsafe line inside one of those add-ons "can wreak havoc on the rest of an otherwise safe application, nullifying all the security guarantees offered by the high-level language and its managed runtime." Worse, add-ons **bypass** the language-level hardening techniques (permission systems, membranes, RWX-on-variables schemes) that the JS-side literature has built up: those mechanisms interpose on JS, and the add-on simply is not JS.

The gap the authors identify is that prior isolation work picks *one* side of the boundary. Language-level schemes protect the JS context but leave the binary unconstrained; binary-level sandboxes constrain the DSO but ignore the JS wrapper, which is itself a capability-holding object graph reachable from the application. Their hypothesis: a **hybrid** permission model, inferred automatically and enforced on both sides simultaneously, can cut the add-on's privilege substantially at a cost low enough that real npm packages would adopt it.

> **(KO)** 핵심 논지는 "경계의 한쪽만 막는 것은 막지 않는 것과 같다"이다. JS 측 방어(권한 시스템·멤브레인)는 네이티브 코드가 그냥 우회하고, 바이너리 샌드박스는 JS 래퍼가 들고 있는 권한 객체를 놓친다. Electron 논문들이 전부 JS 층만 본다는 점에서, 이 프레이밍 자체가 학위논문 §Related Work에 그대로 쓸 수 있는 문장이다.

## 2. Methodology

Three pieces, in order:

1. **Ecosystem study (§5).** Replicate the full npm registry via CouchDB replication, serve it through a local Verdaccio proxy registry, and ask three research questions: what fraction of packages use native modules (RQ1), what ratio of a package's dependencies are native (RQ2), and how popular the native ones are by dependent count (RQ3).
2. **Hybrid permission model + enforcement (§6).** A fine-grained read–write permission model applied *at the add-on's boundary*, enforced by two cooperating components: **BinWrap_L** (language-level interposition, guarding unauthorized use of the language-level bindings) and **BinWrap_B** (binary-level indirection wrapping the whole library and checking permissions on outbound interfaces). Runtime separation is by **thread**: the untrusted add-on runs on a dedicated thread whose *memory view* is narrowed with **Intel MPK/PKU** (`pkey_set` / `wrpkru`, executed in userland so domain switches are cheap) and whose *syscall surface* is narrowed with **seccomp-BPF**. `fork` and `execve` are found not to be genuinely required by native add-ons and are denied outright; core dumps are disabled (they would otherwise let the untrusted domain read memory it cannot map).
3. **Automatic permission inference.** A pair of program analyses derive the permission set over the binary side and the JS side respectively, so the developer does not hand-write policy. Syscall sets are extracted with `sysfilter`.

Threat model assumptions worth noting: W^X is enforced, the add-on contains no self-modifying code, and the hardware provides MPK/PKU or equivalent.

> **(KO)** 방법론에서 학위논문에 직접 이식 가능한 부분은 (a) CouchDB 복제로 npm 레지스트리 전체를 로컬에 떠서 측정하는 방식과 (b) `sysfilter`로 애드온별 syscall 집합을 뽑는 방식이다. 둘 다 Electron 앱 코퍼스(asar 언팩 후 `.node` 수집)에 그대로 적용 가능하다.

## 3. Experiments / Evaluation Setup

**Ecosystem measurement.** Registry snapshot at replication time contained **1,508,366 npm libraries**. Every package with at least one NAN- or NAPI-related dependency (direct or transitive) was analysed.

**Evaluation-set construction (funnel).** From the local registry: packages with a native dependency → **5,073**; installable without manual effort → **4,201**; after de-duplication → **3,508**; those shipping test cases that run out of the box → **400**; final hand-selected evaluation set → **20 native add-ons** (Table 1), chosen for popularity, workload variety, and security exigency. Table 1 records for each add-on its dependent count, C LOC, and syscall count — e.g. `node-sass` (8,457 dependents, 37,365 C LOC, 93 syscalls), `xml.js` (344 dependents, 170K C LOC), `zeroMQ` (323 dependents, 114 syscalls), down to `node-fs-ext` and `node-delta` (0 dependents). Two whole **applications** are included as end-to-end targets: *Video Thumb Grid* (uses `picha`) and *Manta Minnow* (uses `statvfs`). Benchmarks are labelled Macro (the package's own `npm test` suite) or Micro.

**Security evaluation (EQ1).** Four CVEs were selected from Snyk reports and **exploits were implemented from scratch**, mimicking publicly available exploits, then re-run under BinWrap.

**Performance evaluation (EQ3).** `npm test` run **100 times** per package, vanilla Node.js vs. BinWrap, broken out into three measurements: the native-function sandbox alone (BinWrap_B), the dynamic privilege checks alone (BinWrap_L), and combined.

**Platform.** Node.js **v8.9.4**, Linux **v5.4**, 32 GB RAM. No kernel modifications required.

> **(KO)** 평가셋 20개는 작아 보이지만 5,073 → 400 → 20 깔때기가 명시돼 있어 "왜 20개인가"에 답이 되어 있다. 다만 Node.js v8.9.4는 2017년 릴리스로, 2026년 기준 Electron이 쓰는 Node 버전과 격차가 매우 크다 — 재현 시 첫 번째 장애물.

## 4. Results / Key Findings

**How big the native boundary actually is (RQ1–RQ3):**

- **63,381 of 1,508,366** npm libraries (**4.2%** of the ecosystem) depend on a native module directly or transitively. Split: **45,708** on NAN, **23,239** on NAPI, **5,548** on both.
- **76.7%** of those have exactly one native dependency; 13.7% have two, 4.2% three, 2.3% four, 3.1% five-to-ten, and **only 99 libraries** use ten. → the common case is *one* native package per module.
- Packages using NAN/NAPI carry **11 dependencies on average**; the average ratio of NAN dependencies to total dependencies is **24.22%**, NAPI **11.27%**.
- Reach: **8,148** NAN-based modules have dependents (avg **7.2**, max **8,457** — `node-sass`), totalling **58,778** dependent packages. **5,762** NAPI modules have dependents (avg **6.6**, max **2,322**), totalling **38,383**. Combined, **97,161 packages** sit downstream of a native module. Only the top **11** NAN packages exceed 500 dependents; the 50th-most-popular has ≈90.

**Exploit mitigation (EQ1) — 4/4 blocked, by two different mechanisms:**

- **CVE-2018-11499** (`node-sass` ≤ v3.5.5, use-after-free → heap-pointer leak → arbitrary read primitive): blocked by **MPK/PKU memory sandboxing** — reads beyond `libsass`'s allocated pages fail.
- **CVE-2018-18577** (`libtiff` via `picha`, heap overflow on JBIG decompression → arbitrary write): blocked by MPK/PKU — cannot corrupt pages outside the add-on's benign set.
- **CVE-2019-3822** (`libcurl` via `node-libcurl`, v7.36–v7.64, stack overflow during NTLM negotiation → ROP chain built with Ropper calling `system`): blocked by **syscall filtering** — `system` ends in `execve`, which is not in `libcurl`'s benign set.
- **CVE-2020-28248** (`png-img` ≤ v3.1, integer overflow → under-allocated buffer → overwrite of libpng's error callback pointer with `system`): blocked by syscall filtering.

**Syscall reduction (EQ2).** Node.js API functions require the **same 62 syscalls** across all 20 add-ons; the add-on DSOs require roughly the same set. Syscalls inherited from Node.js range from **2** (zeromq) to **35** (node-delta). BinWrap can safely block **more than ≈2/3** of available syscalls in most cases — the exception is `zeromq`, which needs **114** because of network sockets.

**Overhead (EQ3).** Macro-benchmark overhead **0.71%–10.40%**. Micro-benchmarks expose the real cost centre: the domain-transition handshake between the main thread and the restricted thread costs **240×** over a no-thread baseline when using `futex`, reduced to **80×** with inline-ASM spinning on the synchronization variable. (Baseline: a function incrementing a global, called 100M times.)

> **(KO)** 숫자 중 학위논문에 가장 유용한 것은 **97,161개 패키지가 네이티브 모듈 하위에 있다**와 **`execve`/`fork`는 애드온에 실질적으로 불필요하다**는 두 가지다. 후자는 Electron 메인 프로세스 애드온에 대한 syscall 프로파일링 실험의 귀무가설로 그대로 쓸 수 있다. 오버헤드 0.71–10.4%는 매크로 기준이고, 마이크로에서 80–240× 전환 비용이 나온다는 점은 반드시 같이 인용해야 공정하다.

## 5. How to cite in Related Work

> Christou et al. show that the memory-safety guarantees a JavaScript application inherits from its managed runtime end abruptly at the native add-on boundary: 4.2% of the npm registry (63,381 of 1,508,366 packages) depends on a NAN- or Node-API-based native module, and 97,161 packages sit downstream of one [BinWrap, AsiaCCS '23]. Their BinWrap framework responds with a hybrid permission model enforced on *both* sides of the boundary — Intel MPK/PKU narrows the untrusted add-on thread's memory view while seccomp-BPF narrows its syscall set — blocking four real npm CVEs (in `node-sass`, `picha`/libtiff, `node-libcurl`, and `png-img`) at 0.71%–10.40% macro-benchmark overhead. Crucially, BinWrap is a *hardening* mechanism for a runtime, not a discovery technique for applications: it assumes the add-on boundary is where the risk lives and asks how to confine it, leaving open the question of where such boundaries actually occur in shipped desktop software and what an attacker who controls renderer-side JS can reach through them.

> **(KO) 학위논문에서의 포지셔닝:** BinWrap은 **경쟁자가 아니라 동기(motivation)이자 대조군**이다. 세 가지 축에서 갭이 남는다. (1) **대상**: Node.js 서버 애플리케이션과 npm 패키지를 다루고, **패키징된 Electron 앱은 한 번도 분석하지 않는다** — Electron이 `.node` 애드온을 특권 메인 프로세스에 그대로 로드한다는 사실이 이 논문의 위협 모델을 그대로 상속하면서도 측정된 적이 없다. (2) **위협 모델**: 공격 진입점이 서버로 들어오는 untrusted input이지, **렌더러 XSS → preload/IPC → 메인 프로세스 → 네이티브 애드온**이라는 Electron 특유의 체인이 아니다. 이 체인이 BinWrap의 스레드 분리를 어떻게 통과하는지는 미해결. (3) **가용성**: Intel MPK/PKU 하드웨어와 Linux를 요구하므로, Windows/macOS가 주 배포 대상인 Electron 앱에는 현 상태로 적용 불가 — "왜 기존 방어가 Electron에 안 붙는가"의 구체적 근거로 쓸 수 있다. 같은 축의 USENIX Sec '23 *Bilingual Problems*(발견 쪽)와 짝지어 인용하면 "측정은 있었고 방어도 있었으나 둘 다 데스크톱 앱은 비워두었다"는 갭 서술이 완성된다.

## 6. Caveats / what I could not confirm from the text

- **Electron is not mentioned.** A keyword scan of the full text found no occurrence of "Electron". Every claim connecting this work to Electron in §5 above is *my* extrapolation from the shared Node.js/V8/native-add-on substrate, not the authors'.
- **Node.js v8.9.4 / Linux v5.4** is a 2017-era runtime on a 2019-era kernel. Whether the language-level interposition still holds against modern Node (and against Electron's patched V8) is untested and is the first thing a replication would hit.
- **Hardware dependency.** MPK/PKU is described by the authors themselves as not "standard", available in modern Intel server CPUs. AMD and Apple Silicon coverage is not discussed; the paper notes some related mechanisms "cannot be directly applied in x86 and require custom hardware".
- **Figures 5–7 are graphs.** The syscall-set sizes and the per-package overhead curve are plotted, not tabulated. I have the stated ranges (62 shared syscalls, 2–35 inherited, ≈2/3 blockable, 0.71%–10.40%) but **not** per-package overhead values.
- **Evaluation-set size.** 20 add-ons out of 3,508 installable candidates. The funnel is documented and defensible, but the security evaluation rests on **4 CVEs** — small, and all four are memory-corruption bugs in the DSO, so nothing is said about *logic* flaws in the JS wrapper.
- The Distinguished Paper Award is reported by Brown CS news and the AsiaCCS 2023 awards page, not by the PDF itself.
