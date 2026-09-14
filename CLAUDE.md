# CLAUDE.md — kpop-persona-agent

> 이 파일은 Claude Code가 이 저장소에서 작업할 때 항상 먼저 읽는 프로젝트 컨텍스트입니다.

## 1. 프로젝트 한 줄 요약

K-pop 아티스트 페르소나 챗봇을 **장기기억 메모리 아키텍처(RAG + 메모리 계층)** 로 구현하고,
그 성능을 **한국어 페르소나 일관성·사실 회상 평가 벤치마크**로 정량 검증하는 프로젝트.
(연구 주제 조합 "A + E")

## 2. 프로젝트 목적

- AI 아티스트 챗봇이 팬 서비스로 성립하려면 (1) 일관된 페르소나, (2) 세션을 넘는 팬 기억, (3) 정량 품질 평가가 동시에 필요하다.
- 이 저장소는 그 세 가지를 하나의 재현 가능한 연구 프로젝트로 묶는다. 결과물은 동작하는 시스템, 한국어 평가셋, 비교 실험표, 워크숍 논문 초안이다.
- 주제 선택 과정은 `docs/01_topic_selection.md`에 있다.
- 공개 문서에는 개인 배경·지원 목표를 쓰지 않는다. 그런 내용은 `CLAUDE.local.md`(gitignore)에 둔다.

## 3. 코드·설명 스타일

- 작성자는 기계공학 출신으로 AI/NLP 초심자에 가깝다. 코드에는 한국어 주석과 "왜 이렇게 했는지"를 짧게 남긴다.
- 과도한 추상화보다 읽히는 코드 우선. 파일 하나가 한 가지 역할만 하도록 유지한다.
- Python/PyTorch, 비동기 처리, 외부 API 연동에는 익숙하다. 그 수준의 설명은 생략해도 된다.

## 4. 연구 질문

> 다층 메모리(단기 대화 버퍼 + 에피소드 메모리 + 구조화 사실 메모리)를 결합한 아티스트 페르소나 챗봇이
> 수십 세션에 걸친 팬 상호작용에서 **개인화 사실 회상**과 **페르소나 일관성**을 동시에 유지할 수 있는가?

부가 질문: LLM-as-judge 기반 한국어 페르소나 평가가 사람 평가와 얼마나 정렬되는가?

## 5. 시스템 설계 (목표 구조)

```
사용자(팬) ─► 대화 컨트롤러(LangGraph)
                 ├─ 단기 버퍼: 최근 N턴
                 ├─ 에피소드 메모리: 세션 요약 → 벡터DB(Chroma)
                 ├─ 사실 메모리: 팬 이름/생일/최애곡 등 구조화 키-값 (SQLite/JSON)
                 ├─ 페르소나 카드: 가상 아티스트 설정(세계관·말투 규칙)
                 └─ LLM: 오픈소스 7~8B (Qwen3 / EXAONE) 또는 API
평가 하네스 ─► 사실 회상 F1 / 페르소나 일관성(PICon식 심문) / RAGAS faithfulness
```

메모리 쓰기 정책은 **규칙 기반 버전**과 **LLM 판단 버전** 두 가지를 만들어 비교한다.
메모리 read/write는 MCP 툴로 노출하는 것을 고려한다(부트캠프 13주차 MCP 모듈 재활용).

## 6. 평가 계획

- 벤치마크 참조: LoCoMo (ACL 2024), LongMemEval (ICLR 2025), CharacterEval, PICon
- 한국어 자체 평가셋: 가상 아티스트 페르소나 기준 멀티세션 팬 대화 100~200개 합성 후 직접 검수.
  질문 유형은 LongMemEval 분류(single-session / multi-session / knowledge-update / temporal-reasoning / abstention) 차용.
- 지표: 사실 회상 F1, 페르소나 일관성 점수, RAGAS faithfulness, judge–사람 라벨 상관(Spearman, 50개 이상)
- 비교군: 메모리 없음 / 롱컨텍스트만 / RAG만 / 제안 3층 구조

