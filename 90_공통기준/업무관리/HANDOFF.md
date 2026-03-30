# HANDOFF — AI 인수인계 문서

최종 업데이트: 2026-03-30 (Notion 대시보드 재구조화 + Phase 5 안정화 + 문서 정합성 수정)
이 문서는 AI 세션 시작 시 가장 먼저 읽는다.
읽기 순서: HANDOFF.md → STATUS.md → TASKS.md → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

Phase 5(notion_sync.py) 안정화 + Notion 업무리스트 운영 대시보드 재구조화 + TASKS/STATUS/HANDOFF 문서 정합성 수정.

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 수정 | `90_공통기준/업무관리/notion_sync.py` | heading-as-container 폐기 → 페이지 직접 append. pagination, per-page dedup 추가. commit fa8a04fa, 562dffab |
| 수정 | `90_공통기준/업무관리/watch_changes_launcher.vbs` | 한글 경로 인코딩 문제 제거 — WScript.ScriptFullName 기반 상대경로 |
| 완료 | 작업 스케줄러 등록 | `업무리스트_WatchChanges` 로그온 트리거 등록. Python 직접 실행(VBS 우회). PID 정상 확인 |
| 완료 | Slack Bot Token 갱신 | .env 교체 완료, Phase 4 정상 동작 |
| 재구조화 | Notion 📁 업무리스트 운영 | GPT 제안 구조 반영: 운영요약/파이프라인상태/미완료작업/완료이력/바로가기 |
| 수정 | `90_공통기준/업무관리/TASKS.md` | Step6 FAIL분리 [완료] 처리, 스케줄러 [완료] 처리 |
| 수정 | `90_공통기준/업무관리/STATUS.md` | 미완료 목록 정리 (스케줄러/Step6 제거) |
| 확립 | 운영 루틴 | Claude→push→GPT Evaluator 검증→PASS 확정 루틴 정착 |

---

## 3. 미완료 항목

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| 중 | 상태 원본 단일화 설계 | TASKS/STATUS/HANDOFF/Notion이 같은 상태를 각자 보유 → 정합성 문제 반복 원인. 다음 세션 검토 |
| 낮 | 루트 CLAUDE.md 하네스 원칙 승격 | 파일럿 검증 2회 이상 후 검토 (1회 완료) |
| 낮 | 도메인 STATUS.md 점검 | 조립비정산, 라인배치 STATUS.md 경로 반영 확인 |

---

## 4. 다음 AI가 바로 할 일

1. **상태 원본 단일화 설계** — TASKS/STATUS/HANDOFF/Notion이 같은 항목을 각자 보유하는 구조가 정합성 문제의 근본 원인. GPT와 설계 방향 상의 후 구현
2. **OUTER 라인 runOuterLine(295) 재개** — 10_라인배치/CLAUDE.md 참조
3. 루트 CLAUDE.md 하네스 원칙 승격 — 파일럿 2회 후 검토 (현재 1회 완료)

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
