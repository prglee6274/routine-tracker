# IvySyn: Automated Vulnerability Discovery in Deep Learning Frameworks

**Authors:** Neophytos Christou, Di Jin, Vaggelis Atlidakis (Brown University); Baishakhi Ray (Columbia University); Vasileios P. Kemerlis (Brown University)
**Venue / Year:** 32nd USENIX Security Symposium (USENIX Security '23), Anaheim CA, 9–11 August 2023 — **Fall cycle**, pp. 2383–2400
**Links:** [USENIX page](https://www.usenix.org/conference/usenixsecurity23/presentation/christou) · [PDF (open access)](https://www.usenix.org/system/files/usenixsecurity23-christou.pdf) · [Appendix PDF](https://www.usenix.org/system/files/usenixsecurity23-appendix-christou.pdf) · Artifact Evaluation: **Available + Functional + Reproduced**
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** IvySyn fuzzes **native C/C++ code from below** and then automatically **synthesises a high-level (Python) snippet that reaches the same crash through the public API** — the "Proof of Vulnerability" pattern that answers the hardest question in auditing an Electron native addon: *is this memory-safety bug actually reachable from renderer-side JavaScript?*

> **한 줄 요약 (KO):** DL 프레임워크의 네이티브 커널(C/C++)을 **타입 인지 뮤테이션으로 아래에서부터** 퍼징한 뒤, 크래시를 유발한 입력을 고수준 Python API 호출 코드로 **자동 합성(PoV)** 하는 양방향(bottom-up) 프레임워크. TensorFlow·PyTorch 커널 1,159개를 퍼징해 184개에서 크래시, 그중 135개(73%)에 대해 PoV를 3초 이내에 합성. 개발자 확인·수정된 신규 취약점 **61개, CVE 39건**. "네이티브 버그가 관리 언어 API에서 실제로 도달 가능한가"를 기계적으로 증명하는 방법론.

---

## 1. Problem, Gap & Hypothesis

DL frameworks are layered: developer-facing APIs in a managed language (Python) sit on **bindings** that translate arguments, which sit on **kernels** written in memory-unsafe C/C++ for performance and multi-device support (CPU/GPU/TPU). Bugs in kernel code are of special interest because they are memory-safety errors that can corrupt or leak memory or crash the runtime — and in cloud settings (AWS DL Containers, IBM Watson Discovery) "an attacker with access to publicly-available, high-level APIs can send requests with specially-crafted inputs that exploit memory-safety errors in low-level kernel code". The scale of the problem is quantified: **in 2021–2022 alone TensorFlow had more than 280 CVEs assigned** for memory-safety-related vulnerabilities.

The gap is in how prior work approached it: past approaches fuzz **directly on the high-level APIs** and are either *semi-automated*, requiring domain-expert annotations that specify valid argument-value combinations (DocTer), or *not automated at all*, requiring developers to hand-write helper code (Predoo). Fuzzing from the top is hard because the managed-language API surface is vast, weakly specified, and most random inputs die in argument validation before reaching a kernel.

**Hypothesis (the paper's "converse path"):** go **bottom-up**. Native kernel APIs are *statically typed* — that type information is free, machine-readable ground truth that the high-level API does not give you. So (i) fuzz the kernels directly with **type-aware mutation**, which guarantees well-formed calls, and then (ii) **synthesise upward**: map the offending native input back through the bindings into a high-level snippet. The synthesis step is what converts a low-level crash into evidence of an *attacker-reachable* vulnerability. A key enabling property, called out explicitly: kernels are recommended to avoid shared state, each invocation being self-contained, which is what lets IvySyn drop in fuzzing hooks seamlessly.

> **(KO)** 이 논문의 문제 구조는 Electron native addon과 **정확히 동형**이다. renderer JS API ↔ (N-API/NAN 바인딩) ↔ C/C++ addon 구현. "위에서 퍼징하면 인자 검증에 막히고, 아래에서 퍼징하면 도달 가능성을 증명할 수 없다"는 딜레마가 동일하며, IvySyn의 해법(아래에서 퍼징 + 위로 합성)은 그대로 이식 가능한 설계 패턴이다. 다만 **결정적 차이**: DL 커널은 정적 타입 시그니처가 있지만 Node.js N-API addon은 인자를 `napi_value`로 받아 런타임에 풀어내므로 IvySyn이 의존하는 "공짜 타입 정보"가 없다 — 이것이 본 학위논문이 채워야 할 실제 기술적 간극이다.

## 2. Methodology

Two-fold, bottom-up:

1. **Type-aware, mutation-based kernel fuzzing.** IvySyn instruments native kernel implementations to inject fuzzing hooks, then mutates arguments according to their static types. The mutation strategies were compiled from a preliminary study of TensorFlow CVEs and PyTorch bug reports; the taxonomy used in the results is: tensors with random dimension sizes, tensors with extreme values, permutations of original arguments, zero values, lists with extreme values, tensors with empty shape, extreme values in primitive types, empty lists, and deep tensors.
2. **PoV synthesis.** Given a native-level offending input, IvySyn automatically constructs a Python snippet that propagates that input through the corresponding high-level API. The synthesiser relies on the existence of **mappings between high- and low-level APIs** — and the paper notes that "[s]uch mappings are present in any codebase that involves interfacing (safe) managed code with (memory-unsafe) native code."

**Implementation:** ≈1.9 KLOC C/C++ + ≈1.1 KLOC Python + ≈100 LOC shell. Instrumentation uses **Clang v11.0.1** (≈900 LOC): for PyTorch, a Python script driving the Clang Python bindings (≈550 LOC Python); for TensorFlow, a native Clang pass (≈300 LOC C++) plus ≈40 LOC shell. The authors note static binary rewriting (Egalito) or Intel Pin could be supported in future.

> **(KO)** 계측을 **소스 재작성(Clang)** 으로 구현했고 바이너리 재작성은 future work로 남겼다는 점이 중요하다. npm에 배포되는 prebuilt native addon(.node 바이너리)은 소스가 없는 경우가 많으므로, Electron 맥락으로 옮기려면 저자들이 미룬 바로 그 경로(Egalito/Pin류 바이너리 재작성)를 먼저 풀어야 한다. 이는 본 학위논문의 **차별화 포인트로 삼기 좋은 지점**이다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

- **Targets:** TensorFlow and PyTorch, latest production versions.
- **Scale:** **1,159 kernels** fuzzed in total across all experiments (TensorFlow 412, PyTorch 747), with CPU or GPU implementations or both.
- **Efficiency comparison — vs Atheris** (Google's coverage-guided Python fuzzer, used by Google itself on TensorFlow). Because Atheris is not fully automated, the authors used IvySyn to *generate* Atheris drivers and built two variants:
  - **Atheris+** — drivers invoke Python APIs with the correct *number* of arguments, but Atheris picks types from its defaults (no type awareness).
  - **Atheris++** — drivers with type awareness; explicitly **not** an off-the-shelf configuration, it is Atheris enhanced with automation and type awareness *by the authors*.
  Run on **308 TensorFlow kernels** and **283 PyTorch kernels**, measured as crashes uncovered over time. Effectiveness at PoV synthesis was **not** compared against Atheris, because Atheris has no such functionality.
- **Effectiveness comparison — vs DocTer** (annotation-based). DocTer was modified to target the subset of **125 TensorFlow and 105 PyTorch kernels** that were both fuzzed by IvySyn and had directly reusable DocTer annotations (same type signature in the latest API). Compared over **10 runs** each, reporting median and union of successfully synthesised PoVs plus average total running time. Efficiency was not compared against DocTer for reasons given in §7.1.
- **Metrics:** unique crashes found and time-to-find; PoVs successfully synthesised (and synthesis latency); ultimately, developer-confirmed vulnerabilities and CVEs.

> **(KO)** 베이스라인 설계가 매우 공정하다는 점을 배울 것: 저자들이 **경쟁 도구를 자기 손으로 강화(Atheris++)** 한 뒤 그래도 자기 기법이 이긴다고 보고했고, 이길 수 없는 축(PoV 합성)에서는 **비교 자체를 하지 않는다고 명시**했다. 또 DocTer 비교에서는 주석이 재사용 가능한 부분집합으로 범위를 좁혀 비교의 타당성을 확보했다. 학위논문 평가 설계에서 그대로 따라야 할 규범.

## 4. Results / Key Findings — concrete numbers

**Headline:** IvySyn helped TensorFlow and PyTorch developers **identify and fix 61 previously-unknown security vulnerabilities**, with **39 unique CVEs** assigned.

**Crashes vs Atheris (Table 1 — aggregate of 5 iterations per fuzzer per framework, over 308 TensorFlow and 283 PyTorch kernels):**

| Fuzzer | TensorFlow | PyTorch |
|---|---|---|
| Atheris+ | 47 | 9 |
| Atheris++ | 64 | 18 |
| **IvySyn** | **80** | **25** |
| Union All | 87 | 30 |

Time-to-find: on TensorFlow, IvySyn found a **median of 71 crashes in under 10 hours**, whereas Atheris+ and Atheris++ found medians of **5 and 8** respectively — and Atheris++ needed **≈85 hours vs IvySyn's ≈9 hours** to complete. On PyTorch, IvySyn found a **median of 23 crashes in under 18 hours** against a median of **3 crashes** for both Atheris variants in the same window, and took **more than 5× less total time** (**≈81 hours for Atheris++ vs ≈16 hours for IvySyn**).

**Overlap analysis:** the union of crashes found by all fuzzers in the 308 TensorFlow kernels was **87**; since IvySyn alone found 80, only **7** were found by Atheris and not IvySyn — 4 of them triggered by Atheris+ passing *incorrect* argument types (which IvySyn and Atheris++ never do by construction), and the remaining 3 by Atheris++ generating value combinations absent from IvySyn's mutation pools. In PyTorch the union was 30 against IvySyn's 25, so **5** crashes were found by Atheris but not IvySyn — all by Atheris++, again from value combinations outside IvySyn's mutation pools.

The authors are candid that **Atheris++ is not an off-the-shelf tool** but "a customized, strong baseline that borrows type information from IvySyn", and was therefore *expected* to come close on total crashes.

**PoV synthesis (Table 2):**

| Framework | Fuzzed kernels | Unique crashes | Synthesised PoVs |
|---|---|---|---|
| TensorFlow | 412 | 103 | 86 / 103 (83%) |
| PyTorch | 747 | 81 | 49 / 81 (60%) |
| **All** | **1159** | **184** | **135 / 184 (73%)** |

Synthesis took **less than three seconds**. The failures are instructive: in TensorFlow, of 17 failures — 2 kernels deprecated at the Python level, **6 not directly exposed to Python**, 5 needing complex list arguments the synthesiser could not infer, 4 not reproducible with the PyPI pre-built binaries. In PyTorch, of 32 failures — **31 had no Python binding at all**, 1 needed complex inputs.

**Mutation breakdown (Table 3), 135 PoVs by crash type:** SIGSEGV 26 (TF) + 33 (PT), SIGABRT 56 (TF) + 0 (PT), SIGFPE 4 (TF) + 16 (PT). The single most productive strategy was *tensors with random dimension sizes* (46 PoVs), followed by *tensors with extreme values* (25) and *permutations of original arguments* (19). The **39 CVEs** distribute as 21 / 8 / 7 / 3 across those four mutation types, and **17 SIGSEGV / 22 SIGABRT** by crash type.

**vs DocTer:** TensorFlow — median **15 PoVs (union 19) for IvySyn vs 12 (union 16) for DocTer**, average runtime 186 min (σ 5) vs 197 min (σ 6). PyTorch — median **11 PoVs (union 14) vs 7 (union 9)**, average runtime **560 min (σ 20) vs 738 min (σ 14)**. IvySyn wins on both effectiveness and time, without requiring annotations.

> **(KO)** 본 학위논문에 가장 유용한 숫자는 Table 2의 **"크래시 184개 → PoV 135개(73%)"** 와 그 실패 원인 분해다. PyTorch 실패 32건 중 **31건이 "Python 바인딩이 아예 없음"** 이라는 사실은, 네이티브 코드의 상당 부분이 고수준 API에서 도달 불가능하다는 뜻 — 즉 **네이티브 크래시 개수를 취약점 개수로 보고하는 관행에 대한 직접적 반증**이다. Electron addon 감사에서도 "addon 내부 크래시"와 "renderer에서 도달 가능한 취약점"을 반드시 구분해야 한다는 논거로 인용할 것.

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> A recurring difficulty in auditing the boundary between a managed language and native code is establishing *reachability*: a memory-safety fault found by fuzzing native code is only a vulnerability if an attacker can steer the high-level API into it. Christou et al. address this with IvySyn [USENIX Security '23], which exploits the statically-typed nature of native kernel APIs in TensorFlow and PyTorch to perform type-aware mutation fuzzing from below, and then automatically synthesises a Python snippet — a "Proof of Vulnerability" — that reproduces the fault through the public API. Across 1,159 kernels IvySyn found crashes in 184 and synthesised PoVs for 135 of them (73%) in under three seconds each, leading to 61 fixed vulnerabilities and 39 CVEs.
>
> IvySyn's authors note that its synthesis step "assumes the existence of mappings between high- and low-level APIs", which are "present in any codebase that involves interfacing (safe) managed code with (memory-unsafe) native code", and state that although they applied it only to DL frameworks they "anticipate [the] approach to generalize to other, non-DL codebases". Node.js native add-ons — and therefore Electron applications that bundle them — are exactly such a codebase, but they differ in a way that matters: N-API add-ons receive opaque `napi_value` arguments and recover types at run time, so the free static type information IvySyn depends on is absent.

> **(KO) 위치 설정:** 세 가지 역할. (1) **방법론적 조상** — "아래에서 퍼징 + 위로 PoV 합성"이라는 2단 구조 자체를 본 논문이 차용하며, 그 유효성을 top-4 실적(CVE 39건)으로 뒷받침한다. (2) **명시적 확장 초대** — 저자들이 §5에서 "비-DL 코드베이스로 일반화될 것으로 예상한다"고 직접 써 두었으므로, 본 학위논문은 그 초대를 수행하는 작업으로 자리매김할 수 있다(09-20의 "저자가 하지 않겠다고 말한 부분" 규칙의 긍정형 사례). (3) **기술적 차별점 확보** — IvySyn은 정적 타입 시그니처와 소스 재작성(Clang)에 의존하는데 N-API addon은 둘 다 없거나 약하다. 따라서 "타입 정보 없는 바인딩 층에서 어떻게 타입 인지 뮤테이션을 할 것인가"가 본 논문의 고유 기여가 된다. 이 대목에서 REFLECTA(AsiaCCS'25, 런타임 리플렉션으로 타입 복원)와 IvySyn을 **결합**하는 그림이 자연스럽다.
>
> **저자망 메모 (KO):** Vasileios P. Kemerlis(Brown)는 ledger에 이미 in_scope로 있는 **BinWrap**(AsiaCCS'23, Native Node.js Add-ons)의 공저자이고, BinWrap의 제1저자 George Christou와 본 논문 제1저자 Neophytos Christou는 같은 연구망에 있다. 즉 Brown/FORTH 계열이 **"Node.js 네이티브 애드온 방어(BinWrap)"와 "네이티브 바인딩 취약점 발굴(IvySyn)"을 양쪽에서** 하고 있다 — 다음 author-page 마이닝 1순위.

## 6. Caveats / what I could not confirm from the text

- **Read in full:** abstract, §1 Introduction, §2 opening (DL framework architecture: kernels / bindings / high-level APIs), §5 end (limitations + generalisation claim), §6 Prototype Implementation, §7.2–§7.3 evaluation including Tables 1–3 and the IvySyn-vs-DocTer comparison. **Not read line-by-line:** §3–§4 (threat model and design internals), §5 body, §7.1 setup prose beyond the baseline descriptions, §8 Related Work, §9 Conclusion, Appendix.
- **An internal inconsistency in the paper's own PyTorch kernel counts, worth knowing before citing.** Table 1's caption says the experiment covered "308 TensorFlow and 283 PyTorch kernels", but the §7.2 prose says "IvySyn found 25 crashes in **287** kernels" and "the union of all crashes found in the **387** PyTorch kernels was 30". The three figures (283 / 287 / 387) cannot all be right; the crash counts themselves (9 / 18 / 25 / union 30) are consistent between table and prose. **Cite the crash counts, and cite 283 as the PyTorch kernel count (the table caption), noting the discrepancy** — or re-check against the published version. I did not resolve which is correct.
- I did **not** confirm the hardware/OS configuration of the fuzzing experiments, nor the per-run time budget for the Atheris comparison beyond the "to complete" figures quoted.
- The **61 vulnerabilities / 39 CVEs** figures are grounded (abstract, §1, §7.3) but I did **not** extract the individual CVE identifiers, nor verify how the 61 fixed vulnerabilities relate numerically to the 135 synthesised PoVs — the paper does not make that mapping explicit in the sections I read.
- The claim that N-API add-ons lack static type signatures is **my own** assessment based on the Node.js binding model, **not** something IvySyn states. The paper says nothing about JavaScript, Node.js or Electron anywhere in the sections read.
