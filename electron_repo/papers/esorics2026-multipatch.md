# Why Not Fix It Once and for All? An Empirical Study of Multiple Patches for Vulnerability Fixes in Open-Source Software

**Authors:** Weiliang Qi, Youpeng Li, Xinda Wang (George Mason University — affiliation inferred from the ESORICS listing, not stated in the arXiv HTML read) · **Venue / Year:** ESORICS 2026 (31st European Symposium on Research in Computer Security, Rome, 14–18 Sep 2026; Spring Cycle, submission #784) · **Links:** [accepted-papers listing](https://sites.google.com/di.uniroma1.it/esorics2026/program/accepted-papers) · [arXiv HTML 2607.13206v1](https://arxiv.org/html/2607.13206v1) · DOI: none yet (Springer LNCS proceedings not published as of 2026-09-03)

**Scope tag:** ADJACENT

**Relation to a thesis on discovering Electron-app vulnerabilities (one line):** It is the first systematic, venue-published quantification of *incomplete fixes* — the exact phenomenon this repo has documented qualitatively in two SiYuan XSS incomplete-fix chains — and it shows empirically that no existing detector can tell a complete fix from an incomplete one, which converts the repo's case study from an anecdote into an instance of a measured, unsolved problem.

> **한 줄 요약 (KO):** NVD의 25,113개 OSS 보안 패치 CVE 중 1,646개가 다중 패치였고, 그중 641개가 "불완전한 수정(C1)"이었으며, 기존 취약점 탐지 모델 6종 모두 불완전 수정 탐지에서 정확도·F1이 50% 미만(무작위 추측보다 나쁨)으로 무너졌다.

---

## 1. Problem, Gap & Hypothesis

**Problem.** A CVE record is normally read as "one vulnerability, one patch." In practice a substantial minority of CVEs carry *several* patch commits, and a downstream consumer applying only the first one may remain vulnerable. Nobody had measured how often this happens, why, or whether tooling can detect it.

**Gap.** The paper positions itself against three lines of prior work and shows each stops short: (i) large-scale security-patch studies — Li et al.'s "A large-scale empirical study of security patches" *discusses* multi-patch fixes but analyses **only 100 samples**; (ii) patch-correctness work confined to one domain — Wu et al. (KLAUS, Linux) and Kim et al. (PatchVerif, robotic vehicles); (iii) bug-fix (not security-fix) studies — Gu et al. across three OSS projects, Zhong et al. across six Java projects. No systematic, cross-ecosystem study of *security* multi-patch fixes existed.

**Hypothesis (implicit, three-part).** (a) Multi-patch fixes are common enough to matter and have identifiable, recurring causes; (b) they are not a uniform phenomenon — porting a fix across branches is a different failure from botching the fix; (c) the standard research assumption that *post-patch code is non-vulnerable ground truth* is false for a measurable slice of the corpus, which would silently corrupt the datasets that vulnerability-detection research is trained on.

> **(KO)** 핵심 갭은 "선행 연구가 다중 패치를 100개 샘플로만 다뤘다"는 점. 그리고 세 번째 가설이 특히 중요하다 — VD 데이터셋이 "패치 후 코드 = 안전"이라고 가정하는데, 불완전 수정 사례에서는 그 가정 자체가 깨진다.

## 2. Methodology

Four stages, all reconstructible:

1. **Corpus construction.** NVD JSON feeds API, all CVEs published up to **May 2025**. Keep only CVE entries with a reference link explicitly labelled `patch`, and only where the URL contains both `git` and `commit` (i.e. OSS with reachable source). Critically, they **do not count patch URLs** — they parse the embedded commit IDs and de-duplicate on those, because GitHub and GitLab mirrors of the same commit would otherwise inflate the multi-patch count. Obsolete repository addresses (the records span 26 years) were manually re-mapped; separate collectors were written for the GitHub API, cgit and GitLab.
2. **Manual taxonomy.** Three researchers, each with 5+ years of software-security experience. Each independently coded 100 randomly-sampled multi-patch CVEs into a preliminary taxonomy, then merged into a shared codebook; each then independently classified all samples, with disagreements resolved by discussion to consensus. One CVE may fall into more than one category.
3. **Characterisation.** Single- vs multi-patch comparison across programming language, project, CWE, publication year; time interval from first to last patch per category; patch similarity by character-level **Levenshtein distance** plus average hunks and LoC per patch.
4. **Can tooling detect it?** Two detector families tested against the two categories that actually represent *incomplete remediation*: six vulnerability-detection (VD) models against C1 (incomplete fixes), and two vulnerable-code-clone (VCC) tools against A1+A2 (multi-location fixes).

> **(KO)** 방법론에서 배울 점 두 가지. (1) URL이 아니라 **커밋 ID로 중복 제거** — 같은 커밋의 GitHub/GitLab 미러 때문에 다중 패치가 과대 계상되는 것을 막는다. 이 repo가 SiYuan GHSA 레코드 수를 "발견 건수"로 오독했던 09-02 교훈과 정확히 같은 종류의 측정 타당성 문제다. (2) 코드북 기반 3인 독립 코딩 — 석사 논문에서 수동 분류를 정당화할 때 그대로 인용 가능한 절차.

## 3. Experiments / Evaluation Setup — targets, dataset sizes, configs, what was measured

**Corpus.** 25,113 CVEs associated with OSS security patches; **1,646** linked to multiple distinct patch commits; **average 2.55 patches per multi-patch CVE**. Separately, **127** CVE records were found to contain *both* vulnerability-introducing and vulnerability-fixing commits — NVD has no label distinguishing the two, so both appear as "patch."

**Taxonomy and distribution (Table 1, counts of CVE records as of May 2025):**

| Category | Subcategory | # |
|---|---|---|
| A. Multi-location fixes | A1. Different branches or projects | 830 |
| | A2. Different locations within same branch | 30 |
| B. Fix and related changes | B1. Workaround and formal fix | 16 |
| | B2. Fix and documentation updates | 128 |
| **C. Defective fixes** | **C1. Incomplete fixes** | **641** |
| | C2. Bug-introducing fixes | 119 |

**VD experiment (§7.1).** Six models: CodeBERT, UniXcoder, PDBERT, LineVul, VulBERTa (transformer/pre-trained families) and Devign, ReVeal (GNN). LLMs were **deliberately excluded** to avoid pre-training data leakage from public vulnerability databases. Training data built the standard Big-Vul way from *single*-patch NVD cases, split 8:1:1 — Train 8,301 vulnerable / 243,608 non-vulnerable; Valid and Test 1,037 / 30,451 each. Held-out multi-patch test set: **738 vulnerable / 556 non-vulnerable** samples drawn from C1, labelling code *before* the final fix as vulnerable and *after* it as non-vulnerable.

**VCC experiment (§7.2).** ReDebug and FIRE, both chosen because they build fingerprints from scratch (proprietary tools may already carry NVD fingerprints → leakage). Fingerprints generated from the *first* patch in each A1/A2 sequence; the remaining patches form the test set. **252 vulnerability signatures, 266 test samples.**

> **(KO)** 평가 설계에서 가장 중요한 통제: **LLM을 일부러 배제**했다(데이터 누출). 그리고 VCC 도구도 "지문을 처음부터 만들 수 있는" 오픈소스 2종만 선택했다. 데이터 누출 통제를 이렇게 명시하는 방식은 논문 평가 섹션 작성 시 참고할 만하다.

## 4. Results / Key Findings — concrete numbers

**(a) Incomplete fixes are the second-largest category and the largest *defect* category.** C1 = 641 of 1,646 multi-patch CVEs. Worked example: **CVE-2012-0038** (integer overflow in `count`, Linux XFS). The first patch `fa8b18ed` added a max-value check but overlooked that `be32_to_cpu()` returns a 32-bit *unsigned* integer while `count` was declared *signed*, so `count` could go negative and bypass the check; the second patch changed the type. **The complete fix was delayed by 18 days**, during which the incomplete patch sat in a public repository as a hint to attackers before public disclosure.

**(b) XSS is the #1 CWE among multi-patch fixes — 519 CVEs**, holding the same rank it has among single-patch fixes. CWE-94 Code Injection enters the top 10 at #10 (**up 6 ranks** vs single-patch); CWE-200 Sensitive Information Exposure is #2 with 164 (**up 7 ranks**); CWE-22 Path Traversal #7 with 113.

**(c) JavaScript and TypeScript are over-represented in multi-patch fixes.** JavaScript 9.53% of single-patch → **11.68% of multi-patch** (rank 3 in both); TypeScript 3.56% → **4.29%** (rank 8 → 9). C is #1 in both (29.91% → 32.02%), PHP #2 (19.94% → 20.21%).

**(d) Delay.** Overall **31.7% of multi-patch fixes take more than one day** from first patch to last. For C1 (incomplete fixes) specifically: 336 completed in <1 day, **145 in 1–30 days, 33 in 30–360 days, 4 took more than a year**. For C2 (bug-introducing): 48 / 43 / 5 / 1.

**(e) The headline negative result — every detector fails.** On the C1 held-out set, **TPR drops by 7.17 to 28.38 percentage points** relative to the same models' performance on single-patch data. **All six models score accuracy and F1 below 50% on incomplete-fix detection — the paper states this is "worse than random guessing."** Representative rows (VD → incomplete-patch detection): CodeBERT Acc 96.94 → 45.43, TPR 38.54 → 10.16, F1 45.38 → 17.54. PDBERT 96.94 → 45.28, TPR 38.25 → 10.30. UniXcoder 96.85 → 45.36, TPR 39.98 → 13.82. VulBERTa TPR 3.37 → **0.27**, F1 6.48 → 0.53. LineVul F1 75.36 → **5.46** (a 69.90-point collapse). Devign 69.57 → 43.56; ReVeal 71.63 → 48.85. Diagnosis from failure-case inspection: the models **assign the same label to the pre-fix, intermediate and post-fix versions of the same function**, because a security patch changes only part of a function and the variants look nearly identical.

**(f) Clone detectors fail too.** **FIRE's TPR falls from 90.00 to 52.46** (−37.54) on multi-location patches; ReDebug's from 37.56 to **16.75** (−20.81). Both FPRs *also* fall (FIRE 8.57 → 5.23; ReDebug 20.05 → 0.49), meaning the tools miss recurring vulnerabilities rather than over-predicting them.

**(g) Structural causes, not just carelessness.** Ambiguity in CNA Rules 3.0 about whether two projects "share vulnerable code" (worked example CVE-2024-1394, Golang FIPS `openssl` vs Microsoft `go-crypto-openssl`); Git commit-granularity conventions; **5.8% of multi-patch cases contain patches unrelated to the security fix** (changelogs, version bumps, tests, README-only commits — e.g. CVE-2018-8729); omitted *prerequisite* patches (CVE-2023-40173, where an unrecorded intermediate patch makes cherry-picking the two recorded ones logically inconsistent); vendors declining to correct wrong records (CVE-2022-2522). On C2: in **almost all** bug-introducing-fix cases the committer was already a founder, core developer or early collaborator — and **no CVE issued after 2020 falls into C2 at all**, which the authors tie to CNA rule changes that reduced vendor discretion over CVE assignment.

**(h) The dataset-poisoning corollary.** Prior work (CVEfixes, Big-Vul, DiverseVul, and the "how far are we?" line) assumes post-patch code is non-vulnerable ground truth. For the C1 slice that assumption is false, so those datasets contain mislabelled "safe" samples.

> **(KO)** 논문에 직접 쓸 수 있는 숫자 세 개: **C1 = 641건**, **불완전 수정 탐지에서 6개 모델 전부 정확도·F1 < 50%**, **JavaScript는 단일 패치 9.53% → 다중 패치 11.68%로 과대표집**. 특히 (e)의 실패 원인 진단 — "패치 전/중간/후 함수를 모델이 같은 라벨로 분류한다" — 은 SiYuan `escapeAttr` 사례에서 정적 분석이 `SetSanitize(true)`를 건전한 방어벽으로 취급해 세 흐름을 모두 clean으로 표시한 것과 **같은 구조의 실패**다.

## 5. How to cite in Related Work

> Incomplete remediation is not an artefact of any single project's maintenance practices. In the first systematic study of multi-patch vulnerability fixes, Qi et al. identify 1,646 NVD CVEs remediated by more than one patch commit, of which 641 are *incomplete fixes* in which the initial patch failed to eliminate the vulnerability [ESORICS'26]. Cross-site scripting is the single most common weakness class among these multi-patch fixes (519 CVEs), and JavaScript is over-represented relative to its share of single-patch fixes (11.68% versus 9.53%) — precisely the language and bug class that dominate Electron-application advisories. Their evaluation further shows that no existing detector distinguishes a complete fix from an incomplete one: six vulnerability-detection models all fall below 50% accuracy and F1 on incomplete-fix detection, worse than random guessing, and their true-positive rates drop by up to 28.38 points relative to conventional single-patch data. We therefore treat the recurrence of a patched weakness at a sibling sink as a first-class discovery signal rather than as evidence of a poorly maintained project.

