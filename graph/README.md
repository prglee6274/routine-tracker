# 📄 Papers Relationship Graph

논문들이 서로 어떤 관계인지 — 누가 누구를 인용/확장/반박하는지, 저자를 공유하는지, 주제가 얼마나 가까운지 — 인터랙티브 그래프로 보여준다.

## 열기
`graph/index.html` 를 브라우저에서 열면 된다 (자체완결 단일 파일, 인터넷은 vis-network CDN 로드에만 필요).

- **노드** = 논문. 색 = 분야(파랑 interpretability · 빨강 security · 초록 privacy · 회색 other). 크기 = 코퍼스 내 피인용수(영향력).
- **엣지**:
  - **인용** (방향 A→B, A가 B를 참조) — AI가 관계를 분류: `확장(teal)` · `베이스라인(orange)` · `비교(purple)` · `반박(red)` · `배경(gray)`
  - **공저자** (파랑) — 저자를 공유하는 논문
  - **주제 유사도** (초록 점선) — 키워드/서브토픽 공유(강한 것만)
- 좌측 패널에서 엣지·분야·기간 필터, 검색, 물리/이웃강조 토글. 노드 클릭 시 우측에 상세(저자·키워드·arXiv/PDF 링크·관계 목록).

## 파이프라인 (재생성)
리포 루트에서 순서대로:

```bash
python3 graph/extract.py all          # 저자(마크다운) + arxiv-id 인용 (PDF), 캐시 증분
python3 graph/enrich_title_cites.py   # 참고문헌에서 코퍼스 제목 매칭 인용 (id로 안 걸리는 인용 보강)
python3 graph/label_prep.py           # 새 인용 엣지의 in-text 컨텍스트 추출 → cache/edges_to_label.json
#   → edges_to_label.json 의 각 엣지를 extends/baseline/compares/rebuts/background 로 분류,
#     cache/semantic_edges.json 에 누적 (AI 분류; 엣지 많으면 subagent)
python3 graph/build_graph.py          # graph_data.json + index.html 생성
```

## 캐시 (`graph/cache/`, 증분 처리용 — 커밋됨)
- `authors.json` — {arxiv_id: [저자,...]} (마크다운에서 추출)
- `citations.json` — {id: [코퍼스 내 인용 id,...]} (arxiv-id 매칭)
- `citations_title.json` — 제목 매칭 인용
- `semantic_edges.json` — {"A->B": {type, evidence}} AI 관계 라벨 (재계산 비용이 크므로 보존)
- `edges_to_label.json` (transient, gitignore) — 라벨 대기 큐

## 튜닝 (`build_graph.py` 상단 상수)
`TOPIC_MIN_SHARED`, `TOPIC_TOPK_PER_NODE` (주제 엣지 밀도), `AUTHOR_CLIQUE_MAX`, `TOPIC_GENERIC_MAX` (범용 키워드 제외).

매일 새벽 논문 수집(`daily-ai-safety-papers`) 끝에 자동 증분 갱신된다.
