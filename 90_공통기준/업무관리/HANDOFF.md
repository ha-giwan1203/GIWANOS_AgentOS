# HANDOFF — AI 인수인계 문서

최종 업데이트: 2026-03-28 (line-batch-management.skill 패키지화 완료 — v7→v9 기준 전환)
이 문서는 AI 세션 시작 시 가장 먼저 읽는다.
읽기 순서: HANDOFF.md → STATUS.md → TASKS.md → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

`line-batch-management.skill` 패키지화: v7.md(구버전)를 v9 운영 기준(CLAUDE.md)으로 갱신 후 .skill 파일 공식 생성.

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 신규 | `10_라인배치/라인배치_스킬문서_v9.md` | v7 기반, OUTER_RULES v9 적용 (SNAP-ON 추가, LASER MARKING 단축, JS 버전 v9) |
| 신규 | `90_공통기준/스킬/line-batch-management.skill` | v9.md ZIP 패키지 (9,804 bytes) |
| 이동 | `10_라인배치/라인배치_스킬문서_v7.md` | → `98_아카이브/라인배치_스킬문서_v7_archived_20260328.md` |
| 수정 | `10_라인배치/STATUS.md` | 스킬 패키지 완료 기록 |
| 수정 | `90_공통기준/업무관리/TASKS.md` | 스킬 패키지화 완료 이동, [중] 잔여 1건 |

**GitHub 최종 커밋**: 이번 세션 commit 예정

---

## 3. 미완료 항목

TASKS.md 참조.

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| 중 | 보류 판정 유지 1건 후속 조치 | ENDPART 갱신 기준 확인 (라인배치 스킬 패키지화 완료) |
| 낮 | 파일 정리 2차 (99_임시수집 분류) | |
| 낮 | Slack Bot Token 갱신 | account_inactive 상태, 사용자 직접 재발급 필요 |
| 낮 | 작업 스케줄러 등록 | register_watch_task.bat CMD 직접 실행 필요 |
| 낮 | 도메인 STATUS.md 점검 | 10_라인배치 마이그레이션 경로 반영 확인 |

---

## 4. 다음 AI가 바로 할 일

1. STATUS.md와 TASKS.md 확인 후 [중] 우선순위 항목 착수
2. 다음 우선순위: ENDPART 갱신 기준 확인 (TASKS.md [중] 항목)
3. OUTER 라인 runOuterLine(295) 재개 — 10_라인배치/STATUS.md 참조
4. 도메인별 재개 위치: 10_라인배치/STATUS.md, CLAUDE.md 참조

---

## 5. 주의사항

- 업무리스트 폴더 루트에 임의 폴더 생성 금지 (허용: 90_공통기준/, 98_아카이브/, 도메인 하위 폴더)
- GitHub에 대용량 원본 엑셀 적재 금지
- Notion을 AI 작업 기준 저장소로 사용하지 않는다
- Drive 커넥트는 검색·참조 보조용. 편집 기준 아님
- Slack Bot Token이 account_inactive 상태임 — 자동화 알림 발송 전 토큰 갱신 필요
- 현재 브랜치: `main`. 신규 작업 시 새 브랜치 또는 main 직접 커밋 여부 확인 후 진행
- step4 RSP 역추적 코드(row.iloc[2]/row.iloc[4])는 dead code — 수정 불필요, 파이프라인 결과 영향 없음 확인됨
- Notion 표 내 .md/.py 파일명은 백틱으로 감싸야 자동링크 방지됨 (일반 텍스트 입력 시 재자동링크됨)
