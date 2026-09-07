# Too Much of a Good Thing: (In-)Security of Mandatory Security Software for Financial Services in South Korea

**Authors:** Taisic Yun (Theori Inc. / KAIST), Suhwan Jeong (KAIST), Yonghwa Lee (Theori Inc.), Seungjoo Kim (Korea University), Hyoungshick Kim (Sungkyunkwan University), Insu Yun (KAIST), Yongdae Kim (KAIST)
**Venue / Year:** 34th **USENIX Security Symposium** ('25), Seattle, WA, August 2025
**Links:** [USENIX presentation page](https://www.usenix.org/conference/usenixsecurity25/presentation/yun) · [PDF (open access)](https://www.usenix.org/system/files/usenixsecurity25-yun.pdf) · [Prepub PDF (cycle 1)](https://www.usenix.org/system/files/conference/usenixsecurity25/sec25cycle1-prepub-286-yun_0.pdf) · Survey instrument: <https://zenodo.org/records/14738628>
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the *mirror image* of Electron — instead of putting a browser inside a privileged desktop process, KSA 2.0 puts a privileged desktop process behind a `localhost` web API that any web page can call — and the paper shows that the resulting web-content→local-privilege bridge produces exactly the Electron failure catalogue (origin/trust confusion, RCE by chaining exposed APIs, security-control bypass), which makes it the strongest available evidence that the vulnerability class is *architectural*, not Electron-specific.

> **한 줄 요약 (KO):** 한국의 금융·공공 서비스에서 사실상 강제 설치되는 보안 프로그램 묶음(KSA 2.0)은 브라우저 샌드박스를 우회하려고 **로컬 서비스 + 웹 API** 구조를 택했고, 그 결과 웹 페이지가 고권한 시스템 동작을 호출할 수 있게 됐다. 7개 제품에서 **19개 취약점**(키로깅, MITM, 개인키 유출, RCE, 기기 핑거프린팅)을 발견했고, 사용자 연구로 **은행 이용자의 97%가 설치**, **1인 평균 9.06개**가 깔려 있으며 절반 이상이 2022년 이전 구버전임을 보였다.

**Grounding:** written from the **complete open-access prepublication PDF** (USENIX cycle-1 prepub, `sec25cycle1-prepub-286-yun_0.pdf`) — read in full through §8 Related Work and §9 Conclusion. All figures below are read off the paper text. **The word "Electron" does not appear in the paper**; every Electron connection drawn in §5 below is my extrapolation and is marked as such.

## 1. Problem, Gap & Hypothesis

South Korea has, since the 1997 e-government initiative, legally mandated locally-installed security software for Internet banking and public services — the "Korea Security Applications" (KSA) suite: firewall, anti-keylogging, anomaly detection, and certificate management. **KSA 1.0 used ActiveX**; when Microsoft began deprecating ActiveX in 2015, vendors did not abandon the architecture, they *re-implemented it over web protocols*.

That re-implementation is the paper's whole subject. KSA 2.0 runs as a **local server on `127.0.0.1`**, auto-started at boot, holding ports open and waiting for HTTPS/WebSocket requests from web pages. A bank's page script calls KSA's "API" over `localhost` to do the things browsers forbid: read the file system, hook the keyboard device driver, read certificates, enumerate hardware. The authors state the design intent plainly: KSA "**needs to violate the browser's security model and bypass the browser's sandbox**" in order to work at all.

The gap: prior work on KSA is either a decade old (Kim et al. on KSA 1.0) or non-academic (Palant's technical blog series). Nobody had systematically modelled *who* can reach these APIs, nor measured how many of them are installed on real machines.

Hypothesis, implicitly: if a local process trusts web pages more than the browser does, then the attacker set for that process is the attacker set of the *web*, and the browser's protections do not apply.

> **(KO)** 이 §1의 논리 구조가 학위논문 문제 정의와 사실상 동형이다. Electron은 "브라우저를 데스크톱 권한 안에 넣어서" 경계를 무너뜨리고, KSA 2.0은 "데스크톱 권한을 브라우저가 부를 수 있는 API로 노출해서" 같은 경계를 무너뜨린다. **양쪽 모두 원인은 '웹 콘텐츠에 로컬 권한을 준다'는 설계 결정 자체**라는 점을 논문 서론에서 대조군으로 쓰면 좋다.

## 2. Methodology

**A threat-model-first analysis, then three complementary techniques.**

The authors first decompose KSA's access control into three factors — **bind address** (`127.0.0.1` vs. wildcard `0.0.0.0`), **supported protocols** (HTTPS/WSS vs. plain HTTP), and **origin verification** (the HTTP `Origin` header) — and derive four attacker models from them (§3):

| | Attacker | Enabled when |
|---|---|---|
| **T1** | **Remote attacker** — reaches KSA from the public Internet | KSA binds the wildcard address |
| **T2** | **Malicious website** — any page running JS | KSA does not check `Origin` |
| **T3** | **Man-in-the-Middle** — e.g. public Wi-Fi, via SSL stripping | KSA accepts plain HTTP; forged `Origin` |
| **T4** | **Origin spoofer** — compromised renderer or XSS on a whitelisted site | Origin check exists but is only as strong as the renderer |

They explicitly **exclude** the full-chain browser exploit (renderer + sandbox escape) as unrealistic, and justify T4 by citing that renderer exploits vastly outnumber sandbox escapes (**196 vs. 5 in 2022**).

They also draw the comparison that matters for this thesis (§3.3): KSA is **weaker than a browser extension**, because an extension's origin check is enforced by the browser inside its own sandbox, whereas KSA's rests on an HTTP header that a compromised renderer controls.

Analysis techniques (§4.2): **black-box testing** of vendor JS and developer test pages; **reverse engineering** (defeating Themida etc. with `unlicense`, falling back to a debugger when proprietary protection held — PRODUCT E was never fully reversed); and **fuzzing** with **AFLnet** modified to mutate at the *application* layer rather than the SSL layer, plus **AFL++** after patching binaries to swap socket I/O for stdio.

Dataset (§4.1): the **mandatory** KSA programs of South Korea's **17 top-tier banks**, anonymised at the request of a Korean government agency as **PRODUCT A–G** (7 products). Some are also used by `gov.kr` and `mma.go.kr`.

> **(KO)** 방법론에서 훔쳐올 만한 것: **접근제어 요소(바인드 주소/프로토콜/오리진 검증) → 위협모델 표**로 가는 전개. Electron 앱에 그대로 대응시키면 `nodeIntegration` / `contextIsolation` / `sandbox` / `webSecurity` / `setWindowOpenHandler` 조합 → 공격자 모델 표가 된다. Inspectron(USENIX '24)이 설정값을 *수집*했다면, 이 논문은 설정값을 *위협모델로 번역*한다 — 학위논문에서 그 번역 단계를 명시적으로 만드는 것이 기여가 될 수 있다.

## 3. Experiments / Evaluation Setup

Three separate evaluations:

**(a) Vulnerability analysis** — 7 mandatory KSA products (A–G) from all 17 top-tier Korean banks, categorised into four functions (Certificate management, anti-Keylogging, Firewall, Anomaly detection). Measured: which of T1–T4 each product is exposed to; how many vulnerabilities; the impact of each.

**(b) Online survey** — **400 participants** recruited via Embrain, demographically matched to Korean national Internet-user statistics (52% male / 48% female; age bands 20s 21.5% → 60+ 9.25%). Chi-square goodness-of-fit confirmed no significant difference from population parameters for gender (χ²=0.64, df=1, p>0.99) or age (χ²=2.31, df=4, p>0.99). Two sections: knowledge/understanding, and awareness/experience. Three pilot studies; 10-minute instrument.

**(c) Desktop analysis** — **48 participants** who voluntarily installed **HoaxEliminator** (구라제거기), a tool that enumerates and removes unnecessary Internet programs, to *count* installed KSA rather than rely on self-report. Demographically skewed (70.83% male; 91.67% in their 20s), recruited through the institution's bulletin board and social networks.

Also measured, as ecosystem evidence: the **installed version and release date** of PRODUCT E as distributed by nine different institutions (Table 5), and Root-CA handling per product (Table 2: whether the root CA cert is fixed or generated at runtime, and whether it is removed on uninstall).

> **(KO)** 평가 설계에서 배울 점은 **취약점 분석 + 사용자 연구 + 실제 설치 실태 측정**의 삼각 구성이다. Electron 논문 대부분은 첫 번째만 한다. 학위논문에서 "실제로 얼마나 많은 Electron 앱이 위험 설정으로 배포되어 있는가"를 패키지 스캔으로 붙이면 같은 삼각형을 만들 수 있고, HoaxEliminator처럼 **기존 도구를 계측기로 재활용**한 방식은 저비용 대안으로 참고할 만하다.

## 4. Results / Key Findings

**19 vulnerabilities across 7 products** (Table 4), grouped under four design issues:

**(1) Threat-model inconsistency (§5.1).** The anti-keylogging products are the sharpest case: PRODUCT D and PRODUCT E hook the keyboard *device driver*, encrypt keystrokes, and hand them to the **web page** to decrypt. Because the page is trusted, an attacker can instruct KSA to use **symmetric** encryption — sharing the key with the page — or to **disable encryption entirely**, converting the anti-keylogger into a **system-wide keylogger** that captures input from *other web pages* (SOP violation) *and from other programs* (sandbox violation). The authors note the design assumes an adversary who can log keystrokes but cannot reach the web page — which is backwards, since keylogging requires the higher privilege. Vendors **acknowledged the design flaw but declined to remove it**, because deployed services depend on it. The same trust also exposes **deactivation APIs**: an attacker simply turns the protection off (anti-keylogging in D and E; firewall session management and anomaly-detection bypass in E).

**(2) TLS model violation (§5.2).** Because a real CA will not issue a certificate for `127.0.0.1`, **every** KSA installs **its own root CA** into the user's trust store. Table 2: **five of seven** products do not remove that root CA on uninstall. For **PRODUCT E** the authors reverse-engineered the installer, recovered the **encrypted root-CA private key embedded in the binary**, and used it to **sign a certificate for `google.com`** — a working MITM against any machine that has *ever* installed that product, persisting after uninstallation. The authors also establish that the justification for this design is obsolete: browsers dropped mixed-content restrictions for `localhost`.

**(3) Sandbox violation → RCE (§5.3).** **PRODUCT B** was chained to full remote code execution from a malicious web page, in three steps: (i) call KSA's encryption API to produce encrypted malware; (ii) abuse flawed error handling in the `SetLogoPath` API — files **≤256 bytes bypass the digital-signature validation** and are written to a *fixed* location and not deleted — to plant the payload where the attacker can name it; (iii) call `DecFileData`, which decrypts an input file to an **unvalidated output path**, to write the decrypted malware into a sensitive location (e.g. the Start Menu Programs folder). Separately, fuzzing found **5 memory-corruption bugs** (Table 3) — 1 buffer overflow in PRODUCT F (AFL++), and in PRODUCT G 2 buffer overflows, 1 null dereference and 1 segmentation fault (AFLnet), all on Linux. The authors stress both consequences: exploitation needs **no browser vulnerability at all**, and even a *crash* is a security event, because it silently disables the protection.

**(4) Privacy (§5.4).** The anomaly-detection product (E) collects NAT IP, MAC address, IP, VPN IP, OS version + identification number + boot UUID, hardware serial numbers, firewall configuration and remote-access settings. It encrypts this to the vendor's public key — but the vendor's **publicly reachable, unauthenticated developer test page works as a decryption oracle**. Certificate-management products (A, B, C) expose the accredited certificate's fields, including the **user's legal name in plaintext to the web**, plus a trackable serial number — defeating incognito mode.

**Survey (n=400):** **97.35%** of banking users had installed KSA (0% "not installed"; 2.65% unsure); **100%** of the 378 with banking experience used a top-tier bank covered by the analysis. **59.25% did not understand what KSA does.** Only **14.75%** knew it runs continuously as a background service (60.75% thought "only while using the service"). **Not one participant** identified the anomaly-detection/fingerprinting capability that most banks mandate. On uninstallation: 57% use the Windows uninstaller and 8.75% the built-in one — **neither removes the root CA**; only 10.5% used a method capable of complete removal; **20.75% had never uninstalled anything**. The authors conclude **86.5%** remain exposed even after attempting removal. Of 17 banks, **11 require KSA to log in**, but **13** use "installation is required"-style wording.

**Desktop analysis (n=48):** all but two participants had KSA installed; **mean 9.06 total KSA programs per machine (SD 6.96)**, max **24**; mean **4.1** (SD 2.92) of the specific products studied. **27 of 48** were running versions from **2022 or earlier**; the oldest install dated **15 February 2019**. Version fragmentation is structural, not accidental — Table 5 shows PRODUCT E shipped by nine institutions at nine different versions spanning **2019-02-20 to 2023-08-22**, because the *service provider*, not the vendor, distributes the software.

**Disclosure (§5.5).** Closed meeting with FSI, KISA and KISIA in early 2024; embargo to May 2025. Patching is structurally hard because a fix requires changing **both** the binary **and** the JavaScript on every service provider's site. One vendor "fixed" a reported bug by **blocking the `localhost` origin used in the PoC** instead of whitelisting its client domains — stopping the PoC while leaving remote exploitation intact.

> **(KO)** 학위논문에 가장 잘 쓰일 숫자 세 개: **(1) 렌더러 익스플로잇 196 vs 샌드박스 탈출 5 (2022)** — "렌더러가 이미 털린 상태"를 현실적 위협모델로 정당화하는 근거로 그대로 인용 가능. **(2) 1인당 평균 9.06개 설치, 27/48이 2022년 이전 버전** — 데스크톱 보안 소프트웨어의 패치 지연이 실측된 드문 사례. **(3) 7개 중 5개가 언인스톨 후에도 루트 CA를 남긴다** — "제거해도 남는 공격면"이라는 논점.

## 5. How to cite in Related Work

> The risks of granting web content privileged access to the local system are not confined to embedded-browser frameworks. Yun et al. analyse Korea Security Applications (KSA) 2.0, a suite of security programs effectively mandated for South Korean banking and public services, which — after the deprecation of ActiveX — re-implemented privileged host access as a local HTTP/WebSocket server that web pages invoke directly [USENIX Sec '25]. Because that server sits outside the browser sandbox and authenticates callers only by the HTTP `Origin` header, its trust boundary is strictly weaker than a browser extension's: a compromised renderer or an XSS on any whitelisted site suffices to reach it. Across seven mandatory products the authors report 19 vulnerabilities, including a chained arbitrary-file-download and arbitrary-file-move that yields remote code execution from a malicious web page, an anti-keylogging component that can be reconfigured into a system-wide keylogger, and a root-CA private key recoverable from the installer. Complementary user studies (n=400 survey, n=48 desktop analysis) find 97% installation among banking users, an average of 9.06 such programs per machine, and more than half of measured machines running builds from 2022 or earlier.

> **(KO) 학위논문에서의 포지셔닝:** 이 논문은 **경쟁 연구가 아니라 문제의 일반성을 입증하는 증거**로 쓰는 것이 맞다. 세 가지 용도가 있다. (1) **동기 강화**: "웹 콘텐츠 + 로컬 권한 = 취약" 이라는 명제가 Electron이라는 특정 프레임워크의 버그가 아니라 **아키텍처 결정의 결과**임을 다른 구현체에서 독립적으로 확인해준다. Electron에 국한된 연구라는 심사 지적에 대한 방어 논거. (2) **위협모델 템플릿**: T1–T4(원격/악성사이트/MITM/오리진 스푸퍼)는 Electron에 거의 그대로 이식된다 — 특히 T4는 `contextIsolation: false`인 앱에서 렌더러 XSS가 preload 브리지를 장악하는 시나리오와 정확히 대응하며, "렌더러 침해는 현실적이다"라는 전제를 196:5 수치로 정당화해준다. (3) **남는 갭**: 이 논문의 대상은 **브라우저 밖의 네이티브 로컬 서버**이지, **앱 안에 내장된 브라우저**가 아니다. KSA는 `Origin` 헤더라는 (약하지만) 명시적 경계라도 갖고 있는 반면, Electron의 preload/`contextBridge`는 그런 경계가 아예 없고 노출면이 개발자가 손으로 쓴 IPC 채널이다. 또한 분석 대상이 **7개 제품**의 수작업 리버싱이라 자동화·확장 가능한 발견 기법은 제시되지 않는다 — 학위논문이 채울 자리가 바로 거기다.

## 6. Caveats / what I could not confirm from the text

- **Electron is never mentioned.** A keyword scan of the full text returns no hit for "Electron", "Chromium", "CEF" or "WebView". Every bridge to this thesis in §5 is my extrapolation from the shared "web content → local privilege" structure, not the authors' claim.
- **Products are anonymised** (PRODUCT A–G) at the request of a Korean government agency, so the findings **cannot be tied to named vendors** and cannot be independently re-verified against specific software.
- **Table 1 renders as a grid of unlabelled marks in the extracted text.** I can state the *columns* (bind address: localhost / wildcard+filtering / wildcard; protocol: SSL / none; origin check; T1–T4) and the product/type letters, but **I cannot reliably report which specific product falls into which cell.** Do not cite a per-product threat-model mapping from this note without re-reading the rendered PDF.
- **Vulnerability counts per product** come from Table 4, whose "Patched / Mitigated" status columns are also mark-based; I record 19 vulnerabilities in total and the impact column text, but **not** which individual items were fully patched versus merely mitigated.
- The **memory-corruption bugs were found on Linux** builds (Table 3). The paper does not state whether the same bugs affect the Windows builds that the overwhelming majority of Korean users actually run.
- **Desktop-analysis sample is not representative**: 48 participants, 70.83% male, 91.67% aged 20–29, self-selected by willingness to install a tool — the authors flag this themselves. The 9.06 average should be quoted with that caveat attached.
- I read the **cycle-1 prepublication PDF**, not the final camera-ready. Section numbering and figures should be re-checked against `usenixsecurity25-yun.pdf` before citation.
- Appendices A–D (historical background, extra survey responses, HoaxEliminator sample output, additional issues) were **not** read.
