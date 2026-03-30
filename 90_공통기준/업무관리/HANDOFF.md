# HANDOFF — AI 인수인계 문서

최종 업데이트: 2026-03-30 (Step 6 FAIL 분리 구현 완료 + debate-mode v2.0)
이 문서는 AI 세션 시작 시 가장 먼저 읽는다.
읽기 순서: HANDOFF.md → STATUS.md → TASKS.md → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 작업 목적

하네스 엔지니어링(Planner→Generator→Evaluator 3인 체제) 파일럿 도입.
조립비정산 도메인부터 Evaluator 기준표 적용. 루트 CLAUDE.md 반영은 검증 후 승격.

---

## 2. 실제 변경 사항

| 구분 | 대상 | 핵심 변경 |
|------|------|----------|
| 수정 | `05_생산실적/조립비정산/CLAUDE.md` | 하네스 Evaluator 기준표 섹션 추가 |
| 신규 | `90_공통기준/업무관리/하네스_운영가이드.md` | 3인 체제 / 컨텍스트 리셋 / 판정 규칙 (DRAFT) |
| 신규 | `90_공통기준/업무관리/하네스_스킬평가기준표.md` | 스킬 Rubric / 판정 기준 (DRAFT) |
| 수정 | `90_공통기준/스킬/skill-creator-merged.skill` | `harness` 모드 추가 — Planner→Generator→Evaluator 3단계 + 평가기준표 연결 + 피드백 루프 |
| 수정 | `90_공통기준/스킬/debate-mode/SKILL.md` | **v2.0** — 입력방식(native setter+InputEvent), 표형식 금지, Step1.5 미확인응답 점검, push 완료 후 GPT 보고 순서 강제 |
| 수정 | `05_생산실적/조립비정산/03_정산자동화/step6_검증.py` | **FAIL 2레벨 분리** — KNOWN_EXCEPTIONS 레지스트리, `chk()` severity 파라미터, SP3M3 RSP 미매칭 → WARNING, overall 3단계(FAIL/WARNING/PASS) |
| 완료 | Notion 자동화 | STATUS/TASKS 페이지에 GPT 자동 분류 시스템 통합 연결 완료, notion_sync.py 동작 확인 |
| 확립 | 운영 루틴 | Claude→push→GPT Evaluator 검증→PASS 확정 루틴 정착 |

---

## 3. 미완료 항목

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| 완료 | ~~step7 WARNING 별도 섹션 표시~~ | commit 34b04828, GPT PASS |
| 낮 | 루트 CLAUDE.md 하네스 원칙 승격 | 파일럿 검증 2회 이상 후 검토 (1회 완료) |
| 낮 | 작업 스케줄러 등록 | register_watch_task.bat CMD 직접 실행 필요 |
| 낮 | 도메인 STATUS.md 점검 | 10_라인배치 마이그레이션 경로 반영 확인 |

---

## 4. 다음 AI가 바로 할 일

1. **샘플 XLSX 실검증** — step6+step7 파이프라인 실행 후 03_검증결과 시트 색상/행 배치 육안 확인 (GPT 권고)
2. **debate-mode.skill 재빌드** — SKILL.md v2.0 반영 패키징 필요
3. OUTER 라인 runOuterLine(295) 재개 — 10_라인배치/CLAUDE.md 참조

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
