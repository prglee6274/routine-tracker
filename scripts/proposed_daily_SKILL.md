<!--
이 파일은 daily-ai-safety-papers 스케줄 태스크에 적용할 갱신 본문입니다.
스케줄 태스크 세션 안에서는 본인을 수정할 수 없는 정책 때문에 직접 못 덮고
워크스페이스에 둡니다.

적용 방법(둘 중 하나):
  (A) 일반 Claude 세션에서 다음을 부탁하세요:
      "scripts/proposed_daily_SKILL.md 내용으로 daily-ai-safety-papers
       스케줄 태스크 prompt를 update 해 줘."
  (B) Cowork → Settings → Scheduled tasks 에서 daily-ai-safety-papers 의
      prompt 필드를 아래 frontmatter 아래 본문(--- 다음 줄부터 끝까지)으로
      덮어쓰세요.

변경 요약:
  - INDEX 스키마에 category/subtopics/keywords 필드 추가됨을 명시
  - taxonomy 절 추가 (마이그레이션에서 쓴 카테고리·서브토픽 목록)
  - Step 5에 카테고리 분류 작업 추가
  - Step 5b 신규: papers/refs/{id}.json 캐싱 (scripts/fetch_refs.py 호출)
  - 마크다운 템플릿에 카테고리/Refs 줄 추가
  - commit 메시지에 refs 건수 포함
-->

---
name: daily-ai-safety-papers
description: 매일 새벽 4시 - AI privacy/security/LLM interpretability arxiv 트렌딩 논문 Top 10 (v2 갱신 추적, INDEX.json, refs 캐싱, 자동 git push)
---

오늘의 AI privacy / AI security / LLM interpretability 관련 트렌딩 논문 Top 10을 수집한다.

## 워크스페이스
- 루트: `/Users/pang/Documents/Claude/Projects/routine 생성/`
- bash 마운트 경로: `/sessions/sharp-jolly-lamport/mnt/routine 생성/`
- 동일 폴더가 git repo이며 매 실행 끝에 add+commit+push 까지 시도한다.

## 출력 위치
- 인덱스: `papers/INDEX.json` (entry 스키마: `{version, title, first_seen, last_updated, folder, category, subtopics[], keywords[]}`)
- 그날 폴더: `papers/YYYY-MM-DD/` (KST 기준 오늘 날짜)
  - `YYYY-MM-DD.md` — 요약 마크다운
  - `pdfs/{arxiv_id}.pdf` — 논문 PDF (파일명은 version 없는 base id)
- 인용 캐시: `papers/refs/{arxiv_id}.json` — `scripts/fetch_refs.py` 가 채움 (arxiv ar5iv HTML 파싱)

## taxonomy (`INDEX.json` `_taxonomy` 필드와 일치)
- `privacy`: differential_privacy, membership_inference, unlearning, data_extraction, federated_privacy, pii_leakage, agent_privacy
- `security`: jailbreak, prompt_injection, backdoor, adversarial, red_teaming, agent_safety, safety_eval, alignment_robustness, multimodal_attack, defense_mechanism
- `interp`: sae, activation_steering, circuits, probing, feature_attribution, representation, mechanistic_position, interp_method

## 수집 절차

### 1. 후보 모으기 (각 소스에서 따로 수집한 뒤 병합)
- **Hugging Face Daily Papers**: WebFetch `https://huggingface.co/papers`
- **alphaxiv 트렌딩**: WebFetch `https://www.alphaxiv.org/explore` 또는 `https://www.alphaxiv.org/explore?type=trending`
- **arxiv 최근 1~3일**: WebFetch
  - `https://arxiv.org/list/cs.CR/recent`
  - `https://arxiv.org/list/cs.CL/recent`
  - `https://arxiv.org/list/cs.LG/recent`
  - `https://arxiv.org/list/cs.AI/recent`
- **SNS 화제**: WebSearch — 최근 1주일 내 X / Reddit / 블로그에서 화제가 된 논문
  - 예: `arxiv (interpretability OR "ai security" OR "ai privacy" OR jailbreak OR "membership inference") site:x.com OR site:reddit.com`

### 2. 주제 필터 (다음 키워드 중 최소 1개에 해당해야 함)
- **AI privacy**: differential privacy, membership inference, data extraction, federated learning privacy, training data leakage, PII, unlearning
- **AI security**: adversarial attacks, jailbreak, prompt injection, model stealing, backdoor, red-teaming, alignment attacks, agent safety
- **LLM interpretability**: mechanistic interpretability, sparse autoencoder (SAE), circuit analysis, probing, feature attribution, activation patching, representation engineering, scaling monosemanticity

### 3. 중복/v2 처리 (가장 중요)
실행 시작 시 `papers/INDEX.json`을 읽어 메모리에 로드. 후보 논문마다:
- arxiv_id (version 없는 base, 예: `2401.12345`) 와 version (예: `v1`, `v2`, `v3`) 을 추출.
- INDEX 에 같은 base id 가 있고:
  - **version이 같음** → 오늘 후보에서 제외 (이미 다뤘음)
  - **version이 더 높음 (v1 → v2 등)** → 오늘 리스트에 포함하되 `update: true` 로 표시. 항목에 `🔄 Updated v{prev} → v{new}` 라벨. 과거 폴더(`first_seen` 폴더)의 마크다운/PDF도 갱신 (PDF 재다운로드 후 덮어쓰기, 마크다운에는 변경 노트 추가)
  - **PDF 파일이 디스크에 없음** → 다운로드 시도 (이력만 있고 파일 누락된 경우 보충)
