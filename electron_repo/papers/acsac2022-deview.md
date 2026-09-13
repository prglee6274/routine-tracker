# DeView: Confining Progressive Web Applications by Debloating Web APIs

**Authors:** ChangSeok Oh (Georgia Institute of Technology), Sangho Lee (Microsoft Research), Chenxiong Qian (University of Hong Kong), Hyungjoon Koo (Sungkyunkwan University, corresponding author), Wenke Lee (Georgia Institute of Technology)
**Venue / Year:** 38th Annual Computer Security Applications Conference (ACSAC '22), 5–9 December 2022, Austin TX, USA — 15 pages
**Links:** [paper (ACM DL)](https://dl.acm.org/doi/abs/10.1145/3564625.3567987) · [PDF (Microsoft Research, open)](https://www.microsoft.com/en-us/research/wp-content/uploads/2022/09/deview-acsac22.pdf) · [code](https://github.com/shivamidow/deview) · [DOI 10.1145/3564625.3567987](https://doi.org/10.1145/3564625.3567987)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** DeView is the direct successor to Slimium from the same lab and moves the debloating unit from *website* to *installed web-technology application*, explicitly naming Electron as the sibling architecture in its introduction and explicitly comparing its storage cost against "Electron apps (~120 MB)" — making it the closest existing methodological template for per-Electron-app attack-surface reduction, and the paper a thesis must differentiate itself from.

> **한 줄 요약 (KO):** PWA(Progressive Web App)마다 실제로 쓰는 Web API만 남기고 나머지를 Chromium 바이너리에서 제거하는 기법. 두 축: (i) **record-and-replay 프로파일링** — 개발자가 작성한 테스트 케이스/유닛 테스트를 재생해 앱별 필요 Web API 집합을 수집, (ii) **컴파일러 보조 디블로팅** — LLVM 패스로 Web API의 진입 함수(entry function)를 제거. 114개 실제 PWA에서 평균 **Web API의 91.8% 제거**, **478개 CVE 중 76.3% 차단**. 핵심 발견: PWA는 일반 웹사이트와 달리 서로 **공유하는 API 집합이 거의 없어(Jaccard 평균 0.36)** "인기 없는 API를 일괄 제거"하는 기존 전략이 통하지 않고, **앱마다 다른 디블로팅 규칙이 필요**하다. 이 논리가 Electron 앱에 그대로 적용된다.

---

## 1. Problem, Gap & Hypothesis

**Problem.** A PWA is a web application promoted to native-like status: HTML5 features let it reach system services and hardware (WebAudio, WebRTC, WebUSB), hold resources offline (Storage, Service Worker), and describe itself (Web Application Manifest). But it runs on the **shared web runtime** — a Chromium renderer that implements *all* web APIs — so every installed PWA on a device carries an **identical, maximal attack surface** regardless of what it needs. The authors' framing example: *"a Starbucks PWA does not require WebUSB"*, yet a compromised Starbucks PWA can freely reach WebUSB, WebAudio and WebRTC, all of which have had memory-corruption CVEs.

Critically, §1 places this in the same family as the desktop frameworks this thesis studies. The paper's own words: the hybrid approach complements web-app limitations "by allowing a native application to harness web APIs via an embedded system service (e.g., WebView) or a **standalone framework (e.g., Electron)**", adding that "building a desktop application with **Electron** maintains its copies by design" — i.e. Electron's answer to the same problem is *ship your own whole engine*, which is the worst case of exactly the bloat DeView attacks.

**Gap.** Three prior strategies are shown not to transfer to PWAs:

1. **Popularity-based API removal.** Previous studies found most legitimate web applications use *similar* web APIs, so removing unpopular APIs is safe. DeView's measurement kills this for PWAs: **~50% of PWAs use at least 20 web APIs with ≤1% popularity, and at least 60 APIs with ≤10% popularity**.
2. **Snyder et al.'s "high-cost, low-benefit" class removal** (drop SVG, WebAudio, WebGL, WebRTC). Also fails: **63.16% of PWAs use SVG, 17.54% WebAudio, 15.79% WebGL, 8.77% WebRTC**.
3. **A single common debloated browser for all PWAs.** The 114 PWAs collectively touch **3,296 distinct web APIs**, but **~90% of individual PWAs use under 40% of those 3,296** — so a shared build that supports everything is still heavily bloated.

Two technical challenges are named: the **monolithic design** of a browser (per-API modularization is impractical for performance reasons) and the **non-determinism** of identifying a PWA's API set — static analysis of HTML/CSS/JS is hard, browsers carry non-standard APIs, and obfuscation/compat shims introduce redundant code paths. The paper also cites its own predecessor's scale as evidence of difficulty: **Slimium defines 164 distinct Chromium features containing at least 142,968 functions (~40.1 MB), "which is yet far from a complete feature set."**

**Hypothesis.** If the *application developer's own test cases* are used as the profiling driver, then (a) coverage of intended functionality is adequate by construction (minimising accidental removal), and (b) debloating can be done **per application** at compile time rather than per website at run time.

*(KO) gap 논증의 구조가 Electron thesis에 이식 가능한 형태다. "PWA들은 서로 다른 API를 쓴다 → 공통 디블로팅은 불가능 → 앱별로 해야 한다"는 3단 논법인데, Electron 앱은 PWA보다 **더** 이질적이다(각자 자기 Chromium 사본을 들고 다니고, 게다가 Node.js API까지 노출됨). 즉 이 논문의 측정 결과는 Electron에 대해 **더 강하게** 성립할 것으로 예측되며, 그 예측을 실측하는 것이 thesis의 빈 칸 중 하나다.*

## 2. Methodology

Two techniques, deliberately chosen to be browser-implementation-agnostic:

**(i) Record-and-replay web API profiling.** DeView records varying execution paths from **unit tests and test cases written by the application developer**, then replays those paths per PWA to collect the set of web APIs the app actually demands. The rationale is stated explicitly: identifying code coverage from the original developer's test cases "assists in ensuring the intended features of an application are adequately covered (i.e., minimizing unexpected removal)." In the evaluation this is supplemented by manual UI navigation (clicking buttons, filling inputs, scrolling) and by **gremlins.js**, a monkey-testing library, as a safety net for APIs the replay might miss.

**(ii) Compiler-assisted browser debloating.** DeView instruments common browser libraries **at compilation time**, producing a tailored build that admits only the permitted subset of web APIs. Concretely it removes the **entry functions** of unneeded web APIs, using the mapping between a web API and its entry point in the binary. The entry-point list is obtained by **extending Chromium's WebIDL parser (Blink IDL)** to enumerate all web API entry functions, and the removal itself is an **LLVM pass** driven by name-based rules (the paper's Table 1 gives the rules).

Note the division of labour versus Slimium: Slimium inferred feature↔code association heuristically from binaries with relation vectors; DeView gets the association *for free and exactly* from WebIDL, because a "web API" is a declared interface with a generated entry point. That is why DeView can claim to be "lightweight" relative to its predecessor.

*(KO) 두 기법 모두 Electron으로 옮길 때의 난이도가 다르다. (i) record-and-replay는 Electron 앱에 **더 쉽다** — 앱 개발자가 Spectron/Playwright 테스트를 갖고 있는 경우가 많음. (ii) WebIDL 기반 entry function 제거는 Chromium 쪽에는 그대로 적용되지만, **Electron이 추가로 노출하는 표면(preload를 통한 contextBridge API, ipcRenderer, Node 내장 모듈)은 WebIDL에 존재하지 않는다**. 즉 DeView의 매핑 기법은 Electron의 절반만 덮는다 — 이것이 thesis가 파고들 구조적 틈이다.*

## 3. Experiments / Evaluation Setup

- **Platform:** Fedora 32 (kernel 5.8.10); a modified Chromium build (build configuration in the paper's Table 4).
- **PWA corpus:** **114 PWAs**, gathered from the **Alexa Top 100 US sites** plus other online listings (no central PWA repository exists). Non-installable or malfunctioning PWAs were excluded, mostly DRM/codec-related.
- **Web API universe:** **8,249 web APIs** collected from chromestatus's `featurepopularity.json` and `csspopularity.json` popularity data; the 114 PWAs together exercise **3,296 distinct web APIs**.
- **Profiling protocol:** navigate all available UI of each PWA to trigger as many APIs as possible (following Snyder et al.'s feature-detection approach), plus gremlins.js monkey testing to catch misses.
- **CVE corpus:** **1,035 CVEs** collected from Chrome release notes over five years (Jan 2017 – Apr 2022); each CVE's crbug.com ticket was inspected to find those associated with web APIs the PWAs use, yielding **478 web-API-relevant CVEs**, classified into **11 types** (bypass, information disclosure, memory corruption, OOB read, OOB write, overflow, privilege escalation, RCE, spoofing, use-after-free, XSS). CVEs unrelated to web-API exploitation were discarded — the paper's worked example is CVE-2019-5777, a Unicode URL-spoofing attack that involves no web API.
- **Research questions measured:** removable API ratio; security benefit (preventable CVEs); profiling quality versus a monkey-test baseline; developer-side and user-side performance overhead.

*(KO) 데이터셋 설계에서 thesis가 배울 점: CVE 코퍼스를 "Chrome 릴리즈 노트 → crbug 티켓 확인 → Web API 관련만 선별"의 3단계로 구성하고, 관련 없는 CVE를 왜 뺐는지 구체 사례(CVE-2019-5777)로 정당화했다. Electron 앱 대상으로 같은 작업을 한다면 Electron 자체 보안 권고(GHSA) + Chromium CVE + Node.js CVE 세 갈래를 합쳐야 하며, 이 렛저의 context 항목들(SiYuan, Notesnook, DeepChat, DbGate 권고 시리즈)이 그 출발점이 된다.*

## 4. Results / Key Findings

**Removable web APIs.** DeView eliminates **91.84% of web APIs on average, ranging from 75.54% to 98.53%** across the 114 PWAs. Broken down by kind:

| API kind | Mean removed | Range |
|---|---|---|
| HTML | **79.95%** | 47.39% – 94.31% |
| CSS | **68.41%** | 8.47% – 91.86% |
| JavaScript | **94.03%** | 81.12% – 91.62% *(as printed)* |

**Security benefit.** DeView blocks **76.33% of web-API-relevant exploits on average, ranging from 48.33% to 93.31%**, out of the 478 CVEs. Composition of that corpus: **420 JavaScript-exploit CVEs, 48 HTML, 10 CSS**.

**Where it does *not* help — the most useful finding for a vulnerability-discovery thesis.** Effectiveness "slightly differs across attack types: DeView is effective against **bypass and XSS**, whereas **less effective in defeating RCE or other memory-related attacks**." The stated reason is that RCE and memory attacks "mostly exploit **non-web API** methods, such as JavaScript language natures (e.g., TypedArray, RegExp, wasm) or **browser infrastructure (e.g., extensions, PDF, protocol handler)**."

**Bloat evidence.** ~90% of PWAs utilise **15% or below** of all available web APIs. Pairwise similarity of API usage across PWAs has a **Jaccard index of 0.36 on average (min 0.06, max 0.82)** — most PWA pairs have little in common.

**Profiling quality.** The record-and-replay approach **outperformed the gremlins.js monkey test on both code coverage and number of web APIs discovered** (Table 2, three popular PWAs); the monkey test is recommended only as a *supplementary* method.

**Overheads.** Developer-side profiling overhead (recording + Puppeteer) is characterised as negligible in CPU and memory. User-side: an extra load latency of a fraction of a second, **max 0.29 seconds**. On storage, the paper notes its per-app debloated library must be stored per installation, but argues "this storage overhead is still smaller than those of **Electron apps (~120 MB)** that must contain the [engine]."

*(KO) 결과 중 thesis에 가장 값진 것은 "무엇을 못 막는가"다. **RCE와 메모리 계열 공격은 Web API가 아니라 JS 언어 자체(TypedArray, RegExp, wasm)와 브라우저 인프라(확장, PDF, 프로토콜 핸들러)를 탄다**는 관찰은, Web API 표면을 아무리 줄여도 Electron 앱의 XSS→RCE 경로는 남는다는 뜻이다. Electron의 실제 RCE 경로(preload로 노출된 브리지, ipcRenderer, custom protocol handler)는 정확히 DeView가 "못 막는다"고 인정한 범주에 속한다 — 이것이 이 논문을 방어 논문으로 인용하면서도 thesis의 존재 이유를 세우는 지점이다.*

## 5. How to cite in Related Work

> Oh et al.'s DeView [ACSAC '22] applies software debloating to progressive web applications, using record-and-replay profiling over developer-written test cases to determine the web APIs an individual application requires, and an LLVM pass over Chromium's WebIDL-derived entry points to remove the rest. Across 114 real-world PWAs it removes 91.8% of accessible web APIs and neutralises 76.3% of 478 web-API-related Chromium CVEs. Its measurements establish that per-application debloating is *necessary* rather than merely desirable for installed web applications: pairwise API-usage similarity across PWAs has a mean Jaccard index of only 0.36, and popularity-based removal strategies that work for ordinary websites fail because roughly half of PWAs depend on twenty or more APIs used by ≤1% of their peers. DeView positions Electron explicitly as the alternative architecture that solves the same portability problem by shipping a private copy of the engine, and benchmarks its own storage cost against "Electron apps (~120 MB)" — yet it does not evaluate a single Electron application. The gap is twofold. First, Electron's exposed surface is not exhausted by WebIDL: `contextBridge`-published functions, `ipcRenderer` channels and registered custom protocol handlers have no IDL declaration and therefore no entry point for DeView's pass to remove. Second, DeView reports itself least effective precisely against RCE and memory-corruption CVEs, because those exploit JavaScript language primitives and browser infrastructure rather than web APIs — which is the exact class of outcome that an Electron renderer compromise produces.

*(KO) 포지셔닝. DeView는 thesis의 **가장 가까운 선행 방어 연구**이며 세 가지 용도로 쓰인다. (1) 문제 인식 공유: "설치형 웹 기술 앱은 앱마다 필요한 표면이 다르다" — thesis의 전제를 이미 실증해 준 논문. (2) 방법론 템플릿: record-and-replay 프로파일링은 Electron 앱에 더 잘 맞는다(개발자 테스트 스위트 존재). (3) **가장 중요한 대비점**: DeView는 Electron을 서론에서 언급하고 저장 공간 비교에까지 쓰면서도 **Electron 앱은 단 한 개도 평가하지 않았다**. 게다가 그 매핑 기반(WebIDL)은 Electron 고유 표면(contextBridge/ipcRenderer/custom protocol)을 원리적으로 덮지 못하고, 저자들 스스로 RCE·메모리 계열에는 약하다고 인정했다. "Electron에서 실제로 문제가 되는 것은 정확히 DeView가 못 막는 범주"라는 한 문장이 thesis의 gap statement로 바로 쓰일 수 있다.*

## 6. Caveats / what I could not confirm from the text

- **The JavaScript-API removal range is printed as "81.12%–91.62%" against a mean of 94.03%**, which is internally inconsistent (the mean lies outside the stated range). I reproduced the numbers exactly as they appear in §6.2 rather than silently correcting them; the appendix Table 5 presumably resolves this, and I did not read it. **Do not cite the JS range without checking Table 5.**
- The appendix tables were **not** read: Table 5 (per-PWA results for all 114 PWAs — the source of the HTML/CSS/JS/Object breakdown, whose caption reports slightly different averages of 79.75%, 68.25%, 90.24% and 94.04% for HTML, CSS, JS Object and JS) and Table 6 (the 478-CVE list). Note the caption figures differ from §6.2's prose figures, and the caption distinguishes "JS Object" from "JS" where the prose does not. This discrepancy is unresolved.
- I read the abstract, §1 Introduction, §3.1 Preliminaries, §3.2 Challenges (partially), §5 Implementation (headline only), §6.1–§6.5 Evaluation, and the storage-overhead paragraph of §7. I did **not** read §2 Background, §3.3 threat model, §4 (design), or §8 Related Work in full.
- The **"~120 MB" figure for Electron apps** is DeView's own aside in a storage-overhead discussion and carries **no citation or measurement in the text I read**. Slimium's independently measured figures (Slack 109.4 MB, BlueJeans 111.6 MB) are the better-grounded numbers and should be preferred.
- The claim that `contextBridge`/`ipcRenderer`/custom protocol handlers fall outside DeView's WebIDL-derived mapping is **my inference** from the described mechanism (entry functions enumerated by extending Blink's IDL parser), not a statement made in the paper. It should be verified against §4/§5 before being asserted in a thesis.
