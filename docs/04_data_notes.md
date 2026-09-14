# 04. AI Hub 데이터셋 구조 노트

> 2026-09-14 다운로드·구조 확인 기준. 원본은 `data/raw/aihub/` 아래에 두고 절대 커밋하지 않는다.
> 왜 이 문서인가: 평가셋 설계와 로더 코드를 짤 때 매번 zip을 열어보지 않도록 필드 구조를 한 번에 정리해 둔다.

## 다운로드 현황

| 폴더 | 데이터셋 | 용량 | zip 수 | 상태 |
|---|---|---|---|---|
| `044.페르소나 대화/` | 2022 한국어 블렌더봇 데이터 | 132 MB | 80 | 승인·다운로드 완료 |
| `141.한국어 멀티세션 대화/` | 한국어 멀티세션 대화 (2022) | 543 MB | 12 | 승인·다운로드 완료 |
| `011.일상대화 한국어 멀티세션 데이터/` | 생성형AI 일상대화 한국어 멀티세션 (2023) | 2.9 GB | 12 | 승인·다운로드 완료 |

공통 구성: `Training/` · `Validation/` × `01.원천데이터(TS/VS)` · `02.라벨링데이터(TL/VL)`.
**라벨링데이터(L)만 쓰면 된다.** 원천데이터는 같은 대화의 요약·페르소나 정보가 빠진 버전이다.

### 압축 해제 주의

- `044.페르소나 대화`의 zip은 내부 파일명이 CP949(한글 Windows) 인코딩이라 macOS `unzip`이 "Illegal byte sequence"로 실패한다.
  → Python `zipfile`로 열고 파일명은 `name.encode('cp437').decode('cp949')`로 되돌린다. 또는 zip을 풀지 않고 `zipfile.read()`로 바로 읽는다.
- 나머지 두 데이터셋은 파일명이 `/`로 시작해 `unzip`이 경고를 내지만 정상적으로 풀린다.
- 로더는 **zip을 풀지 않고 바로 읽는 방식**으로 짠다. 3.5 GB를 풀어두면 디스크·동기화 부담만 커진다.

---

## 044. 페르소나 대화 (블렌더봇)

- 파일 단위: 대화 1개 = JSON 1개. 주제 20개(가족, 아티스트/공연, 여가/오락 …)별로 zip이 나뉜다.
- 화자 2명이 각자 페르소나 문장 5개를 받고 그 인물인 것처럼 대화. 단일 세션.

```
info
 ├ id, name, category, topic            # 예: topic '아티스트/공연'
 ├ evaluation {avg_rating, grade}       # 대화 품질 평가(1~5)
 └ personas[2]
     ├ persona_id
     └ persona[5] {profile, profile_major, profile_minor}
           # 예: "나는 대학원에서 물리학을 전공하고 있다." / 직업군 / 학생
utterances[N] {utterance_id, persona_id, text, terminate}
```

**프로젝트 활용**
- `TL_아티스트,공연` / `TL_미디어,콘텐츠` 주제가 팬 대화 말투 참고에 가장 가깝다.
- 페르소나 문장 형식("나는 ~다." 5문장 + 대분류/소분류 태그)을 가상 아티스트 카드 설계에 차용한다.
- 한계: 세션 1개짜리라 장기기억 평가에는 못 쓴다. 페르소나 일관성 judge 개발용 예시로만 쓴다.

---

## 141. 한국어 멀티세션 대화 (2022)

- 파일 단위: 멀티세션 대화 1개 = JSON 1개. `session2/3/4` zip은 세션 개수 기준 분류.
- 화자 2명(사람 대 사람) 각자 페르소나 5문장. 세션 사이에 "5일" 같은 시간 간격이 명시된다.

```
FileInfo {filename, sessionLevel}
participantsInfo {speaker1, speaker2: gender, age, occupation, 거주지, educationLevel}
personaInfo
 ├ clInfo {personaID, personaFeatures[5], speakerType}   # 예: "나는 중학교 수학 교사이다."
 └ cpInfo {…}
topicInfo {topicID, topicType, topicTitle}                # 예: 교육 / 전공
sessionInfo[k]
 ├ nthSession, sessionID, prevSessionID
 ├ prevTimeInfo {timeNum, timeUnit}                      # 예: 5 / 일
 ├ dialog[N] {speaker, utterance, summary, date, time}
 │     # summary: 그 발화에서 새로 드러난 페르소나 사실 ("나는 문창과라 글을 쓰고 있다.")
 ├ sessionPersonaSummary {speaker1[], speaker2[]}        # 이 세션에서 새로 나온 사실
 └ prevAggregatedpersonaSummary {speaker1[], speaker2[]} # 이전 세션까지 누적된 사실
```

