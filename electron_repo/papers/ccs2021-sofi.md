# SoFi: Reflection-Augmented Fuzzing for JavaScript Engines

> ⚠️ **GROUNDING WARNING — READ FIRST.** The full text of this paper was **NOT** reachable in this run. ACM DL is paywalled; the SMU InK institutional copy (`ink.library.smu.edu.sg/.../3460120.3484823.pdf`) fetched as an **empty body**. Everything below is written from (a) the paper's published abstract/summary as indexed by ACM and Semantic Scholar and (b) two reachable secondary sources: REFLECTA (AsiaCCS'25), which positions itself against SoFi in its Table 1 and §6.1, and *SoK: Prudent Evaluation Practices for Fuzzing* (IEEE S&P 2024), which re-examined SoFi's reported bugs. **No number below is taken from SoFi's own evaluation tables, because those were not readable.** Do not quote a figure from this note in the thesis without first obtaining the PDF.

**Authors:** Xiaoyu He, Xiaofei Xie, Yuekang Li, Jianwen Sun, et al. (Singapore Management University / Nanyang Technological University and collaborators)
**Venue / Year:** ACM CCS 2021 (SIGSAC Conference on Computer and Communications Security)
**Links:** [ACM DOI 10.1145/3460120.3484823](https://doi.org/10.1145/3460120.3484823) · [Semantic Scholar record](https://www.semanticscholar.org/paper/b421a16d45e9d4ae05b3122e0171b68410f85b0d) · PDF: paywalled, no open copy found
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** SoFi is the paper that introduced *reflection-based discovery of an object's unseen attributes and methods* as a fuzzing primitive for JavaScript — the mechanism a thesis needs to enumerate an Electron preload bridge whose API is defined by the application and documented nowhere.

> **한 줄 요약 (KO):** JS 엔진 퍼징에서 **리플렉션으로 객체의 미지의 속성·메서드를 발견**해 변이에 사용하고, 문법·의미 오류가 난 테스트 케이스를 **자동 복구**하는 기법. REFLECTA(AsiaCCS'25)의 직계 조상이며 "명세 없이 API 표면을 찾는다"는 문제 설정의 출발점. 단, 보고된 버그의 유효성에 대해 후속 SoK가 심각한 반박을 제기했으므로 **결과가 아니라 기법을 인용**해야 한다.

---

## 1. Problem, Gap & Hypothesis

The stated gap, per the abstract: semantic-aware JavaScript fuzzers of the day relied on **manually written rules** to reason about semantics, which is labour-intensive, incomplete and engine-specific; and such fuzzers **cannot generate method calls that are absent from the initial seed corpus or the pre-defined rules**. That second clause is the important one for this thesis — it names *under-specification of the callable surface*, not weak search, as the binding constraint on bug discovery.

Hypothesis: a fine-grained program analysis can identify the variables available at each program point and infer their types for mutation, and *reflection* can go further and surface attributes and methods the fuzzer had never seen, so that the fuzzer becomes engine-general with no manual configuration.

> **(KO)** 문제 설정이 이 논문의 진짜 기여다. "수동 규칙은 불완전하고 엔진 종속적이며, 시드 코퍼스에 없는 메서드는 절대 호출되지 않는다." — Electron 앱의 `ipcMain` 핸들러 이름 집합이 정확히 이 상황에 놓여 있다.

## 2. Methodology

Three ingredients, as described in the abstract:

1. **Fine-grained program analysis** to identify the variables available for mutation at a given point and to infer their types.
2. **Automatic repair** of syntactically/semantically invalid test cases, rather than discarding them — so a mutation that breaks type correctness is fixed instead of wasted.
3. **Reflection-based analysis** to identify *unseen* attributes and methods of objects, which are then fed back into mutation.

The claimed consequence is generality: SoFi works across different JavaScript engines "without any manual configuration (e.g., the grammar rules)".

> **(KO)** ① 변수·타입 추론 ② 무효 테스트케이스 자동 복구 ③ 리플렉션 기반 미지 API 발견. ②의 "버리지 말고 고친다"는 아이디어는 Electron IPC 퍼징에서도 그대로 유효하다 — 채널 인자 스키마를 틀리면 핸들러가 즉시 반환해 버리므로, 폐기 대신 복구가 처리량을 지배한다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**NOT RECOVERABLE FROM THE SOURCES AVAILABLE THIS RUN.** What is known:

- Targets were modern JavaScript engines; the secondary source (S&P'24 SoK) names **V8, SpiderMonkey and JavaScriptCore** as the engines in which SoFi claimed vulnerabilities.
- The abstract states SoFi was compared against state-of-the-art techniques on (i) proportion of semantically valid inputs generated, (ii) code coverage, (iii) number of bugs detected.
- Campaign lengths, repetition counts, hardware, statistical treatment and the baseline set: **unknown, not read.**
- Reproducibility, from REFLECTA §6.1: SoFi **was not released as open source**, so REFLECTA could not compare against it and cites prior work reporting the same unavailability.

> **(KO)** 평가 설정을 확인하지 못했다. 특히 반복 횟수·신뢰구간 같은 퍼징 평가 관행 항목을 확인할 수 없었고, 6절의 후속 SoK 지적과 합쳐 보면 이 부분을 직접 읽기 전에는 어떤 수치도 쓰면 안 된다.

## 4. Results / Key Findings — concrete numbers

**No numbers are available to me.** The abstract-level claims are that SoFi outperforms the state of the art on semantic validity, code coverage and bug count. Two grounded facts *about* those results come from secondary sources:

- **Disputed bug claims.** *SoK: Prudent Evaluation Practices for Fuzzing* (Schloegel et al., IEEE S&P 2024) reports that **all seven vulnerabilities SoFi claimed in actively used modern browser engines (V8, SpiderMonkey, JavaScriptCore) were invalid and rejected by the respective engine developers — six of the seven before the conference submission deadline.** This is a peer-reviewed secondary finding, not a rumour, and it is the single most important thing to know before citing SoFi's results.
- **Unavailability.** REFLECTA (AsiaCCS'25) lists SoFi in its Table 1 as one of five state-of-the-art scripting-language fuzzers, marking it semantic-aware but requiring an initial corpus and single-language, and records that it could not be evaluated against because there is no open-source release.

> **(KO)** 결과 섹션은 사실상 비어 있다. 대신 확실한 것은 두 가지: **(a) 주장된 7개 취약점이 모두 무효 판정을 받았다는 S&P'24 SoK의 지적, (b) 오픈소스 미공개로 후속 연구가 비교조차 못 했다는 사실.** 논문의 *기법*은 인용 가치가 높지만 *실적 수치*는 인용하면 안 된다.

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> The idea of letting the target itself declare its callable surface originates with SoFi (He et al., CCS 2021), which combined variable/type inference, automatic repair of invalid test cases, and a reflection-based analysis that surfaces attributes and methods absent from the seed corpus and from any hand-written rule. Its framing of the problem — that a semantic-aware fuzzer relying on manual rules is "labor-intensive, incomplete and engine-specific", and structurally unable to call a method it was never told about — transfers directly to the Electron setting, where the privileged surface reachable from a renderer is defined per application rather than by a specification.
> REFLECTA (AsiaCCS 2025) later generalised the same primitive across four languages and six engines while removing the seed-corpus requirement.
> SoFi's reported findings should, however, be cited with care: a subsequent systematisation of fuzzing evaluation practice (Schloegel et al., IEEE S&P 2024) found that all seven vulnerabilities SoFi claimed in V8, SpiderMonkey and JavaScriptCore were rejected as invalid by the engine developers, and the tool was never released, so no independent comparison exists.

**(KO) 위치 잡기 — 취약점 *발견* 논문 대비:** ① **계보 인용**으로 쓰는 것이 가장 안전하다: SoFi(CCS'21) → COOPER(NDSS'22) → REFLECTA(AsiaCCS'25)로 이어지는 "명세 없는 표면의 자동 발견" 계보의 출발점. ② **반례/경고 사례**로도 쓸 수 있다 — 퍼징 논문의 버그 개수 주장이 어떻게 검증 없이 통과될 수 있는지에 대한 S&P'24의 지적과 묶어서, 본 논문의 평가 설계(개수보다 재현 가능한 오라클 우선)를 정당화하는 데 쓰라. ③ 남긴 공백: SoFi는 **엔진 내장 객체**에 리플렉션을 걸었을 뿐, 호스트가 주입한 객체에는 걸지 않았다.

## 6. Caveats / what I could not confirm from the text

- **The entire paper body is unread.** ACM paywall; the SMU InK mirror returned an empty response. Sections 1–7, all tables, all figures, the threat model, the baseline set, the campaign configuration and the bug table are **unverified**.
- **The author list above is partial and may be imprecise.** Search results consistently give "He, Xie" as the leading pair and name Xiaoyu He, Xiaofei Xie, Yuekang Li and Jianwen Sun; the full author list and affiliations were not confirmed from the paper itself. Verify before citing.
- I could not confirm from SoFi's own text whether its reflection step runs *inside* the target engine (as REFLECTA's does) or is reconstructed externally — an important distinction if the technique is to be transplanted to an Electron renderer.
- The S&P'24 SoK finding is reported here **as summarised in search results**, not read from the SoK PDF itself. It is on the ledger as an exclusion (`IEEE S&P 2024`) and should be read directly before the claim is repeated in the thesis.
- Scope note: admitted as ADJACENT on the same ground as Favocado and COOPER — it contributes a *discovery technique for an unspecified API surface*, not a property of an engine. This is the line that keeps Fuzzilli (NDSS'23), Montage (USENIX'20) and "Fuzzing JavaScript Engines with a Graph-based IR" (CCS'24) excluded: those target engine internals and the JIT pipeline, where no host application sits on the other side of the surface.
