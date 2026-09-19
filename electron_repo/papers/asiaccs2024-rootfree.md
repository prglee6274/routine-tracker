# RootFree Attacks: Exploiting Mobile Platform's Super Apps From Desktop

**Authors:** Chao Wang (The Ohio State University), Yue Zhang (Drexel University), Zhiqiang Lin (The Ohio State University)
**Venue / Year:** ACM AsiaCCS 2024 (Singapore, 1–5 July 2024), Round 1 · Session 10 "Web Security" · 13 pages
**Links:** [ACM DOI 10.1145/3634737.3645001](https://doi.org/10.1145/3634737.3645001) · [PDF (author-hosted)](https://chaowang.dev/publications/asiaccs24.pdf)
**Scope tag:** PRIMARY

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the closest published analogue of the Electron threat model outside Electron itself — a desktop host application that embeds a browser engine, ships its own software sandbox because the desktop OS gives it none, and hands third-party web content a privileged file-system API — and it shows that host-implemented sandbox is bypassable with a string-rewriting bug that yields instant local code execution without administrator rights.

> **한 줄 요약 (KO):** 모바일용으로 설계된 슈퍼앱(WeChat/WeCom)이 Windows 데스크톱으로 이식되면서, OS가 제공하던 프로세스·파일 격리가 사라지고 **호스트 앱이 소프트웨어로 직접 구현한 샌드박스**만 남는다. 저자들은 (a) 미니앱 패키지 암호화(키=appID)를 깨고, (b) `getNativePathByJsPath`의 `"../"` 치환 검사 결함을 이용해 샌드박스를 탈출, `WeChatXFile` 실행 파일을 덮어쓴 뒤 `wx.openDocument`를 호출해 **관리자 권한 없이 즉시 RCE**를 달성했다. Tencent에 3건 개별 신고, 전부 high severity, 버그바운티 수령. Electron 앱이 preload/IPC로 웹 콘텐츠에 로컬 권한을 주는 구조와 **위협 모델이 동일**하다.

---

## 1. Problem, Gap & Hypothesis

A "super app" (WeChat, WeCom, Alipay, Paytm, Grab, Zalo, Kakao) hosts third-party *miniapps* written in JavaScript and executed inside the host. WeChat alone reports ~1.2 billion monthly users and over 4.3 million miniapps (Alipay ~120 thousand). The miniapp paradigm was designed for Android and iOS, where the OS supplies the isolation: per-app UID plus SELinux on Android, a per-app sandbox and secure enclaves on iOS. WeChat and WeCom then ported the whole thing to Windows.

**The gap:** the security literature on app-in-app systems is entirely mobile. Nobody had asked what happens to a host application's security assumptions when the same host is re-hosted on a desktop OS whose threat model is the opposite — a multi-user OS that grants the machine owner root by default, permits arbitrary kernel modules and debuggers, and enforces no meaningful inter-application data isolation. The paper's Table 1 states the discrepancy as a matrix: user privileges (non-root / non-root / **root**), process isolation of app code, data, runtime and TEE availability (✓ ✓ / ✓ ✓ / **✗ ✗**), in-app APIs (all / all / **subset**), rendering engine (XWeb / WKWebView / **XWeb**), logic engine (JSCore / JavaScriptCore / **JSCore, built on V8**).

**Hypothesis:** where the mobile OS used to provide a guarantee and the desktop OS does not, the host app must re-implement that guarantee in its own user-space code — and those re-implementations are where the bugs are. Four research questions follow: has the vendor guarded against privileged local software at all (RQ1); is the key management behind its encryption sound (RQ2); does the cross-platform discrepancy weaken the miniapp sandbox (RQ3); and can a miniapp exploit the desktop OS's different resource-management policy (RQ4)?

> **(KO)** 이 논문의 진짜 기여는 "모바일 OS가 대신 해주던 격리를 데스크톱에서는 **앱이 직접 구현해야 한다**, 그리고 그 자체 구현이 취약점의 온상"이라는 일반 명제다. Electron 앱도 정확히 같은 처지다 — Chromium의 사이트 격리는 브라우저 문맥에서만 의미가 있고, `nodeIntegration`/`contextBridge`로 열린 경계는 앱 개발자가 스스로 지켜야 한다.

## 2. Methodology

Reverse engineering driven by **cross-platform differential analysis**, not automation. Three steps:

1. **Alignment.** WeChat is too big to analyse statically (Windows 172 MB, Android 223 MB, iOS 230 MB) and is written in a different language per platform (C/C++, Java, Objective-C), so binary-level diffing is impossible. The authors exploit the one artefact that *is* identical across platforms — the miniapp's own JavaScript — plus system-call-level behaviour, which is comparable even when the host binaries are not. They build a test miniapp, hook the system APIs on all three platforms, and diff the observed file operations.
2. **Attack-surface identification.** Files are partitioned into *platform-independent* and *Windows-unique*. Two Windows-unique, encrypted-only-on-Windows artefacts fall out: the `wxapkg` miniapp package and `WeChatApps.data`, the database of cached/shortcut miniapps. Encryption on Windows and plaintext on mobile is itself the tell — it marks exactly where the vendor knew the OS was not protecting them.
3. **Exploitation.** Dynamic hooking of the cryptographic APIs with Frida plus backward slicing from their arguments to recover key derivation; static decompilation with JEB and IDA Pro for the sandbox check; then hand-written proof-of-concept attacks. Total ≈ 2,000 LoC across five languages (JavaScript, Bash, Golang, C/C++, TypeScript). The authors are explicit that reverse engineering, attack-surface assessment and case-study construction were all manual.

**Deliberately out of scope:** API differences (delegated to the authors' own APIDiff, USENIX Sec'23) and the rendering/logic engines themselves ("they all serve the same purposes without much change"). Threat model assumes a trusted OS kernel and trusted backends, a malicious native Windows program *or* a malicious miniapp, and — importantly — **no administrator privilege by default**.

> **(KO)** 방법론은 자동화가 아니라 **"같은 앱의 서로 다른 플랫폼 빌드를 서로의 오라클로 쓰는"** 차분 분석이다. 이 아이디어는 Electron에 그대로 이식 가능하다: 동일 앱의 웹 버전과 데스크톱 버전이 같은 JS를 실행할 때, 웹에서 막히는 호출이 데스크톱에서 통과한다면 그 지점이 바로 권한 경계의 구멍이다. 단, 논문 스스로 수작업임을 인정하므로 **자동화 여지가 곧 연구 공백**이다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

There is no large-scale dataset; this is an attack paper with case studies.

- **Target:** WeChat (Windows, Android, iOS) plus WeCom, which shares the miniapp framework. The authors state that among the super apps examined, **only WeChat executes miniapps on its desktop platform** — Alipay has a desktop build but no desktop miniapps.
- **API surface referenced:** 985 miniapp APIs in total; testing each on three platforms would be 2,955 runs, which is why layer-up analysis was narrowed by hand to resource-access APIs (microphone, camera, location, contacts, file system).
- **Tooling:** Frida for dynamic hooking, JEB + IDA Pro for decompilation, WeChat's own miniapp development tools and SDKs, several registered accounts, own machines only.
- **What was measured:** not detection rates but *feasibility* — whether each of the three attacks works, and on which platforms. Table 2 reports the result as a platform matrix: all three attacks are ✗ on Android, ✗ on iOS, ✓ on Windows.
- **Case studies:** Table 4 lists **10 real WeChat miniapps** (appIDs partially redacted) with attack method and consequence.

## 4. Results / Key Findings — concrete numbers

**(A1) Miniapp code confidentiality and integrity, from layer below.** The Windows build encrypts the `wxapkg` package; Android and iOS ship it in plaintext. Hooking all crypto APIs revealed a function in `WeChatWin.dll` taking a 32-byte buffer, ciphertext, and an output buffer. Backward slicing showed the 32-byte key is **PBKDF2 output over the appID with the constant salt `"saltiest"`**, and forward slicing showed the **second-last byte of the appID** also derives an XOR key used alongside the AES key. In other words the "secret" is the 18-byte, publicly-assigned appID, and the construction is a non-standard custom algorithm (first 1024 bytes decrypted with Key1, etc.). Consequences from Table 4, all real apps: a **hard-coded passcode in a hotel miniapp usable to unlock rooms**; hard-coded coupon codes leaked from three promotion miniapps; and — after *rewriting* the decrypted code and re-encrypting — phishing overlays that harvest passwords in a short-video miniapp and **bank details in two shopping miniapps**, silent recording of delivery addresses and orders, location tracking through a public-transport miniapp, and message capture in an instant-messaging miniapp.

**(A2) Data integrity of `WeChatApps.data`.** Same broken-key story applied to the Windows-only database that records which miniapps the user may invoke by shortcut, enabling a malicious miniapp to be planted into the user's own launcher.

**(A3) Sandbox escape, from layer up — the RCE.** The Windows file sandbox is a software abstraction over the `wxfile://` scheme implemented in `applet::AppletUtils::getNativePathByJsPath` (address `0xABE042`). The check **replaces `"../"` and `"..\\"` with the empty string, but validates the path *before* the replacement and never re-validates afterwards.** The bypass is the classic collapse: `..././..././..././..././password.txt` becomes `../../../../password.txt` after rewriting. Since Windows adds no access control of its own, a malicious miniapp holding `wx.getFileSystemManager` can then read, write or delete anywhere the user can.

Two paths to code execution are demonstrated. The first writes a payload into `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp` — silent, but needs the super app to be running as administrator, and only fires on reboot. The second needs **neither administrator rights nor a reboot and produces no warning**: overwrite `WeChatXFile`, an executable in WeChat's own installation folder that is loaded on demand to open non-executable documents, then call `wx.openDocument` before it has been loaded into memory. Delivery is a single click on a link or chat message pointing at the malicious miniapp. Beyond RCE the same primitive supports overwriting `hosts` to redirect domains to phishing servers, mass file theft, and ransomware-style encryption; the authors note the distribution reach is a 1.2-billion-user platform.

**Disclosure outcome:** three independent reports to Tencent, one per attack class. **All three were ranked high severity and all earned bug bounties.** A3 has been patched and the authors confirm it no longer works; A1 was patched with VMProtect obfuscation and A2 was in progress at the time of writing.

> **(KO)** 숫자보다 **결함의 모양**이 중요하다: 경로 정규화 순서 오류 하나가 호스트 앱이 제공하던 유일한 격리를 무너뜨렸고, 그 결과가 관리자 권한 없는 즉시 RCE였다. Electron의 `webContents`/`protocol.registerFileProtocol`/커스텀 스킴 핸들러에서 동일한 "치환 후 재검증 누락" 패턴을 찾는 것이 바로 실행 가능한 연구 항목이다.

## 5. How to cite in Related Work

> Desktop ports of hybrid application hosts inherit a threat model their sandbox was never designed for. Wang et al. show that when WeChat's miniapp runtime moved from Android and iOS to Windows, the OS-provided guarantees of process, code and data isolation disappeared and had to be re-implemented inside the host application itself [RootFree, AsiaCCS'24]. Both re-implementations failed: the package encryption protecting third-party miniapp code derives its key from the publicly-assigned appID, and the file-system sandbox validates paths before rather than after collapsing `../` sequences. A malicious miniapp — reachable by a single click on a chat message — can therefore write outside its sandbox, overwrite an executable in the host's own installation directory, and obtain code execution on the desktop without administrator privileges. The same structure characterises Electron applications, which likewise grant web content a privileged local API and likewise rely on application-level rather than OS-level confinement; unlike WeChat, however, they are built by tens of thousands of independent developers rather than a single vendor with a bug-bounty programme.

