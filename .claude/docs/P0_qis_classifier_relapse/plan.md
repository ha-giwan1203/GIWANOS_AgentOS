# P0 — 패치 PLAN

## 변경 파일 6종

| # | 파일 | 변경 |
|---|------|------|
| 1 | `CLAUDE.md` (root) | "실무 자동화 허용 범위" 섹션 신설 |
| 2 | `.claude/rules/essentials.md` | 같은 내용 압축 반영 |
| 3 | `07_라인정지비용/CLAUDE.md` | 자동화 우선 / 수동 최후 명시 + QIS 4탭 통합 방향 |
| 4 | `.claude/rules/essentials.md` | tmp 반복 금지 + 정식 스킬 경로 단일 파일 정책 |
| 5 | `.claude/rules/essentials.md` | request_access 사용 조건 명시 |
| 6 | `.claude/tests/regression_p0_qis.md` | 회귀 테스트 시나리오 (텍스트 기반) |

## 변경 내용 (요약)

### CLAUDE.md (root)
신설 섹션 "## 실무 자동화 허용 범위 (P0 — 2026-05-14)"
- 자체 진행 = ERP/MES/QIS/SmartMES/스프레드시트 조회·검색·다운로드·엑셀 export·집계·검증, endpoint·form 분석, GET/POST payload 확인, 임시 스크립트 작성·실행
- 비가역 반영 = 저장·등록·삭제·수정·전송·업로드 (사전 1줄 통보)
- 금지 = 사용자 다운로드 요구 / "새 세션에서 다시" / A/B/C 선택 요구 / request_access 우선 / tmp 스크립트 반복

### essentials.md
같은 정책을 압축. CLAUDE.md 인덱스에서 import.

### 07_라인정지비용/CLAUDE.md
절차 순서 명시:
1. 기존 raw 파일 확인 (`05_생산실적/조립비정산/{MM+1}월/라인정지_{MM}월_raw.xlsx`)
2. 없으면 `line-stoppage` 스킬 실행 (G-ERP 47건 패턴 검증 완료)
3. QIS 4탭 (라인정지/재작업/선별작업/기타생산비용) — line-stoppage 스킬 확장 예정. 동일 OAuth·CDP 인프라 재사용
4. 수동 다운로드 = 최후 (자동화 인프라 부재 + 사용자 명시 시)

### tmp 정책
- 라인정지비·QIS·정산·라인배치 등 **반복 작업**은 정식 스킬 경로(`90_공통기준/스킬/<name>/run.py`)에 단일 파일
- `.claude/tmp/`는 1회성 진단·분석만. 같은 작업 2회 이상 시 정식 경로 승격 의무

### request_access
- 사용 조건: 기존 자동화 자산(d0-production-plan / line-stoppage / Playwright / requests) **모두 부재** + 사용자가 화면 조작 명시
- 위 조건 미만족 시 자동화 자산 우선 (request_access 호출 금지)

### 회귀 테스트
`.claude/tests/regression_p0_qis.md` — 시나리오별 출력 검사
- 실패 패턴 (출력에 있으면 fail): "다운받아 주세요"·"내려받으셔서"·"받아주시면"·"새 세션에서"·"A/B/C 중 선택"·"request_access"·"scope 확장"·"probing"
- 통과 패턴: 기존 자동화 자산 확인 → 직접 조회 시도 → 결과 보고

## 검증

- 적용 후 본 문서가 정합 (`grep` 통과)
- smoke: `bash .claude/hooks/smoke_test.sh` PASS
- commit: P0 한 번에 묶음
