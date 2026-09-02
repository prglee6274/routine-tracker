# Lost in Translation: Exploring the Risks of Web-to-Cross-platform Application Migration

**Authors:** Claudio Paloscia, Kostas Solomos, Mir Masood Ali, Jason Polakis (University of Illinois Chicago) · **Venue / Year:** *Proceedings on Privacy Enhancing Technologies* **2025(4), pp. 24–39** (PoPETs / PETS 2025) · **Links:** [PDF](https://petsymposium.org/popets/2025/popets-2025-0117.pdf) · DOI [10.56553/popets-2025-0117](https://doi.org/10.56553/popets-2025-0117) · artifact <https://github.com/masood/electron-wpt> · CC-BY-4.0

**Scope tag:** PRIMARY *topically* — but **PoPETs is NOT one of the 9 watched venues**, so this is filed as `context_non_venue`, not `in_scope`. See §6.

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** This is the peer-reviewed publication of the differential-testing line the ledger had been tracking only as a UIC master's thesis, and it establishes — with a reusable, released harness — that Electron's *default* enforcement of SOP, CORS, CSP, HTTPS upgrade, X-Frame-Options and Permissions-Policy diverges from Chrome's in ways that are exploitable, which is the strongest available argument that Electron vulnerabilities must be hunted at the *framework-semantics* level and not only in application code.

> **한 줄 요약 (KO):** 브라우저용 웹 코드를 Electron으로 그대로 옮기면 SOP·CORS·CSP·HTTPS 업그레이드·X-Frame-Options·Permissions-Policy가 **기본 설정에서** 브라우저와 다르게(대체로 더 느슨하게) 동작하며, 저자들은 Web Platform Tests를 Electron에 이식한 차분 테스트 프레임워크로 8개 Electron 버전(2021–2024)에서 이를 체계적으로 입증하고 **신규 취약점 4건**을 찾았다.

---

## ⚠ Ledger status — this fires an existing promotion trigger, partially

The ledger's `context_non_venue` entry *"Differential Security Analysis of Cross-Platform Electron Applications"* (Claudio Paloscia, MS thesis, UIC, 2025) carried the note: **"PROMOTION TRIGGER: if Polakis's group publishes this differential analysis at a watched venue (a plausible follow-up to Inspectron), promote to in_scope PRIMARY."**

The group **did** publish it — at **PoPETs 2025(4)**, which is a strong peer-reviewed venue but **not one of the 9 watched venues**. So the trigger fires *halfway*: the work is no longer merely a thesis, it is a peer-reviewed paper with a released artifact and full text, but the venue rule still keeps it out of `in_scope[]`. It is therefore recorded as a **new, richly-grounded `context_non_venue` entry that supersedes the thesis entry**, and the thesis entry is annotated to point here. Handle exactly as ElectroVolt and Electrolint are handled: cite it, be precise about the venue type.

---

## 1. Problem, Gap & Hypothesis

**Problem.** Cross-platform desktop development works by *migrating* web-application code into a native shell. Code written to run "within the confines of a browser, with all the security checks and safeguards that that entails" is redeployed into an environment with direct filesystem and Native API access. The authors ask what breaks in that translation, and name the resulting mismatches **security lacunae** — a term borrowed from linguistics for semantic gaps that cause misunderstanding across contexts.

**Gap.** Prior Electron work is cited as covering two things and stopping: susceptibility to remote code execution (the CCS'22 XRCE line) and misconfiguration/outdated-engine measurement (Inspectron, ref. [5], the same lab). Neither asks whether Electron *itself* enforces the web platform's own security mechanisms the way a browser does. And, decisively: **"unlike traditional browsers, Electron lacks a dedicated testing framework, leaving critical security mechanisms unexplored at scale."** Browsers have Web Platform Tests; Electron has nothing.

**Hypothesis.** Because Electron introduces execution contexts with no browser analogue — `file://` top-level documents loaded via `loadFile()`, WebViews, WebContentViews, nested embeddings such as iframe-in-WebView — the security mechanisms defined for browser contexts will either not apply, apply inconsistently, or apply with different semantics, and developers migrating code will not notice because nothing warns them.

> **(KO)** 이 논문의 갭 진술이 특히 인용 가치가 높다: **"Electron에는 전용 테스트 프레임워크가 없다."** 브라우저에는 WPT가 있는데 Electron에는 없다는 비대칭이, 왜 Electron 프레임워크 자체의 시맨틱을 검증하는 연구가 비어 있었는지를 한 문장으로 설명한다. 논문 서론의 "왜 아직 안 됐는가" 문단에 그대로 쓸 수 있다.

## 2. Methodology

Two phases (Figure 1).

**Phase I — Empirical (manual) testing.** Hand-written, self-contained HTML test pages, each exercising one security header, deployed across a controlled multi-domain/multi-subdomain server. Header variants are selected by URL query string (e.g. `/setcookie?samesite=strict`) so a single template serves many scenarios; each page logs its own pass/fail and POSTs the result to a collection endpoint. Every header is exercised in **three embedding contexts** — top-level, iframe, WebView — and in **two fetch modes** — remote and local. Selenium drives the empirical phase. Table 1 lists 23 headers tested; the security-relevant subset is carried into Phase II.

**Phase II — Retrofitting Web Platform Tests to Electron.** WPT cannot run from `file://`: it needs a live server to resolve `domain[www]`-style placeholders, tests compute resource URLs at runtime, and same-origin/cross-origin policies behave differently locally. The authors solve this with a five-step pipeline:
1. Run WPT under default configuration to trigger the tests.
2–3. Insert a **mitmproxy** between the WPT server and the browser; the proxy captures responses *after* the WPT server has already substituted all placeholders with fully-resolved domains and ports, and stores **only the top-level frames** on the local filesystem — every dependent resource stays server-hosted, because storing e.g. an `X-Frame-Options` sub-resource locally would destroy the very policy the test checks.
4. Add a new `--local-files-path` argument to the WPT runner, plus per-engine request rewriting: in **Electron**, `webRequest.onBeforeRequest` rewrites `file://` to `http://` and fills in missing subdomain/port (Listing 2, Algorithm 1); in **Chrome**, which has no native interception, a purpose-built extension using `declarativeNetRequest` applies ordered rewrite rules (specific patterns before general ones).
5. **Differential analysis**: a regex-based log parser normalises failure kinds (error / fail / timeout) and compares Chrome against Electron run-for-run, with manual validation of edge cases.

**Threat model.** An attacker script *already inside the renderer process*, arriving by one of three realistic routes: (i) a compromised NPM package pulled in at build time, (ii) a dynamically loaded remote script, or (iii) a user socially engineered into importing a malicious file. From there the attacker exploits the lacunae to reach local resources, bypass origin restrictions, or escalate privileges.

> **(KO)** 방법론에서 가장 실용적인 세부 두 가지. (1) **"상위 프레임만 로컬에 저장한다"** — 하위 리소스를 로컬에 저장하면 테스트하려는 정책 자체가 무력화되므로 반드시 서버에 남겨야 한다. 차분 테스트를 직접 구현할 때 반드시 알아야 할 함정. (2) Electron은 `webRequest.onBeforeRequest`로 내부 요청 가로채기가 되지만 Chrome은 안 돼서 확장을 따로 만들어야 했다 — **비교 대상을 동등하게 만드는 비용**이 어디에 드는지 보여준다.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

- **Preliminary/empirical phase:** Electron **30.0.6**.
- **WPT phase: 8 Electron versions with their matching Chromium builds, spanning three years (Table 3)** — 12.0.2/Chromium 89 (Mar 2021), 25.2.0/114 (Jun 2023), 26.2.1/116 (Sep 2023), 27.0.2/118 (Oct 2023), 28.1.4/120 (Jan 2024), 29.1.4/122 (Mar 2024), 30.0.6/124 (May 2024), 31.3.0/126 (Jul 2024).
- **WPT baseline:** repository commit **`d92dadb2`**, pushed **16 Aug 2024**.
- **Tooling:** Selenium (empirical automation), mitmproxy (WPT proxying), custom Chrome extension, custom Electron harness.
- **Host:** MacBook Air M1, macOS Sonoma 14.6. Attack feasibility additionally tested on **Windows**.
- **WPT categories exercised (Table 2), four groups:** *Security* (secure-contexts, mimesniff, referrer-policy, mixed-content, permissions-policy, document-policy, cookie-deprecation-label, browsing-topics); *APIs & Permissions* (fullscreen, geolocation-sensor, navigation-API, credential-management, clipboard, permissions-request/revoke, notifications, idle-detection, server-timing); *Web Components* (shadow-DOM, IndexedDB, service-workers, beacon, captured-mouse-events, payment-method-id, payment-handler, encoding, JS, webauthn, URL, XHR); *User Interaction & Media* (screen-capture, picture-in-picture, screen-details, bluetooth, remote-playback, audio-output, PNG, device-memory, contacts, payment-request, background-sync).
- **Real-world study: 30 Electron applications**, randomly selected from the official Electron showcase across popularity and functionality tiers. Launched in debugging mode and instrumented with **Puppeteer** to extract runtime resources, explicitly *"following the methodology proposed by Ali et al. [5]"* (Inspectron). Measured: local-file inclusions (iframes, scripts), local files inside WebViews, and CSP deployment.

**What was measured:** whether each mechanism is enforced identically in Chrome and Electron across the three embedding contexts and two fetch modes, and — where they diverge — whether the divergence is exploitable.

> **(KO)** 평가 규모 요약: **Electron 8개 버전 × 3년치**, WPT 4개 카테고리, 실제 앱 **30개**. 실제 앱 분석은 Inspectron과 같은 방법론(Puppeteer + 디버깅 모드)을 명시적으로 재사용했다 — 같은 연구실이라 재현이 쉬웠다는 점도 방법론 선택의 현실적 이유로 참고할 것.

## 4. Results / Key Findings — concrete numbers

**Table 4 — eight mechanism divergences. Four are new (★), three are known-and-unfixed (✗), one is fixed (✓):**

| Mechanism | Vulnerability | Impact | Affected | State |
|---|---|---|---|---|
| SOP | Local-file privileges | Access to sensitive user data and credentials | All | ★ new |
| CORS | Local-file bypass | Data exfiltration via arbitrary cross-origin requests | All | ★ new |
| CSP | Local-file enforcement | No restriction on local file execution or verification | All | ★ new |
| HTTPS | WebView enforcement | MitM via embedded insecure content | All | ★ new |
| X-Frame-Options | WebView enforcement | Clickjacking → unauthorised interaction, data exfiltration | All | ✗ known |
| Permissions-Policy | WebView inheritance | Embeddings inherit sensitive API permissions | All | ✗ known |
| Cookies | Injection of invalid characters | Session fixation, cookie-jar desynchronisation | All | ✗ known |
| Cookies | SameSite attribute | CSRF, session manipulation | 12.0.2 only | ✓ fixed |

Note that **six of the eight are marked "All"** — they are present in every one of the eight versions tested across three years, i.e. they are design properties, not regressions.

**The core finding — Electron treats every local file as the same origin.** Chrome assigns `file://` documents a **null origin**, so a page cannot programmatically read other local files. Electron treats *all* local files as one origin, so an attacker-controlled HTML file dropped on disk inherits the application's origin and privileges, **with no user interaction once the app is launched**. Listing 3 gives the working chain: set `window.location.href = "ftp://user:psw@ftp.server"`, wait 5 s, then create an `<iframe src="file:///Volumes/ftp.server/malicious.html">`. Electron **permits automatic FTP connections** — "an attack vector explicitly blocked in modern browsers." Consequences named: read other local files; `fetch()` system files; recover the logged-in username from log files and application data that embed absolute paths; reach browser cookies and SSH keys.

**Platform asymmetry, tested on both OSes.** On **Windows** the attack is *stealthy* — Electron opens the FTP connection with no system-level notification. On **macOS** an FTP connection triggers a system prompt requiring explicit user approval, which the authors describe as a real but partial limitation. They argue the attack remains highly effective given Windows' share.

**CORS.** Cross-origin requests from a local file **fail in Chrome** (no `Access-Control-Allow-Origin`) and **succeed in Electron**. Local execution contexts are simply exempt. Combined with `nodeIntegration: true` WebViews — which the authors note is common, citing Inspectron — an attacker bypasses the restriction *without needing any application-specific vulnerability*.

**CSP.** There is no CSP directive for `file://` URLs anywhere in the web platform, and Electron does not extend enforcement to local files. **A strict CSP in an Electron app applies only to remotely-served content**; local files execute scripts and load resources with no policy-based restriction whatsoever.

**HTTPS.** Electron performs **no automatic HTTP→HTTPS upgrade** — it follows exactly the scheme given to `loadURL()` — and does **not natively enforce HSTS** (developers must do it in a preload script). Electron **WebViews do not enforce Mixed Content Blocking**, so injecting an `<iframe>` at an `http://` URL renders with no warning and no notification.

**Permissions.** With no `setPermissionRequestHandler`, Electron **grants all permission requests indiscriminately**. The `Permissions-Policy` header *is* enforced, but only when the top-level document is served from a remote origin — local files are unregulated. Worse, OS-level permissions are granted **to the whole application, not per web origin**, so once the user allows the camera or filesystem, *every* embedded page and WebView inherits it. The paper cites the Signal plaintext-encryption-key incident as an illustration of what filesystem access can reach.

**X-Frame-Options.** Not applied to WebViews or WebContentViews. `X-Frame-Options: DENY` blocks a standard iframe and does **not** block a WebView. The authors are careful here: this is **not** an unintended flaw — prior disclosures confirm Electron deliberately bypasses XFO in WebViews for developer flexibility.

**Cookies.** Both Chrome and Electron store cookies containing non-printable characters above ASCII 127, contrary to spec — but `document.cookie` then returns an **empty string**, producing **cookie-jar desynchronisation**. A subdomain attacker (`attacker.example.com`) injects a malformed cookie for `example.com`; the Electron app then rejects the legitimate session cookie and accepts the crafted one → session fixation. Separately, **Electron 12 fails to enforce SameSite** entirely.

**Real-world deployment study, n = 30 (Table 5):**
- **25 of 30** load their main renderer from a `file://` URL. Split: **Local→Local 17**, **Local→Remote 8**, Remote→Remote 5.
- Among the 8 that mix, **3** pull in third-party analytics, consent management, advertising and federated auth (Google SSO); **2** embed remote content via iframes (one from Cookiebot, one first-party).
- **5** apps deploy at least one WebView; **3 of those 5 load content directly from the filesystem into the WebView.** Named example: the browser app **Biscuit**, where an attacker delivering a crafted `file://` link via in-app message, email or Slack gets it rendered in a WebView with full app privileges.
- **Figma** is named as a case of local-main-interface + first- and third-party remote fetches — "bypasses browser security controls such as the Same-Origin Policy."
- **12 of 30** deploy a CSP; all 12 are judged insufficient because CSP cannot regulate local content. **Cacher** wrote all its directives against the **unsupported `file:` scheme**, so the whole policy is silently ignored.
- **VS Code** is the one positive example: it disables `file://` and registers a custom `vscode://` scheme, then writes its CSP against that — effective, but the authors stress how much extra effort it takes.

**Disclosure outcome.** Reported to Cacher (CSP misconfiguration) and to the Electron team with a technical report and PoCs. **Electron acknowledged and declined**: the behaviours "align with Electron's intended security model," `file://` handling "is intentional and documented," and developers are expected to avoid such deployments or define their own security models — *the same response Inspectron received.*

**Proposed countermeasure.** A new CSP directive, **`file-src`**, with keywords `none` (block all local files), `self` (only the system-protected install directory, e.g. `C:\Program Files\`), `sha256-` (hash-pinned), `nonce-` (base64 nonce), `path-` (explicit absolute paths). Listing 4 shows it composing with existing directives without conflict. The authors state they plan to propose it for adoption.

> **(KO)** 논문에 인용할 만한 숫자: **30개 중 25개가 `file://` 메인 렌더러**, **WebView 사용 5개 중 3개가 로컬 파일을 WebView에 로드**, **CSP 배포 12개 전부 불충분**, **8개 버전·3년에 걸쳐 6개 결함이 "All"**. 그리고 가장 논쟁적인 대목: **Electron 팀이 "의도된 동작"이라며 수정을 거부했다.** Inspectron 때와 동일한 반응이라는 점이 중요하다 — 프레임워크가 고치지 않는다면 앱 단위 발견 연구의 필요성이 오히려 커진다.

## 5. How to cite in Related Work

> Electron's divergence from browser security semantics is not incidental but architectural. Paloscia et al. retrofit the Web Platform Tests suite to Electron and run it differentially against Chrome across eight Electron releases spanning 2021–2024, identifying eight mechanism-level divergences — six of them present in every version tested [PoPETs'25]. Four are newly reported: Electron assigns all local files a single shared origin rather than Chrome's null origin, exempts local execution contexts from CORS, provides no CSP directive capable of regulating `file://` content, and omits both HTTPS upgrading and mixed-content blocking inside WebViews. Their study of 30 showcase applications finds 25 loading their main renderer from `file://`, three of the five WebView-using applications loading local files into those WebViews, and all twelve deployed Content Security Policies unable to constrain local content. The Electron maintainers declined the report as consistent with the framework's intended security model.

> **(KO) 취약점 *발견* 논문 대비 위치:** 이 논문은 **차분 테스트(differential testing)** 라는 네 번째 발견 계열을 차지한다. 기존 지형은 — Inspectron(블랙박스 설정 감사), NDSS'23 DOM-tree type / COINDEF(방어), Buzz to Boom(방향성 퍼징) — 이었고, 여기에 "브라우저를 오라클로 삼아 프레임워크 시맨틱의 이탈을 찾는" 방식이 추가된다. 두 가지로 활용할 것.
> 1. **경쟁 방법론으로 정직하게 배치.** 만약 논문이 차분 테스트를 쓴다면 이 논문이 직접적 선행 연구이므로 반드시 델타를 명시해야 한다 — 예: 이 논문은 *프레임워크*의 정책 시맨틱을 검사하지, *애플리케이션*의 sink를 검사하지 않는다. 30개 앱 분석도 저자들 스스로 정적 리소스 추출에 그쳤다고 인정한다("런타임 권한 요청, API 수준 접근, WebView 실행 흐름의 동적 분석은 본 연구 범위 밖").
> 2. **남겨진 갭이 명시적이다.** 저자들이 결론에서 **"웹 코드의 Electron 이관을 자동화하고 보안 lacunae를 보완하는 코드 리트로핏 프레임워크"** 를 유망한 미래 연구로 지목했다. 논문이 그 방향이 아니더라도, "저자들이 직접 열어 둔 갭"으로 인용할 수 있다.
> 3. **`file://` 단일 오리진 결과는 이 repo의 SiYuan/Notesnook/DbGate/Vikunja XSS→RCE 관찰과 곱해진다.** 그 앱들의 렌더러가 `file://`에서 로드된다면, XSS 하나가 얻는 것은 앱 컨텍스트 실행만이 아니라 **전체 로컬 파일 오리진**이다. 이 논문이 그 증폭 계수를 정당화해 준다.

## 6. Caveats / what I could not confirm from the text

- **Venue rule.** PoPETs is peer-reviewed and well-regarded but **is not among the 9 watched venues** (USENIX Sec, IEEE S&P, NDSS, CCS, ACSAC, RAID, ESORICS, AsiaCCS, DSN). Per repo precedent (Electrolint → *Array* journal; ElectroVolt → Black Hat) this stays in `context_non_venue`. Do **not** cite it as a top-4 security-conference paper.
- **Grounding.** Full text fetched and read for: Abstract, §1 Introduction, §2 Background (all three subsections), §3 System Overview (both phases), §4 Experimental Evaluation in full including Tables 3, 4 and 5 and all mechanism subsections, §5 Discussion in full including disclosures and the `file-src` proposal, and the opening of §6 Related Work plus §7 Conclusions header. **Not read:** the body of §6 Related Work, Appendix A (the per-application configuration breakdown), and the references list beyond ref. [1].
- **No aggregate WPT pass/fail counts.** The paper reports *which* mechanisms diverge (Table 4) but the portion read contains **no count of how many WPT tests were executed or how many failed per Electron version**. If the thesis needs "N of M tests diverged," that number is not in the text as read — check Appendix A or the artifact repository.
- **Table 5's rows do not sum to 30 in one place.** Text says 25 apps use a local origin; Table 5's origin rows are 17 + 8 + 5 = 30, so Local→Local (17) + Local→Remote (8) = 25 reconciles. Recorded because it looks like a discrepancy at first glance and is not one.
- **Author affiliation is uniformly UIC** for all four authors; **Mir Masood Ali is also first author of Inspectron** (USENIX Sec '24, already `in_scope`), and Inspectron is ref. [5] throughout. Treat the two as one research programme when discussing independence of evidence.
- **The Signal encryption-key example is cited from a BleepingComputer article** (ref. [2]), not from the authors' own measurement. Do not present it as this paper's finding.
- **The `file-src` directive is a proposal only** — not implemented, not evaluated, not standardised. The paper says the authors "plan to propose" it. No adoption claim.
- **Electron versions tested stop at 31.3.0 (Jul 2024).** As of this note (Sep 2026) Electron is many major versions further along, and the 2026 upstream advisory batches already in this ledger (CVE-2026-34764..34781, CVE-2026-70597..70612) postdate the study entirely. The "Affected Versions: All" column should be read as "all eight versions tested, 12.0.2 through 31.3.0," not as a claim about current Electron.
