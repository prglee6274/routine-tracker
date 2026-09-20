# GLeeFuzz: Fuzzing WebGL Through Error Message Guided Mutation

**Authors:** Hui Peng, Zhihao Yao, Ardalan Amiri Sani, Dave (Jing) Tian, Mathias Payer (Purdue University; University of California, Irvine; EPFL — affiliations per the USENIX listing)
**Venue / Year:** 32nd USENIX Security Symposium (USENIX Security '23), Anaheim CA, 9–11 August 2023 — **Summer cycle**
**Links:** [USENIX page](https://www.usenix.org/conference/usenixsecurity23/presentation/peng) · [PDF (open access)](https://www.usenix.org/system/files/usenixsecurity23-peng.pdf)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** The paper's own framing is that WebGL is a JavaScript API giving **remote, unsandboxed** web content access to the host's native graphics stack, and it names **Electron** explicitly as one of the frameworks where WebGL is enabled by default — so it is a worked example of the exact escalation shape a thesis on Electron cares about (attacker-controlled web content → standard JS API → native C/C++ code → host privileges), attacked by a fuzzer that **abandons code coverage as the feedback signal**.

> **한 줄 요약 (KO):** WebGL은 웹 콘텐츠가 호스트의 **네이티브 그래픽 스택(GL 라이브러리·GPU 드라이버)** 에 원격·비샌드박스로 접근하게 해주는 JS API이며, 논문은 Electron·Cordova·ChromeOS·Android WebView·iOS WKWebView에서 기본 활성화됨을 명시한다. 커버리지 수집이 불가능한 대상(다중 프로세스 + 폐쇄소스 드라이버)이라, **브라우저가 개발자에게 뱉는 오류 메시지를 피드백 신호로 대체**해 입력 뮤테이션을 유도하는 것이 핵심 기여. Chrome 4 · Safari 2 · Firefox 1, 총 **신규 취약점 7건**.

---

## 1. Problem, Gap & Hypothesis

WebGL is a standardised set of JavaScript APIs for GPU-accelerated graphics, supported by all modern browsers. The security argument in the abstract is blunt: "Security of the WebGL interface is paramount because it exposes remote and unsandboxed access to the underlying graphics stack (including the native GL libraries and GPU drivers) in the host OS."

Crucially for this ledger's scope, §1 and §2.1 both extend that reach past browsers:

> "Going beyond browsers, WebGL is also enabled in mobile and desktop application frameworks (e.g., the Android WebView component, iOS WKWebView, or **Electron**)." (§1)
>
> "Support for WebGL has gone far beyond browsers in desktops and mobile devices. Application frameworks such as **Electron** and CORDOVA are built on top of the browser stack; and the GUI of ChromeOS fully builds on the chrome browser. … **WebGL is by default enabled in all these frameworks and gadgets.**" (§2.1)

Architecturally: WebGL calls issued in the **renderer process** are redirected over **IPC** to a shared **GPU process**, which is launched with access to GPU drivers. Chrome's ANGLE translates WebGL calls to the platform API (OpenGL/OpenGL ES on Unix-like systems, Direct3D on Windows), which then drives vendor GPU drivers — "mostly in closed-source binary format". Defensive checks are deployed in both the renderer and the GPU process (renderer-side to avoid IPC cost; GPU-side because that is where the danger is).

**The gap is a tooling gap, and it is the interesting part.** State-of-the-art fuzzing cannot be applied here because of (1) a huge input state space, and (2) **the infeasibility of collecting code coverage** across concurrent processes, closed-source libraries, and kernel device drivers. Coverage-guided fuzzing — the default assumption of the whole field — is simply unavailable against this target.

**Hypothesis:** browsers emit *meaningful* error messages to help developers debug WebGL programs, and those messages say **which part of the input failed** (incomplete arguments, invalid arguments, unsatisfied dependencies between API calls). Error messages can therefore substitute for coverage as the mutation-guiding feedback signal.

> **(KO)** 이 논문을 in_scope로 판단한 근거는 저자들이 **직접** Electron을 지목했다는 점이다(§1, §2.1). 즉 "브라우저 일반 버그"라는 EXCLUDE 항목에 해당하지 않는다 — 공격면의 다른 쪽 끝에 **웹 콘텐츠를 호스팅하는 데스크톱 앱**이 앉아 있다고 논문 스스로 규정한다. 더 중요한 방법론적 시사점: **커버리지를 못 쓰는 상황에서 대상이 스스로 뱉는 진단 정보를 피드백으로 재활용한다**는 발상은, 소스도 계측도 없는 prebuilt Electron 앱(.asar + .node)을 감사할 때 그대로 필요한 사고방식이다.

## 2. Methodology

- **Static analysis to build the feedback model.** GLeeFuzz analyses **Chrome's** WebGL implementation to identify dependencies between **error-emitting statements** and the **rejected parts of the input**. Error messages are classified into type 1 and type 2. The analysis builds an ICFG and VFG (using SVF) over the WebGL implementation's LLVM bitcode and then computes, per error message, the **target argument or the dependent API set** to mutate.
- **Error-message-guided mutation.** At run time the executor collects error messages from the browser and the fuzzer focuses mutation on the input parts the messages implicate, rather than mutating blindly.
- **Cross-browser generality.** The static analysis is done once on Chrome (the open-source implementation), but the resulting fuzzer is pointed at Chrome, Firefox **and Safari** — i.e. the model learned from one implementation transfers to closed ones.
- **Baseline built by the authors.** No random-mutation WebGL fuzzer existed, so they implemented **GLeeFuzz-R**, a variant mutating inputs randomly following the **Syzkaller** strategy, on top of their own system.

Because coverage cannot be collected, the evaluation uses **the number of successfully executed APIs** (APIs returning without an error message) and **the number of error messages triggered** as coverage proxies.

> **(KO)** 설계에서 배울 두 가지. (1) **오픈소스 구현 하나(Chrome)에서 모델을 뽑아 폐쇄 구현(Safari)에 전이**시키는 구조 — Electron 맥락에서는 오픈소스 Electron 런타임에서 모델을 뽑아 상용 Electron 앱에 적용하는 것과 동형이다. (2) **커버리지 대용 지표를 명시적으로 정의하고 그 한계를 인정**한 점. 계측 불가 대상에 대한 평가 설계의 모범 사례.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**Target matrix (Table 1) — 5 operating systems × 3 browsers × a broad GPU spread:**

| OS | Platform | Browsers | GPU |
|---|---|---|---|
| Windows | x86-64 Desktop | Chrome, Firefox | Intel, NVIDIA, AMD |
| Linux | x86-64 Desktop | Chrome, Firefox | Intel, NVIDIA, AMD |
| macOS | Mac mini | Chrome, Firefox, Safari | Intel, Apple M1 |
| Android | Android smartphones | Chrome | Adreno, Mali, PowerVR |
| iOS | iPhone | Safari | PowerVR, Apple GPU |

Concretely: Intel UHD 630, NVIDIA GeForce GTX 980 and AMD Radeon RX 550 on Windows 10 and Ubuntu 18.04; Intel UHD 630 and Apple M1 on macOS 11.6; OnePlus 9 Pro / OPPO Reno2 / OPPO Reno5 with Adreno 660, PowerVR 9446 and Mali G77 on Android 11; iPhone 6s Plus and iPhone X with PowerVR 7660 and Apple GPU on iOS 11.4.

- **Static-analysis experiments** ran on Ubuntu 20.04 LTS, x86-64, Intel i7-8086K, 32 GB RAM, over **12.3 MB of LLVM bitcode**.
- **Comparative fuzzing (GLeeFuzz vs GLeeFuzz-R):** **five runs of 12 hours each**, targeting Chrome on x86-64 desktops running Ubuntu 18.04 with 16 GB RAM. Because browser restarts after a tab crash are heavyweight and add noise, the authors recorded generated inputs over time and **replayed non-crashing inputs in sequence** to measure time fairly.
- **Vulnerability hunting:** the platform ran **intermittently for more than two months** across the Table 1 matrix.

Deliberate choice worth noting: they targeted **common, well-tested hardware** (Intel, NVIDIA, AMD, Apple) rather than niche GPUs, on the grounds that finding bugs there is harder — supported by the observation that **only 87 CVEs have been assigned across all WebGL implementations since WebGL appeared in 2011**.

> **(KO)** 평가 설계에서 가장 정직한 부분은 "브라우저 재시작이 측정을 오염시키므로 비크래시 입력만 재생해 시간을 측정했다"는 대목이다. 크래시가 많이 나는 퍼저일수록 wall-clock이 불리해지는 편향을 스스로 교정한 것. 또 **87 CVE/12년** 이라는 기저율 제시는 "7건 발견"의 의미를 독자가 평가할 수 있게 해준다 — 적은 수의 취약점을 보고할 때 반드시 따라 해야 할 서술 전략이다.

## 4. Results / Key Findings — concrete numbers

**Error-message inventory (Table 2).** Static analysis found **998 error messages in WebGL v1** (706 type 1 + 292 type 2) and **2,934 in WebGL v2** — "[t]his large number calls for an automatic approach to identify the error messages." (Over-approximating virtual-call callees means these counts may include false positives.)

**Static-analysis cost.** ICFG + VFG construction: **20.4 seconds** (shared by both versions). Static analysis on top: **40.7 s** for v1 and **120.1 s** for v2.

**GLeeFuzz vs GLeeFuzz-R (5 × 12 h on Chrome).** GLeeFuzz spent **217× the wall time launching the browser**, explained by **202× the number of browser crashes** — i.e. error-message guidance produced two orders of magnitude more crashes than random mutation. Both fuzzers spend only about **2%** of their time generating and mutating inputs, so the guidance adds negligible overhead. GLeeFuzz also reached higher proxy-coverage faster on both proxy metrics.

**New vulnerabilities (§7.4, Table 4).** Running intermittently for **more than two months**, the platform produced "over a thousand crash detections", reduced by triage to **7 previously unknown vulnerabilities: 4 in Chrome, 2 in Safari, 1 in Firefox**. Two of the seven were triggered in the **GPU process**, whose security impact is confirmed because that process is **shared among** clients; the text describes assertion failures in the restarted GPU process and memory corruption in the GPU process "potentially allowing remote" exploitation. The abstract's summary: "The Chrome vulnerabilities allow a remote attacker to freeze the GPU and possibly execute remote code at the browser privilege."

> **(KO)** 인용 가치가 가장 높은 숫자는 **"202배의 크래시"** (오류 메시지 유도 vs 무작위)와 **"WebGL v1 998개 / v2 2,934개의 오류 메시지"** 다. 후자는 "대상이 이미 내보내는 진단 정보의 양이 사람이 수작업으로 다룰 수 없는 규모"라는 논거로, Electron 앱의 로그·예외·devtools 경고를 피드백으로 쓰자는 제안을 정당화할 때 재사용 가능하다. 한편 **크래시 1,000+건 → 확정 취약점 7건**이라는 비율은 퍼징 결과 보고 시 크래시 수와 취약점 수를 혼동하면 안 된다는 점을 다시 보여준다(IvySyn 노트의 184→135 논점과 동일 계열).

## 5. How to cite in Related Work

Draft English sentences, ready to adapt:

> Not every attack surface admits coverage-guided fuzzing. Peng et al. attack WebGL [USENIX Security '23], a standard JavaScript API that — as they stress — "exposes remote and unsandboxed access to the underlying graphics stack (including the native GL libraries and GPU drivers) in the host OS", and which is enabled by default not only in browsers but in desktop application frameworks such as Electron and Cordova. Because WebGL execution spans concurrent processes, closed-source vendor libraries and kernel drivers, code coverage cannot be collected at all; GLeeFuzz therefore replaces the coverage signal with the browser's own developer-facing error messages, using static analysis of Chrome's implementation to link each of the 998 (WebGL v1) and 2,934 (v2) error messages to the input element it rejects. Against a random-mutation baseline it triggered 202× as many browser crashes, and over two months of intermittent fuzzing it yielded 7 previously unknown vulnerabilities — 4 in Chrome, 2 in Safari, 1 in Firefox — two of them in the shared GPU process.

> **(KO) 위치 설정:** 두 가지 용도. (1) **공격면 근거** — "Electron 앱은 브라우저 엔진을 통째로 들여오면서 브라우저의 네이티브 공격면까지 함께 상속한다"는 주장을 논문 저자의 문장으로 뒷받침한다. Electron 보안 논의는 보통 nodeIntegration/IPC에만 집중하는데, WebGL처럼 **기본 활성화된 표준 웹 API가 네이티브 코드로 직행하는 경로**도 함께 상속된다는 점은 공격면 서술을 넓혀준다. (2) **방법론적 선례이자 대조군** — 커버리지를 쓸 수 없는 대상에서 "대상이 스스로 노출하는 진단 신호"로 피드백을 대체한 사례. 단, 본 학위논문과의 대조점을 분명히 할 것: GLeeFuzz는 **표준화된 API(WebGL 명세)** 를 공격하므로 표면이 사전에 알려져 있지만, Electron 앱의 preload/IPC 표면은 **앱마다 다르고 명세가 없다**. 즉 GLeeFuzz는 "피드백 문제"를 풀었고 본 논문은 그 앞단의 **"표면 발견 문제"** 를 함께 풀어야 한다 — REFLECTA와 짝지어 인용하면 이 구분이 선명해진다.

## 6. Caveats / what I could not confirm from the text

- **Read in full:** abstract, §1 Introduction, §2.1 background on the WebGL stack and its reach beyond browsers, §2.2 opening, the process-architecture description (renderer → IPC → GPU process, ANGLE, where checks are deployed), §7 evaluation opening, §7.1 static-analysis results, §7.2 effectiveness-of-error-messages setup and results, §7.4 new vulnerability findings. **Not read line-by-line:** §3–§6 (threat model, fuzzer design internals, static-analysis implementation details), §7.3 body, §8 onwards (related work, discussion, conclusion), and **Table 4 itself** (the per-vulnerability breakdown).
- **Author affiliations were taken from the USENIX listing, not re-verified against the PDF header.** Confirm the author list and affiliation mapping before citing.
- **The evaluation never runs on Electron.** Electron is named as an affected framework in §1 and §2.1 only; every experiment targets Chrome, Firefox or Safari. Any claim that these seven vulnerabilities are exploitable *in an Electron application* would be an extrapolation this paper does not make and I did not verify. This is the main reason the scope tag is ADJACENT rather than PRIMARY.
- I did **not** extract the CVE identifiers (if any) for the 7 vulnerabilities, nor the contents of Table 4, nor Table 3.
- The phrase "possibly execute remote code at the browser privilege" is the paper's own hedged wording; I could not confirm from the sections read whether full RCE was demonstrated or only assessed as plausible.
- The "87 CVEs across all WebGL implementations since 2011" figure is the paper's citation of an external source (reference [45]); I did not verify it independently.