> **(KO) 위치 잡기:** 이 논문은 **동기 부여용이자 방법론 선례**로 동시에 쓸 수 있다. (a) 동기: "웹 콘텐츠 + 데스크톱 호스트 + 앱 자체 구현 샌드박스" 조합이 실제로 RCE로 이어진다는 검증된 사례. (b) 공백: 저자들이 남긴 자리가 크다 — 전 과정이 **수작업 리버싱**이고, 대상이 **단일 앱(WeChat)**이며, 저자 스스로 **렌더링·로직 엔진 경계는 범위 밖**이라고 명시했다. 즉 "여러 Electron 앱에 자동으로 적용 가능한 발견 기법"은 여전히 비어 있고, 그것이 본 논문(석사 논문)의 자리다. (c) 대조군: 이 논문은 *공격*이고, COINDEF·Inspectron 같은 *도구/방어*와 짝지어 인용하면 "사례는 있으나 자동화가 없다"는 논지가 선명해진다. 주의 — 심사자가 "이건 미니앱이지 Electron이 아니다"라고 말할 수 있으므로, **XWeb 렌더러 + V8 기반 JSCore + 호스트 제공 권한 API**라는 아키텍처 동형성을 한 문장으로 먼저 못 박을 것.

## 6. Caveats / what I could not confirm from the text

