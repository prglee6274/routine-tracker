# Jasmine: Scale up JavaScript Static Security Analysis with Computation-based Semantic Explanation

> ⚠️ **GROUNDING WARNING — read before citing.** The full text of this paper was **not reachable** on 2026-09-14. It is IEEE-paywalled (IEEE Xplore returned an empty body; the IEEE CSDL page is JavaScript-rendered and returned an empty shell), there is **no arXiv preprint**, and the first author's own publications page links the title back to itself with **no author-hosted PDF**. Everything below is grounded in (a) the confirmed bibliographic record, (b) the published abstract as returned by search over IEEE Xplore/CSDL, and (c) the author's own page listing. **No experimental number in this note comes from the paper body, because the body was not read.** Sections 3 and 4 are therefore deliberately thin and flagged. Re-fetch through an institutional IEEE subscription before citing any figure.

**Authors:** Feng Xiao (Georgia Institute of Technology), Zhongfu Su (Wuhan University), Guangliang Yang (Fudan University), Wenke Lee (Georgia Institute of Technology)
**Venue / Year:** 45th IEEE Symposium on Security and Privacy (IEEE S&P / "Oakland" 2024), 19–23 May 2024, San Francisco CA — pp. 296–311
**Links:** [paper (IEEE Xplore)](https://ieeexplore.ieee.org/document/10646682/) · [CSDL](https://www.computer.org/csdl/proceedings-article/sp/2024/313000a296/1ZZvDhsesSc) · [author page](https://fxiao.me/publications/) · DOI 10.1109/SP54263.2024.00183
**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** Jasmine is the same first author's follow-up to the CCS '22 cross-platform RCE study already in this ledger, and it attacks the tooling bottleneck that any large-scale Electron vulnerability hunt runs into — that off-the-shelf JavaScript static analysers (CodeQL, WALA) silently fail on the complex operations and semantics real applications are written in.

> **한 줄 요약 (KO):** JavaScript 정적 보안 분석이 실제 애플리케이션에서 왜 실패하는지를 "복잡한 연산·의미론(complex operations and semantics)" 문제로 규정하고, 이를 해소하는 **computation-based semantic explanation (CSE)** 기법과 프로토타입 Jasmine을 제시. 1만 개 이상 실제 JavaScript 프로그램에 적용해 이런 복잡 연산이 널리 퍼져 있으며 GitHub CodeQL과 IBM WALA 같은 최신 정적 도구를 심각하게 방해함을 보임. **주의: 본문 미확보(IEEE 유료), 아래 수치는 초록 기반.**

---

## 1. Problem, Gap & Hypothesis

**Problem (from the abstract).** Static analysis techniques for JavaScript "often suffer serious precision issues and may miss serious vulnerabilities," and the situation worsens on **modern JavaScript applications characterized by complex operations and semantics**. The framing is thus not "we need a new detector for vulnerability class X" but "the *substrate* every JS detector is built on degrades on real code."

**Gap.** The abstract positions the work against **the state of the art in deployed static tooling specifically — GitHub's CodeQL and IBM's WALA** — rather than against academic detectors. The claim is empirical: complex operations and semantics are *prevalent in practice* and *heavily impede* those tools. This is a different kind of gap claim from the rest of the ledger's JS-analysis papers (ODGEN, NodeMedic-FINE, GHunter, Bullseye), which each target a vulnerability class; Jasmine targets the analysis capability itself.

**Hypothesis (as stated).** A **computation-based semantic explanation** of JavaScript operations can "effectively identify and resolve common failures arising from complex semantics in static data flow analysis," thereby improving detection of potential vulnerabilities — i.e. semantics that defeat conventional modelling can be *explained* in terms of the computation they perform, and that explanation restores data-flow tractability.

*(KO) 이 논문의 gap 주장은 렛저의 다른 JS 분석 논문들과 종류가 다르다. 다른 논문들이 "프로토타입 오염을 찾겠다", "npm 취약점을 찾겠다"처럼 **취약점 클래스**를 겨냥한다면, Jasmine은 **분석 기반 자체가 실제 코드에서 무너진다**는 주장을 한다. Electron 앱 대규모 분석을 계획하는 thesis에게는 이 쪽이 더 직접적인 제약 조건이다 — 번들러를 거친 Electron 렌더러 코드는 정확히 "복잡한 연산·의미론"의 극단 사례이기 때문.*

## 2. Methodology

**Computation-based semantic explanation (CSE).** Described in the abstract as "a novel semantic understanding approach to combat complex semantics in JavaScript security analysis," which identifies and resolves failure modes that arise in **static data-flow analysis** when semantics are complex. **Jasmine** is the prototype implementation of CSE.

⚠️ Beyond this, the mechanism is **unknown to me**. I could not determine: what a "computation" is taken to be as the unit of explanation; whether CSE operates on source, on an IR, or on an existing framework's graph; whether it is a pre-pass that rewrites/normalises code before an existing analyser runs, or a replacement analysis; how it relates to the object-dependence-graph line (ODGEN, USENIX '22) already in this ledger; or whether it uses dynamic information. **Do not paraphrase a mechanism for this paper from this note.**

*(KO) 방법론은 사실상 미확보 상태다. CSE가 (a) 기존 분석기 앞단의 정규화 패스인지, (b) 독립적인 분석 엔진인지조차 초록만으로는 판별되지 않는다. 이 구분은 thesis에서 "우리는 Jasmine을 파이프라인에 끼워 쓸 수 있는가" 여부를 결정하므로 본문 확보 시 최우선 확인 항목.*

## 3. Experiments / Evaluation Setup