**프로젝트 활용 (핵심)**
- `dialog[].summary`가 곧 **"이 발화에서 저장할 사실"** 정답 라벨이다. 메모리 쓰기 정책(규칙 vs LLM)의 정밀도·재현율을 이걸로 직접 잰다.
- `prevAggregatedpersonaSummary`는 **사실 메모리의 정답 상태**다. 세션 k 시작 시점에 메모리에 있어야 할 사실 목록.
- `prevTimeInfo`로 temporal-reasoning 질문("5일 전에 뭐 한다고 했지?")을 만들 수 있다.

---

## 011. 생성형AI 일상대화 한국어 멀티세션 (2023)

- 파일 단위: 멀티세션 대화 1개 = JSON 1개. 구조는 141과 비슷하지만 **사람(apprentice) 대 챗봇(wizard)** 구도다.
- wizard는 문서 검색 결과(`context.contents`)를 보고 답하는 지식 챗봇. 세션 간격은 1시간~7주로 다양하다.

```
participantsInfo {speaker1, speaker2 + major}
personaInfo
 ├ apprenticeInfo {personaID, personaFeatures[3], speakerType}
 │     # 예: "나는 색소폰 연주를 가끔 한다", "나는 요즘, 자주 화가 난다"
 └ wizardInfo {personaFeatures[1]}                        # 예: "나는 인물에 대해 잘 아는 챗봇이다."
topicInfo {largeCategory, mediumCategory, smallCategory} # 예: 직업 / 예술·디자인·방송 / 인물
sessionInfo[k]
 ├ prevTimeInfo {timeNum, timeUnit}                      # 1시간 ~ 7주
 ├ sessionKeywords[]
 ├ dialog[N] {speaker, utterance, timestamp(ms), summary,
 │            context {query, contents[{documentID, documentTitle, content[]}]},
 │            selectedContents[]}
 ├ sessionSummary {apprentice[], wizard[], dialogSummary}
 └ prevAggregatedSummary {apprentice[], wizard[]}
```

세션 간격 분포(검증 session2 300개 표본): 1시간·2주·7주·3시간·6주·7시간·1주·5주·6일·2시간·4시간·1일 순으로 고르게 섞여 있다.

**프로젝트 활용**
- 사람 대 챗봇 구도가 "팬 대 아티스트 챗봇"과 가장 닮았다. 평가셋 합성 시 세션 구조·시간 간격·요약 형식을 이 데이터 형식에 맞춘다.
- `dialogSummary`(세션 요약 한 문장)는 에피소드 메모리 요약 프롬프트의 출력 형식 참고.
- 주의: wizard 발화에 실존 인물(가수·지휘자) 위키 정보가 들어 있다. 페르소나 학습·생성에는 쓰지 않고 구조만 참고한다(윤리 원칙).

---

## 평가셋 설계에 바로 가져갈 것

| LongMemEval 질문 유형 | 만들 때 쓸 필드 |
|---|---|
| single-session | 141/011 `dialog[].summary` |
| multi-session | 141/011 `prevAggregatedSummary` 누적 사실 |
| knowledge-update | 141 `sessionPersonaSummary`에서 이전 사실과 충돌하는 항목 |
| temporal-reasoning | 141/011 `prevTimeInfo` + `date`/`timestamp` |
| abstention | 페르소나에 없는 사실을 묻는 질문을 직접 생성 |

## 다음 작업

- [ ] `src/data/aihub_loader.py`: zip을 풀지 않고 세 데이터셋을 공통 스키마(`sessions[] → turns[] {speaker, text, facts[]}`)로 읽는 로더 (2주차)
- [ ] 141 데이터로 규칙 기반 사실 추출기의 정밀도·재현율 기준선 측정 (4주차)
- [ ] 011 형식을 참고해 팬–아티스트 합성 대화 스키마 확정 (6주차)
