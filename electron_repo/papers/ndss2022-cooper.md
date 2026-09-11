# COOPER: Testing the Binding Code of Scripting Languages with Cooperative Mutation

**Authors:** Peng Xu (TCA/SKLCS, Institute of Software, Chinese Academy of Sciences; University of Chinese Academy of Sciences), Yanhao Wang (QI-ANXIN Technology Research Institute), Hong Hu (Pennsylvania State University), Purui Su (TCA/SKLCS, ISCAS; School of Cyber Security, UCAS)
**Venue / Year:** Network and Distributed Systems Security Symposium (NDSS) 2022, 24–28 April 2022, San Diego, CA · ISBN 1-891562-74-6
**Links:** [PDF](https://www.ndss-symposium.org/wp-content/uploads/2022-353-paper.pdf) · [DOI 10.14722/ndss.2022.24353](https://dx.doi.org/10.14722/ndss.2022.24353)
**Scope tag:** PRIMARY

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** COOPER's central finding — that the binding layer of a scripting-language-embedding desktop application takes input from **two dimensions** (the script *and* the host's native document/state), so mutating the script alone misses most bugs — transfers directly to Electron, where the renderer's JavaScript is only one input and the app's own loaded content, window/session state and IPC message payloads are the other.

> **한 줄 요약 (KO):** Favocado(NDSS'21)가 스크립트 한 축만 변이해 바인딩 코드를 퍼징한 데 반해, COOPER는 **네이티브 입력(PDF/DOCX 파일 자체)과 스크립트 코드를 동시에(cooperative) 변이**한다. 네이티브 객체를 의미적 유사 클래스로 군집화하고, 대량 실행 통계로 "어떤 객체 클래스가 어떤 스크립트 API와 관련 있는지"를 추론한 뒤 그 관계를 따라 표적 변이. Adobe Acrobat·Foxit Reader·Microsoft Word에서 신규 버그 **134개**(수정 59, CVE 33, 버그바운티 총 $22K). 스크립트만 변이할 때보다 Acrobat 1.5배·Foxit 1.8배 더 많은 고유 버그.

## 1. Problem, Gap & Hypothesis

Commercial desktop software embeds scripting languages to let documents drive the application: Adobe Acrobat accepts JavaScript inside PDFs, IDA Pro exposes a Python binding, Microsoft Word exposes an object model to scripts. The binding layer between the high-level script and the C/C++ host "is prone to produce inconsistent representations or miss security checks."

**The gap the paper names explicitly:** every prior approach tests **one dimension only**. Static checkers (the authors cite Brown et al.'s set of per-bug-class checkers) do not scale, produce false alarms, and yield no triggering input. Dynamic specification checkers only report what the supplied input happens to reach. And the state-of-the-art fuzzer — **Favocado** — "merely modifies JavaScript statements in order to trigger bugs in the binding layer." But the binding layer sits between two input channels, and *"one cannot completely replace another"*: the paper's motivating example is that features such as **font** in Acrobat are only reachable from the native PDF input, so no amount of JavaScript mutation will ever exercise the binding code that handles them.

**Hypothesis:** many binding bugs arise from the **interplay between the program's initial state (set by the native input) and the dynamic operations (issued by the script)**, and can therefore only be triggered by two-dimensional mutation. Naïvely mutating both dimensions at random fails, because the native input contains many objects irrelevant to the binding layer and the script only accepts particular program states — so the mutation must be *guided by an inferred relationship* between native object classes and script APIs.

*(KO) 이 논문이 본 논문(thesis)에 주는 가장 큰 프레이밍: **"바인딩 취약점 = 초기 상태 × 동적 연산"**. Electron으로 옮기면 초기 상태 = 로드된 웹 콘텐츠·앱 설정(`webPreferences`)·세션/쿠키·열려 있는 창 구조, 동적 연산 = 렌더러가 보내는 IPC 메시지와 `contextBridge` API 호출. 한쪽만 흔드는 기존 Electron 감사 도구(예: 정적 설정 검사)는 구조적으로 이 교차항을 못 본다는 주장이 이 논문으로 정당화된다.*

## 2. Methodology

**Cooperative mutation**, built from three techniques:

1. **Object clustering.** The native input (a PDF, a DOCX) contains a huge number of objects; COOPER clusters them into *semantically similar classes* to shrink the native-side mutation space. (The paper's Table IV shows a worked example: class ID **449**, containing **335,482** objects, whose high-frequency attributes the authors then match against the PDF specification.)
2. **Statistical relation inference.** Rather than reasoning about the binding source, COOPER runs a large number of executions and *statistically infers* which object classes are related to which script APIs — comparing attribute frequencies across executions where a given API succeeded versus failed. (Table VI reports the inference details; for annotation APIs in Acrobat the most relevant class is the one carrying the `/AP` attribute, and the validation in §on Page objects confirms the inferred high-frequency attributes match the 30 entries the PDF format defines for a Page object, including the required `MediaBox`.)
3. **Targeted cooperative mutation.** Use the inferred relation to pick a native object *and* the script code that manipulates the state that object produces, so mutation energy is spent on inputs that actually reach binding code.

**Validation of the inference step is a notable methodological move:** the authors do not just assert that clustering works — they take a large class, inspect its high-frequency attributes, and check them against the PDF specification's definition of a `Page` object. That is a cheap, reusable way to show an unsupervised step is doing something real.

*(KO) 방법론 교훈 두 가지: (i) 바인딩 코드의 소스가 없어도(Acrobat·Word는 closed-source) **실행 통계만으로** 네이티브 객체↔스크립트 API 관계를 복원할 수 있다 — Electron 앱도 대부분 소스가 없는 배포 번들이므로 그대로 적용 가능한 전략. (ii) 비지도 추론 단계의 타당성을 **명세 문서와 대조**해 검증하는 서술 패턴은 본 논문에서도 그대로 쓸 만하다.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**Targets — 3 applications, 2 scripting languages:** Adobe Acrobat (JavaScript in PDF), Foxit Reader (JavaScript in PDF), Microsoft Word.

**Ablation design — five configurations (paper's Table II), each run for one week (7 days = 168 hours)** on Acrobat and Foxit:

| Configuration | What it mutates |
|---|---|
| `full` | COOPER with relationship guidance (both dimensions, guided) |
| `random` | both dimensions, no relationship guidance |
| `object` | native objects only |
| `script` | script code only |
| `Domato` | external baseline (grammar-based, script-side only) |

Crashes were triaged to real, unique bugs; Fig. 9 plots unique bugs over time per configuration, Table VII maps which configuration found which bug ID.

**Microsoft Word was a limited test:** "due to the time limit," only the `Paragraph`, `Table`, `Range` and `Pane` APIs were tested, for one week.

**Coverage measurement:** the authors explicitly argue whole-program coverage is the wrong metric here and measure **binding-code (script) coverage** for Acrobat and Foxit instead.

*(KO) 평가 설계의 강점: 5-way ablation으로 "두 축 변이"와 "관계 유도" 각각의 기여도를 분리해 보여준다. 약점: Word는 4개 API·1주로 사실상 예비 실험이며, Word 버그 18개는 다른 두 타깃과 같은 강도로 평가된 수치가 아님.*

## 4. Results / Key Findings — concrete numbers

**Headline: 134 previously unknown bugs across 3 applications, in 10 bug categories; 40% rated high impact on application security. 59 fixed and 33 assigned CVEs at publication. $22K total bounty for 17 of the reported bugs.** All 134 bugs are triggered through **90 script APIs across 11 object classes**.

Per target:

| Target | New bugs | Breakdown given | CVEs / vendor rating | Bounty |
|---|---|---|---|---|
| **Adobe Acrobat** | **60** | 12 use-after-free, 1 heap buffer overflow, 1 stack buffer overflow | **23** assigned CVEs, **15** marked *critical* (arbitrary code execution) | **$18K** for 7 exploitable vulns |
| **Foxit Reader** | **56** | 18 use-after-free, 1 heap overflow, 7 heap overread | **10** UAFs assigned CVEs, marked *critical* | **$4K** |
| **Microsoft Word** | **18** | 3 use-after-free, 5 heap overread, 8 null-pointer reference, 1 memory error, 1 access violation | reported to Microsoft | — |

**Ablation — the numbers that carry the argument (one week each):**

- `full` (relationship-guided, two-dimensional): **18** unique bugs in Acrobat, **14** in Foxit.
- `random` (two-dimensional, unguided): 12 in Acrobat, 9 in Foxit → **relationship guidance finds 50% more unique bugs in Acrobat and 55.6% more in Foxit.**
- `object` only: 4 in Acrobat, 3 in Foxit → cooperative mutation finds **3.5×** more in Acrobat, **3.7×** more in Foxit.
- `script` only: 8 in Acrobat, 5 in Foxit → cooperative mutation finds **1.5×** more unique bugs in Acrobat and **1.8×** more in Foxit.
- `Domato`: **6** bugs in Acrobat, **6** in Foxit.

The authors' own explanation for the weak `object`-only result: Acrobat's native parsing has already been fuzzed extensively by prior work, and object-only mutation can hardly reach the binding interfaces at all. `full` covered almost all bugs found by every other configuration.

**Case studies.** CVE-2021-21028 (Acrobat DC 2020.012.20048, use-after-free) is the emblematic one: the PoC is a **two-page PDF whose annotation objects carry empty names** (`/NM ()`), plus three lines of JavaScript — `annot.setProps(annot.getProps()); annot.page=1;`. The bug is unreachable by script mutation alone because the *empty name in the native object* is what sets up the vulnerable state. CVE-2021-21035 is a second Acrobat UAF of the same shape. Named CVEs visible in Table III include CVE-2020-9704 (`Doc.exportAsFDFStr`, buffer error, ACE), CVE-2021-28561 (`Doc.zoomType`, heap buffer overflow, ACE), CVE-2021-39849/39850/39851/39852/39853/39854 (null-pointer dereference DoS), CVE-2020-9702/9703 (stack exhaustion DoS), and for Foxit CVE-2021-31441/31451/31456/31457/31458 and CVE-2021-34831/34832/34852/34974/34975 (all use-after-free → arbitrary code execution, via `Annot.destroy`, `Annot.popupOpen`, `Field.richText`, `Annot.readonly`, `Field.delay`, `Annot.delay`, `Annot.trasitionToStat` [sic]).

*(KO) 인용 가치가 가장 높은 수치: **script-only 대비 1.5×/1.8×**. 이것이 "스크립트만 흔드는 퍼징은 바인딩 버그의 상당수를 구조적으로 놓친다"는 정량적 증거이며, Electron 퍼저를 설계할 때 "IPC 메시지만 흔들지 말고 앱 상태도 같이 흔들라"는 설계 근거가 된다. CVE-2021-21028의 "빈 이름 `/NM ()` + 3줄 JS" PoC는 슬라이드에 그대로 넣을 만한 최소 예제.*

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Xu et al. subsequently showed that script-side mutation alone is structurally insufficient for binding-layer testing. Because a scripting-enabled application consumes input along two dimensions — the script and the host's own native document — bugs that depend on the initial state established by the native input are unreachable by script mutation; their COOPER prototype mutates both dimensions cooperatively, guided by a statistically inferred relation between native object classes and script APIs, and found 1.5× (Adobe Acrobat) and 1.8× (Foxit Reader) more unique bugs than script-only mutation in matched one-week campaigns, for a total of 134 previously unknown bugs across Acrobat, Foxit Reader and Microsoft Word, 33 of which received CVEs [COOPER, NDSS'22]. Both Favocado and COOPER nonetheless assume a threat model in which the *document* is the attacker and the host application is a single trust domain to be kept memory-safe. An Electron application inverts this: the script is web content that the application itself renders, the binding layer (`contextBridge`, the preload script, and native add-ons) is the intended *privilege boundary* rather than merely a convenience API, and a logic-level bypass of that boundary is as damaging as a memory-safety bug in it.

*(KO) 포지셔닝: COOPER는 **기법적 직계 조상이자, 본 논문이 채워야 할 gap을 가장 선명하게 규정해 주는 논문**이다. 세 갈래로 쓰면 좋다. (i) 동기: 데스크톱 앱의 바인딩 레이어는 두 축 입력을 받으므로 한 축만 보는 도구는 불완전하다 → 기존 Electron 감사 도구(정적 `webPreferences` 검사류)의 한계를 지적하는 근거. (ii) 남긴 gap 1 — **위협 모델**: Favocado·COOPER 모두 "악성 문서 → 앱 메모리 손상"이지, "웹 콘텐츠 → 로컬 권한 탈취"가 아니다. Electron에서는 바인딩이 곧 권한 경계이므로 메모리 안전성이 아니라 **논리적 경계 우회**가 핵심이고, 이는 두 논문 어느 쪽도 다루지 않는다. (iii) 남긴 gap 2 — **명세 부재**: COOPER는 네이티브 포맷(PDF/OOXML)이 표준 명세를 가진 세계를 전제한다. Electron 앱의 "네이티브 입력"에 해당하는 것(앱 상태, 세션, IPC 채널 집합)은 명세가 없고 앱마다 다르므로, 관계 추론 단계를 어떻게 대체할지가 새 연구 문제가 된다. Favocado(NDSS'21) → COOPER(NDSS'22) → Bilingual Problems(USENIX'23) → Best of Both Worlds(S&P'26) → From Documentation to Zero-day(CCS'26) 계보를 한 문단으로 묶고, 그 문단 끝에 "이 계보 전체가 Electron의 위협 모델을 다룬 적이 없다"로 전환하는 구성이 가장 깔끔하다.*

## 6. Caveats / what I could not confirm from the text

- The full NDSS PDF was fetched, but read **selectively**: §I (introduction/problem/gap) in full, then §V–§VI (evaluation, bug tables, ablation, case studies, coverage) by targeted grep and two focused reads. **§II–§IV — the design and implementation of clustering, inference and mutation — were read only through grepped fragments**, so the algorithmic detail in §2 above is summarised at a coarser level than the evaluation.
- **Code coverage results were not recovered as numbers.** The text confirms the authors measured *binding-code (script) coverage* rather than whole-program coverage for Acrobat and Foxit and plotted it over hours, but the figures themselves did not survive PDF-to-text conversion. Do not cite a coverage percentage.
- Table II (the five configurations) is referenced but its exact per-configuration parameter settings were **not read**; the configuration descriptions above are reconstructed from how §VI describes each run, which is reliable for *what* each config mutates but not for seed counts or machine specs.
- **No hardware/VM specification for the fuzzing campaigns was recovered** — unlike Favocado, which states 8 VMs at 2 cores/4 GB. Do not compare throughput between the two papers.
- The bug totals reconcile exactly (60 + 56 + 18 = 134), which is a good sign, but the "10 categories" and "40% high impact" figures come from the Table III caption rather than from counting rows, and the per-category totals across all three targets were not independently verified.
- Whether COOPER's artifact was released is **not** established from the portions read; no repository URL was seen.