> **(KO) 이 논문이 취약점 *발견* 논문 대비 어디에 위치하는가:** 이 논문은 **방어도 발견 도구도 아니고 "측정"** 이다. 그래서 경쟁 상대가 아니라 **논문의 전제를 정당화해 주는 근거**로 쓰는 것이 맞다. 세 가지 용도가 있다.
> 1. **동기 부여.** "SiYuan 한 앱에서 불완전 수정 체인이 두 개 나왔다"는 이 repo의 관찰이 특이 사례가 아니라 641건 규모 현상의 한 인스턴스임을 보증한다. 심사위원이 "그건 그 프로젝트가 관리가 안 된 것 아니냐"고 물을 때의 직접적 답변.
> 2. **갭 확보.** §7.1/§7.2의 실패 결과가 **탐지 쪽 공백을 저자들이 스스로 열어 놓았다.** VD 모델은 패치 전/후 함수를 구별하지 못하고, 클론 탐지기는 형제 위치를 놓친다. Electron 앱에서 "같은 sink 패밀리의 형제 위치를 열거하는" 발견 기법은 바로 이 공백을 겨냥한다고 주장할 수 있다.
> 3. **측정 타당성 경고 재사용.** 09-02에 이 repo가 스스로 발견한 "GHSA 레코드 수 ≠ 발견 건수" 문제와 이 논문의 "URL 수 ≠ 패치 수, 그래서 커밋 ID로 중복 제거" 및 "5.8%는 보안과 무관한 패치"가 같은 계열의 문제다. 논문에서 CVE/advisory 개수로 추세를 주장할 때 이 논문을 인용해 방법론적 주의를 표명하면 방어가 단단해진다.
>
> **주의:** 이 논문에는 Electron이 한 번도 등장하지 않는다. PRIMARY가 아니라 ADJACENT로 인용하고, "JavaScript 비중" 이상의 Electron 관련성을 주장하지 말 것.

