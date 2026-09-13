# Slimium: Debloating the Chromium Browser with Feature Subsetting

**Authors:** Chenxiong Qian, Hyungjoon Koo, ChangSeok Oh, Taesoo Kim, Wenke Lee (all Georgia Institute of Technology)
**Venue / Year:** 27th ACM SIGSAC Conference on Computer and Communications Security (CCS '20), 9–13 November 2020, Virtual Event, USA — pp. 461–476, 16 pages
**Links:** [paper (ACM DL)](https://dl.acm.org/doi/10.1145/3372297.3417866) · [PDF (author-hosted)](https://kevinkoo001.github.io/assets/pdf/ccs20-slimium.pdf) · [DOI 10.1145/3372297.3417866](https://doi.org/10.1145/3372297.3417866)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Slimium is the Chromium-side counterpart to the Node-side attack-surface-reduction papers already in this ledger (Mininode, HODOR), and — decisively for scope — its own §6.4.1 reliability study *measures two real Electron applications* (Slack 109.4 MB, BlueJeans 111.6 MB of shipped code) and argues that a per-app debloated Chromium at 91.4 MB would beat both, making it the only paper in the ledger that puts a number on how much dead Chromium an Electron app ships.

> **한 줄 요약 (KO):** Chromium(약 110MB, 리눅스 커널보다 큼)에서 "사용되지 않는 기능 코드"를 제거해 공격면을 줄이는 프레임워크. 핵심은 164개 feature를 디블로팅 단위로 정의하고 **relation vector** 기법으로 feature↔object 파일을 매핑한 뒤, 웹페이지 프로파일링 결과에 맞춰 바이너리를 잘라내는 것. 40개 사이트 대상 평균 23.85MB(정의된 feature 코드의 53.1%, 전체의 21.7%) 제거 · CVE 94건(61.4%) 무력화. **§6.4.1에서 Slack·BlueJeans(둘 다 Electron)와 Zoom의 코드량을 직접 측정**하여 Electron 앱이 얼마나 많은 죽은 Chromium 코드를 싣고 다니는지 수치화한, 이 렛저 유일의 논문.

---

## 1. Problem, Gap & Hypothesis

**Problem.** Chromium has inflated far past its original "lightweight browser" design goal. The paper's own measurements: the code chunk in an official Chromium release is **around 110 MB — larger than the Linux kernel**, with **roughly 40% of source code coming from third-party software**. Every feature shipped (PDF viewer, WebRTC, VR, …) is attack surface that a given user or a given application never exercises.

**Gap.** Two prior lines both fall short at browser scale:

- **Feature *blocking* rather than removal.** Snyder et al. proposed a browser extension that selectively blocks low-benefit/high-risk features by cost-benefit evaluation, blocking 15 of 74 Web API standards and avoiding **52% of all CVEs** while preserving usability on **94.7%** of tested sites. Slimium's objection is structural: *the binary code for the blocked feature still resides in memory*, and the mechanism — intercepting JavaScript APIs — can be circumvented.
- **Generic code debloating** (binary-analysis-based specialization, compiler-assisted approaches such as PieceWise, and ML-based debloating) **does not scale to an application of this size**.

The stated reason debloating fails here is not merely volume but a *structural* property: the browser embeds many large inner-components that are strongly connected to one another (Blink's DOM pipeline reaches into Skia and the GPU; V8 exposes Web APIs through a large binding interface). The authors' static call graph makes this concrete — **86.7% of all 483K function nodes are connected either directly or indirectly**. Under that topology, dependency-graph-based removal yields almost nothing removable, while dynamic tracing removes code accidentally because paths diverge drastically even across repeat visits to the same page.

**Hypothesis.** If the debloating *unit* is raised from the function/basic-block level to a **human-meaningful "feature"** (WebRTC, WebGL, FIDO U2F, …), then (a) the connectivity problem becomes tractable, because features are what actually get used or not used as a block, and (b) the mapping from feature → binary code can be inferred approximately but usefully, rather than soundly and uselessly.

*(KO) 이 논문의 gap 주장이 Electron 논문에 그대로 이식된다. "함수/블록 단위 디블로팅은 Chromium 규모에서 안 된다 — 483K 노드 중 86.7%가 서로 연결되어 있기 때문"이라는 측정치는, Electron 앱을 대상으로 같은 시도를 할 때 반드시 인용·반박해야 하는 기준선이다. 동시에 "feature 단위로 올리면 된다"는 해법은 Electron 앱에 **더 유리**하다: 브라우저는 임의의 사이트를 방문해야 하지만 Electron 앱은 자기 자신 하나만 렌더링하므로 feature 집합이 훨씬 고정적이다.*

## 2. Methodology

**Step 1 — Define a feature set.** The authors, with browser-expert input, identify **164 Chromium features**, backed by **6,527 source code files**. The summary row of their feature table reports **164 features / 142,968 functions / 41,097 objects / 153 CVEs** associated with the defined feature set.

**Step 2 — Feature-code mapping via *relation vectors*.** This is the paper's technical core and the transplantable idea. Rather than trying to decide soundly which object files implement a feature, Slimium computes a two-dimensional **relation vector R⃗ = (r_c, r_s)** where `r_c` captures call-invocation relatedness and `r_s` a structural/distance relatedness, applied in stages:

1. Identify objects from the call graph.
2. Compute `(r_c, r_s)` for an **object–object** relation vector `R_O`.
3. Compute `(r_c, r_s)` for a **feature–object** relation vector `R_F`.

The relation vector is explicitly a *metric of relatedness*, not a proof — it lets Slimium pull in object files that plausibly belong to a feature without requiring a sound dependency analysis.

**Step 3 — Webpage profiling.** Dynamic profiling records which features a target site actually exercises. The paper is candid about the cost of doing this reliably: converging on a stable feature set **requires continuous visits of 172 times on average**.

**Step 4 — Hybrid binary instrumentation.** Removal is performed on the binary with feedback from the feature-code mapping plus profiling results, and tuned by four hyperparameters (the two relation-vector components `r_c`, `r_s`, plus thresholds); the reported operating point is **(r_c, r_s, T) = (0.7, 0.7, 0.3)**.

*(KO) 방법론의 두 부분을 분리해서 볼 것. (a) relation vector 기반 feature-code 매핑은 "정확성 대신 실용성"을 택한 근사 기법이고, (b) 172회 반복 방문이라는 프로파일링 비용은 이 접근의 실질적 약점이다. Electron 앱에 적용한다면 (b)가 크게 줄어든다 — 앱 개발자가 자기 앱의 테스트 케이스를 갖고 있기 때문이며, 이는 바로 후속 논문 DeView(ACSAC'22)가 택한 길이다.*

## 3. Experiments / Evaluation Setup

- **Platform:** 64-bit Ubuntu 16.04.
- **Target:** Chromium (the open-source base of Chrome; the paper consistently says "Chromium", noting Chrome adds proprietary features).
- **Feature corpus:** 164 defined features / 6,527 source files / 142,968 functions / 41,097 objects.
- **Website corpus:** **40 popular websites drawn from 10 categories**, exercised with *a series of real user activities per site* rather than merely loading the landing page (Table 2 records the activity script per site).
- **Measured:** (i) how much relevant code the relation-vector technique discovers for the feature-code map; (ii) how well prompt webpage profiling identifies needed features; (iii) code reduction; (iv) CVE reduction; (v) reliability (does the debloated browser still work).
- **Security-feature check:** code coverage was measured for four load-bearing web security mechanisms — **SOP 8.3%, CSP 39.1%, SRI 34.0%, CORS 79.0%** average coverage across the 40 sites. SOP/CSP/SRI are deliberately *not* in the feature set, so Slimium never removes them; CORS is in the map but is so heavily exercised (min/max coverage 60.5%/85.8%) that nothing is removed.

*(KO) 평가 설계에서 눈여겨볼 점: 보안 기능(SOP/CSP/SRI)을 feature 집합에서 아예 빼서 "절대 제거되지 않음"을 보장했다는 점. 디블로팅 논문이 스스로 만들 수 있는 최악의 사고(보안 메커니즘을 잘라버리는 것)를 설계 단계에서 차단한 것이며, Electron 앱 디블로팅을 설계할 때 그대로 따라야 할 안전장치다.*

## 4. Results / Key Findings

**Headline.** Across the 40 websites, Slimium removes **94 CVEs (61.4%)** by cutting **23.85 MB of code (53.1% of the defined-feature code, 21.7% of the whole of Chromium)**.

**Code reduction, broken down:**

- **53.1% (23.85 MB)** of feature code removed on average per category-specific debloated variant.
- The one exception is the **Remote Working** category at **41.4% removal**, because those sites use WebRTC.
- A **single** debloated variant that must support **all 40 websites** still removes **38.8% (≈17.4 MB)** — i.e. even a one-size-fits-all build wins, though a per-target build wins much more.

**Reliability.** Repeating the full activity scripts on the debloated mutations produced **flawless browsing in all cases with no crash**. Failure mode is fail-closed by design: if a page triggers code for a removed security feature, the debloated Chromium raises an **illegal instruction exception and stops loading the page**, rather than silently serving the page without that protection.

**The Electron measurement (§6.4.1, the reason this paper is in this ledger).** As a case study the authors examine three Remote Working services that ship native applications on top of a Chromium engine:

| Application | Shipped code | Engine |
|---|---|---|
| Slack | **109.4 MB** | **Electron (embedded Chromium + Node.js)** |
| BlueJeans | **111.6 MB** | **Electron (embedded Chromium + Node.js)** |
| Zoom | **99.6 MB** | Chromium engine |
| *Slimium's debloated Remote Working variant* | **91.4 MB** | debloated Chromium |

That is **up to 18.1% code reduction versus the shipped Electron apps, while maintaining every needed functionality**. (Webex was excluded from the comparison because it runs on a JVM.)

*(KO) 이 표가 이 논문을 Electron 논문으로 만드는 지점이다. Slack·BlueJeans가 각각 109.4MB·111.6MB를 싣고 다니는데, 그 앱이 실제로 쓰는 기능만 남긴 Chromium은 91.4MB면 충분하다 — 즉 Electron 앱은 **자기가 쓰지도 않는 약 18% 이상의 엔진 코드를 공격면으로 기본 탑재**한다는 측정치다. 단, 이 18%는 "Remote Working 카테고리 4개 사이트를 모두 지원하는" 변형 기준이므로, 단일 앱 하나만 지원하면 훨씬 더 줄어들 여지가 있다(카테고리 평균 53.1% 제거와 비교). 이 격차 자체가 논문이 남긴 빈 칸이다.*

## 5. How to cite in Related Work

> Attack-surface reduction for the two halves of the Electron runtime has been studied asymmetrically. On the Node.js side, Mininode [RAID '20] and HODOR [CCS '23] reduce what application code and system calls a Node process can reach. On the Chromium side, Qian et al.'s Slimium [CCS '20] debloats the browser engine itself by raising the debloating unit from functions to 164 human-meaningful features, mapped to object files through a *relation vector* heuristic; across 40 websites it removes 23.85 MB of code (53.1% of feature code) and neutralises 94 CVEs (61.4%). Notably, Slimium's own case study measures two Electron applications — Slack (109.4 MB) and BlueJeans (111.6 MB) — and shows that a Chromium build restricted to the features those services actually exercise needs only 91.4 MB, an 18.1% reduction. Slimium thus supplies the clearest existing evidence that Electron applications ship a large quantity of unreachable-but-exploitable engine code, yet it stops short of treating an Electron application as the unit of analysis: its profiling target is a *website* visited by a general-purpose browser, and it requires an average of 172 repeat visits to stabilise a feature set — a cost that does not arise when the "site" is a single packaged application with its own test suite.

*(KO) 포지셔닝. 이 논문은 **방어 쪽 기준선(defense baseline)**이자 동시에 **문제 규모의 증거**로 이중 인용 가능하다. (1) 동기 부여용: "Electron 앱은 안 쓰는 엔진 코드를 18% 이상 싣고 다닌다(Slimium §6.4.1)" — 취약점 탐색 논문의 서론에서 공격면 크기를 정당화하는 데 쓰기 좋음. (2) 대비용: Slimium은 **브라우저**를 대상으로 하고 **웹사이트**를 프로파일링 단위로 삼는다. 이 논문이 남긴 빈 칸은 명확하다 — Electron 앱은 단일 렌더러·고정된 feature 집합·개발자가 소유한 테스트 스위트를 가지므로 프로파일링 비용(172회 방문)이 사라지고, 반대로 브라우저에는 없는 새로운 축(renderer→main IPC, preload, nodeIntegration)이 추가된다. 즉 "Slimium을 Electron에 그대로 돌리면 된다"가 아니라, **Electron에서는 잘라내야 할 표면이 Chromium feature 집합과 다르다**는 것이 thesis의 주장이 될 수 있다. (3) 또한 후속작 DeView(ACSAC'22, 같은 그룹)가 이미 "웹사이트 대신 PWA 단위"로 옮겨갔으므로, thesis는 그 궤적의 다음 칸(= Electron 단위)에 자신을 위치시킬 수 있다.*

## 6. Caveats / what I could not confirm from the text

- **The 164-feature table's per-column semantics were read from the summary row only.** The row reads `Total 164 142,968 41,097 153 25 15`; I am confident about *164 features / 142,968 functions / 41,097 objects / 153 CVEs*, but the final two columns (25, 15) appear in the same row and I did **not** locate the column headers, so I have not attributed them and they should not be cited.
- **The "94 CVEs (61.4%)" and "153 CVEs" figures are not obviously the same denominator.** The abstract's 61.4% is stated over the 40-website evaluation; the feature table's 153 is a property of the defined feature set. I did not reconcile them and have reported each in its own context.
- **"up to 18.1% code reduction"** is the paper's own phrasing for the Electron comparison. I read the surrounding paragraph but did not verify whether 18.1% is computed against Slack (109.4 → 91.4 = 16.5%) or BlueJeans (111.6 → 91.4 = 18.1%). The arithmetic matches **BlueJeans**, so the figure is most likely the best case, not the average — treat "up to" as load-bearing when citing.
- I read the abstract, §1 Introduction, §4.2 (feature-code mapping / relation vectors), §6 Evaluation §6.1–§6.4.1, and the feature-table summary row. I did **not** read §2–§3 (background/overview), §4.1, §4.3, §5, §6.4.2–§6.5, §7 Discussion, or §8 Related Work in full — so the related-work positioning above is inferred from §1's framing rather than from the paper's own §8.
- No claim is made here about whether Slimium's binary rewriting works on an Electron-packaged Chromium; the paper does **not** debloat Slack or BlueJeans — it only *measures* them and compares against its own browser build.