- INDEX 에 없으면 → 신규 처리

### 4. 랭킹 후 Top 10 선정 (다음 가중 평가)
- HF Daily Papers / alphaxiv 트렌딩 등재 (가장 강한 시그널, +3)
- SNS 언급 (트위터/Reddit/블로그 댓글 수, +2)
- 업로드 최신성 (최근 1-3일, +1)
- 영향력 있는 기관/저자 (Anthropic, DeepMind, OpenAI, Google Research, Meta FAIR, MIT, Stanford, CMU 등, +1)
- v2 이상 업데이트는 신규 후보보다 살짝 페널티 (-0.5) — 새 논문 우선

### 5. 각 논문 처리
- arxiv abstract 페이지 (`https://arxiv.org/abs/{base_id}`) WebFetch 로 제목·저자·abstract·version 확보
- PDF 다운로드: `mcp__workspace__bash` 로
  ```
  curl -fL --retry 2 -o "/sessions/sharp-jolly-lamport/mnt/routine 생성/papers/YYYY-MM-DD/pdfs/{base_id}.pdf" "https://arxiv.org/pdf/{base_id}.pdf"
  ```
  실패 시 마크다운에 "PDF 다운로드 실패" 표기하고 계속.
- **카테고리 분류**: abstract + 키워드 후보를 보고 `category` (privacy/security/interp 중 하나) 와 `subtopics` (위 taxonomy에서 1~4개 선택, 가장 핵심 topic이 첫 항목) 를 결정. `keywords` 는 마크다운에 적은 키워드 리스트와 동일하게 저장.
- INDEX 갱신:
  ```
  entries[base_id] = {
    version, title,
    first_seen, last_updated: today, folder: "YYYY-MM-DD",
    category, subtopics: [...], keywords: [...]
  }
  ```
  (신규면 first_seen=today, 갱신이면 first_seen 유지)

### 5b. References 캐싱
오늘 처리한 모든 base_id 에 대해 `scripts/fetch_refs.py` 를 호출해 `papers/refs/{base_id}.json` 을 생성:
```
cd "/sessions/sharp-jolly-lamport/mnt/routine 생성" && \
python3 scripts/fetch_refs.py {base_id_1} {base_id_2} ... --sleep 1.0
```
스크립트는 arxiv ar5iv HTML 에서 `<ul class="ltx_biblist">` 안의 `<li class="ltx_bibitem">` 를 파싱해 각 reference 의 label/text/year/arxiv_id/url 를 JSON 으로 저장. HTML 빌드가 없거나 비표준 레이아웃이면 `count:0` + `note:"unavailable: ..."` 스텁을 남기고 다음으로 넘어감 (실패 자체는 워크플로를 막지 않음). 마크다운에는 `Refs` 줄에 건수 표기.

### 6. 마크다운 형식
```
# AI Safety/Interpretability Papers — YYYY-MM-DD

> 출처: HF Daily {n1} · alphaxiv {n2} · arxiv recent {n3} · SNS {n4} · 갱신 {n5}

## {순위}. {제목}  {🆕 또는 🔄 Updated v1→v2}

- **저자**: {저자 리스트, 5명 초과 시 et al.}
- **카테고리**: `{category}` / {subtopics 콤마 구분}
- **키워드**: `keyword1`, `keyword2`, ...
- **출처**: HF Daily / alphaxiv / arxiv recent / SNS
- **arxiv**: [{base_id}](https://arxiv.org/abs/{base_id}) ({version})
- **PDF**: [`./pdfs/{base_id}.pdf`](./pdfs/{base_id}.pdf)
- **Refs**: [`./refs/{base_id}.json`](../refs/{base_id}.json) ({refs_count}건)

**핵심 요약** (3-5문장 한국어):
{문제 → 방법 → 결과/기여 순으로 간결하게. abstract 직역 금지, 본인이 이해한 압축}

{v2 갱신인 경우 추가:}
**v{prev} → v{new} 변경점**: {abstract diff에서 보이는 주요 변경 1-2문장}
```

### 7. 갱신된 옛 항목 처리
v2 갱신이 있었던 경우, `papers/{first_seen_folder}/{first_seen_folder}.md` 파일의 해당 논문 섹션 끝에 다음을 append:
```
> 🔄 {today_date}: v{prev} → v{new} 로 갱신됨. 변경점: {요약}
```

### 8. README.md 업데이트 (선택)
필요하면 루트 `README.md` 의 "최근 추가" 같은 섹션을 갱신할 수 있다 (지금은 스킵해도 됨).

### 9. Git commit + push
실행 끝에 다음을 bash 로 실행:
```
cd "/sessions/sharp-jolly-lamport/mnt/routine 생성" && \
git add -A && \
git diff --cached --quiet || git -c user.email=gwangyeal@gmail.com -c user.name="무명의 석사생" commit -m "papers: add YYYY-MM-DD top 10 (n new, m updated, r refs)" && \
git push 2>&1 | tail -20 || echo "[push 실패 — remote 미설정 또는 인증 문제, 로컬 커밋만 유지]"
```

## 작업 끝
사용자에게 `computer:///Users/pang/Documents/Claude/Projects/routine 생성/papers/YYYY-MM-DD/YYYY-MM-DD.md` 링크와 함께 한 줄 요약 (신규 X편, 갱신 Y편, refs 캐시 Z건, 핵심 토픽 N개) 만 짧게 보고.