## 6. Caveats / what I could not confirm from the text

- **Grounding.** Read from the **arXiv HTML preprint (2607.13206v1)**, not the ESORICS/Springer camera-ready, which does not exist yet (conference is 14–18 Sep 2026). Numbers may shift between preprint and proceedings. Sections read in full: Abstract/§1 header, §2 (Background, partial), §3 Data Collection, §4 Categorization incl. Table 1 and §4.3, §5 Contributing Factors, §6 incl. Tables 2–4, §7 incl. Tables 5–7, §8 Related Work, §9 Discussion/Conclusion. **Not read line-by-line:** §1 Introduction body, §4.1–§4.2 worked examples, §6.0.1 figure values (Fig. 10 similarity/complexity numbers are described qualitatively in the text but the plotted values were not extracted).
- **Author affiliations** are not stated in the arXiv HTML portion read. The ESORICS listing gives only names ("Weiliang Qi, Youpeng Li and Xinda Wang"). Verify before citing.
- **Table 6 arithmetic not independently checked.** The deltas are embedded in MathML in the HTML render; I transcribed the base values and the stated deltas but did not verify that base − delta equals the reported figure in every cell.
- **"Worse than random guessing"** is the authors' characterisation of sub-50% accuracy/F1 on a test set that is itself imbalanced (738 vulnerable / 556 non-vulnerable, i.e. 57/43). Random guessing on that split would not sit exactly at 50%. Quote the claim as theirs, not as an independent conclusion.
- **The C2 "no CVE after 2020" claim** is asserted without a supporting table in the portion read. Treat as an observation, not a measured result.
- **No Electron, NW.js, npm-ecosystem or desktop-framework breakdown** appears anywhere in the text. The JavaScript/TypeScript shares are language-level only; there is no way to tell from this paper how many of those JS multi-patch fixes were in Electron applications.
- **Springer DOI and final page numbers unavailable** until the LNCS volume is published.
