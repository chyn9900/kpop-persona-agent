# kpop-persona-agent

**장기기억 메모리 아키텍처 기반 K-pop 아티스트 페르소나 챗봇과 한국어 페르소나 평가 벤치마크**

가상 K-pop 아티스트 페르소나 챗봇을 다층 메모리(단기 버퍼 + 에피소드 메모리 + 구조화 사실 메모리)로 구현하고,
수십 세션에 걸친 팬 상호작용에서 **개인화 사실 회상**과 **페르소나 일관성**을 한국어 벤치마크로 정량 평가한다.

## 연구 질문

> 다층 메모리(단기 대화 버퍼 + 에피소드 메모리 + 구조화 사실 메모리)를 결합한 아티스트 페르소나 챗봇이
> 수십 세션에 걸친 팬 상호작용에서 **개인화 사실 회상**과 **페르소나 일관성**을 동시에 유지할 수 있는가?

부가 질문: LLM-as-judge 기반 한국어 페르소나 평가는 사람 평가와 얼마나 정렬되는가?

## 아키텍처

```
사용자(팬) ─► 대화 컨트롤러 (LangGraph)
                 │
                 ├─ 단기 버퍼        : 최근 N턴 원문
                 ├─ 에피소드 메모리  : 세션 요약 → 벡터DB (Chroma) → 유사도 검색
                 ├─ 사실 메모리      : 팬 이름·생일·최애곡 등 키-값 (SQLite/JSON)
                 ├─ 페르소나 카드    : 가상 아티스트 세계관·말투 규칙 (YAML)
                 └─ LLM              : 오픈소스 7~8B (Qwen3 / EXAONE) 또는 API
                 │
                 ▼
             응답 생성
                 │
                 ▼
   메모리 쓰기 정책 (규칙 기반 vs LLM 판단, 두 버전 비교)
                 │
                 ▼
   평가 하네스 ─► 사실 회상 F1 / 페르소나 일관성 (PICon식 심문) / RAGAS faithfulness
```

메모리 read/write는 MCP 툴로 노출하는 것을 고려한다.

## 평가 계획

- **참조 벤치마크**: LoCoMo (ACL 2024), LongMemEval (ICLR 2025), CharacterEval, PICon
- **한국어 자체 평가셋**: 가상 아티스트 페르소나 기준 멀티세션 팬 대화 100~200개 합성 후 직접 검수.
  질문 유형은 LongMemEval 분류 차용: single-session / multi-session / knowledge-update / temporal-reasoning / abstention
- **지표**
  - 사실 회상 F1
  - 페르소나 일관성 점수 (LLM-as-judge)
  - RAGAS faithfulness
  - judge–사람 라벨 상관 (Spearman, 50개 이상)
- **비교군**: 메모리 없음 / 롱컨텍스트만 / RAG만 / 제안 3층 구조

## 로드맵 (10주)

| 주차 | 목표 |
|---|---|
| 1 | 저장소·문서 정리, 데이터 신청, 벤치마크 포맷 확인, 페르소나 카드 설계 |
| 2 | 최소 동작 파이프라인 + 일관성 점수 1개 자동 산출 |
| 3~5 | 3층 메모리 구현, 쓰기 정책 2종, 지식 갱신·시간 추론 대응 |
| 6~8 | 한국어 평가셋 합성·검수, judge 구현, 사람 라벨 상관 계산 |
| 9~10 | 비교 실험 4종, 결과표, 워크숍 논문 초안 |

상세 체크리스트: [docs/02_roadmap.md](docs/02_roadmap.md)

## 윤리 원칙

- **실존 아티스트의 이름·말투·목소리·사진은 사용하지 않는다.** 페르소나는 가상 아티스트로 직접 설계한다.
- 공개 데이터(AI Hub, PersonaChat, LoCoMo, LongMemEval)는 라이선스 조건을 따르며 원본을 저장소에 커밋하지 않는다.
- API 키·모델 가중치·원본 데이터는 `.gitignore`로 제외하고 `.env.example`만 커밋한다.

## 저장소 구조

```
persona/      가상 아티스트 페르소나 카드
src/memory/   단기·에피소드·사실 메모리, 쓰기 정책 2종
src/agent/    LangGraph 대화 그래프
src/retrieval/ 임베딩·벡터DB
src/llm/      모델 로더 (로컬 / API)
eval/         평가셋(검수본), judge 프롬프트·스코어러, run_eval.py
docs/         리서치 보고서, 주제 후보, 로드맵, 학습 계획
```

## 문서

- [01 연구 주제 후보 비교와 선택 근거](docs/01_topic_selection.md)
- [02 10주 로드맵](docs/02_roadmap.md)
- [03 학습 계획](docs/03_study_plan.md)
- [04 AI Hub 데이터셋 구조 노트](docs/04_data_notes.md)

## 라이선스

MIT © 2026 Chanyeon Byun
