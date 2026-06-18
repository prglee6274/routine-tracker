# Bullseye: Detecting Prototype Pollution in NPM Packages with Proof of Concept Exploits

**Authors:** Tariq Houis, Shaoqi Jiang, Mohammad Mannan, Amr Youssef (Concordia University, Canada)
**Venue / Year:** NDSS 2026
**Links:** [paper](https://www.ndss-symposium.org/ndss-paper/bullseye-detecting-prototype-pollution-in-npm-packages-with-proof-of-concept-exploits/) · [PDF](http://users.encs.concordia.ca/home/m/mmannan/publications/Bullseye-NDSS2026.pdf) · [code](https://github.com/Madiba-Research/Bullseye) · DOI: n/a (NDSS)
**Scope tag:** ADJACENT
**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Prototype pollution is the canonical XSS→RCE escalation primitive inside Electron's Node-enabled processes, and Bullseye is a state-of-the-art *discovery* engine for exactly that bug class in the npm packages Electron apps bundle.
> **한 줄 요약 (KO):** Bullseye는 npm 패키지의 프로토타입 오염(prototype pollution) 취약점을 PoC 익스플로잇과 함께 자동으로 찾아내는 동적 분석 도구로, 44,513개 패키지에서 290개의 제로데이를 오탐 없이 발견하고 149개 CVE를 받았다.

## 1. Problem, Gap & Hypothesis
Prototype pollution lets an attacker inject properties into `Object.prototype` (via `__proto__`, `constructor.prototype`), corrupting every inheriting object and frequently escalating to ACE/RCE. The authors argue existing detectors are caught in a precision/recall bind: **static** tools (e.g., ODGen) suffer scalability blow-ups (path/object explosion) and high false positives because they cannot see the runtime context that would render a flow unexploitable; **dynamic** tools have low false positives but high false *negatives* because poor code reachability (wrong argument types/values, shallow entry-point coverage) means vulnerable code is never executed. Hypothesis: a dynamic framework that (a) systematically enumerates *all* package entry points, (b) generates context-aware exploit inputs by fusing the package's own test-suite inputs with known prototype-pollution payloads, and (c) confirms hits with robust runtime oracles can drive false negatives *and* false positives down while staying scalable to tens of thousands of packages.
*(KO) 핵심 갭: 정적 분석은 오탐·확장성 문제, 동적 분석은 도달성(reachability) 부족으로 인한 미탐 문제. Bullseye는 진입점 전수 탐색 + 컨텍스트 기반 입력 생성 + 런타임 오라클로 둘 다 잡겠다는 가설.*

## 2. Methodology
Bullseye is a fully automated dynamic-analysis pipeline. (1) **Comprehensive module & entry-point identification**: it resolves indexed and non-indexed modules declared in `package.json`, detects dynamic imports at runtime, and enumerates entry points including dynamic exports, complex export objects, and class-method-style entry points. (2) **Context-aware exploit generation**: instead of random/fixed inputs, it reuses developer-provided inputs harvested from the package's own test suite (project-specific *valid* inputs that reach deep code paths) and augments them with prototype-pollution exploit inputs extracted from prior work; each entry point is executed with its relevant candidate inputs. (3) **Dual runtime validation oracles**: a first oracle recursively checks whether a polluted prototype property actually appears on `Object.prototype` after execution; a second **differential** oracle compares object state pre- vs. post-execution to catch more complex side effects the first oracle misses. Only inputs that trip an oracle are reported, yielding validated PoCs rather than candidate flows.
*(KO) 개발자 테스트 입력을 익스플로잇 입력과 결합해 도달성을 끌어올리고, 두 개의 부작용(side-effect) 오라클로 실제 오염 여부를 런타임에서 확정 → PoC까지 자동 생성.*

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured
Bullseye was run on **44,513 highly popular Node.js packages** (each with 10,000+ weekly npm downloads) plus **5,879 lower-download packages**, completing the full run in **under 8 hours**. The evaluation measures zero-day discovery count, false-positive rate, entry-point coverage, scalability (throughput to >50,000 packages), and a comparison against state-of-the-art static/dynamic detectors (e.g., ODGen and dynamic predecessors) on false negatives and false positives. Responsible disclosure with PoC code was carried out for every finding.
*(KO) 평가 대상: 인기 패키지 44,513개 + 저인기 5,879개 = 5만 개 이상, 8시간 미만. 측정 항목: 제로데이 수, 오탐률, 진입점 커버리지, 확장성, SOTA 대비 미탐/오탐.*

## 4. Results / Key Findings — concrete numbers
- **290 packages** found with **zero-day** prototype pollution, reported across **807 unique entry points**, with **no false positives**.
- **149 CVEs** assigned (as of July 22, 2025); of these **66 made public**, with **25 rated critical** and **34 high**.
- Scales to **>50,000 packages** in <8 hours; the test-suite-input augmentation is credited with uncovering significantly more zero-days than prior work, and Bullseye reports outperforming the state of the art on **both** false negatives and false positives.
- Reference point for the FP/scalability gap it targets: prior static tool ODGen reportedly fails to *complete* analysis on ~50% of tested npm packages.
*(KO) 결과: 290개 패키지/807개 진입점에서 제로데이, 오탐 0. CVE 149개(공개 66, critical 25, high 34). ODGen이 절반을 분석 완료조차 못한 것과 대비.*

## 5. How to cite in Related Work
> Prototype pollution remains one of the most consequential escalation primitives in the JavaScript/Node.js ecosystem, capable of turning attacker-controlled input into arbitrary code execution. Houis et al. present Bullseye, a fully automated dynamic-analysis framework that fuses developer-supplied test-suite inputs with known prototype-pollution payloads and validates candidate flows through dual runtime oracles, discovering zero-day prototype pollution in 290 of ~50,000 analyzed npm packages with no false positives and 149 assigned CVEs. The work demonstrates that systematic entry-point coverage plus runtime side-effect oracles can surface hundreds of previously unknown vulnerabilities at ecosystem scale.

*(KO) 포지셔닝: Electron 앱은 npm 패키지를 그대로 번들링하고 main/preload 측에서 Node 권한으로 실행하므로, Bullseye가 찾는 패키지 단위 프로토타입 오염은 Electron 위협 모델에서 XSS→RCE 사슬의 '엔진'이 된다. 본 논문은 (a) 패키지 생태계 단위의 취약점 탐지에 강하지만 (b) Electron 고유의 renderer↔main IPC·contextBridge·preload 노출 경계는 다루지 않는다 → "Node 패키지 레벨 탐지는 성숙했으나 Electron 애플리케이션 경계에서의 탐지는 여전히 공백"이라는 동기/갭 인용으로 사용. Silent Spring(USENIX'23)과 같은 라인의 후속·보완 작업으로 배치.*

## 6. Caveats / what I could not confirm from the text
- Grounding: built from the author-hosted full-text PDF (abstract + introduction + methodology/contribution paragraphs). I did not read every evaluation table end-to-end, so the breakdown of CVE severities beyond the abstract's 25 critical / 34 high, and the exact head-to-head numbers vs. each named prior tool, were not individually verified line-by-line.
- The paper targets npm packages/Node.js, **not** Electron specifically; the Electron relevance is analytical (shared runtime + escalation primitive), not claimed by the authors.
- CVE counts are time-stamped "as of July 22, 2025" in the paper and will have grown; treat as a lower bound.
- "Outperforms state-of-the-art" is the authors' framing; the precise baselines and metrics should be checked against the evaluation section before quoting comparatively.
