# NatiSand: Native Code Sandboxing for JavaScript Runtimes

**Authors:** Marco Abbadini, Dario Facchinetti, Gianluca Oldani, Matthew Rossi, Stefano Paraboschi (Università degli studi di Bergamo)
**Venue / Year:** 26th International Symposium on Research in Attacks, Intrusions and Defenses (**RAID '23**), Hong Kong, 16–18 October 2023 · 15 pages
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3607199.3607233) · [PDF (author-hosted, UniBG SecLab)](https://cs.unibg.it/seclab-papers/2023/RAID/natisand.pdf) · DOI 10.1145/3607199.3607233 · Artifact: <https://github.com/unibg-seclab/natisand> (open source, CC-BY)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Names the exact hole an Electron threat model has to account for — a JS runtime's permission system stops at the JS/native boundary, so any binary or shared library the runtime executes runs with the **full privileges of the user running the whole application**, entirely outside the reference monitor.

> **한 줄 요약 (KO):** Node.js·Deno·Bun 모두 JS 코드는 안전하게 격리하지만 **바이너리 실행과 공유 라이브러리 로드에는 아무 격리도 제공하지 않는다**는 지적에서 출발해, Landlock(파일시스템)·eBPF(네트워크)·Seccomp(IPC)로 네이티브 컴포넌트 단위 샌드박스를 Deno에 구현. 32개 고위험 CVE 익스플로잇을 차단하면서 Minijail/Sandbox2/Wasm보다 오버헤드가 낮음.

**Grounding:** written from the complete open-access PDF (author-hosted CC-BY copy at cs.unibg.it). All figures below are read off the paper text.

## 1. Problem, Gap & Hypothesis

Modern JS runtimes secured themselves with **permission flags** — Deno shipped a default-deny model in 2018, and Node.js followed with a similar flag-based control model two years later (still experimental as of the paper's writing). The authors' observation is that this entire mechanism is a **JS-only reference monitor**. The moment an application calls `command`/`Deno.run` (spawn a binary) or `dlopen`/FFI (load a shared library), execution leaves the engine-managed context. Native code "does not access system resources using the APIs provided by the JS runtime and the reference monitor of the JS runtime is bypassed" — it runs "with the same privileges of the user executing the entire JS application."

The gap is that granting `--allow-run` or `--allow-ffi` is **all-or-nothing at runtime granularity**, which the authors argue is doubly wrong: it violates least privilege *and* it enlarges the attack surface, because the JS application legitimately needs many privileges for its own components, and the native component inherits all of them.

Hypothesis: resource confinement can be pushed down to **per-native-component granularity**, expressed in a single JSON policy, enforced by composable Linux primitives, with **no application code changes** (including no changes to third-party dependencies) and lower overhead than general-purpose sandboxers.

Three concrete harm classes motivate the design: **filesystem compromise** (databases, executables, private keys, user files all reachable), **privilege escalation via IPC** — a compromised binary opening a channel to a system service for a confused-deputy attack (the paper cites CVE-2020-16125 and CVE-2021-3560 as demonstrations) — and **malicious network channels** (reverse shells, exfiltration).

> **(KO)** 이 §1은 학위논문 문제 정의에 거의 그대로 옮길 수 있다. 특히 "권한 플래그는 JS 전용 레퍼런스 모니터다"라는 문장은 Electron의 `contextIsolation`/`sandbox` 옵션에도 동일하게 적용된다 — 그 옵션들 역시 렌더러의 JS 층만 다루지, 메인 프로세스가 로드하는 `.node` 바이너리에는 아무 영향이 없다.

## 2. Methodology

A design-and-build paper, not a measurement paper. Architecture:

- **Three resource categories**, default-deny for sandboxed native code: **filesystem**, **IPC**, **network**. The developer grants access explicitly in a single JSON policy file describing each compartment's *ambient rights*.
- **Enforcement primitives.** **Landlock** (LSM, kernel ≥ 5.13) for filesystem — thread-based rulesets, inherited by children via `clone`, only ever narrowable after `landlock_restrict_self()`, and stackable with SELinux/AppArmor/SMACK. **Seccomp** for syscall filtering including argument-flag inspection — e.g. `mmap` permitted only with `MAP_ANONYMOUS`/`MAP_PRIVATE`, `mknod`/`mknodat` denied with `S_IFIFO`/`S_IFSOCK`. **eBPF** (via `libbpf`, Compile Once–Run Everywhere) on LSM hooks for the cases Seccomp cannot decide, because it cannot dereference pointers without TOCTOU risk — specifically `bind`, `connect`, `open`, `openat`.
- **IPC policy.** Globally visible IPC is denied by default: FIFOs/named pipes, message queues, named semaphores, non-private shared memory, signals, UNIX named sockets. Parent–child channels inherited through `clone` (pipes, unnamed socket pairs) are left alone, since both ends share a security context and are invisible to other host services.
- **No root at runtime** to configure or activate compartments; **no application changes**.
- **Policy generation.** An interactive CLI tool derives policies, intended to be run against a test suite and wired into CI/CD.
- **A new API, `Deno.nativeCall()`**, lets the developer sandbox individual native *functions* (rather than whole libraries) where the risk is worth the cost.

Threat model: OS trusted; binary utilities may be malicious (supply chain) or vulnerable; **JS-side attacks are explicitly out of scope** — the engine and the runtime permission system are assumed to render JS securely. The attacker's vector is untrusted, unsanitized input reaching a native dependency, in whatever form that dependency consumes (strings, images, video, audio).

> **(KO)** 위협 모델의 마지막 문장이 이 논문의 가장 큰 제약이자, 학위논문 입장에서는 가장 큰 기회다. "JS 코드 공격은 범위 밖"이라고 명시했기 때문에, **렌더러 XSS에서 출발하는 Electron 체인**은 이 방어가 설계상 다루지 않는 영역이다.

## 3. Experiments / Evaluation Setup

**Platform (both halves):** Ubuntu 22.04 LTS, AMD Ryzen 3900X, 64 GB RAM, 2 TB SSD. Implementation integrated into **Deno**.

**7.1 Exploit mitigation.** A sample of **32 high-severity CVEs** (Table 3) affecting binaries and libraries widely used by web applications, grouped into three classes: **Arbitrary Code Execution (25 CVEs)**, **Arbitrary File Overwrite (4)**, **Local File Inclusion (3)**. Targets span ImageMagick, GraphicsMagick, OpenCV, FFmpeg, libjpeg-turbo, libsndfile, Ghostscript, SQLite, Git, ExifTool, TensorFlow, Sockeye, PyTorch Lightning, Unzip, GNU Tar, UnRAR, POCO, Pip, OpenSSL, GNSockets. These affect open-source modules totalling **2.6M downloads/week** on npm and deno.land/x (`sharp`, `fluent-ffmpeg`, `flat`, `sqlite`). Protocol: (i) verify public PoCs exploit the vulnerable utility; (ii) verify the vulnerability is reachable *through the JS module interface* (npm modules run under Deno's Node compatibility mode); (iii) re-run with NatiSand enabled and confirm the attack fails **and** benign requests still succeed. The only change made was passing a `native-sandbox` CLI argument with a generated policy.

**7.2 Performance — four benchmarks.**
- **I (executables, server-side):** 17 common Linux utilities spawned via `Deno.run()`, timed with `Deno.bench()` (which auto-scales repetitions), across four configurations: Deno / NatiSand / **Minijail** / **Sandbox2**.
- **II (executables, remote client):** three microservices — GraphicsMagick sharpen, ImageMagick sharpen, Tesseract OCR — measured with `wrk` over 30 s, 1 Gbps / 10 ms link, 100 warmup requests.
- **III (libraries, server-side):** libxml2 (open, query), libpng (verify, info), opus (encode, create), sqlite3 (open, query on the Northwind DB); configurations Deno / NatiSand / **WebAssembly**.
- **IV (libraries, remote client):** libpng, opus, sqlite3 exposed as microservices, `wrk` as in II.

> **(KO)** 실험 설계에서 배울 점은 **(ii) 단계** — "CVE가 존재한다"가 아니라 "JS 모듈 인터페이스를 통해 실제로 도달 가능하다"를 별도로 검증한 것. Electron 앱의 `.node` 애드온에 대해 같은 도달 가능성 검증을 하려면 IPC/preload 경로까지 한 단계 더 붙여야 한다.

## 4. Results / Key Findings

**Security.** All **32 CVEs**' exploits were blocked with **no functionality loss** and no modification to the application or its dependencies. The authors' worked example is CVE-2022-2566 (FFmpeg heap OOB, ACE via a malicious MP4): NatiSand denies the compromised component access to confidential files, reverse shells, privileged IPC, and unauthorized network hosts. They state the limit explicitly — sandboxing "cannot eliminate vulnerabilities, nor it can make infeasible to use them in an exploit chain."

**Benchmark I (Table 4), slowdown vs. plain Deno.** Cost amortizes with test duration; NatiSand beats both competitors everywhere. Worst case `b2sum` (2.37 ms baseline): NatiSand **2.88×** vs. Minijail 7.19× vs. Sandbox2 9.37×. Mid-range `ls` (4.75 ms): **1.76×** vs. 3.72× / 4.68×. Long-running `curl` (81.27 ms): **1.16×** vs. 1.23× / 1.24×; `wget` (53.24 ms): **1.13×** vs. 1.18× / 1.42×. `sort` (14.37 ms): **1.43×** vs. 1.44× / 1.77×.

**Benchmark II.** NatiSand shows **approximately 5–10 ms less latency per microservice** than Minijail and Sandbox2.

**Benchmark III (Table 5), slowdown vs. plain Deno, NatiSand vs. Wasm.** libxml2 open (9.33 µs baseline): **2.51×** vs. Wasm 8.96×. libxml2 query (11.53 µs): **1.63×** vs. 4.35×. libpng verify (11.58 µs): **9.61×** vs. 13.34× — the worst case for both. libpng info (28.33 µs): **9.39×** vs. 12.63×. opus encode (58.67 µs): **1.55×** vs. 2.03×. opus create (203.72 µs): **1.64×** vs. 1.70×. sqlite3 open (63.62 µs): **1.54×** vs. 5.68×. sqlite3 query with `nativeCall` (143.98 µs): **1.51×** vs. 2.43×. Plain Deno keeps a consistent advantage for operations under ~30 µs.

**Benchmark IV.** Client-observed degradation is *smaller* than the server-side III numbers; Wasm suffers significant latency degradation from JIT compilation plus the memory marshalling needed to move data across the Wasm linear-memory boundary.

**Usability findings (argued, not measured).** Against Minijail/Sandbox2: those force application changes and require deep knowledge of capabilities, namespaces, and Seccomp filters, and can only restrict IPC and network via **namespaces**, which are coarser-grained than NatiSand policies. Against Wasm: requires a Wasm-compatible build of the library (the authors had to compile `opus` with Emscripten and `libpng` with the WASI SDK by hand), WASI restricts ambient rights only programmatically and only at **directory** granularity, and the developer must manually allocate and marshal bytes.

> **(KO)** 인용할 때 가장 강한 숫자는 "32개 CVE 전부 차단, 기능 손실 없음, 애플리케이션 수정 없음"과 Table 4/5의 대조 배수다. 반대로 정직하게 같이 써야 할 숫자는 libpng의 **9.4–9.6×** — 짧고 빈번한 네이티브 호출에서는 이 접근이 싸지 않다는 뜻이다.

## 5. How to cite in Related Work

> Abbadini et al. observe that the permission systems adopted by modern JavaScript runtimes — Deno's default-deny flags and Node.js's later equivalent — constitute a JS-only reference monitor: once an application invokes a binary or loads a shared library, that code executes with the full privileges of the user running the application, entirely outside the runtime's control [NatiSand, RAID '23]. Their NatiSand prototype pushes confinement down to per-native-component granularity using Landlock, eBPF, and Seccomp behind a single JSON policy, blocking exploits for 32 high-severity CVEs in binaries and libraries reached through npm and deno.land/x modules with 2.6M weekly downloads, at consistently lower overhead than Minijail, Sandbox2, or WebAssembly-based isolation. The work is deliberately scoped to *confining* native code once its boundary is known, and its threat model places attacks on JavaScript code out of scope — leaving unaddressed how an adversary who first compromises the JavaScript side of a desktop application reaches those native components in the first place.

> **(KO) 학위논문에서의 포지셔닝:** NatiSand는 **방어 대조군**이자 **동기 논거**다. 남는 갭 세 가지. (1) **위협 모델의 방향**: 공격이 서버로 들어오는 untrusted input에서 시작한다고 가정하고 JS 측 침해를 명시적으로 배제한다. Electron의 실제 체인은 정반대 방향 — **렌더러 XSS → contextIsolation/preload 우회 → 메인 프로세스 → 네이티브 코드** — 이며, 이 시작점이 NatiSand의 가정 밖이다. (2) **런타임/플랫폼**: Deno에 구현되었고 Landlock·eBPF·Seccomp에 의존하므로 **Linux 전용**이다. Electron 앱의 주 배포 대상인 Windows/macOS에는 이식 경로가 논의되지 않는다 — Related Work에서 "기존 네이티브 격리 방어가 왜 데스크톱 앱에 그대로 적용되지 않는가"의 두 번째 근거(첫 번째는 BinWrap의 Intel MPK/PKU 하드웨어 요구). (3) **발견 vs. 완화**: 어떤 네이티브 컴포넌트가 위험한지 *찾아내는* 문제는 다루지 않고, 이미 알려진 CVE 32개를 차단하는 것으로 평가한다. 패키징된 Electron 앱에서 `.node` 애드온이 어디에, 얼마나, 어떤 도달 경로로 존재하는지는 여전히 미측정.
> 같은 축의 세 논문을 묶어 인용하면 서사가 완성된다 — **Bilingual Problems**(USENIX Sec '23, 발견·측정) / **BinWrap**(AsiaCCS '23, Node.js 애드온 방어) / **NatiSand**(RAID '23, 런타임 네이티브 실행 방어). 셋 다 Electron 앱을 하나도 분석하지 않는다.

## 6. Caveats / what I could not confirm from the text

- **Electron is never mentioned.** A keyword scan of the full text found zero occurrences of "Electron". Every Electron connection drawn in §5 is my extrapolation from the shared Node.js/V8 substrate, not the authors' claim. Note this is a *stronger* silence than in *Bilingual Problems*, which at least names Electron.js once.
- **No false-positive / policy-quality evaluation.** The CLI policy generator is described and recommended for CI/CD, but the paper reports no measurement of how often generated policies are too tight (breaking benign behaviour) or too loose. "No functionality loss" is asserted for the 32-CVE experiment, not quantified across a corpus.
- **Figures 4 and 5 are graphs.** Benchmark II and IV latency/throughput values are plotted; I have only the authors' stated "approximately 5 to 10 ms less latency" summary for II, and no numeric values for IV.
- **The 32 CVEs are a curated sample**, described as "a representative sample" — no selection protocol or population is given, so this is not a prevalence measurement.
- **Linux-only by construction.** The authors themselves note (in Related Work) that JS-side protection schemes can run in user space and therefore "do not limit the portability of the JS runtime to Linux systems" — an implicit acknowledgement that NatiSand does.
- **Sibling work not read.** The same group's *Cage4Deno* (AsiaCCS '23) is the narrower predecessor covering only subprocess filesystem confinement; it is recorded in this repo's `excluded[]` and I read only its abstract.
