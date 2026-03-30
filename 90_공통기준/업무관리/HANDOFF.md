# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-03-30 (상태 원본 단일화 + 업무 원본 2계층 규칙 + 스킬 설치 + Notion 동기화 완료)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

상태 원본 단일화 규칙 확립 + 업무 원본 2계층 규칙 추가 + 스킬 버전 갱신/미설치 스킬 설치 + Notion 동기화 + GPT PASS 루틴 완료.

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 신설 | `CLAUDE.md` | 상태 원본 단일화 규칙 섹션 + 업무 원본 계층 규칙 섹션 + 세션 시작 판단 규칙 섹션 추가. commit 597df4f2, 870bfb8b, 18fb0fed |
| 재정의 | `TASKS.md` | 상태 유일 원본 선언 헤더 + 현업 원본과 역할 구분 주석 추가 |
| 재정의 | `STATUS.md` | 완료 이력 테이블 삭제 → 운영 요약/재개 위치/주의사항/경로 전용으로 재구성. 상태성 표현 제거 |
| 재정의 | `HANDOFF.md` | 상태 선언 제거, 세션 메모 전용 + TASK 참조 방식 가이드 명시 |
| 설치 | 스킬 3종 | `chomul-module-partno`, `supanova-deploy`, `line-batch-outer-main` 미설치 스킬 AppData에 추출 |
| 갱신 | `debate-mode` | v1.2 → v2.2 (contenteditable DIV 입력, 완료 감지 개선) |
| 동기화 | Notion STATUS | commit 18fb0fed 기준 반영. 스케줄러 ✅ 완료, 신규 완료 항목 6건 추가. GPT PASS |
| 동기화 | Notion TASKS | 대기 중 정리 (낮 우선순위 2건만 유지), 완료 이력 신규 행 추가. GPT PASS |
| 확립 | 운영 루틴 | Claude→push→GPT PASS→Notion 동기화 루틴 정착 |

---

## 3. TASKS 참조 항목

> 상태 판정은 TASKS.md 기준. 아래는 참조용 요약.

| 우선순위 | TASKS 참조 항목 | 비고 |
|---------|---------------|------|
| 낮 | 루트 CLAUDE.md 하네스 원칙 승격 | 파일럿 검증 2회 이상 후 검토 (1회 완료) |
| 낮 | 도메인 STATUS.md 점검 | 조립비정산, 라인배치 STATUS.md 경로 반영 확인 |

---

## 4. 다음 AI가 바로 할 일

1. **OUTER 라인 runOuterLine(295) 재개** — 10_라인배치/CLAUDE.md 참조
2. 루트 CLAUDE.md 하네스 원칙 승격 — 파일럿 2회 후 검토 (현재 1회 완료)
3. 도메인 STATUS.md 점검 — 조립비정산, 라인배치

**GPT 협업 루틴**: 작업 완료 → push → GPT 지정 채팅방 보고 → PASS 확인

---

## 5. 주의사항

- 업무리스트 폴더 루트에 임의 폴더 생성 금지 (허용: 90_공통기준/, 98_아카이브/, 도메인 하위 폴더)
- GitHub에 대용량 원본 엑셀 적재 금지
- Notion을 AI 작업 기준 저장소로 사용하지 않는다
- Drive 커넥트는 검색·참조 보조용. 편집 기준 아님
- Slack Bot Token 갱신 완료, 멘션(<@U096LU8KNN8>) 추가 완료 — 폰 알림 정상 동작 확인됨
- 현재 브랜치: `main`. 신규 작업 시 새 브랜치 또는 main 직접 커밋 여부 확인 후 진행
- step4 RSP 역추적 코드(row.iloc[2]/row.iloc[4])는 dead code — 수정 불필요, 파이프라인 결과 영향 없음 확인됨
- Notion 표 내 .md/.py 파일명은 백틱으로 감싸야 자동링크 방지됨 (일반 텍스트 입력 시 재자동링크됨)
- 상태 원본 단일화 완료 (TASKS 단일 원본) — STATUS/HANDOFF/Notion은 참조 전용
- 현업 업무 원본: `90_공통기준/업무관리/업무_마스터리스트.xlsx` — AI 세션과 현업 업무 구분 필수
