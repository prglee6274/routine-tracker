# Cross-Language Attacks

**Authors:** Samuel Mergendahl, Nathan Burow, Hamed Okhravi (all MIT Lincoln Laboratory)
**Venue / Year:** **Network and Distributed System Security Symposium** (**NDSS '22**), 24–28 April 2022, San Diego, CA
**Links:** [NDSS paper page](https://www.ndss-symposium.org/ndss-paper/auto-draft-259/) · [PDF (open access)](https://www.ndss-symposium.org/wp-content/uploads/2022-78-paper.pdf) · DOI 10.14722/ndss.2022.24078 · ISBN 1-891562-74-6
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the foundational statement of the mechanism that makes an Electron app's native `.node` add-ons dangerous — when a memory-safe language and a mitigated unsafe language are linked into one address space, each side's defence assumes the *other* side upholds an invariant it does not, and an attacker who alternates between them completes an exploit that neither language permits alone.

> **한 줄 요약 (KO):** Rust·Go 같은 안전 언어를 기존 C/C++ 코드베이스에 점진적으로 도입하면 각 언어의 방어 기법이 **익스플로잇의 서로 다른 단계**를 끊기 때문에, 공격자가 언어 경계를 왔다 갔다 하면 **어느 쪽 검사도 위반하지 않으면서** 제어흐름 탈취를 완성할 수 있다(Cross-Language Attack, CLA). Firefox 바이너리 전수 분석으로 이 조건이 실제로 얼마나 흔한지 정량화.

**Grounding:** written from the **complete open-access NDSS PDF** (`2022-78-paper.pdf`). Abstract, §I Introduction, the CLA taxonomy sections (bounds-check bypass, lifetime bypass, double free, intended FFI interactions, concurrency), and the Firefox quantification tables were read directly. Sections read only in part are flagged in §6. All numbers below are read off the paper text.

## 1. Problem, Gap & Hypothesis

Memory-corruption attacks against C/C++ have resisted decades of sanitizers and runtime mitigations, which "provide partial protection at best." Rust and Go promise to end this by construction — Rust via a strong type system, compile-time ownership checks for temporal safety, and compile-/run-time bounds checks for spatial safety; Go via garbage collection for temporal safety.

Because rewriting a large codebase wholesale is infeasible, the industry consensus is **gradual deployment**: rewrite components in a safe language inside an existing unsafe application. The paper lists the real deployments — **Firefox** (Servo CSS style calculation, Dogear bookmark merger, the MP4 metadata parser, the `neqo` QUIC implementation), **Tor**, **Windows**, **Google Fuchsia**, and Linux flavours in Rust; **Docker**, **Kubernetes**, **CockroachDB**, **BoltDB** in Go.

The gap: everyone had analysed each language's safety in isolation. Nobody had analysed the security of the **multi-language application** that gradual deployment actually produces.

**Hypothesis:** language safety checks and unsafe-language exploit mitigations (e.g. CFI, shadow stacks) break **different stages** of an exploit. Where two languages meet, their assumptions are mutually incompatible, and an attacker can "maneuver between the languages" so that no single check is ever violated. The paper's thesis, stated bluntly: gradual deployment of safe languages, "if not done with extreme care, can indeed be detrimental to security."

Critically, the authors restrict themselves to the *hard* case: the unsafe side **has** protection applied (e.g. CFI on C/C++), and the safe side contains **no `unsafe` code of its own**. So the vulnerability is not "someone wrote `unsafe`" — it is the boundary itself.

> **(KO)** 이 §1의 주장을 Electron으로 번역하면 이렇게 된다. Electron은 렌더러 쪽을 `contextIsolation`·`sandbox`·CSP 같은 **JS/웹 계층 방어**로 지키고, 메인 프로세스가 로드하는 `.node` 애드온은 **C/C++ 계층 방어**(있다면 CFI 등)로 지킨다. 두 방어는 서로 다른 익스플로잇 단계를 끊고, 서로가 상대편이 지켜줄 것이라 가정한다 — CLA가 말하는 바로 그 조건이다. "안전 언어를 섞으면 안전해진다"는 통념을 정면으로 반박하는 논문이라 학위논문 서론의 반전 논거로 강하다.

## 2. Methodology

**A systematization plus a taxonomy plus a measurement**, not a tool paper.

**(a) A model of exploit stages.** The authors build a model of how each class of check — language safety checks on the safe side, runtime mitigations on the unsafe side — breaks a *different* stage of an exploit, then compose the two languages' threat models. The composition introduces a new element they call a **Language Transfer node**: a point where the application deliberately hands control or data to the other language (e.g. through FFI). Conservatively, **every node in each constituent language's threat model must connect to the Language Transfer node**, because the guarantees that separated them no longer hold across it.

**(b) A taxonomy of CLA variants**, each demonstrated with concrete code, primarily in Rust (with Go samples in Appendix A) — organised by which exploitation stage the language mismatch reopens:

- **Rust bounds-check bypass** — Rust's spatial safety guarantees "may silently fail" when a pointer crosses FFI: C/C++ corrupts a function pointer that Rust later calls, having never violated a Rust-side check.
- **Rust lifetime bypass** — the ownership model assumes it alone controls deallocation.
- **Double free / use-after-free via FFI** — nothing prevents a double free that originates on the C side; once FFI is involved, "responsibility for memory management returns to the programmer, reintroducing such errors," and Rust "can no longer claim temporal memory safety if it successfully compiles."
- **Return-address corruption** — because Rust is memory-safe it does **not** deploy a shadow stack, so C/C++ can corrupt the return address of a previously-called Rust function and it will **never be checked** (their Fig. 5).
- **Intended FFI interactions** — data the two sides *mean* to share also goes wrong: passing bad values; function pointers crossing the boundary (the Rust compiler does warn, and a `transmute` inside an `unsafe` block is required, but the authors argue this is routinely overlooked); and **serialization errors** from representation mismatches (C null-terminated strings vs. Rust strings) — noting that serialization is a known bug source but had been studied for *inter*-application I/O (network, files, IPC), **not intra-application language boundaries**.
- **Concurrency** — in a multi-threaded program, a C/C++ function with an arbitrary write on one thread can attack a Rust function on another, which **removes the ordering constraints** that the sequential attacks need. CLA is therefore "more general than just FFI issues."

**(c) Automated analysis of Firefox** to quantify how often the structural preconditions occur in a large, real, representative codebase.

> **(KO)** 방법론에서 훔쳐올 것은 **"Language Transfer node"**라는 모델링 장치다. 두 위협모델을 합칠 때 경계 노드를 하나 두고 **양쪽의 모든 노드를 그 노드에 연결**해버리는 보수적 합성 방식인데, Electron에 옮기면 **IPC 채널 / preload `contextBridge` / N-API 호출**이 각각 Transfer node가 된다. 학위논문에서 렌더러·메인·네이티브 3계층 위협모델을 합칠 때 그대로 쓸 수 있는 형식.

## 3. Experiments / Evaluation Setup

The quantitative component is a **binary-level static analysis of Firefox**, chosen as "representative of large, commonly-used code bases." Measured per language (Rust vs. C/C++) and for the whole binary:

- total **functions**
- total **call sites**
- **transfer points** — call sites that cross the language boundary
- **indirect calls** and **dynamic calls**

Each cell is reported as a pair (X%, Y%) where X is the fraction within that language and Y is the fraction of the whole-binary total that comes from that language.

Code samples and the analysis are released online. Go equivalents of the Rust examples are in Appendix A.

> **(KO)** 평가 설계가 단순하지만 설득력이 있는 이유: "CLA가 이론적으로 가능하다"에서 멈추지 않고 **실제 대형 애플리케이션에 언어 경계가 몇 개나 있는지**를 세어서 공격면의 절대 크기를 보여준다. Electron 앱 코퍼스를 대상으로 `.node` 애드온 개수·N-API 호출 지점 수를 같은 방식으로 세는 실험은 학위논문 측정 챕터의 좋은 후보다.

## 4. Results / Key Findings

**Firefox is overwhelmingly still C/C++, and the boundary between the two is large in absolute terms.**

| | Rust | C/C++ | Entire binary |
|---|---|---|---|
| **Functions** | 487,763 (100%, **26.68%**) | 1,340,347 (100%, **73.32%**) | 1,828,110 |
| **Call sites** | 327,653 (100%, **9.23%**) | 3,220,415 (100%, **90.77%**) | 3,548,068 |
| **Transfer points** | 12,118 (**3.70%**, 5.32%) | 215,778 (**6.70%**, 94.68%) | **227,896** (6.42%) |
| **Indirect calls** | 179,598 (**54.81%**, 64.04%) | 100,843 (3.13%, 35.96%) | 280,441 (7.90%) |

Reading the rows: Rust supplies **26.68% of functions but only 9.23% of call sites**. **6.42% of all call sites in the binary — 227,896 of them — are language transfer points**, of which 12,118 originate in Rust (3.70% of Rust's own call sites). And the striking asymmetry: **54.81% of Rust's call sites are indirect**, versus 3.13% on the C/C++ side, so Rust contributes **64.04%** of the binary's indirect calls despite being the minority language — indirect calls being exactly the control-flow targets a hijack wants, and exactly what Rust's memory safety (rather than a shadow stack or CFI) is presumed to protect.

**Qualitative findings, per attack variant.** The authors present a summary table of which mechanism each variant defeats (corrupt dynamic bound; double free; intended FFI interactions; concurrency safety), and establish three general points beyond the individual samples: (1) memory-management responsibility silently reverts to the programmer at the FFI boundary, voiding Rust's temporal-safety claim for the whole program; (2) **intra-application serialization across a language boundary is an unstudied bug class** — prior serialization work assumed inter-application I/O; (3) multi-threading **generalises** CLA beyond FFI call sequencing, because a cross-thread arbitrary write needs no ordering relationship with the victim at all.

They also note, for balance, that Go's garbage collector costs roughly **~25% CPU utilization** depending on workload and makes its runtime substantially more complex than Rust's — relevant to which safe language a gradual deployment picks.

> **(KO)** 학위논문에서 인용 가치가 가장 높은 숫자는 **"Rust 호출 지점의 54.81%가 간접 호출이고, 바이너리 전체 간접 호출의 64.04%를 Rust가 만든다"**이다. 안전 언어를 도입하면 오히려 제어흐름 탈취의 표적이 되는 간접 호출이 늘어난다는, 직관에 반하는 결과라 서론에서 강한 문장을 만든다. **227,896개 전이 지점(전체 호출 지점의 6.42%)**은 "언어 경계는 예외적 사건이 아니라 구조적 상수"라는 주장의 근거.

## 5. How to cite in Related Work

> The security consequences of mixing a memory-safe language with an unsafe one are not additive. Mergendahl et al. show that language safety checks and unsafe-language exploit mitigations interrupt *different stages* of an exploit, so that composing them creates mutually incompatible assumptions at the boundary: an attacker who alternates between the two languages can complete a control-flow hijack that neither language would permit alone [NDSS '22]. Their examples include C/C++ corrupting a function pointer that Rust subsequently invokes without violating any Rust-side bounds check, and corruption of the return address of a Rust function — unchecked precisely because Rust, being memory-safe, deploys no shadow stack. An automated analysis of Firefox quantifies how routine these conditions are: 227,896 of 3,548,068 call sites (6.42%) are language transfer points, and although Rust accounts for only 9.23% of call sites, 54.81% of them are indirect, contributing 64.04% of the entire binary's indirect calls. The authors conclude that gradual deployment of safe languages, performed without extreme care, can be detrimental to security.

> **(KO) 학위논문에서의 포지셔닝:** 이 논문은 **Electron을 전혀 다루지 않지만, 이 저장소의 네이티브 경계 계보 전체가 서 있는 이론적 토대**다. 인용 위치는 세 곳이다. (1) **JS↔C/C++ 축의 도입부**: Bilingual Problems(USENIX Sec '23, 발견)·BinWrap(AsiaCCS '23, 방어)·NatiSand(RAID '23, 방어)는 모두 "네이티브 경계가 위험하다"를 전제로 삼는데, **왜 위험한지의 일반 이론**을 준 것이 이 논문이다. 셋보다 먼저 인용하면 문단 구조가 깔끔해진다. (2) **Mir(CCS '21)의 배제 조항과 짝짓기**: Mir은 네이티브 라이브러리를 위협모델에서 빼면서 그 이유로 "메모리 안전성에 의존하는 런타임 보호를 우회할 수 있다"고 적었다 — CLA는 그 문장이 왜 옳은지를 메커니즘 수준에서 증명한다. 두 논문을 연달아 인용하면 "JS 층 방어는 네이티브 층에서 무효화된다"가 두 저자 그룹의 독립적 진술로 성립한다. (3) **남는 갭 — 이것이 핵심**: CLA는 **Rust/Go ↔ C/C++**를 다루지, **JavaScript(V8/GC 런타임) ↔ C/C++**를 다루지 않는다. JS 쪽에는 Rust의 소유권 검사도, 컴파일타임 경계 검사도 없고 대신 **GC와 V8 힙 구조**가 있으므로, 전이 지점의 성격이 다르다(N-API 타입 변환, 핸들 스코프, 콜백 등). 또 측정 대상이 **브라우저 바이너리 하나**이고 **패키징된 Electron 앱은 0개**다. "CLA를 Electron의 `.node` 경계로 이식해 전이 지점을 세고 실제 체인을 구성한다"는 것은 문헌상 비어 있는 자리이며, 학위논문의 기여로 직접 서술 가능하다.

## 6. Caveats / what I could not confirm from the text

- **Neither Electron nor JavaScript/Node.js is the subject.** The safe languages studied are **Rust and Go**; the JS↔native boundary is *not* analysed. Every transfer of this work to Electron in §5 is my extrapolation, explicitly flagged as an open gap rather than a result.
- **§V–§VII were read only in part.** I have the attack taxonomy, the Firefox metric tables, and the general claims, but **not** the full defence discussion (§VII-A, §VII-B on generalising to Go and other language combinations) end-to-end.
- **Table of attack variants vs. defeated mechanisms** renders in the extracted text as rows of quotation marks (`Corrupt Dynamic Bound " " "`, `Double Free " "`, etc.). I can name the rows — corrupt dynamic bound, double free, intended FFI interactions, concurrency safety — but **cannot reliably say which specific mechanism each variant defeats**. Re-read the rendered PDF before citing that table.
- **The Firefox analysis is a static, binary-level count of structural preconditions**, not a demonstration of exploitable bugs in Firefox. The paper does not claim to have exploited Firefox, and this note should not be cited as if it did.
- **"Dynamic calls"** appears as a fourth metric row in the tables; the extracted text cut off before its values, so I have **no numbers** for it.
- **Appendix A (Go code samples)** was not read.
- The paper is from **2022**; Firefox's Rust share has almost certainly changed since, so the 26.68%/73.32% split should be quoted as a 2022 measurement.
