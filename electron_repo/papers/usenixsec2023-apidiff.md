# One Size Does Not Fit All: Uncovering and Exploiting Cross Platform Discrepant APIs in WeChat

**Authors:** Chao Wang, Yue Zhang, Zhiqiang Lin (all The Ohio State University)
**Venue / Year:** 32nd USENIX Security Symposium (USENIX Security 2023)
**Links:** [USENIX (open access)](https://www.usenix.org/conference/usenixsecurity23/presentation/wang-chao) · [PDF (author-hosted)](https://chaowang.dev/publications/sec23a.pdf) · [Artifact](https://github.com/OSUSecLab/APIDiff)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** APIDIFF is an automated, *specification-free* discovery technique for the privileged API surface a hybrid host exposes to the web content it runs — it enumerates that surface by executing every documented API on each platform build and diffing the outcomes — and its single most transferable finding is that **the desktop build of a hybrid app enforces permission checks that the mobile builds enforce, on 17 APIs, and skips them**.

> **한 줄 요약 (KO):** 같은 하이브리드 앱(WeChat)의 Android·iOS·**Windows** 빌드에 1,031개 in-app API를 자동 생성 테스트로 전부 실행시키고 결과를 차분 비교하는 도구. 존재(109개)·권한(17개)·출력(22개) 불일치를 찾았고, 특히 **Windows에서 `wx.record`(마이크) 등이 사용자 동의 없이 호출된다**. "명세 없는 호스트 제공 API 표면을 **차분 실행**으로 밝혀낸다"는 발상은 Electron preload/IPC 표면 감사에 그대로 이식 가능하다.

---

## 1. Problem, Gap & Hypothesis

Miniapps are written once in JavaScript and run inside a super app on Android, iOS and — for WeChat and WeCom — Windows. The promise is write-once-run-anywhere; the reality is that each platform build implements the in-app API surface separately, in a different native language, against a different OS. The paper's opening example is the one to remember: **WeChat on Windows lets a miniapp call `wx.record` and capture microphone audio without asking the user**, while the mobile builds prompt.

**The gap:** prior app-in-app security work studied resource management, identity confusion and request forgery *within* the mobile ecosystem. Nobody had treated the *set of platform builds of one host* as a differential oracle, and nobody had systematically enumerated where the desktop build diverges. The authors note WeChat "is currently the only platform that supports miniapps on desktop platforms", which makes it both the only available subject and an under-examined one.

**Hypothesis:** if the same miniapp API is supposed to behave identically everywhere, then any observed divergence in *existence*, *required permission* or *output* is a bug or a security-relevant asymmetry, and the divergence can be detected automatically without any specification of what the API is supposed to do — one build is the specification for another.

> **(KO)** 핵심은 **"명세가 없으면 서로를 명세로 쓴다"**. 이것이 Electron 논문에 직접 재사용 가능한 논증 구조다: Electron 앱의 IPC 핸들러에는 Web IDL 같은 기계가 읽을 수 있는 명세가 없지만, 같은 서비스의 **웹 버전 / 데스크톱 버전**, 혹은 같은 앱의 **버전 간 빌드**가 서로의 오라클이 될 수 있다.

## 2. Methodology

APIDIFF has three components:

1. **Test Case Generator.** For each API it synthesises a snippet with correctly-initialised parameters, resolves inter-API dependencies (call ordering — e.g. `wx.createInterstitialAd` → `InterstitialAd.load` → `.show`), and mutates parameter values for coverage. The paper reports the shape of the surface that makes this tractable: of the API set, **231 APIs take no parameters at all**, **107 need supplied data**, and **364 need the three standard callbacks** (success / fail / complete). Parameter seeds come from a domain-guided brute-force approach rather than from documentation parsing.
2. **Code Executor.** WeChat has disabled JavaScript dynamic code execution inside miniapps for security reasons, so the usual compile-then-execute route is unavailable. The authors instead **reverse-engineered WeChat's debug protocol**: when the IDE pushes code to a running miniapp it calls an internal `evaluate` function, so APIDIFF feeds generated code straight into `evaluate` and logs the return value and error code. Runs are distributed by a simple client–server task queue — one server holds the API queue, one client per platform pulls tasks — so all three platforms are exercised in parallel.
3. **Discrepancies Analyzer.** Purely error-code and return-value based policies. *Existence*: one platform succeeds, another returns `not supported`. *Permission*: one platform returns `permission errors`, another does not. *Output*: same input, different output across platform or device.

A neat engineering detail worth stealing: rather than parsing and clicking permission dialogs (which stall the run — a miniapp aborts after a 5-minute wait), each API is run **twice, once with all permissions granted and once with all denied**, and the permission requirement is read off the logged error message.

Manual effort is confined to the initial study of error codes; after that the tool runs unattended. Exploitation of the discovered discrepancies is *not* automated — attacks are hand-built case studies, because they depend on API semantics.

> **(KO)** 오라클이 **"에러 코드와 반환값"**뿐이라는 점이 중요하다. 크래시도, 메모리 오염도, 정보 흐름 추적도 필요 없다. Electron IPC 표면에 같은 설계를 적용하면 — 같은 채널을 서로 다른 권한 문맥(렌더러 vs preload, `contextIsolation` on/off)에서 호출하고 반환값을 비교 — 무거운 분석 없이도 권한 검사 누락을 찾을 수 있다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

- **Subject:** WeChat, three platform builds. WeCom uses the same framework and is not separately reported. macOS was tested but excluded — the authors judge the macOS miniapp environment still under development and report only iOS, Android and Windows.
- **API set:** **1,031 miniapp APIs.**
- **Hardware:** **six devices — two Windows-11 desktops, two Android-13 phones, two iOS-16 phones.** Two devices per platform is deliberate: it separates *platform*-specific from *device*-specific divergence, which matters for the fingerprinting result.
- **Supporting tooling:** JEB and IDA Pro for static inspection, Frida for dynamic confirmation, several registered accounts, self-built miniapps for the attack demonstrations.
- **Measured:** counts of discrepant APIs in each of the three categories, per platform pair, plus category breakdowns and hand-built exploit case studies.

## 4. Results / Key Findings — concrete numbers

**Existence discrepancies: 109 APIs**, falling into **32 categories**. By pair: **105 between Windows and Android**, 40 between Windows and iOS, 69 between Android and iOS.

**Permission discrepancies: 17 APIs**, in **10 categories including location**. By pair: **16 between Windows and Android**, **17 between Windows and iOS**, and **exactly 1 between Android and iOS** (the Bluetooth API). This asymmetry is the paper's most useful single fact for a desktop-focused thesis: **the two mobile builds agree with each other almost perfectly on when to demand permission, and the desktop build is the outlier in essentially every case.** The concrete instance given up front is microphone capture via `wx.record` proceeding on Windows with no user consent.

**Output discrepancies: 22 APIs**, in **8 categories including UI, media and device**. By pair: 8 Windows/Android, 12 iOS/Windows, 14 Android/iOS. Because these differ across *devices* as well as platforms, they are fingerprintable: a malicious miniapp can build a stable signature from API outputs, the miniapp analogue of browser fingerprinting.

**Three attack families** are demonstrated by hand: (i) existence discrepancies let an attacker pick the platform where a *security* API is missing — the Bluetooth example is an Android build enforcing authentication that the Windows and iOS builds do not, yielding a MitM; (ii) permission discrepancies let a malicious miniapp reach location, camera and audio on the platform that forgot to check; (iii) output discrepancies yield device fingerprinting.

**Disclosure:** reported to Tencent, bug bounties received, findings ranked high severity, some already patched. APIDIFF is open-sourced at `github.com/OSUSecLab/APIDiff`.

> **(KO)** 인용할 때 가장 강한 숫자는 **권한 불일치 17개 중 16–17개가 Windows 쪽**이라는 비대칭이다. "데스크톱 빌드가 권한 검사를 빠뜨린다"는 명제를 한 줄로 뒷받침한다.

## 5. How to cite in Related Work

> A hybrid application host exposes a privileged API surface for which no machine-readable specification exists, so the surface must be recovered empirically. Wang et al. show that the platform builds of a single host can serve as oracles for one another: APIDIFF generates a test case per API, executes it on the Android, iOS and Windows builds of WeChat through the host's own debug channel, and classifies divergence in API existence, required permission and output [USENIX Sec'23]. Across 1,031 APIs it reports 109 existence, 17 permission and 22 output discrepancies, with the permission discrepancies overwhelmingly concentrated on the desktop build — 16 of 17 against Android and 17 of 17 against iOS, versus a single divergence between the two mobile builds. The technique needs no specification, no source and no memory-safety oracle, only an error code and a return value. It has not, however, been applied to an application-defined surface: WeChat's 1,031 APIs are documented by a single vendor, whereas an Electron application's bridge is invented per application and enumerated nowhere.

