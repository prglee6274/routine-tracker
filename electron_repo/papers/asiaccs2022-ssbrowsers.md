# Server-Side Browsers: Exploring the Web's Hidden Attack Surface

**Authors:** Marius Musch, Robin Kirchner, Max Boll, Martin Johns (all TU Braunschweig, Germany)
**Venue / Year:** ACM AsiaCCS 2022 (ASIA CCS '22, May 30 – June 3 2022, Nagasaki, Japan), 14 pages
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3488932.3517414) · [author PDF](https://loxo.ias.cs.tu-bs.de/papers/2022_AsiaCCS_SSBrowsers.pdf) · DOI 10.1145/3488932.3517414
**Scope tag:** ADJACENT
**Grounding:** full text read from the TU Braunschweig author-hosted PDF (Sections 1–8 including all tables). All numbers below are from that text.

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It is the first large-scale empirical measurement of *applications that embed a full browser engine and feed it attacker-controlled web content* — the exact architecture of an Electron app — and it quantifies the bundled-engine patch gap that makes that architecture dangerous.

> **한 줄 요약 (KO):** 서버에서 Puppeteer/Headless Chrome 같은 "서버사이드 브라우저"(SSB)를 돌려 공격자가 지정한 URL을 방문하는 사이트가 상위 10만 도메인 중 254곳 확인되었고, 그중 168곳(약 2/3)이 PoC 익스플로잇이 공개된 구버전 브라우저 엔진을 쓰고 있었다 — 즉 "앱에 브라우저 엔진을 번들로 넣으면 자동 업데이트가 끊긴다"는 Electron의 핵심 문제를 서버 쪽에서 실증한 논문.

## 1. Problem, Gap & Hypothesis

Modern pages are JavaScript-rendered, so back ends that need page content can no longer use `curl`/`wget`-style *server-side requests* (SSRs) that only fetch HTML as a string. They increasingly run what the authors coin **server-side browsers (SSBs)**: real rendering engines with JavaScript enabled (PhantomJS, Headless Chrome, Puppeteer) running headless on the server. Link previews in messengers and social networks, search-engine crawlers, and URL-reputation services (Symantec Sitereview, VirusTotal) all summon an SSB to an arbitrary, *user-supplied* URL.

The gap: prior SSR work (Pellegrino et al. 2016; Jabiyev et al. 2021; Orange Tsai 2017) studied SSRF — abusing the requester as a *confused deputy* to reach the internal network. Nobody had studied the other attack: **directly exploiting the requesting engine itself**. The paper's Section 2.1 states this explicitly as the "so far over-looked scenario", with no forged request and no confused deputy — the attacker uses the service as intended and serves a JS exploit from their own page.

The hypothesis is a patch-gap hypothesis, and it is the paper's most transferable idea. Desktop browsers auto-update; embedded engines do not, *by design*. The paper quotes the Puppeteer repository directly: Google sees "Puppeteer as an indivisible entity with Chromium. Each version of Puppeteer bundles a specific version of Chromium — the only version it is guaranteed to work with. […] This is not an artificial constraint." Unattended updates could silently break the automation API, so operators pin — and the engine rots.

Four research questions: RQ1 how many sites trigger SSRs at all; RQ2 how many of those are real browsers; RQ3 which browser and version; RQ4 how many are vulnerable to public exploits.

> **(KO)** 핵심 논리 구조가 Electron 논문과 동일하다. "호스트 앱이 렌더링 엔진을 번들로 소유하면, 엔진 보안 패치가 앱의 릴리스 주기에 인질로 잡힌다." Puppeteer의 "indivisible entity with Chromium" 인용문은 Electron 앱의 Chromium 핀 고정 문제를 설명할 때 그대로 쓸 수 있는 1차 근거다.

## 2. Methodology

Three parts, each independently reusable.

**(a) Blind discovery of SSRs.** The crawler supplies a *unique subdomain* under the authors' control at every plausible injection point and waits to be visited back. Three channels: (i) HTTP headers — a preliminary study over 25 Burp "Collaborator Everywhere" headers found that 98% of header-triggered SSRs came from `Referer` alone and that 24 of the other headers *reduced* crawl success by up to 28%, so only `Referer` was used; (ii) URL parameters — the query strings of all subresource requests are scanned for encoded URLs, plus a fixed list of 22 candidate parameter names (`url`, `uri`, `ref`, `referer`, `host`, `src`, `target`, `preview`, `proxy`, …), each replaced *one at a time* to maximise the chance the back end still processes the request; (iii) HTML forms, filled by a constraint-satisfying form-filling algorithm that inserts the monitoring URL into as many fields as possible. Ethics: no attack payload, a disclaimer page with opt-out at every experiment subdomain, form de-duplication, one submission per form; 5 opt-outs honoured on top of 27 previously blocked domains.

**(b) Bot/human discrimination from a single request.** Because behavioural analysis and CAPTCHAs are unavailable for a one-shot visit, the paper exploits the fact that it *knows when to expect the visit*: a 3-minute window from the trigger. Four supplementary bot indicators each **double** the window — known-crawler UA, HTTP-UA vs `navigator.userAgent`/`navigator.platform` mismatch, `innerWidth > outerWidth` screen inconsistency (not applied to self-declared mobile), and missing `navigator.plugins` (headless Chromium has no PDF Viewer / Native Client entries). With three of four indicators the window becomes 24 minutes. Deliberately conservative: everything is a human until proven otherwise.

**(c) Version fingerprinting without trusting the UA.** A 590-entry list of `window` globals was compiled once from Chrome 89 alpha over an HTTP origin (so no HTTPS-only features); the inline script probes each and returns a 590-bit feature vector, which is mapped back to versions using Mozilla's MDN `browser-compat-data`. Table 1 shows the discriminating power: `WeakRef` present + `AggregateError` absent pins Chrome 84 exactly. Where the three sources (HTTP UA, JS UA, fingerprint) disagree, the paper conservatively takes the **newest** of the three — deliberately under-counting vulnerability.

> **(KO)** (c)가 이 논문에서 논문 주제와 가장 직접적으로 연결되는 부분이다. "번들된 엔진의 실제 버전을 UA 문자열을 믿지 않고 블랙박스로 판정한다"는 기법은 Electron 앱 블랙박스 감사(Inspectron 계열)에 그대로 이식 가능하다. Electron 앱도 `process.versions.chrome`을 앱이 마음대로 감출 수 있으므로, 기능 존재 여부로 엔진 버전을 역산하는 접근이 유효하다. (b)의 "타이밍 + 지표 결합" 설계는 본 논문에는 덜 관련.

## 3. Experiments / Evaluation Setup

- **Target set:** Tranco top 100,000, list generated 2021-03-02.
- **Crawl:** 60 parallel crawlers on Chromium 89.0.4389.72, 2021-03-03 → 2021-03-11 (~1 week), plus one further week of monitoring after the last page visit so that early-ranked and late-ranked sites get equal response time.
- **Per-site depth:** same-site links to depth 10 or 50 pages, whichever first (50 sampled at random if the landing page already has more); 30 s load-event timeout + 3 s for pending requests.
- **Coverage achieved:** ~79% of the 100k successfully visited (failures: ~8% network/DNS, ~4% HTTP error on the front page, 5.5% off-domain redirects discarded, ~3.5% other). **~2.6M pages on ~79k sites.**
- **Injection volume:** 22.2M forms discovered, ~2.5M submitted after de-duplication; 18M modified GET requests across ~5.6M distinct URLs.
- **De-duplication of incoming traffic:** unique request = unique `<target domain, asn, user agent>` tuple; attribution by *target* domain (so a form on a.com POSTing to b.com counts against b.com), ASN-level rather than IP-level de-duplication to stop cloud-hosted third parties dominating, and all `Googlebot` requests explicitly dropped.
- **Vulnerability criterion (deliberately conservative):** a version counts as vulnerable only if *full public details plus a PoC* existed at crawl time. That means Chrome ≤86 = vulnerable; Chrome 87 and 88 are counted **safe** even though the paper argues a skilled attacker could 1-day them from public source diffs.

## 4. Results / Key Findings

- **RQ1:** 168,055 total incoming requests → **11,367 unique**, on **4,850 unique domains** (~6% of the ~79k successfully crawled sites), 8,636 unique IPs, 917 unique ASes. JS-enabled: 7,503 of all requests (4.5%), but 1,973 of unique requests (17.4%) and 760 unique domains (15.7%). Forms were the most productive trigger overall.
- **Timing:** ~35% of all requests arrived within 1 minute of the crawler's visit, covering ~50% of responding domains; only 22% for JS-enabled visitors.
- **RQ2:** after bot filtering, **532 unique requests on 254 distinct domains** were real automated browsers. 433 requests / 192 domains qualified on the plain 3-minute rule; a further 99 requests / 62 domains only via the extended indicator-based windows. Trigger split across the 254 domains: forms **167 (65.7%)**, header 58 (22.8%), parameter 34 (13.4%).
- **Skew to popular sites:** 51 SSBs in the top 10,000 vs an average of 23 per 10,000 across the remaining 90,000; 30 in the top 5,000 and 14 in the top 1,000. Categories (Symantec WebPulse): Technology 69, Business 57, Shopping 25, Education 21, News 14, Other 39.
- **Hosting:** on 63 of 254 domains, requests came from ≥2 ASNs; 20 domains from ≥4; one from 22 different ASNs. Top source ASes were Azure (35 domains), Google Cloud (34), and two AWS ASes (18 each).
- **RQ3 — UA lying is routine:** 532 requests carried 157 distinct HTTP UAs. **13** requests had an outright HTTP-UA vs JS-UA mismatch; a further **124** had matching UAs but a contradicting `navigator.platform` (e.g. claiming iPhone/Windows while reporting `Linux x86_64`) — ~one quarter (137) of unique bot requests lied, and the paper calls this a lower bound. Of the 250 requests where fingerprint ≠ claimed UA, **80% (201) claimed to be *older*** than they were and 41 claimed to be newer. Of the 124 OS-liars, only 12 had a truthful browser version.
- **RQ4 — the headline:** **405 of 532 unique requests (76%)** ran a version vulnerable to a public PoC, covering **168 of the 254 domains (~2 in 3)**. Resulting-UA distribution: Chrome 84 = 150 requests / 68 domains (released 07/20, CVE-2020-6559 with PoC), Chrome 88 = 100 / 83 (the then-current stable, 19% of requests), Chrome 85 = 95 / 39 (CVE-2020-6575), Chrome 86 = 84 / 44 (CVE-2020-16015), Edge 85 = 12 / 10. Chrome 84+85+86 alone are >60% of unique requests. All three cited CVEs work on Linux, need no user interaction, and had public PoCs. Even inside the top 10,000 domains, over half the SSB sites were vulnerable.
- **Self-declared under-approximation:** limited crawl depth, no authenticated crawling, and the conservative 3-minute bot cutoff all mean slower or login-gated SSBs were missed; the authors state the real prevalence is likely higher. They also cannot tell how many SSBs sit inside a sandbox or isolated network, since confirming exploitation was ruled out on legal/ethical grounds.

## 5. How to cite in Related Work

> Applications that embed a browser engine inherit its vulnerabilities but not its update cadence. Musch et al. demonstrated this empirically for *server-side browsers* — headless Chrome and Puppeteer instances that back ends summon to user-supplied URLs — showing that of 254 such deployments discovered across the Tranco top 100k, 168 (roughly two thirds) ran engine versions for which public proof-of-concept exploits already existed, and that the most common version was over eight months old at the time of measurement [Musch et al., AsiaCCS '22]. Their explanation is structural rather than operational: because the automation layer is version-locked to a specific engine build, an unattended engine update risks breaking the host application, so operators pin and the engine ages. The same coupling holds for Electron applications, which ship a pinned Chromium inside the application bundle. Musch et al. also show that self-reported version metadata cannot be trusted in this setting — a quarter of the automated browsers they observed misrepresented their user agent, and 80% of the mismatching ones claimed to be *older* than they were — motivating the feature-probing fingerprint they use to recover the true engine version from the outside.

> **(KO) 논문 내 위치:** 이 논문은 "동기 부여용"과 "방법론 이식용"의 이중 역할을 한다.
> (1) **동기:** Electron 취약점 연구의 정당화 근거 중 가장 반박하기 어려운 것이 "번들 엔진의 패치 지연"인데, 이 논문은 그 주장을 *측정으로* 뒷받침하는 몇 안 되는 top-tier 자료다. Puppeteer 공식 문서 인용("indivisible entity with Chromium")까지 붙어 있어 인용 효율이 높다.
> (2) **방법론:** 590개 전역 객체 feature probing으로 엔진 버전을 블랙박스 판정하는 기법은, Electron 앱이 버전 정보를 감추거나 위조해도 실제 Chromium 버전을 알아내는 감사 도구로 재사용할 수 있다.
> (3) **남긴 빈틈 (여기가 논문의 기여 공간):** 이 논문의 위협 모델은 *엔진 자체의 메모리 버그 → 서버 장악*으로 끝난다. Electron에서는 엔진 버그 없이도 `nodeIntegration`/`contextIsolation` 오설정만으로 렌더러의 JS가 곧바로 로컬 권한을 얻는다 — 즉 **훨씬 낮은 비용의 경로**가 존재한다. 또한 이 논문은 서버 측만 다루므로 데스크톱 앱의 파일시스템·IPC·프리로드 표면은 전혀 측정되지 않았다. "번들 엔진 패치 지연 × Electron 고유의 권한 브리지"의 결합 효과는 아직 아무도 측정하지 않았고, 그 자리가 본 학위논문의 위치다.

## 6. Caveats / what I could not confirm from the text

- **This is a server-side, not a desktop, study.** Nothing in it measures an Electron, CEF, or WebView desktop application. It is admitted as ADJACENT strictly for the shared architecture (host application embeds a pinned engine and feeds it attacker-controlled content) and for the transferable fingerprinting method. Do not cite it as evidence about desktop apps.
- The vulnerability figure is a *version-based* estimate, not demonstrated exploitation — ethically and legally the authors could not fire exploits, so "vulnerable" means "running a version with a public PoC", and the paper cannot say how many targets were additionally sandboxed, containerised, or network-isolated. Section 6 concedes this openly.
- The conservative choices cut both ways and the authors argue they under-count: Chrome 87/88 are scored safe despite being 1-day-able from public diffs; the newest of three UA sources is used; slow and login-gated SSBs are missed.
- Measurement is a single snapshot from **March 2021**. Chrome's release cadence has since moved to four weeks, so the absolute staleness figures should not be quoted as current.
- Appendices A (form-filling pseudocode) and B (per-trigger effectiveness breakdown) were referenced but not read in detail for this note.
- Related work chased for the ledger: Pellegrino et al., "Uses and Abuses of Server-Side Requests" (RAID 2016) and Lauinger et al., "Analysing the Use of Outdated JavaScript Libraries on the Web" (NDSS 2017) are both direct ancestors but fall outside `backfill_from_year=2020`; Stivala & Pellegrino on link-preview trustworthiness (NDSS 2020) is in the window but is a social-engineering study with no code-execution angle. All three are recorded in the ledger's `excluded[]` so they are not re-chased.
