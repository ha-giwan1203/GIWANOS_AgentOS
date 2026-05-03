# 업무리스트 프로젝트

@.claude/rules/essentials.md

자동차 부품 제조업(삼송 G-ERP) 업무 자동화 저장소.

## 인덱스 (Phase 2 통폐합 — 세션137)

상시 로딩 1개 파일로 압축. 5개 → 1개 (data-and-files / external_models / hook_permissions / incident_quote / work_mode_protocol → essentials).
incident_quote.md는 폐기 (Round 2 합의: 흡수 없이 archive). 폐기본은 `98_아카이브/_deprecated_v1/rules/`에 보존.

| 주제 | 문서 |
|------|------|
| 작업 모드 5종 + R1~R5 + E + hook/permissions + 외부 모델 + 데이터·파일 + 운영 | [.claude/rules/essentials.md](.claude/rules/essentials.md) |
| 토론모드 코어 | `90_공통기준/토론모드/CLAUDE.md` |

## 핵심 원칙 (요약)

- **사용자 명시 발화 = 1순위 입력**. 발화가 있으면 그 안에서 Claude가 세부 판단·실행. 발화 부재 시 SKILL.md/메모리/기존 답변 grep으로 도출. 세부 결정을 사용자에게 떠넘기지 않는다.
- **질문 허용 5조건 (그 외 묻기 금지)**: (1) 필수 입력값 부재 (2) 기준 문서·실물 데이터 충돌 (3) ERP/MES 비가역 반영 직전 대상/일자/라인/건수 확인 (4) hook/settings/SKILL Step/CLAUDE.md 수정 = C 모드 전환 (5) 사용자가 명시적으로 선택 요구. 자세한 근거는 `feedback_authority_ladder.md`.
- **모드 판정 후 진입**: A 실무 / B 분석 / C 시스템 수정 / D 토론 / E 장애 복구. 상세는 work_mode_protocol.md.
- **시스템 수정은 plan-first + R1~R5**. 세부는 work_mode_protocol.md C 섹션.
- **시스템 개선은 모드 E 또는 사용자 명시 모드 C 요청에 한정** (glimmering-churning-reef 안전안).
- **Git이 기준 원본**. 미푸시 상태를 완료로 간주 금지.
- **Git 워크플로우 (durable authorization)**: 본 저장소는 워크트리+머지 모델 운영 중. 사용자가 "푸시해라"·"push해라"·"main에 푸시해라"·"머지하고 푸시" 등 push 발화 시 `git push origin main` 즉시 허용 (머지 commit 포함, 별도 재확인 단계 생략). PR 워크플로우 의무 아님.

## 도메인 진입

| 키워드 | 도메인 문서 |
|--------|-----------|
| 토론 / 토론모드 / 3자 토론 / 공동작업 / 공유 | `90_공통기준/토론모드/CLAUDE.md` → `/debate-mode` 스킬 |
| NotebookLM / 노트북 / 노트북lm | `90_공통기준/notebooklm/CLAUDE.md` → `/notebooklm` 스킬 |
| 정산 / 조립비 / settlement | `05_생산실적/조립비정산/CLAUDE.md` |
| 라인배치 / OUTER / ERP 라인배정 | `10_라인배치/CLAUDE.md` |
| MES 업로드 / 실적 올려 | `90_공통기준/스킬/production-result-upload/SKILL.md` |
| 일상점검 / ZDM | `90_공통기준/스킬/zdm-daily-inspection/SKILL.md` |
| ERP/MES 잔존 청소 / D0 중복 | `90_공통기준/erp-mes-recovery-protocol.md` |
| 급여 / 단가 | `02_급여단가/CLAUDE.md` |
| 생산계획 | `04_생산계획/CLAUDE.md` |
| 생산관리 | `06_생산관리/CLAUDE.md` |

도메인 키워드 감지 시 해당 문서를 먼저 읽는다.

## 상태 원본

- TASKS: `90_공통기준/업무관리/TASKS.md` (AI 작업 상태 유일 원본)
- HANDOFF: `90_공통기준/업무관리/HANDOFF.md` (세션 인수인계 메모)
- STATUS: 각 도메인 하위 `STATUS.md`
- 우선순위: TASKS > STATUS > HANDOFF > Notion
- 현업 업무 마스터: `90_공통기준/업무관리/업무_마스터리스트.xlsx`
- 상세 점검: `/현재상태` 슬래시 명령어로 lazy load

## 완료 판정 (사람/GPT 판정 — 자동 게이트 아님)

기준 문서 확인 + 반영 위치 확인 + Git 실물 존재 + TASKS.md 비충돌 → PASS.
미충족 시: 정합 / 부분반영 / 미반영 / 보류 / 기준 미확인 / 임시검토.

종료 시 갱신 순서: TASKS → 도메인 STATUS → HANDOFF → Notion.

## 응답 형식

- 일반 질문: 결론 / 이유 / 다음 행동
- 시스템 분석(B): 관찰 / 판단 / 필요한 확인
- 시스템 수정(C): plan-first + R1~R5
- 토론모드(D): 라벨/검증/채택보류버림

자동 형식 슬롯 강제 안 함. 사용자 명시 요청 시 활성.

**자체 판단 형식 (질문 허용 5조건 외 모든 결정)**: 판단 → 근거 → 실행 → 검증. "어떻게 할까요"·"진행할까요"·"A/B 중 선택"·"원하시면"·"사용자 결정 대기" 표현 금지.

## 금지

- 원본 xlsx/docx/pdf 직접 수정
- 승인 없는 파일명/시트명/컬럼명 변경
- 검증 없이 값 덮어쓰기
- Git 미확인 추측 답변
- 미푸시 상태를 완료로 간주
- Claude 설명만 듣고 PASS
