# AI Safety & Trending Repos — Daily Tracker

매일 새벽 4시(KST) 자동으로 갱신되는 개인 트래커.

- **`papers/`** — AI privacy / security / LLM interpretability 분야 트렌딩 arxiv 논문 Top 10 (Hugging Face Daily Papers, alphaxiv, arxiv 최근 업로드, X/Reddit 화제)
- **`repos/`** — security / tools / LLM 분야 GitHub 트렌딩 레포 Top 10 (GitHub Trending + 최근 24h 스타 급상승)

## 디렉터리 구조

```
.
├── README.md
├── .gitignore
├── papers/
│   ├── INDEX.json              # arxiv_id → {version, first_seen, last_updated, title}
│   └── YYYY-MM-DD/
│       ├── YYYY-MM-DD.md       # 그날의 Top 10 요약
│       └── pdfs/{arxiv_id}.pdf # 원문 PDF
└── repos/
    ├── INDEX.json              # owner/repo → {first_seen, last_seen, days_on_list, last_stars}
    └── YYYY-MM-DD.md           # 그날의 Top 10 요약
```

## 자동 처리되는 것

### 논문
- 이미 본 논문 (`papers/INDEX.json`에 등록된 arxiv_id) → 같은 버전이면 스킵
- v2/v3 등 새 버전이 뜨면 → **🔄 Updated** 태그로 다시 포함하고 기존 폴더의 마크다운/PDF 갱신
- 기관/저자, HF Daily/alphaxiv 등재 여부, SNS 화제, 업로드 최신성으로 가중 랭킹

### 레포
- 동일 레포 재등장 시 → 연속 트렌딩 일수 (🆕 첫 등장 / 🔥 N일 연속 / 🔁 재등장) 표시
- 24h 스타 증가량(velocity) 계산 (어제 INDEX와 diff)
- 노이즈 필터: 한국어/중국어 번역본, 단순 awesome-list, 학습 노트, 최근 30일 커밋 0인 레포 제외
- security / tools / llm 카테고리 균형 유지

## 수동 운영

```bash
# 그날 결과 직접 다시 돌리고 싶을 때 — Cowork 사이드바의 "Scheduled" 섹션에서 Run now
# git push가 자동으로 안 됐다면
git push
```

루틴은 매 실행 끝에 `git add -A && git commit && git push` 까지 자동으로 시도하며, remote가 없거나 push 실패 시 로그만 남기고 종료한다.
