# SandTrap: Securing JavaScript-driven Trigger-Action Platforms

**Authors:** Mohammad M. Ahmadpanah (Chalmers University of Technology), Daniel Hedin (Chalmers / Mälardalen University), Musard Balliu (KTH Royal Institute of Technology), Lars Eric Olsson (Chalmers), Andrei Sabelfeld (Chalmers)
**Venue / Year:** 30th USENIX Security Symposium (USENIX Security '21), August 11–13 2021, pp. 2899–2916 · ISBN 978-1-939133-24-3
**Links:** [paper](https://www.usenix.org/conference/usenixsecurity21/presentation/ahmadpanah) · [PDF](https://www.usenix.org/system/files/sec21-ahmadpanah.pdf) · [author page](https://smahmadpanah.github.io/publications/) · full version + code linked from the paper's reference [2] (cse.chalmers.se)
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** SandTrap is the canonical demonstration that Node.js's own `vm` module is not a security boundary — every host↔sandbox interaction point (prototypes, shared objects, module cache) becomes an escape vector — which is exactly the argument a thesis needs when explaining why Electron's `contextIsolation` and `contextBridge`, which are the same membrane pattern applied to renderer↔main, are hard to get right.

> **한 줄 요약 (KO):** IFTTT·Zapier·Node-RED 같은 JavaScript 기반 트리거-액션 플랫폼의 샌드박스를 실제로 탈출(prototype poisoning으로 다른 사용자 데이터까지 유출)해 보인 뒤, Node.js `vm` + 프록시 기반 양방향 멤브레인으로 모듈/API/값/컨텍스트 4단계 접근제어를 강제하는 모니터 SandTrap을 제안한 논문. Electron의 contextBridge와 **같은 멤브레인 문제**를 다루기 때문에, "격리 경계를 넘나드는 객체가 하나라도 있으면 그것이 곧 공격면"이라는 명제의 최고 인용 근거.

## 1. Problem, Gap & Hypothesis

Trigger-Action Platforms (TAPs) — IFTTT, Zapier, and the open-source Node-RED — let end users install third-party "apps"/"flows" written in JavaScript. The platform sits as a **person-in-the-middle** between trigger and action services, holding OAuth delegation tokens, so compromising the TAP compromises every connected service. The paper reports IFTTT's scale from the vendor's own figures: **18 million users running more than a billion apps a month across more than 650 partner services**.

The gap: platforms had assumed that ad-hoc restrictions (IFTTT's static TypeScript checks + "no I/O" documentation claim; Zapier's per-user Lambda; Node-RED's assumption of a trusted single user) were sufficient isolation. The authors' hypothesis is that these are **not implementation bugs but a fundamental problem** of integrating third-party JavaScript, and that the fix requires *fine-grained* access control at four levels — module, API, value, and context — rather than the all-or-nothing isolation that `vm`, `isolated-vm`, SES and WebAssembly provide.

Two attack scenarios are separated (Fig. 1): (a) the victim installs a malicious app — applies to all three platforms; (b) the victim has **only benign apps** but a co-tenant's malicious app breaks the isolation boundary — applies to IFTTT's *multi-user* architecture, where one Node.js Lambda instance is reused across users to avoid cold-start cost.

*(KO) 핵심 gap: "격리는 있다/없다의 이분법이 아니다." vm·isolated-vm·SES는 all-or-nothing이라 호스트와 샌드박스가 객체를 공유해야 하는 실제 통합 시나리오를 못 다룬다 — Electron이 preload에서 `contextBridge.exposeInMainWorld`로 객체를 노출할 때 겪는 문제와 정확히 동일한 구조.*

## 2. Methodology

Three-part method:

1. **Manual exploit construction against live platforms** (§3, §4), escalating through successive vendor patches. The IFTTT chain is the instructive one:
   - **PoC v1** — evade the web-UI static check with `eval`; `require("/var/runtime/RAPIDClient.js")` to grab the AWS Lambda runtime module (relying on `require`'s module cache so the imported runtime *is* the live instance); poison `rapid.prototype.nextInvocation`; exfiltrate via `https.request`. Functionality of the poisoned method is preserved, so exfiltration is invisible.
   - **PoC v2** — after IFTTT disallowed `eval`/`Function`, removed `require` from the TypeScript type system and locked down Lambda network access: reintroduce `require` via a bare `declare var require : any`, obtain a function through `(() => {}).constructor.call(...)` (bypassing the `Function` filter), and exfiltrate through the *app's own* action capability — `Email.sendMeEmail.setBody(result)` — rather than the Lambda's network.
   - **PoC v3** — after IFTTT adopted `vm2` sandboxing: the `Meta.currentUserTime` / `Meta.triggerTime` objects are *created outside the sandbox and passed in*, so poisoning the `tz` method on the `moment` prototype lets the attacker rewrite time for **other users' apps**, controlling whether their time-conditional actions run or are skipped.
2. **Empirical ecosystem measurement** of Node-RED (§4.2, §4.3) — scraping the package catalog and the published-flow catalog, applying the Bastys et al. source/sink security-labelling method, and manually reviewing the top-25 most downloaded nodes and flows.
3. **Design, implementation and evaluation of SandTrap** (§5, §6) — a JavaScript monitor combining the Node.js `vm` module with **fully structural, proxy-based two-sided membranes**, plus a policy language and a **policy-generation mode** (run the app with representative inputs, harvest an allowlist, then hand-tune). Policies come in two tiers: *baseline* policies (written once per platform, no developer involvement) and *advanced* app-specific policies.

*(KO) 방법론에서 배울 점: (i) 벤더 패치를 따라가며 PoC를 3세대까지 진화시킨 점 — Electron 논문에서 `nodeIntegration:false` → `contextIsolation:true` → `sandbox:true` 단계별 우회를 서술할 때 그대로 쓸 수 있는 서술 구조. (ii) "정책 생성(policy generation)" 자동화 — 방어 논문이 실무 채택되려면 정책을 사람이 쓰지 않아도 되게 만들어야 한다는 교훈.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**Vulnerability side (targets and datasets):**

| Target | Setup / dataset |
|---|---|
| IFTTT | Live platform + a test clone of IFTTT's Lambda function deployed on AWS Lambda (mock data), for confirming exfiltration |
| Zapier | Own test account only, no other users involved; two zaps (one benign with Dropbox access, one malicious without) |
| Node-RED package catalog | **2,122 packages scraped, 5,316 nodes total** |
| Node-RED security labelling | **408 node definitions** from the **top 100** packages, using Bastys et al.'s source/sink labelling |
| Node-RED flow catalog | **1,181 unique** (JSON-parsable, non-empty, non-duplicate) published flow definitions; a further **1,453 empty, invalid or duplicate entries** were encountered while scraping |
| Manual review | Top **25** most downloaded nodes and flows |

**Defence side (what was measured):** SandTrap was instantiated to all three platforms and, for each, run on secure and deliberately-insecure versions of benchmark apps; the paper reports whether the monitor accepts/rejects, the LoC of the final policy, and wall-clock overhead. Overhead is the **average of 20 runs** per case, comparing execution with vs. without SandTrap. IFTTT was evaluated on a locally hosted IFTTT Node.js runtime (equivalent to Lambda for filter-code processing since the modifications touch nothing network-related); Zapier likewise on a local Zapier runtime; Node-RED on the local single-user deployment that is its main use case.

Node-RED benchmark cases: `Lowercase` (deny-all module policy; attack reads `/etc/passwd` via `fs.readFile` and exfiltrates via `https.request`), `Dropbox out` (API-level policy; attack exfiltrates via `https.request.write`), `Email` (value-level policy delimiting `stream.Transform.write` to the user-specified recipient), and the `Water utility` SCADA flow (global/flow context; baseline policy blocks `_context.global.set` / `_context.flow.set`).

*(KO) 평가 설계 참고점: 취약점 파트는 "실 플랫폼 + 자체 클론"으로 윤리 문제를 피했고, 방어 파트는 각 케이스마다 **secure 버전은 통과 / insecure 버전은 차단**을 모두 보였다. Electron 도구를 평가할 때도 false positive(정상 앱 차단)를 반드시 같이 보고해야 함을 시사.*

## 4. Results / Key Findings — concrete numbers

**Vulnerabilities**

- All three platforms were breakable. IFTTT's break is the most severe because instance reuse means **Node.js instances are kept alive for up to 30 minutes** processing filter code from arbitrary apps and users — so a single poisoning collects *all* requests and responses on that instance for 30 minutes, and the attacker simply re-triggers to continue.
- Impact estimated via Bastys et al.: **35%** of IFTTT apps have access to private data through sensitive triggers (images, videos, SMS, emails, contact numbers, voice commands, GPS), and **98%** use sensitive actions.
- **Coordinated disclosure outcomes:** IFTTT acknowledged a "critical" vulnerability and shipped a patch **within days**, then returned after each patch asking the authors to verify it; the authors' first report already recommended proxy-based sandboxing, which is what IFTTT ultimately adopted. Zapier confirmed it reuses execution sandboxes per user per language and that the PoC exposed unintended behaviour, tracing it to a **bug in Node.js integration caching**. **Bug bounties were received from both IFTTT and Zapier.**

**Node-RED ecosystem measurement**

- Packages average **4.16 JavaScript files / 793.45 LoC**; *official* packages average **1.76 files / 506.77 LoC** — i.e. third-party packages are large enough to camouflage an attack.
- Packages average **1.85 direct dependencies** on other Node.js packages, commonly `fs`, `request` and `os` — powerful APIs by default.
- Security labelling of the 408 node definitions: **privacy violations may occur in 70.40% of flows, integrity violations in 76.46%**.
- Shared-context exposure: **at least 228 published flows** use flow or global context in at least one member node, and **at least 153 packages** directly read from or modify the shared context. Node type resolution is by plain **string**, so multiple packages can claim the same type — a name-squatting substitution attack into a previously secure flow.
- Concrete physical-consequence example: the "Water Utility Complete Example" SCADA flow keeps `tank1Level` / `tank1Start` / `tank1Stop` in the global context; a malicious node that rewrites them can either starve the pump (never start) or cause physical damage by continuous pumping (never stop).

**SandTrap effectiveness and cost**

- In all reported cases SandTrap **accepts the secure and rejects the insecure version**.
- Policy sizes (average LoC of final policy): **185 (IFTTT), 260 (Zapier), 2,650 (Node-RED)** — the Node-RED figure being an order of magnitude larger is itself a finding about how much surface a module-enabled platform exposes. Tuning a value-sensitive case typically "amounted to modifying a single record" (e.g. allowlisting an email address); adding parameterised IFTTT policies takes "a few minutes".
- **IFTTT overhead:** average **4.10 ms** across **25** apps, maximum observed **6.35 ms** — tolerable against IFTTT's 15-minute execution allowance. Against a re-implementation of IFTTT's own `vm2`-based patch, SandTrap adds only **0.53 ms** to sandbox creation and **0.42 ms** to filter-code evaluation.
- **Zapier overhead:** average **4.87 ms** over 10 use cases; the worst case (loading all built-in modules) **< 7 ms**; **no run exceeded 12 ms**.
- **Node-RED overhead:** loading dominates, but since nodes are loaded once at start-up, steady-state flow execution overhead is **< 3 ms**, and **no run exceeded 100 ms** including both loading and triggering.
- Feature comparison (Table 3) against `vm2`, JSand and NodeSentry: only SandTrap provides *all* of policy generation, full JavaScript + CommonJS support, breakout hardening, local object views, proxy control, controlled cross-domain prototype modification, and fine-grained access control. `vm2` supports neither cross-domain prototype-hierarchy modification nor fine-grained access control; JSand is built on SES and therefore cannot run full JavaScript.

## 5. How to cite in Related Work

> Ahmadpanah et al. showed that language-level JavaScript isolation degrades precisely at the points where a sandbox must share objects with its host: across three successive hardening rounds of IFTTT's filter-code sandbox they escaped first through `eval` and the `require` module cache, then through the `Function` constructor, and finally — after IFTTT adopted `vm2` — by poisoning the prototype of a `moment` object that had been *created outside the sandbox and passed in*, thereby controlling the trigger time observed by other users' applications [SandTrap, USENIX Sec '21]. Their measurement of the Node-RED ecosystem found that 70.40% of published flows admit privacy violations and 76.46% admit integrity violations under a source/sink labelling of 408 node definitions, with at least 228 flows and 153 packages touching a shared global or flow context. Their defence, SandTrap, combines the Node.js `vm` module with two-sided proxy membranes to enforce module-, API-, value- and context-level policies at an average overhead of 4.10 ms (IFTTT) and 4.87 ms (Zapier). The same membrane pattern underlies Electron's `contextBridge`, and the same failure mode — a single object crossing the boundary with a mutable prototype — applies there; unlike a trigger-action platform, however, an Electron renderer's escape lands directly on the user's filesystem rather than on a cloud tenant.

*(KO) 포지셔닝: 이 논문은 **방어(defense) 쪽 대조군**으로 쓰는 것이 가장 강력하다. 세 가지 용도가 있다. (1) **동기 부여** — "vm2도 뚫렸다"는 사실은 Electron의 contextIsolation을 '이미 해결된 문제'로 치부하는 리뷰어에 대한 직접적 반박이 된다. (2) **대조** — SandTrap은 정책을 강제하는 *방어* 논문이므로, 취약점 *발견* 논문인 내 논문과 정면 경쟁하지 않고 "정책은 있으나 그 정책을 어디에 걸어야 하는지 알아내는 문제는 여전히 열려 있다"는 식으로 gap을 만들 수 있다. (3) **남긴 gap** — SandTrap은 (a) 정책 생성이 여전히 반자동(Node-RED 정책 2,650 LoC!)이고, (b) 서버사이드 Node.js 런타임만 다루며 **렌더러 프로세스·Chromium·DOM이 개입하는 Electron 구조는 전혀 다루지 않는다**. Electron에서는 공격자 입력이 신뢰되지 않은 웹 콘텐츠(DOM)에서 출발해 preload를 거쳐 main으로 가는데, SandTrap의 위협 모델(악의적 앱 *제작자*)은 이 경로를 포함하지 않는다. 이 두 지점이 내 논문의 자리다.*

## 6. Caveats / what I could not confirm from the text

- Read the **USENIX open-access conference PDF in full**; all numbers above are from that text. However, the paper repeatedly defers detail to a **full version [2]** (Tables 4, 5 and 6, and the details of the Node-RED empirical studies and the shared-resource exfiltration cases). I did **not** fetch the full version, so the *per-case* overhead breakdowns and the per-case Zapier/Node-RED tables are cited only via the summary sentences in the conference version.
- Overhead figures are single-machine wall-clock averages of 20 runs; the paper does not state the hardware, and the IFTTT/Zapier evaluations were run on **local re-hostings** of those runtimes rather than the production platforms, so the absolute milliseconds are indicative rather than production-representative.
- The 70.40% / 76.46% figures are the *potential* for violation under a source/sink labelling (following Bastys et al.), **not** confirmed exploitable vulnerabilities. Cite them as attack-surface estimates, not as a vulnerability count.
- The 35% / 98% IFTTT figures are **not this paper's measurement** — they are quoted from Bastys et al. [8]. Attribute accordingly.
- The "18 million users / billion apps a month / 650 partner services" figures are IFTTT vendor claims cited by the paper [38], as of 2021; they are certainly stale by now.
- Zapier's exploit was demonstrated on the authors' **own single test account**, so its cross-user impact is explicitly characterised by the authors as reduced and partly hypothetical (contingent on Zapier later allowing users to share zaps containing JavaScript).
- SandTrap's soundness/transparency proof is stated for "an essential model of Node-RED" (per the authors' licentiate thesis description); the conference paper does not carry the full formal development, so I cannot confirm the exact scope of the formal guarantee from this text alone.
