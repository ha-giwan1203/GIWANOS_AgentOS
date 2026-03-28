---
name: debate-mode
description: >
  Claude가 브라우저로 ChatGPT 화면을 직접 읽고 반박/질문을 생성하여 반자동 AI 대 AI 토론을 진행하는 스킬.
  사용자가 "토론모드", "AI 토론", "GPT랑 토론해", "debate-mode", "ChatGPT에게 반박해", "GPT 의견 들어봐",
  "토론 시작", "GPT랑 싸워봐", "GPT한테 물어보고 반박해", "AI끼리 토론" 등을 언급하면 반드시 이 스킬을 사용할 것.
  API 없이 브라우저 자동화만으로 동작하며, Claude가 비판자·검증자 역할을 맡고 GPT가 제안자 역할을 한다.
  GPT-Claude 4라운드 공동 설계 토론으로 합의된 핵심 로직(완료 감지 2중 신호 + read_page assistant 블록 추출)을 사용한다.
---

# 토론모드 (debate-mode) 스킬

## 개요

Claude가 브라우저에서 ChatGPT 화면을 직접 읽고, 이전 답변을 바탕으로 반박/질문을 생성하여 반자동 AI 대 AI 토론을 이어가는 Cowork 스킬.

**GPT와 Claude의 4라운드 설계 토론을 통해 합의된 핵심 로직 기반.**

- API 사용 금지
- Notion 등 외부 저장소 불필요
- 브라우저 화면 텍스트 직접 읽기 방식
- 로컬 로그 파일 저장
- 목적: 완전 무인 자동화가 아닌 실전형 반자동 코워크

---

## 트리거 조건

사용자가 다음을 언급하면 이 스킬을 사용:
- "토론모드", "AI 토론", "GPT랑 토론", "debate-mode"
- "ChatGPT에게 반박해", "GPT 의견 들어봐"
- "토론 시작", "GPT랑 싸워봐"

---

## 합의된 핵심 로직 (GPT-Claude 공동 설계)

### 1. 완료 감지 (2중 신호)
```
신호 1: read_page → 전송버튼 enabled 상태 확인
신호 2: get_page_text 2회 비교 (2초 간격, 동일하면 완료)
제외:   aria-busy (ChatGPT 실제 노출 여부 불확실 → 제거)
```

### 2. 최신 답변 식별
```
read_page → role=assistant 블록 필터 → 마지막 visible 항목 추출
```

### 3. 읽기 방식 우선순위
```
1순위: read_page (접근성 트리, DOM 변경에 강인)
2순위: get_page_text (노이즈 있으나 완료 비교용으로 활용)
3순위: CSS 선택자 (최후 수단, DOM 변경 취약)
```

---

## 실행 절차

### Step 1. 초기화
1. ChatGPT 탭 확인 (`tabs_context_mcp`)
2. ChatGPT 새 채팅 열기 (`navigate https://chatgpt.com/new`)
3. 로그 파일 초기화 (`logs/debate_YYYYMMDD_HHMMSS.md`)
4. 토론 주제 및 라운드 수 확인 (기본: 4라운드)

### Step 2. 역할 설정
- **Claude**: 반대측 / 비판자 / 검증자
- **GPT**: 찬성측 / 제안자 / 설계자
- **심판**: Claude가 마지막에 요약 및 합의안 정리

### Step 3. 토론 루프 (최대 6라운드)
```
[라운드 N]
1. 현재 주제/질문을 ChatGPT 입력창에 입력 (computer → type → Return)
2. 완료 감지 대기:
   - read_page에서 전송버튼 enabled 확인
   - get_page_text 스냅샷 A 저장
   - 2초 대기
   - get_page_text 스냅샷 B 저장
   - A == B → 완료 확정
3. 최신 답변 추출:
   - read_page → assistant role 마지막 블록 텍스트
4. 답변 로그 저장 (logs/ 폴더)
5. 반박/질문 생성:
   - GPT 답변 핵심 3가지 추출
   - 논리적 허점 / 현실 제약 / 미합의 쟁점 지적
   - 300자 이내로 압축
6. 다음 라운드 입력으로 전환
```

### Step 4. 종료 조건
- 최대 라운드 도달
- "합의" 키워드 GPT 답변에서 감지
- 동일 주장 2회 이상 반복 감지
- 오류 3회 연속

### Step 5. 마무리
1. Claude가 전체 토론 요약 작성
2. 합의안 / 미합의 쟁점 분리
3. 즉시 실행안 3가지 도출
4. 로그 파일 최종 저장

---

## 토론 규칙

| 항목 | 기준 |
|------|------|
| 최대 라운드 | 6턴 |
| 답변 길이 | 200~400자 |
| 새 논점 | 매 턴 최소 1개 이상 |
| 반복 주장 | 2회 이상 시 종료 트리거 |
| 오류 재시도 | 최대 3회 |
| 마지막 출력 | 합의안 + 즉시 실행안 |

---

## 로그 구조

```
logs/
├── debate_YYYYMMDD_HHMMSS.md
├── debate_YYYYMMDD_HHMMSS.json
└── errors/
```

### 로그 항목 (턴별)
```
- Debate ID
- Round
- Speaker (Claude / GPT)
- Prompt
- Response
- Key Points (핵심 3가지)
- Timestamp
- Status
```

---

## 오류 대응

| 상황 | 대응 |
|------|------|
| 전송버튼 미감지 | computer → screenshot → 수동 위치 재확인 |
| 완료 신호 불일치 | 5초 추가 대기 후 재확인 |
| 답변 블록 미감지 | get_page_text 전체 텍스트 fallback |
| 3회 연속 실패 | 토론 중단, 현재까지 로그 저장 후 보고 |

---

## 금지 사항

- API 직접 호출 금지
- 동일 주장 3회 이상 반복 금지
- 6라운드 상한 초과 금지
- 억지 합의 금지 (합의 안 되면 미합의로 명시)