From the abstract only:

- **Corpus:** **more than 10,000 real-world JavaScript programs.**
- **Baselines:** **GitHub CodeQL** and **IBM WALA** — both named explicitly as "state-of-the-art static techniques" that the study measures interference against.
- **Measured:** (i) the prevalence of complex operations and semantics in practice; (ii) the degree to which they impede the baselines' "regular security validations."

⚠️ **Not known:** how the 10K programs were sampled (npm packages? web apps? GitHub repos?); whether any are Electron or desktop applications; the vulnerability classes targeted; whether a ground-truth benchmark (e.g. SecBench.js, already a context item in this ledger) was used; precision/recall figures; number of new bugs or CVEs found; runtime cost. **The 10K figure is the only dataset number I can ground.**

*(KO) 평가 설계에서 thesis에 결정적인 미확인 항목은 단 하나 — **10K 코퍼스에 Electron/데스크톱 앱이 포함되었는가**. 포함되지 않았다면(그럴 가능성이 높다: 같은 저자의 CCS'22 논문이 이미 cross-platform 쪽을 따로 다뤘음) Jasmine은 thesis에게 "서버·웹 코드에서 검증된 도구를 Electron 번들 코드에 처음 적용한다"는 명확한 기여 공간을 남긴다.*

## 4. Results / Key Findings

Only two findings can be stated with grounding, both from the abstract:

1. **Complex operations and semantics are prevalent** in the >10K real-world JavaScript programs analysed.
2. They **heavily impede state-of-the-art static techniques — specifically CodeQL and WALA — from performing regular security validations.**

⚠️ **No quantitative result is available to me.** There is no grounded number for how many programs were affected, by how much detection improved, how many vulnerabilities Jasmine found that the baselines missed, or how many were zero-days. **Any percentage attributed to this paper in a thesis draft must come from the paper itself, not from this note.**

*(KO) 정량 결과 전무. 초록의 "prevalent"와 "heavily impede"는 정성 표현이며, 이를 수치로 옮겨 적는 순간 날조가 된다. 인용 시 반드시 본문 확보 후 수치를 채울 것.*

## 5. How to cite in Related Work

Two draft sentences that are safe to use **without** the paper body, because they assert only what the abstract asserts:

> Beyond detectors for specific vulnerability classes, a parallel line questions whether the underlying analysis machinery holds up on real JavaScript at all. Xiao et al.'s Jasmine [S&P '24] introduces computation-based semantic explanation, a technique for resolving the analysis failures that complex JavaScript operations and semantics induce in static data-flow analysis; applied to over ten thousand real-world JavaScript programs, it finds such constructs to be prevalent and to substantially impede production static analysers including GitHub's CodeQL and IBM's WALA.

A third sentence, to be added **only after the body is read** and the bracketed claims verified:

> [VERIFY FIRST] Jasmine's corpus is drawn from <…>, and does not include packaged desktop applications, whose renderer-side code is typically bundler-transformed and minified — the very conditions under which Jasmine reports existing analysers to degrade.

*(KO) 포지셔닝. Jasmine은 thesis의 **도구 제약 논거(tooling-limitation argument)**로 쓰는 것이 가장 정직하고 강력하다. 즉 "Electron 앱을 대규모 정적 분석하려 했더니 CodeQL이 조용히 실패했다"를 저자 개인의 경험담이 아니라 **S&P'24에서 1만 개 프로그램으로 실증된 현상**으로 인용할 수 있다. 추가로 저자 라인이 갖는 서사적 가치가 크다: Feng Xiao는 Hidden Properties(USENIX'21) → Cross-platform RCE/XRCE(CCS'22) → Jasmine(S&P'24)로 이어지는데, 이는 "Node.js 공격 클래스 발견 → Electron/크로스플랫폼 RCE → 그 발견을 스케일업하기 위한 분석 기반 개선"이라는 궤적이다. thesis는 자신을 이 궤적의 다음 칸에 놓을 수 있다.*

## 6. Caveats / what I could not confirm from the text

- **The entire paper body.** IEEE Xplore and IEEE CSDL both returned empty content to the fetcher on 2026-09-14; no arXiv version, no author-hosted PDF, no institutional mirror was found across four searches (including semanticscholar-, researchgate-, gatech- and fudan-restricted queries). Sections 2, 3 and 4 above are consequently incomplete by design.
- **Confirmed bibliographic facts** (multiple independent sources agree): title, the four authors and their affiliations, IEEE S&P 2024, pages 296–311, DOI 10.1109/SP54263.2024.00183, date 19 May 2024. The author list and venue are additionally confirmed on the first author's own page and on Wenke Lee's lab publications page, so the record itself is solid even though the content is not.
- **"CSE" is my abbreviation of convenience**, taken from the abstract's phrasing "computation-based semantic explanation (CSE)"; I have not verified that the paper itself uses that acronym consistently.
- **No artifact located.** The first author's other projects are released under `github.com/xiaofen9` (e.g. Lynx for the USENIX '21 paper); a targeted search for a Jasmine artifact under that account returned nothing. Absence here is weak evidence — the search may simply have missed it.
- **Scope tag rationale, stated openly:** admitted as ADJACENT on the same basis as ODGEN (USENIX '22) — a JavaScript vulnerability-*discovery* capability paper rather than a desktop-app paper — reinforced by author continuity with the ledger's PRIMARY Electron entry (`ccs2022-xrce-xguard`). If the body turns out to evaluate only server-side Node.js code with no relevance to bundled desktop applications, the tag stands but the Related Work use narrows to the tooling-limitation argument in §5.
