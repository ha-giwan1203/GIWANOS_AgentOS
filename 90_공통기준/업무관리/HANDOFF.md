# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-03-31 (커버리지 96% + auto-commit 실동작 확인 + 스킬 10종 패키징 — GPT 공동작업)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

자동화 체인 복구 + Hooks 실전 패턴 적용 + 외부 리소스 분석 (GPT 공동작업).

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 수정 | `auto_commit_config.yaml` | branch: "업무리스트"→"main", push_on_commit: false→true (f0a62cba) |
| 신설 | `protect_files.sh` | PreToolUse 보호 파일 deny/log 2계층 (로컬) |
| 갱신 | `notify_slack.sh` | 60초 dedup 스팸 방지 (로컬) |
| 신설 | `AGENTS_GUIDE.md` | 6계층 아키텍처 맵 + 구성요소 목록 + 세션 체크리스트 (487f1a8d) |
| 신설 | research 4건 | watch_changes_commit_fail, hooks_실전패턴, 멀티에이전트_A2, 아키텍처_B1 |
| 신설 | plan 4건 | 위 research 대응 plan 문서 |
| 수정 | STATUS.md/HANDOFF.md | doc-check FAIL 3건 + task-status-sync FAIL 4건 수정 |

---

## 3. TASKS 참조 항목

> 상태 판정은 TASKS.md 기준. 아래는 참조용 요약.

| 우선순위 | TASKS 참조 항목 | 비고 |
|---------|---------------|------|
| ~~낮~~ | ~~루트 CLAUDE.md 하네스 원칙 승격~~ | **완료** — 공통 4원칙 승격됨 |
| ~~낮~~ | ~~도메인 STATUS.md 점검~~ | **완료** (2026-03-31) |

---

## 4. 다음 AI가 바로 할 일

1. ~~auto_commit_config 수정~~ — 완료 (f0a62cba, GPT PASS)
2. ~~Hooks 실전 패턴 적용~~ — 완료 (0db38bcb, GPT PASS)
3. ~~A2 멀티에이전트 research~~ — 완료 (0e0bf1d2, subagents 적합 판정)
4. ~~A2 subagent 파일럿~~ — 완료 (GPT PASS)
5. ~~B1 아키텍처 정리~~ — 완료 (AGENTS_GUIDE.md, GPT PASS)
6. ~~auto-commit 실제 커밋 확인~~ — **완료** (TASKS.md에 자동 항목 생성 확인)
7. ~~영상/리소스 안건 10건~~ — 완료
8. ~~커버리지 맵 19%→96%~~ — 스킬 10종 패키징 완료 (26/27)
9. [대기] Slack files:write scope — 사용자 조작 필요
10. [대기] #5 급여 정산 스킬화 — research 필요 (커버리지 유일 미커버)
11. [차단] 정산 파이프라인 4월 테스트 — 4월 데이터 대기

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