> **(KO) 위치 잡기:** **선행 방법론**으로 인용할 것 — "명세 없는 호스트 API 표면을 차분 실행으로 자동 열거한다"는 설계가 이 석사 논문이 하려는 일과 같은 계열이다. 동시에 **공백을 세 가지로 지목**할 수 있다: (1) 대상 API가 *벤더가 문서화한* 고정 집합이라 열거 문제 자체가 반쯤 풀려 있다 — Electron은 앱마다 표면이 다르므로 열거가 본질적 난제다; (2) 오라클이 "플랫폼 간 불일치"여서 **모든 빌드가 똑같이 취약하면 아무것도 못 찾는다** — Electron 단일 빌드에는 비교 대상이 없다; (3) 익스플로잇이 전부 수작업이다. 09-18 NDSS'26 항목(ground-truth invariant와 machine-readable spec의 부재)과 **같은 공백을 다른 각도에서** 말하고 있으므로 두 편을 나란히 인용하면 논지가 가장 강해진다.

## 6. Caveats / what I could not confirm from the text

- **Grounding:** strong but partial. I read the abstract, §1, the APIDIFF architecture overview (§4 intro), §4.2 Code Executor, §4.3 Discrepancies Analyzer, §5.1 setup and §5.2 results in full from the author-hosted PDF. I did **not** read §2–§3 (background and the discrepancy taxonomy), most of §4.1's parameter-seeding details, or §6's attack case studies end-to-end. Every number quoted above comes from text I read; do not add further numbers from this paper without re-reading.
- The 1,031 figure is the API population APIDIFF works over; I did not verify from the text how many of those were successfully executed versus skipped, so **do not state that all 1,031 were tested**.
- The Windows-skew in permission checks is real as reported, but the paper does not, in what I read, establish *why* — whether it reflects a deliberate desktop product decision, a porting oversight, or the absence of an OS permission broker on Windows. That causal question is open and is worth stating as open.
- This is a **miniapp** paper, not an Electron paper; the word Electron does not appear. The architectural mapping to Electron (host-provided privileged API ↔ `contextBridge`/`ipcRenderer`) is mine.
- The companion paper RootFree (AsiaCCS'24, now `asiaccs2024-rootfree`) explicitly carves API differences out of its own scope and delegates them here, so the two should be read and cited as a pair.
