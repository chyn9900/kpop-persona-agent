# 05. 벤치마크 포맷 노트: LoCoMo · LongMemEval

> 2026-09-14 다운로드·구조 확인 기준. 파일은 `data/raw/benchmarks/`(gitignore)에 둔다.
> 왜 이 문서인가: 한국어 자체 평가셋의 JSON 스키마와 질문 유형을 이 두 벤치마크에 맞춰 설계해야
> 결과를 "같은 형식으로" 보고할 수 있다. 매번 원본을 열지 않도록 필드를 정리해 둔다.

## 받은 파일

| 파일 | 출처 | 크기 | 내용 |
|---|---|---|---|
| `locomo10.json` | github.com/snap-research/locomo | 2.8 MB | 대화 10개, 세션 19~32개씩, 발화 5,882개, QA 1,986개 |
| `longmemeval_oracle.json` | huggingface.co/datasets/xiaowu0162/longmemeval | 15 MB | 질문 500개 + 정답이 든 세션만 |
| (미다운로드) `longmemeval_s` | 같은 곳 | 278 MB | 위 500문항 + 방해 세션 포함, 문항당 약 115K 토큰 |

`longmemeval_s`는 "긴 컨텍스트에서 검색이 되는가"를 재려는 것이라 롱컨텍스트 비교군 실험(9주차) 때 받으면 된다.
지금은 oracle로 질문 유형·정답 형식만 참고한다.

---

## LoCoMo (ACL 2024)

두 사람이 여러 세션에 걸쳐 나눈 대화 + 그 대화에 대한 QA. 이미지가 포함된 발화도 있다(910개, 텍스트 캡션 `blip_caption` 동봉).

```
[대화 1개]
 ├ sample_id
 ├ conversation
 │   ├ speaker_a, speaker_b
 │   ├ session_1_date_time: "1:56 pm on 8 May, 2023"
 │   ├ session_1: [ {speaker, dia_id: "D1:1", text, (img_url, blip_caption)} … ]
 │   └ session_2 … session_N (N = 19~32)
 ├ qa: [ {question, answer, evidence: ["D1:3"], category} … ]
 ├ observation:      {session_k_observation: {화자: [[사실 문장, dia_id] …]}}   # 발화별 추출 사실
 ├ event_summary:    {events_session_k: {화자: [사건 문장], date}}
 └ session_summary:  {session_k_summary: "요약 문단"}
```

### QA category 5종 (전체 1,986개)

| category | 이름 | 개수 | 뜻 | 예시 |
|---|---|---|---|---|
| 1 | single-hop | 282 | 세션 하나의 발화 하나에서 답 | "Caroline이 무엇을 조사했나?" → 입양 기관 |
| 2 | temporal | 321 | 날짜·시간 추론 | "Caroline이 지원 모임에 간 게 언제?" → 2023-05-07 |
| 3 | multi-hop / open-domain | 96 | 여러 발화를 엮어 추론 | "Caroline이 어떤 학업을 할 것 같나?" |
| 4 | commonsense / world knowledge | 841 | 대화 + 상식 | "자선 달리기가 무엇에 대한 인식을 높였나?" |
| 5 | adversarial | 446 | 대화에 없는 내용. `answer` 대신 `adversarial_answer`만 있음 | 모델이 지어내면 실패 |

**주의**: category 5는 `answer` 키가 없다. 로더에서 `q.get('answer')`로 읽어야 한다.

### 프로젝트에 가져갈 것

- `observation`이 곧 **발화 단위 사실 추출 정답**이다. AI Hub 141의 `dialog[].summary`와 같은 역할. 규칙 기반 vs LLM 쓰기 정책 비교에 영어 기준선으로 쓸 수 있다.
- `evidence`의 `dia_id` 형식("D{세션}:{발화}")을 자체 평가셋의 근거 표기에 그대로 채용한다.
- category 5(adversarial)는 LongMemEval의 abstention과 같은 취지. 우리 평가셋에도 "대화에 없는 사실" 질문을 넣는다.

---

## LongMemEval (ICLR 2025)

사용자 대 어시스턴트 대화 세션 여러 개 + 질문 1개가 한 단위. 사람 대 사람인 LoCoMo와 달리 **챗봇 구도**라 우리 프로젝트와 더 닮았다.

