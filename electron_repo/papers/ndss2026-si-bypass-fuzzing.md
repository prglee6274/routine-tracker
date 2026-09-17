# Are your Sites Truly Isolated? Automatically Detecting Logic Bugs in Site Isolation Implementations

**Authors:** Jan Drescher, David Klein, Martin Johns (all TU Braunschweig)
**Venue / Year:** Network and Distributed System Security Symposium (NDSS) 2026 — 23–27 February 2026, San Diego, CA
**Links:** [paper page](https://www.ndss-symposium.org/ndss-paper/are-your-sites-truly-isolated-automatically-detecting-logic-bugs-in-site-isolation-implementations/) · [PDF](https://www.ndss-symposium.org/wp-content/uploads/2026-f902-paper.pdf) · DOI 10.14722/ndss.2026.240902 · [artifact](https://github.com/si-bypass-fuzzing) · [Zenodo](https://doi.org/10.5281/zenodo.17750615)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It is the first automated *discovery* method aimed squarely at the renderer→privileged-process IPC boundary under a **compromised-renderer** threat model — the same boundary and the same threat model as an Electron renderer that has been taken over by XSS and is now talking to the main process.

> **한 줄 요약 (KO):** 렌더러가 이미 장악되었다고 가정하고, 렌더러가 특권 프로세스로 보내는 IPC 메시지를 후킹·변조하는 퍼저와 프로세스 단위 유출 탐지 오라클(leak/process sanitizer)을 만들어 Chrome·Firefox의 Site Isolation 우회 버그 4건(그중 1건은 CVE-2024-9392, 현상금 $8,000)을 찾아냈다. 브라우저 논문이지만 "렌더러 침해 이후 IPC 경계"를 자동으로 공격한다는 점에서 Electron 논문에 가장 가까운 방법론이다.

---

## 1. Problem, Gap & Hypothesis

Site Isolation (SI) puts all content of one *site* (scheme + eTLD+1) into its own sandboxed renderer process, so that a memory-corruption bug in the renderer cannot reach another site's data. Its correctness therefore rests entirely on the **privileged browser process**: that process must (a) track which renderer belongs to which site, and (b) re-check the origin/URL of every request a renderer makes, because any check performed *inside* the renderer can be removed by a renderer compromise. When either fails, the result is an **SI bypass** — cross-site data theft, cookie theft, or Universal XSS. SI shipped in Chrome in 2018 and Firefox in 2021 (Safari was implementing it at the time of writing), and both vendors rank SI bypasses in the second-highest tier of their bug-bounty programmes.

The gap: SI bypasses are *semantic* bugs. They produce no crash, so AddressSanitizer-style oracles cannot see them, and prior browser fuzzing targeted the DOM engine, the JIT, or memory bugs in IPC endpoints — not the policy logic. Two research questions follow: **RQ1** how can a cross-process data leak be reliably *detected*, and **RQ2** how can the *arbitrary malicious behaviour* of a compromised renderer be modelled so the bug is triggered in the first place.

*(KO) 핵심 갭은 "크래시가 없는 의미론적 버그"라는 점이다. 샌드박스 자체가 아니라 샌드박스를 관리하는 특권 프로세스의 정책 로직이 표적이며, 이것이 Electron의 main 프로세스 역할과 정확히 대응된다. 저자들은 렌더러 침해를 전제(presuppose)하고 그 다음 단계만 자동화했다.*

## 2. Methodology

Three parts, derived from a prior systematic study of real bypasses:

1. **Vulnerability analysis (§III).** All Chromium bug-tracker entries tagged `Internals>Sandbox>SiteIsolation`, the Firefox SI meta-bugs, and every NVD CVE whose description mentions Site Isolation were read by hand — 1,328 reports examined, of which **39** were genuine SI bypasses (listed in the appendix Table V). They fall into three classes: **(1) missing checks** (most common — the browser process never verifies the renderer's claimed site, or the only check lives renderer-side), **(2) bypassed checks** (4 reports — a check exists but is skipped, e.g. a renderer that ignores `SIGTERM` outlives the browser-side control structure holding its process lock), **(3) origin confusion** (the browser process itself derives the wrong site, typically after a complex cross-site navigation).
2. **Modelling the compromised renderer (RQ2).** The key empirical observation is that vendor-accepted PoCs for SI bypasses need only *minor* renderer deviations: circumvent renderer-side checks, and **spoof origin-related parameters in outgoing IPC messages**. So instead of simulating arbitrary compromise, the fuzzer patches the browser's IPC-bindings generator to add hooks, then intercepts and mutates the renderer's outgoing IPC messages — using the browser process as a confused deputy. An `IPCFuzzer` JS API (e.g. `IPCFuzzer.mutate_url(...)`, `IPCFuzzer.activate_leak_sanitizer()`) exposes this to the generated test case.
3. **Two novel oracles (RQ1).** A **leak sanitizer** seeds victim-site storages with a magic string and flags it appearing in IPC messages arriving at the attacker's process; a **process sanitizer** tags each process with the site of its first document and flags cross-site process reuse/sharing (bugs that leak nothing directly but still re-open a Spectre window). Inputs are generated from the browser's own **Web IDL** definitions, so the generator covers the full JS API surface rather than a hand-written grammar, and each statement is wrapped in try/catch/finally both for robustness and to measure semantic validity.

*(KO) 방법론에서 이 논문이 이식 가능한 이유: (a) 위협 모델을 "렌더러 침해 이후"로 고정했고, (b) IPC 바인딩 생성기를 패치해 후킹 지점을 자동 삽입했고, (c) 크래시가 아니라 "사이트 간 데이터 흐름"을 오라클로 삼았다. Electron에서는 (a)가 XSS 성공 이후 상태, (b)는 `ipcMain`/`contextBridge` 핸들러, (c)는 렌더러가 main으로부터 받아내는 특권 결과에 각각 대응된다.*

## 3. Experiments / Evaluation Setup

Three evaluation steps plus a campaign. Validity and coverage runs: Debian 12, AMD EPYC 7713, 64 cores, 64 GB RAM; 24 h per browser.

- **Semantic validity** of generated JS, measured via the catch/finally console-log counters over a 24 h run per browser. Separate inputs per browser because each uses its own Web IDL.
- **Known-bug reproduction:** three historical Chrome SI bypasses (CVE-2022-1637 class 3, CVE-2019-5856 class 1, CVE-2018-18345 class 1) reproduced on two old Chrome builds (99.0.4844.84 and 67.0.3396.99), run in Docker on Ubuntu 18.04 / 14.04; time-to-trigger measured with a 24 h cap. Playwright 1.18.1 for Chrome 99; Puppeteer for Chrome 69 (no Playwright supports it). The authors note the browser *instrumentation* was harder to backport than the browser patches.
- **Oracle evaluation:** five *additional* known SI bypasses sampled at random, reproduced by applying both the fuzzer patches and the bug report's own PoC patch, then checking whether either sanitizer fires.
- **Coverage:** LLVM `trace-pc-guard` edge bitmap in shared memory to aggregate across processes; totals are 6.9 M edges (Chrome) and 3.0 M edges (Firefox). Baseline is **FuzzOrigin** (the USENIX Sec '22 UXSS fuzzer); because FuzzOrigin's Selenium instrumentation no longer works on current browsers, only its *input generator* was used, driven by this paper's instrumentation. Coverage is reported both over all processes and over the privileged browser process alone (networking and storage services forced in-process so they count).
- **Campaign:** one month total — two weeks each on patched builds of Chromium 127.0.6497.0 (6ac2222a) and Firefox 121.0 (c00a6f0c), on an AMD EPYC 7702P (128 cores, 500 GB), with **50 fuzzer instances** in parallel Docker containers.
- **Renderer kills:** a separate 10 h run per browser counting iterations that ended with the browser process killing the renderer for misbehaving.

*(KO) 평가 규모는 크지 않다 — 두 브라우저, 한 달, 50 인스턴스. 대신 "알려진 버그 재현 시간"과 "오라클의 위양성/위음성"을 분리해서 측정한 구성이 깔끔하며, 논문을 쓸 때 그대로 베낄 만한 평가 설계다.*

## 4. Results / Key Findings

- **Semantic validity:** 89.5 % of executed statements run without an exception on Chrome, 85.3 % on Firefox. The gap is attributed to unsupported Web IDL extended attributes causing calls into unavailable interfaces.
- **Known-bug reproduction:** CVE-2019-5856 triggered in **under one minute** (so often that the sanitizer had to be switched off to let other bugs surface); CVE-2018-18345 in **≈14 minutes**; CVE-2022-1637 — the origin-confusion class, requiring a navigation chain *plus* a spoofed parameter — after **11.4 hours**. Trigger difficulty tracks the class, not the browser.
- **Oracle accuracy:** on the five sampled PoCs the leak sanitizer caught 3 and the process sanitizer caught 1; both missed CVE-2022-3044 (clipboard leak whose PoC uses MojoJS bindings, a code path the leak sanitizer does not observe). Counting the three fuzzer-evaluation bugs as well, the reported **false-negative rate is 12.5 %**, and **no false positives** were observed — by design, since the generator knows the ground-truth site of every document, so any observed cross-site flow or process reuse *is* a bypass.
- **Coverage:** the authors state plainly that absolute edge coverage is low, and argue it is the wrong metric here — the HTML parser and the renderer-side engine are deliberately out of scope, and the bugs live only in privileged processes, hence the separate browser-process bitmap. (Per-hour coverage values are only given as a plotted figure and are not quoted here.)
- **Four new bugs** from the month-long campaign:
  | Bug | Browser | Class | Severity | ID |
  |---|---|---|---|---|
  | `Window.name` not reset on cross-site navigation → leaks to next site (violates HTML standard) | Chrome | 1 | S4 | #384781865 |
  | Visited URLs broadcast to all renderers for `:visited` styling → compromised renderer sniffs browsing history | Firefox | 1 | S3 | #1938107 |
  | CORB not implemented → `no-cors` cross-site response bodies visible to the compromised renderer | Firefox | 1 | S3 | #1532642 (instance of a known issue) |
  | **History origin confusion** — renderer-side-only check on `history.replaceState`'s URL; mutating the URL *in the IPC message* makes the browser process store the spoofed URL, and the next reload loads the victim document into the attacker's renderer → victim cookies + JS execution in victim origin | Firefox | 3 | S2 | **CVE-2024-9392, $8,000 bounty** |
  The PoC for the last one is four lines of JS (activate sanitizer, `IPCFuzzer.mutate_url(...)`, `history.replaceState("foo","",null)`, `location.reload()`).
- **Renderer kills:** 8.7 % of Chrome iterations and 13.1 % of Firefox iterations ended with the browser process killing the renderer — i.e. even deliberately narrow IPC mutations trip the browser's own misbehaviour detection often.

*(KO) 가장 인용 가치가 높은 숫자 셋: (1) 1,328건 검토 → 39건만이 실제 SI 우회 (즉 이 버그 클래스는 희소하고 수동 발견에 의존해 왔다), (2) 버그 트리거 시간이 클래스별로 1분 / 14분 / 11.4시간으로 3자리 수 차이 — "탐색 공간이 아니라 전제 조건의 복잡도"가 비용을 지배한다, (3) 위음성 12.5 %, 위양성 0 % — 오라클을 ground truth로 설계하면 위양성이 구조적으로 0이 된다는 논거.*

## 5. How to cite in Related Work

> Recent work has begun to automate the discovery of *semantic* failures at the boundary between untrusted web content and the privileged process that hosts it. Drescher et al. [NDSS'26] classify all 39 known Site Isolation bypasses in Chrome and Firefox out of 1,328 examined bug reports, and observe that nearly all of them require only that a compromised renderer spoof origin-related parameters in the IPC messages it sends to the browser process. They accordingly build a Web IDL-driven fuzzer that hooks the IPC bindings layer to mutate outgoing messages, paired with process-level oracles that flag cross-site data leaks and cross-site process reuse, and report four new bugs including a Firefox history-confusion flaw (CVE-2024-9392). Their threat model — a renderer that already executes attacker-controlled code, attacking the privileged process through the IPC surface it is legitimately given — is precisely the post-XSS state of an Electron renderer. Their target, however, is a *browser*, whose browser process re-validates every renderer claim by design; an Electron main process, by contrast, exposes application-defined IPC handlers written by app developers, with no equivalent of a process lock and frequently no origin check at all. The question of how far an IPC-mutation fuzzer with a privilege-violation oracle carries over to that setting is open.

*(KO) 위치 설정: 이 논문은 "동기"이자 "대조군"이다. 동기로는 — 렌더러 침해 이후 IPC 경계를 자동으로 공격한다는 발상 자체가 이 논문으로 학계에서 정당화되었으므로, Electron에서 같은 일을 하겠다는 주장의 전제를 깔아 준다. 대조군으로는 — 브라우저의 browser process는 process lock과 site 검사라는 방어를 *설계상* 갖고 있고 그 로직의 버그를 찾는 것이 이 논문의 기여인데, Electron main 프로세스에는 그런 방어가 애초에 없고 앱 개발자가 쓴 임의의 핸들러만 있다. 즉 남겨진 갭이 명확하다: (a) 오라클을 어떻게 정의할 것인가 — 브라우저는 "site"라는 ground truth가 있어 위양성 0이 가능했지만 Electron 앱에는 그에 대응하는 불변식이 없다; (b) IPC 인터페이스가 Web IDL처럼 기계 판독 가능한 스펙으로 존재하지 않는다(앱마다 다른 `ipcMain.handle` 문자열 채널). 이 두 갭이 곧 "Electron IPC 퍼징의 어려움"을 설명하는 가장 좋은 재료다.*

## 6. Caveats / what I could not confirm from the text

- **Grounding.** Read in full: abstract, §I Introduction, §II-A Background/Site Isolation, §III (all three classes + three case studies), the opening of §IV Fuzzer Design, §VI Evaluation A–E in full, the opening of §VII Discussion, §VIII Related Work, the opening of §IX. **Not read line-by-line:** the bulk of §IV (generator/lowering design), all of §V Fuzzer Implementation, the rest of §VII, and appendix Table V (the full 39-bug list).
- The word **"Electron" does not appear** in the parts I read, and neither does any desktop-app case study. Every measured target is Chrome or Firefox. This paper must be cited as a *browser* paper whose method transfers, never as evidence about Electron. The ADJACENT tag reflects that.
- Coverage percentages are given only as a plotted figure (Fig. 7); I deliberately quote no numeric coverage value.
- Table IV's browser column uses glyphs that did not survive text extraction; the browser attribution above is reconstructed from the prose ("the discovered Chrome bug" for `Window.name`; "Case Study: Firefox History Confusion"; Firefox named explicitly for CORB and for visited-URL broadcasting). Verify against the rendered PDF before quoting the table.
- The $8,000 bounty and CVE-2024-9392 are stated by the authors; not independently verified against Mozilla's advisory.
- **Scope-consistency note for future runs.** Two other site-isolation papers sit in `excluded`: "Isolated and Exhausted" (USENIX Sec '23, SI abused for host DoS) and "State of Browser Process-Isolation: The Same-Site Weakness" (S&P '26). Both are measurements/attacks *about* browser SI. This one was admitted because its contribution is a **reusable discovery technique at the renderer↔privileged-process IPC boundary** — the same reason Favocado and COOPER are in scope for the engine-binding boundary. Keep that distinction if a further SI paper appears.
