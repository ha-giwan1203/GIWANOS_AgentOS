# 업무리스트 프로젝트

@.claude/rules/cowork-rules.md
@.claude/rules/data-and-files.md

자동차 부품 제조업(삼송 G-ERP) 업무 자동화 저장소.

## 인덱스 (debate_20260428_201108_3way 빼는 안 1 적용 — 세션122)

상시 로딩량 감축: 핵심 원칙만 루트에 남기고, 세부 절차는 하위 문서로 분리. 항상 읽는 문서는 짧게, 필요할 때만 깊게.

| 주제 | 문서 |
|------|------|
| 작업 모드 5종 + 우선순위 + R1~R5 + E 정량 | [.claude/rules/work_mode_protocol.md](.claude/rules/work_mode_protocol.md) |
| hook vs permissions 경계 + 훅 등급 | [.claude/rules/hook_permissions.md](.claude/rules/hook_permissions.md) |
| 외부 모델 호출 + /rewind 한계 + 문서 조회 + 운영 안정성 | [.claude/rules/external_models.md](.claude/rules/external_models.md) |
| 토론모드 코어 | `90_공통기준/토론모드/CLAUDE.md` |
| 데이터 처리·파일 정리 | `.claude/rules/data-and-files.md` |
| 공동작업 원칙 | `.claude/rules/cowork-rules.md` |

## 핵심 원칙 (요약)

- **사용자 명시 지시 최우선**. 다른 자동 사다리는 그 아래.
- **모드 판정 후 진입**: A 실무 / B 분석 / C 시스템 수정 / D 토론 / E 장애 복구. 상세는 work_mode_protocol.md.
- **시스템 수정은 plan-first + R1~R5**. 세부는 work_mode_protocol.md C 섹션.
- **시스템 개선은 모드 E 또는 사용자 명시 모드 C 요청에 한정** (glimmering-churning-reef 안전안).
- **외부 ERP/MES 반영은 실행 전 대상/일자/라인/건수 1줄 확인**.
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

## 응답 형식 (debate 빼는 안 2 — 세션122)

기본 응답에서 **자동 출력 금지**:
- 라벨 / PASS·부분PASS·보류 자동 출력
- R1~R5 자동 출력
- A~E 모드 헤더 자동 출력 (선택적 표기 조건은 work_mode_protocol.md "헤더 표기 조건")
- 채택/보류/버림 자동 출력
- Pre/Post Task 자동 선언

기본값 응답 형태:
- 일반 질문: 결론 / 이유 / 다음 행동
- 시스템 분석(B): 관찰 / 판단 / 필요한 확인
- 시스템 수정(C): 그때만 plan/R1~R5
- 토론모드(D): 그때만 라벨/검증/채택보류버림

명시 요청 또는 C/D 판정 시에만 형식 슬롯 활성.

## 금지

- 원본 xlsx/docx/pdf 직접 수정
- 승인 없는 파일명/시트명/컬럼명 변경
- 검증 없이 값 덮어쓰기
- Git 미확인 추측 답변
- 미푸시 상태를 완료로 간주
- Claude 설명만 듣고 PASS