- **Grounding:** strong. The full 13-page author-hosted PDF was read; every number above (172/223/230 MB, 985 APIs, 2,955, ~2,000 LoC, 10 case studies, 3 reports, 1.2 B users, 4.3 M miniapps, `0xABE042`, the `"saltiest"` salt) is taken from the paper text.
- The paper is **not about Electron** and never uses the word. XWeb is Tencent's own Chromium-derived renderer, not CEF or Electron's `BrowserWindow`; the architectural equivalence argued above is mine, not the authors'. Do not attribute it to them.
- **No measurement of prevalence.** Three attacks, one vendor, ten hand-picked miniapps. There is no claim about how many miniapps or hosts are affected, and no statistical evaluation of any kind.
- The A1 crypto description is partly inferential even in the paper's own words ("we conclude that **very likely** WeChat uses the miniappID as the key"). Treat the key-derivation detail as reverse-engineered inference, not vendor-confirmed fact.
- Attack A2's mechanics are summarised here only from §4.2's framing; I read §4.2 through the A1 discussion and the tables, not the full A2 walkthrough, so do not quote specifics of the `WeChatApps.data` manipulation without re-reading.
- The WeChat version numbers under test are not recorded in the portion read, and A3 is stated to be patched — any reproduction attempt needs the exact build, which is not given here.
