# Round 2 — GPT 본론 응답

> 모델: gpt-5-5-thinking / 5,098자 / 3회 안정
> 가장 강조: R2-2 (행동 교정 메타 0의 경계)

## 한 줄 요약

R5가 도메인 스킬 5개 hook 의존도 0회를 확인했다면 메타 계층을 살릴 명분은 약함. 핵심은 **삭제를 겁내지 말고, 안전·기능에 필요한 최소 5개만 남기는 것**.

## R2-1 4지표 목표선 — 동의

수치별:
- always-loaded ~7100 → <1000: 동의
- rules 300줄 5개 → 100줄 1개: 동의
- Slash 33개 → 5개: 동의
- Skill 평균 305줄 → 80줄: **조건부 동의** (단 MANUAL.md / GLOSSARY / verify script 분리 전제)
- Hook 36개 → 5개: 동의
- Subagent 9개 → 5개: 동의
- Permissions 130개 → 15개: 동의 (포괄 패턴 중심)
- Worktree 17개 → **active 3개** (즉시 삭제 X / archive 후 prune)

**놓칠 약점**: 목표 수치를 "즉시 삭제 수치"로 오해 위험. 실행은 baseline 기록 → archive/backup → prune → verify 순서.

## R2-2 행동 교정 메타 0 — 동의 (가장 강조)

incident_quote.md rules 폐기 동의:
- 본문은 안전 가이드처럼 보여도 작동 방식은 명제형 ("특정 조건이면 응답 도입부에 인용하라")
- 결정론적 보호가 아니라 **행동 교정 프롬프트** → Claude 응답 스타일·판단 흐름 조작
- session_start_restore.sh + incident_repair.py가 이미 기능 수행

처리:
- rules/*에서 제거
- 핵심 내용은 session_start_restore.sh 출력 또는 incident_repair.py 결과로 흡수
- 응답 도입부 강제 인용·명제형 주의 문구·행동 교정 문장 폐기
- archive에는 남기되 active load 금지

**중요 추가 (Claude 선행 답안에 없던 신규)**: completion_gate도 주의. 보존 동의하지만 이 hook이 행동 교정 메시지를 뿜으면 다시 독.

completion_gate 허용 동작:
- git 상태 확인
- 필수 상태문서 갱신 여부 확인
- 미커밋 변경 확인
- 실패 시 deterministic 사유 출력

completion_gate 금지 동작:
- Claude 행동 지침 출력
- 반성 유도
- "다음부터 이렇게 하라" 장문 출력
- GPT/Gemini/share-result 유도

**놓칠 약점**: 가장 위험한 건 "안전 가이드니까 예외로 남기자". **행동 교정 메타는 항상 좋은 명분으로 살아남음**. 안전 가이드라도 실행 코드/검증 명령/보호 hook이 아니면 active load에서 빼야.

## R2-3 GLOSSARY/RAG — 동의

GLOSSARY 채택 동의 + RAG 보류 동의.

### GLOSSARY 권장 구조 (Claude 선행 답안 보강)
```
90_공통기준/glossary/
├── GLOSSARY.json         (제조 용어·약어)
├── LINE_CODES.json       (라인 코드)
├── PROCESS_CODES.json    (공정 코드)
└── PARTNO_RULES.json     (품번 suffix 규칙·SUB/OUTER/ASSY 관계)
```

GLOSSARY에 넣을 것: 제조 용어 / 라인 약어 / 공정명 / ERP·MES 필드명 / 품번 suffix 규칙 / SUB·OUTER·ASSY 관계 / 자주 헷갈리는 한국어·영문 표현

GLOSSARY에 넣지 말 것: 업무 절차 / Claude 행동 규칙 / 토론모드 규칙 / 완료 판정 원칙 / 세션 이력

### RAG 도입 종료 조건 (보류 해제 트리거)
- manual/glossary 50개 이상으로 증가
- grep/read 검색 시간이 반복적으로 3분 이상
- 용어 오판 incident 7일간 5건 이상
- 동기화/색인/권한 관리자 명확

**놓칠 약점**: Gemini는 RAG를 도메인 복잡도 해결책으로 밀 가능성. Claude는 GLOSSARY를 또 SKILL.md에 설명형으로 풀어넣을 가능성. 둘 다 회피. **GLOSSARY는 짧고 기계가 읽는 데이터**, RAG는 지금 보류.

## Round 2 GPT 최종 판정

- 헤비유저 목표 수치: 동의
- 행동 교정 메타 0: 동의
- incident_quote.md rules 폐기: 동의
- GLOSSARY.json: 채택 동의
- RAG: 보류 동의
- Option 3 Hybrid 유지: 동의
- 핵심 5개 hook 보존: 동의 (단 completion_gate는 deterministic 전용으로 축소)
- 세트 A 안전 우선안: 동의
- 31개 hook 폐기: Phase별 진행
- 새 hook/gate/RAG 추가 금지

## 핵심 메시지

> **목표는 새 규칙 추가가 아니라 active load와 행동 교정 메타 제거다.**
> "안전 가이드니까 예외로 남기자"가 가장 위험한 명분.
> 행동 교정 메타는 항상 좋은 명분으로 살아남는다.
