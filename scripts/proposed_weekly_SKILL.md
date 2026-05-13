<!--
NEW 스케줄 태스크: weekly-paper-review
스케줄: 매주 일요일 23:55 KST (cron: `55 23 * * 0`)

적용 방법:
  (A) 일반 Claude 세션에서:
      "scripts/proposed_weekly_SKILL.md 를 weekly-paper-review 라는
       새 스케줄 태스크로 만들어 줘. cron='55 23 * * 0'."
  (B) Cowork → Settings → Scheduled tasks → +New 로 생성:
      - taskId: weekly-paper-review
      - cronExpression: 55 23 * * 0
      - prompt: 아래 frontmatter 다음 본문(--- 이후) 전체

작업 의도:
  지난 7일(월요일 00:00 ~ 일요일 23:55 KST) 동안 INDEX.json 에 first_seen
  으로 들어온 논문들을 category × subtopic 으로 클러스터링해서 한 페이지로
  요약. 다음 주에 어디를 더 깊이 볼지, 어느 토픽이 식어가는지 한눈에.
-->

---
name: weekly-paper-review
description: 매주 일요일 23:55 KST - 지난 7일치 논문을 카테고리 × 서브토픽으로 클러스터링한 회고 마크다운 생성
---

지난 7일간 수집한 AI safety / privacy / interpretability 논문들을 한 페이지로 회고한다.

## 워크스페이스
- 루트: `/Users/pang/Documents/Claude/Projects/routine 생성/`
- bash 마운트 경로: `/sessions/sharp-jolly-lamport/mnt/routine 생성/` (실제 마운트 이름은 세션마다 다르므로 `ls /sessions/*/mnt/` 로 먼저 확인)
- 같은 폴더가 git repo이며 작업 끝에 add+commit+push 까지 시도한다.

## 출력 위치
- `papers/weekly/YYYY-Www.md` (ISO 주차, 예: `2026-W19.md`)
  - 디렉토리 없으면 `mkdir -p`

## 기간 정의 (KST 기준)
- **이번 주**: 이번 주 월요일 00:00 → 이번 주 일요일 23:55
- `INDEX.json` 의 `first_seen` 이 이 범위 안인 entry 들이 대상

## 절차

### 1. 기간 산출 + 대상 entry 수집
```bash
cd "/sessions/sharp-jolly-lamport/mnt/routine 생성"
python3 - << 'PY'
import json, datetime, os
TZ = datetime.timezone(datetime.timedelta(hours=9))
now = datetime.datetime.now(TZ)
# 이번 주 월요일 00:00 KST
weekday = now.weekday()  # Mon=0 .. Sun=6
monday = (now - datetime.timedelta(days=weekday)).replace(hour=0,minute=0,second=0,microsecond=0)
sunday = monday + datetime.timedelta(days=6, hours=23, minutes=55)
iso_year, iso_week, _ = now.isocalendar()
print(f"week={iso_year}-W{iso_week:02d}  range={monday.date()} → {sunday.date()}")
idx = json.load(open("papers/INDEX.json"))
in_range = []
for aid, e in idx["entries"].items():
    fs = e.get("first_seen","")
    try:
        d = datetime.date.fromisoformat(fs)
    except: continue
    if monday.date() <= d <= sunday.date():
        in_range.append((aid, e))
print("count:", len(in_range))
PY
```

### 2. 클러스터링
대상 entry 들을 `(category, primary_subtopic)` 으로 그룹화. primary_subtopic = `subtopics[0]`.
같은 카테고리 안에서는 subtopic 그룹 크기 내림차순, 그룹 안에서는 first_seen 오름차순으로 정렬.

서브토픽이 비어 있는 entry 는 `(category, "_uncategorized")` 로 모음.

### 3. 마크다운 작성
```
# Weekly Paper Review — YYYY-Www  ({Mon} ~ {Sun} KST)

> 이번 주 신규 {N}편 · privacy {p} · security {s} · interp {i}편
> (직전 주 대비 {±x}편, 신규 서브토픽 {…}, 식어가는 서브토픽 {…})

## 한 주의 흐름 (3-5문장 한국어)

{이번 주 새로 들어온 논문들에서 보이는 주제 패턴, 반복되는 키워드, 눈에 띄는
기관/저자, 어느 카테고리가 두꺼웠는지 등을 자유 서술. 직전 주의 review 마크다운
이 있다면 참조해 비교 한 줄 추가.}

---

## privacy ({p}편)

### {subtopic_slug} ({n}편)
- **[{title}](../{folder}/{folder}.md#L{anchor})** — {arxiv_id} · {first_seen}
  - {one-line takeaway: 마크다운 핵심 요약 첫 문장에서 발췌하거나 압축}
- ...

### ...

## security ({s}편)

(같은 형식)

## interp ({i}편)

(같은 형식)

---

## 다음 주에 더 볼만한 것 (선택, 2-3개)

- {예: "SAE 관련 논문이 이번 주 3편 — 그 중 X 논문의 평가 방법론을 다음 주 깊이 읽어볼 가치"}
- ...

## refs 메모

- 이번 주 추가된 references 총 {합계}건, 그 중 arxiv 인용 {n}건
- 내부 cross-reference (이번 주 논문이 INDEX에 이미 있는 다른 논문을 인용): {n}건 — `scripts/refs_xref.py` 로 확인 가능 (없으면 스킵)
```

### 4. (선택) cross-reference 카운트
`papers/refs/{aid}.json` 의 references 중 arxiv_id 가 INDEX 에 존재하는 경우를 카운트:
```python
import json, os
idx = json.load(open("papers/INDEX.json"))
known = set(idx["entries"].keys())
xref = 0; total_ax = 0
for f in os.listdir("papers/refs"):
    d = json.load(open(f"papers/refs/{f}"))
    for r in d.get("references", []):
        if r.get("arxiv_id"):
            total_ax += 1
            if r["arxiv_id"] in known:
                xref += 1
print(f"arxiv refs: {total_ax}, internal xref: {xref}")
```

### 5. Git commit + push
```bash
cd "/sessions/sharp-jolly-lamport/mnt/routine 생성" && \
git add -A && \
git diff --cached --quiet || git -c user.email=gwangyeal@gmail.com -c user.name="무명의 석사생" commit -m "weekly: review YYYY-Www" && \
git push 2>&1 | tail -10 || echo "[push 실패 — 로컬 커밋만 유지]"
```

## 작업 끝
사용자에게 한 줄: `computer:///Users/pang/Documents/Claude/Projects/routine 생성/papers/weekly/YYYY-Www.md` 링크 + "이번 주 N편, 핵심 토픽 T1·T2·T3" 정도만 짧게 보고.
