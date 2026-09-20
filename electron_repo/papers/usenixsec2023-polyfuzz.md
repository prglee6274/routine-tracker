# PolyFuzz: Holistic Greybox Fuzzing of Multi-Language Systems

**Authors:** Wen Li, Jinyang Ruan, Guangbei Yi (Washington State University); Long Cheng (Clemson University); Xiapu Luo (The Hong Kong Polytechnic University); Haipeng Cai (Washington State University, corresponding author)
**Venue / Year:** 32nd USENIX Security Symposium (USENIX Security '23), Anaheim CA, 9–11 August 2023 — **Summer cycle**, pp. 1379–1396
**Links:** [USENIX page](https://www.usenix.org/conference/usenixsecurity23/presentation/li-wen) · [PDF (open access)](https://www.usenix.org/system/files/usenixsecurity23-li-wen.pdf) · [Appendix PDF](https://www.usenix.org/system/files/usenixsecurity23-appendix-li-wen.pdf) · ISBN 978-1-939133-37-3 · Artifact Evaluation: Available (Figshare)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** PolyFuzz is the first greybox fuzzer that treats a program written in two languages as **one** fuzzing target with unified cross-language coverage feedback — the exact capability an Electron auditor needs for the JavaScript → native-addon path — and the paper *itself* states that no prior work fuzzes "JavaScript code interfaced with C/C++", leaving precisely that language pair open.

> **한 줄 요약 (KO):** 다중 언어(Python-C, Java-C) 프로그램을 **하나의 대상으로 통합해** 퍼징하는 최초의 그레이박스 퍼저. 언어 경계를 넘는 커버리지 피드백 + 입력·분기조건 관계를 회귀분석으로 학습하는 시드 생성(SASG)이 핵심. 15개 실제 다중언어 시스템에서 단일언어 퍼저 대비 커버리지 25.3~52.3% 향상, 신규 취약점 14개(CVE 5건). **결정적으로 JS↔C/C++ 조합은 구현하지 않았고, 논문 스스로 Favocado조차 "단일 언어 퍼저"라고 규정하며 이 빈칸을 명시**한다.

---

## 1. Problem, Gap & Hypothesis

Multi-language construction (C for speed, Python/Java for programmability) is long-standing, prevalent practice — and it introduces vulnerabilities *beyond* those inside each language unit, arising from **cross-language information flow**. The paper cites prior work demonstrating the criticality of these (CVE-2021-41497, CVE-2021-41500 and six other high-severity CVEs).

The gap is stated sharply. Static cross-language information-flow analysis suffers excessive false positives and is heavily language-specific; dynamic information-flow analysis (PolyCruise, NDroid) fixes the precision problem but is **bounded by the coverage of whatever test inputs happen to exist**. Fuzzing is the standard cure for input scarcity — but existing fuzzers are "exclusively aimed at single-language software and predominantly focused on C/C++". Applying a single-language fuzzer to multilingual code treats every other language unit as a black box in its entirety.

Two challenges follow. **Challenge-1:** greybox fuzzing must exercise flow across heterogeneous language units *without* explicitly analysing the language-interfacing mechanism (which would cost efficiency and extensibility). **Challenge-2:** the space of language combinations is large, so a per-combination fuzzer is infeasible, yet greybox fuzzing inherently needs language-specific internal knowledge.

**Hypothesis:** whole-system coverage feedback plus an explicit, *learned* model of the relationship between input segments and branch predicates will exercise cross-language flow without any interface-specific analysis, and a custom unifying IR can confine the language-specific part to a minimum.

> **(KO)** 이 문제 정의는 Electron 논문에 거의 그대로 이식된다. "renderer의 JS 입력이 preload/IPC를 거쳐 native addon의 C++까지 흐르는데, JS 퍼저는 C++를 블랙박스로, C++ 퍼저는 JS를 블랙박스로 본다"는 문장이 PolyFuzz의 Challenge-1과 동형이다. 또한 "동적 분석은 기존 입력의 커버리지에 갇힌다"는 논거는 왜 순수 정적/동적 분석이 아니라 **입력 생성**이 필요한지를 정당화하는 데 재사용할 수 있다.

## 2. Methodology

PolyFuzz is built on **AFL++** as the core fuzzing agent and has three moving parts:

1. **Holistic coverage measurement and feedback.** Basic-block coverage is measured across *all* language units of the system and fed back to seed scheduling as a single signal, rather than per-unit signals.
2. **Sensitivity-analysis-based seed generation (SASG).** Because multi-language systems suffer acute initial-seed scarcity, PolyFuzz opens with a seed-generation phase that models the semantic relationship between (segments of) the input and branch predicates using **regression** — selected adaptively on the fly from linear, RBF and polynomial models. SASG comprises seed partitioning and sampling, constant expansion, regression modelling, and seed-block assembling. Fuzzing then proceeds conventionally and **adaptively switches back** to seed generation when it stalls.
3. **A custom IR for unified run-time value probing.** Only a minimal language-specific analysis is needed — for holistic coverage measurement and for harvesting the variable values the regression model needs. Everything else is language-agnostic, which is what buys extensibility (Challenge-2).

Implemented for **C, Python, Java and their combinations**.

> **(KO)** 설계상 가장 재사용성 높은 아이디어는 (3)의 "커스텀 IR로 언어별 의존성을 최소 면적에 가둔다"는 전략이다. Electron으로 확장할 때도 V8 측 계측과 native addon(N-API) 측 계측을 각각 얇게 만들고 나머지를 언어 무관하게 두는 동일한 분할이 가능하다. (2)의 SASG는 "초기 시드가 없다"는 Electron IPC 감사의 현실적 난점과 직접 대응한다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

- **Multi-language subjects: 15 real-world systems — 10 Python-C and 5 Java-C** (Table 1, profiled by size in KLOC, branch variables, and branch variables with constant integer constraints).
- **Single-language subjects: 15 real-world benchmarks** randomly selected from Google OSS-Fuzz — **5 each for C, Python and Java** (Table 2).
- **Baselines** (no multi-language fuzzer existed): **Honggfuzz** for C, **Jazzer** for Java, **Atheris** for Python; plus author-built variants **Atheris-C-ext** and **Jazzer-C-ext** that additionally count covered C code; plus **AFL++** on the C benchmarks; plus **PolyFuzz-NSA** (PolyFuzz with SASG disabled) for the ablation.
- **Protocol:** all fuzzers run on the same benchmark with the **same initial inputs**; drivers targeted the same APIs across fuzzers, adapted per fuzzer's input interface. No drivers were written for C APIs because the C units in these projects are all internal libraries. OSS-Fuzz drivers were reused for the single-language fuzzers.
- **Budget:** coverage results averaged over **5 repetitions of 24-hour runs**.
- **Metrics:** #basic blocks covered (primary), #paths as reported by AFL++'s algorithm (reference; third metric for the PolyFuzz vs PolyFuzz-NSA comparison), and #bugs. Crashes were **manually validated** — a PoC was developed for each reported issue, and a crash counted as a new bug only if its call stack differed from all previously confirmed bugs.
- **Research questions:** RQ1 effectiveness on real-world multilingual systems (§5.2); RQ2 effectiveness on single-language programs vs SOTA single-language fuzzers (§5.3); RQ3 importance of SASG (§5.4).

> **(KO)** 방법론적으로 본받을 점: (a) 공정성을 위해 **동일 초기 시드·동일 드라이버 타깃**을 명시했고, (b) 크래시를 자동 집계하지 않고 **PoC로 재현 + 콜스택 기준 중복제거**를 수동 수행했으며, (c) 5회 반복 평균으로 퍼징 실험의 분산을 다뤘다. 세 가지 모두 퍼징 논문 심사에서 반드시 요구되는 항목이므로 본 학위논문 실험 설계의 체크리스트로 삼을 것. 다만 (d) **다중언어 퍼징 벤치마크 자체가 없어서 저자들이 직접 만들어 기여**했다는 점은, Electron 취약점 발굴에서도 동일한 벤치마크 부재 문제가 있음을 시사한다.

## 4. Results / Key Findings — concrete numbers

**Multilingual programs (RQ1).** With a 24-hour budget and identical seeds, PolyFuzz achieved **25.3% higher block coverage and found 1 more bug than Jazzer** (Java-C), and **52.3% higher block coverage and 10 more bugs than Atheris** (Python-C).

**Single-language programs (RQ2).** PolyFuzz still beat the specialists on their own turf: **+11.0% vs Jazzer, +20.1% vs Atheris, +10.1% vs Honggfuzz** in block coverage; and **+7.6% block / +11.4% path coverage vs AFL++**.

**Ablation (RQ3).** SASG is the load-bearing component: PolyFuzz-NSA "ran into a stalemate after running for 12 hours", whereas with SASG the learning continues throughout the campaign and coverage keeps growing (Figure 7, Pillow, averaged over 5×24 h). The paper's own summary: SASG "contributed significantly to PolyFuzz's performance in terms of both coverage and bug triggering".

**Vulnerabilities (Table 10) — 14 new bugs, 5 CVEs:**

| Benchmark | #Bug | Status | PoC | Symptom | #CVE |
|---|---|---|---|---|---|
| Libsmbios | 1 | pending | ✓ | segment fault | 0 |
| Pillow | 1 | fixed | ✓ | out of memory | 1 |
| Ultrajson | 1 | fixed | ✓ | segment fault | 1 |
| Aubio | 1 | pending | ✓ | memory leak | 0 |
| Bottleneck | 7 | pending | ✓ | segment fault | 1 |
| Jansi | 1 | pending | ✓ | out of memory | 1 |
| Pyyaml | 1 | pending | ✓ | recursion error | 0 |
| Javaparser | 1 | confirmed | ✓ | JVM hung | 1 |
| **Total** | **14** | — | | | **5** |

Of the 14, **12 are multilingual vulnerabilities and 2 single-language**; two had been fixed by the time of writing. The worked example (Figure 8) is a NULL-pointer dereference in **Ultrajson**: input read into a Python variable `data` is passed to `ujson.dump`, flows into the C function `SortedDict_iterNext`, and `PyUnicode_AsEncodeString` returns NULL on a specific input, causing a NULL deref — exploitable for DoS.

> **(KO)** 숫자 중 가장 인용가치 높은 것은 **Atheris 대비 +52.3% 커버리지 / +10 버그**다. 이는 "고수준 언어 퍼저를 그대로 쓰면 네이티브 쪽을 못 본다"는 주장의 정량적 근거이며, Electron 맥락에서 "renderer만 퍼징하면 addon 버그를 놓친다"로 번역된다. 반대로 주의할 점은 **신규 취약점 14개 중 7개가 단일 프로젝트(Bottleneck)에 몰려 있다**는 것 — 취약점 수를 기법의 우수성 지표로 쓸 때 조심해야 한다는 반례로도 인용 가능하다.

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Cross-language vulnerability discovery has so far been studied for the Python–C and Java–C boundaries. Li et al. introduced PolyFuzz [USENIX Security '23], the first greybox fuzzer to treat a multi-language system holistically, combining whole-system coverage feedback with a regression-based model of the relationship between input segments and branch predicates; across 10 Python–C and 5 Java–C subjects it achieved 25.3–52.3% higher block coverage than the single-language fuzzers Jazzer and Atheris and uncovered 12 previously unknown multilingual vulnerabilities, with 5 CVEs assigned.
>
> Crucially, PolyFuzz does not cover the JavaScript–C/C++ boundary. The authors explicitly classify Favocado — which targets the binding layer of JavaScript engines — as "a single-language fuzzer, rather than fuzzing JavaScript code interfaced with C/C++", and state that they are "not aware of prior work explicitly addressing holistic fuzzing of multilingual code". An Electron application is precisely such a multilingual system: renderer-side JavaScript reaches C/C++ native addons through preload bridges and IPC, yet no holistic fuzzer exists for that pair.

> **(KO) 위치 설정:** 이 논문은 **동기(motivation)이자 명시적 빈칸(gap)** 으로 쓰는 것이 가장 강력하다. 세 가지 용도가 있다. (1) "다중언어 시스템은 각 언어 단위의 합보다 더 많은 취약점을 갖는다"는 전제를 top-4 논문으로 뒷받침한다. (2) **§8 Related Work에서 저자들이 직접 Favocado를 '단일 언어 퍼저'로 강등시키며 JS↔C/C++ holistic fuzzing이 미해결임을 선언**했다 — 이 문장은 본 학위논문의 gap statement를 남의 입으로 말해주는 최고급 인용이다. 09-20 런의 교훈("저자가 '우리는 이것을 하지 않는다'고 말하는 대목이 형제 논문과 빈칸의 최대 밀집 구간")이 다시 적중한 사례. (3) 방법론 차용: SASG의 회귀 기반 시드 생성은 IPC 채널명·인자 타입을 모르는 상태에서 Electron IPC 표면을 공략할 때 REFLECTA(런타임 리플렉션)와 상보적으로 조합할 수 있다.

## 6. Caveats / what I could not confirm from the text

- **Read in full:** abstract, §1 Introduction (challenges, contributions, headline results), §5.1 evaluation setup and metrics, §5.2 opening of RQ1, §5.4/§5.5 ablation conclusion and vulnerability discussion incl. Table 10 in full, §8 Related Work (multi-language testing, cross-language security analysis). **Not read line-by-line:** §2 background/motivating example, §3–§4 design internals (IR, sensitivity analysis mechanics), §6 discussion, §7 threats to validity, Appendix.
- **Per-subject numbers in Tables 3–9 were not transcribed.** Only the aggregate deltas reported in the abstract and §1 are quoted above. The identity of the 15 multilingual subjects (Table 1) was not extracted beyond the 8 projects that appear in the vulnerability table.
- The split "12 multilingual + 2 single-language" comes from the abstract/§1; Table 10 itself does not label rows as multilingual vs single-language, so I did not attempt to attribute individual rows.
- **No JavaScript/Node.js support.** Confirmed from the text: the implementation covers C, Python, Java. JS appears only in §8 (Gillian's IR was implemented for JavaScript and C; Favocado is discussed and dismissed) and in a bibliography entry for a tree-sitter grammar. I could **not** confirm from the paper whether extending PolyFuzz's IR to V8/Node would be straightforward — the authors claim extensibility but demonstrate it only across C/Python/Java.
- "5 CVEs assigned" is grounded (Table 10 total); I did **not** obtain the individual CVE identifiers — the paper defers per-vulnerability detail to `NewVulnerabilities.pdf` inside the artifact package, which I did not fetch.
