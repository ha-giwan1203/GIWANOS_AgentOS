# 업무리스트 프로젝트

자동차 부품 제조업(삼송 G-ERP) 업무 자동화 저장소.

## 도메인 진입

| 키워드 | 도메인 문서 |
|--------|-----------|
| 토론 / 토론모드 / 공동작업 | `90_공통기준/토론모드/CLAUDE.md` |
| 정산 / 조립비 / settlement | `05_생산실적/조립비정산/CLAUDE.md` |
| 라인배치 / OUTER / ERP 라인배정 | `10_라인배치/CLAUDE.md` |
| MES 업로드 / 실적 올려 | `90_공통기준/스킬/production-result-upload/SKILL.md` |
| 일상점검 / ZDM | `90_공통기준/스킬/zdm-daily-inspection/SKILL.md` |

도메인 키워드 감지 시 해당 문서를 먼저 읽는다.

## 상태 원본

작업 상태는 **TASKS.md에만 기록**한다.
- 우선순위: TASKS.md → STATUS.md → HANDOFF.md → Notion
- 현업 업무: `업무_마스터리스트.xlsx` 우선. AI 작업: TASKS.md 우선
- Git이 기준 원본. Notion은 보조. 중복 유지 금지

## 완료 판정 (사람/GPT 판정 기준 — 자동 게이트 아님)

기준 문서 확인 + 반영 위치 확인 + Git 실물 존재 + TASKS.md 비충돌 → PASS
미충족 시: 정합 / 부분반영 / 미반영 / 보류 / 기준 미확인 / 임시검토

> completion_gate는 TASKS/HANDOFF 갱신 여부만 검사하는 최소 게이트다. 위 4개 기준 전체를 자동 검증하지 않는다.

## 종료 시 갱신
1. TASKS.md → 2. 도메인 STATUS.md → 3. HANDOFF.md → 4. Notion (필요 시)

## 운영 안정성
- settings/hook 파일 변경 후 반드시 세션 재시작 (변경사항은 세션 시작 시 캐싱됨)
- 장시간 세션 방치 금지 — 도메인/의제 전환 시 세션 재시작 권장

## 금지
- 원본 xlsx/docx/pdf 직접 수정
- 승인 없는 파일명/시트명/컬럼명 변경
- 검증 없이 값 덮어쓰기
- Git 미확인 추측 답변
- 미푸시 상태를 완료로 간주
- Claude 설명만 듣고 PASS