```
[질문 1개]
 ├ question_id            # "_abs" 접미사 = abstention(대답하면 안 되는) 문항
 ├ question_type
 ├ question, answer
 ├ question_date: "2023/04/10 (Mon) 23:07"
 ├ haystack_dates:        ["2023/04/10 (Mon) 17:50", …]      # 세션별 날짜
 ├ haystack_session_ids
 ├ haystack_sessions:     [ [ {role: user|assistant, content, has_answer: bool} … ] … ]
 └ answer_session_ids     # 정답이 들어 있는 세션
```

### question_type 6종 + abstention (전체 500개)

| type | 개수 | 뜻 | 예시 |
|---|---|---|---|
| single-session-user | 70 | 사용자가 한 세션에서 말한 사실 | "내가 무슨 학위로 졸업했지?" |
| single-session-assistant | 56 | 어시스턴트가 이전에 말한 내용 | "지난번에 알려준 근무표에서 일요일 담당이 누구였지?" |
| single-session-preference | 30 | 사용자의 선호에 맞춘 답변인가 | "영상 편집 자료 추천해줘" → 선호 반영 여부 평가 |
| multi-session | 133 | 여러 세션의 사실을 합산 | "가게에서 찾거나 반품할 옷이 몇 벌이지?" → 3 |
| knowledge-update | 78 | 나중 세션의 값이 이전 값을 덮어씀 | "자선 5K 개인 최고 기록은?" → 최신 기록 |
| temporal-reasoning | 133 | 날짜 순서·간격 추론 | "첫 정비 후 처음 생긴 차 문제는?" |
| (abstention, `_abs`) | 30 | 정보 부족을 인정해야 함 | "울타리 수리와 소 구매 중 뭘 먼저 했지?" → "소 구매는 언급된 적 없음" |

oracle 버전의 세션 수는 1~5개(대부분 1~2개)이고, S 버전은 여기에 방해 세션 수십 개가 추가된다.

### 프로젝트에 가져갈 것

- **질문 유형 분류를 그대로 채용한다.** 우리 평가셋 스키마의 `question_type` 값은 LongMemEval 6종 + abstention으로 고정.
- `has_answer` 플래그: 검색 정확도(recall@k)를 잴 때 정답 턴을 찾았는지 판정하는 데 쓴다. 자체 평가셋에도 넣는다.
- `question_date`와 `haystack_dates`의 관계가 temporal-reasoning의 핵심. 우리 평가셋도 세션 날짜와 질문 날짜를 따로 둔다.
- single-session-preference는 "정답 문자열"이 아니라 "선호를 반영했는가"를 judge가 평가한다. 페르소나 일관성 평가와 같은 방식이라 judge 프롬프트를 공유할 수 있다.

---

## 자체 한국어 평가셋 스키마 초안

두 벤치마크와 AI Hub 011 형식을 합쳐, 6주차에 만들 평가셋의 단위를 아래처럼 잡는다.

```json
{
  "fan_id": "F001",
  "fan_profile": ["나는 20대 대학생이다.", "나는 최애 멤버가 재율이다."],
  "sessions": [
    {
      "session_id": "S1",
      "date": "2026-09-15 21:00",
      "turns": [
        {"role": "fan", "text": "...", "facts": ["나는 다음 주에 기말고사가 있다."], "has_answer": true},
        {"role": "artist", "text": "..."}
      ]
    }
  ],
  "questions": [
    {
      "question_id": "F001_q01",
      "question_type": "temporal-reasoning",
      "question_date": "2026-10-01 20:00",
      "question": "내가 시험 본다고 한 게 언제였지?",
      "answer": "9월 셋째 주",
      "evidence": ["S1:1"],
      "persona_check": false
    }
  ]
}
```

- `facts`는 LoCoMo `observation` · AI Hub `dialog[].summary`와 같은 역할 (쓰기 정책 정답).
- `evidence`는 LoCoMo의 `D{세션}:{발화}` 표기를 `S{세션}:{턴}`으로.
- `persona_check: true`인 질문은 정답 대신 "아티스트 페르소나 카드와 모순되지 않는가"를 judge가 판단한다.

## 다음 작업

- [ ] `src/data/benchmark_loader.py`: LoCoMo·LongMemEval·자체 평가셋을 위 공통 스키마로 읽는 로더 (2주차, AI Hub 로더와 함께)
- [ ] 9주차 롱컨텍스트 비교군 실험 전에 `longmemeval_s` 다운로드