## 7. 데이터·윤리 원칙

- **실존 아티스트의 이름·말투·목소리·사진은 사용하지 않는다.** 가상 아티스트 페르소나를 직접 설계한다.
- 공개 데이터: AI Hub 페르소나 대화·멀티세션 대화(승인 필요, 저장소에 원본 커밋 금지), PersonaChat, LoCoMo, LongMemEval.
- 데이터 원본·API 키·모델 가중치는 `.gitignore` 처리. `.env.example`만 커밋.

## 8. 저장소 구조 (목표)

```
kpop-persona-agent/
├─ CLAUDE.md                  # 이 파일
├─ README.md                  # 연구 질문·아키텍처·평가 계획 1페이지 (외부용)
├─ CLAUDE.local.md             # 비공개 컨텍스트 (gitignore)
├─ docs/
│   ├─ 01_topic_selection.md           # 연구 주제 8개 비교 + A+E 선택 근거 (공개용 요약)
│   ├─ 02_roadmap.md                   # 10주 로드맵 체크리스트
│   ├─ 03_study_plan.md                # 부트캠프 모듈 학습 순서
│   └─ 04_data_notes.md                # AI Hub 데이터셋 구조 노트
├─ private/                   # 개인 메모·원본 리서치 (gitignore, 커밋 금지)
├─ persona/
│   └─ artist_card.yaml       # 가상 아티스트 페르소나 카드
├─ data/raw/aihub/            # AI Hub 원본 zip (gitignore, 커밋 금지)
├─ src/
│   ├─ memory/                # short_term.py, episodic.py, factual.py, policy_rule.py, policy_llm.py
│   ├─ agent/                 # LangGraph 대화 그래프
│   ├─ retrieval/             # 임베딩·벡터DB
│   └─ llm/                   # 모델 로더(로컬/API)
├─ eval/
│   ├─ datasets/              # 합성 평가셋(검수본만)
│   ├─ judge/                 # LLM-as-judge 프롬프트·스코어러
│   └─ run_eval.py
├─ notebooks/
├─ tests/
├─ .env.example
├─ .gitignore
├─ pyproject.toml (또는 requirements.txt)
└─ LICENSE
```

## 9. 로드맵

| 주차 | 목표 |
|---|---|
| 1 | 저장소·README·문서 정리, AI Hub 신청, 벤치마크 포맷 확인, 페르소나 카드 설계 |
| 2 | 최소 동작 파이프라인(페르소나 프롬프트 + 단기 버퍼 + 벡터 검색), 일관성 점수 1개 자동 산출 |
| 3~5 | 3층 메모리 구현, 쓰기 정책 2종, 지식 갱신·시간 추론 케이스 대응 |
| 6~8 | 한국어 평가셋 합성·검수, judge 구현, 사람 라벨 50개 상관 계산 |
| 9~10 | 비교 실험 4종, 결과표, 4쪽 워크숍 논문 초안 |

## 10. 작업 규칙 (Claude Code용)

- 커밋 메시지: `type(scope): 요약` 형식, 한국어 요약 허용. 예) `feat(memory): 에피소드 메모리 요약·저장 구현`
- 브랜치: `main` 보호, 기능은 `feat/*`, 문서는 `docs/*`
- 새 파일 생성 시 이 문서의 구조를 따르고, 구조를 바꿀 때는 이 문서도 함께 수정한다.
- 실행 환경: macOS(주 개발) + Windows WSL2(Ubuntu 22.04, GPU 실험). GPU는 24GB 단일 카드 가정.
- 외부 API 호출 코드는 반드시 `.env`에서 키를 읽는다. 키를 코드에 쓰지 않는다.
- 설명은 한국어로. 기계공학 출신 초심자가 읽는다는 전제로 "왜"를 한 줄 덧붙인다.
- 불확실한 라이브러리 버전·API는 추측하지 말고 확인 후 사용한다.
