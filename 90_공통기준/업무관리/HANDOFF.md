# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-03-31 (루트 CLAUDE.md 하네스 검증 원칙 승격 — GPT 공동작업 완료)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

하네스 파일럿 2회차 완료 + 루트 CLAUDE.md 하네스 원칙 승격 (GPT 공동작업).

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 수정 | `skill-creator-merged.skill` | harness 모드 Known Exception 처리 규칙 추가, 피드백 루프 4단계 절차표 교체. commit c7dd616f |
| 신설 | `90_공통기준/업무관리/research_하네스2회차.md` | 1회차 결과 현황·구조 파악·변경 영향 범위. SHA: a8c9a892 |
| 신설 | `90_공통기준/업무관리/plan_하네스2회차.md` | Step 1-3 구현 계획, GPT PASS 승인완료. SHA: 54272678 |
| 완료 | `plan_하네스2회차.md` | Step 1-3 체크박스 완료, Evaluator PASS 95점 기록 |
| 갱신 | `TASKS.md` | 하네스 2회차 완료 항목 추가, 루트 CLAUDE.md 승격 완료 표시 |
| 승격 | `CLAUDE.md` | `## 하네스 검증 원칙` 섹션 신설 — 공통 4원칙(사용시점/3인체제/KnownException/피드백루프) |

---

## 3. TASKS 참조 항목

> 상태 판정은 TASKS.md 기준. 아래는 참조용 요약.

| 우선순위 | TASKS 참조 항목 | 비고 |
|---------|---------------|------|
| ~~낮~~ | ~~루트 CLAUDE.md 하네스 원칙 승격~~ | **완료** — 공통 4원칙 승격됨 |
| 낮 | 도메인 STATUS.md 점검 | 조립비정산, 라인배치 STATUS.md 경로 반영 확인 |

---

## 4. 다음 AI가 바로 할 일

1. **OUTER 라인 runOuterLine(295) 재개** — 10_라인배치/CLAUDE.md 참조
3. 도메인 STATUS.md 점검 — 조립비정산, 라인배치
4. 새 작업 시 research.md → plan.md 승인 → 구현 순서 준수 (Plan-First 워크플로우)

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
