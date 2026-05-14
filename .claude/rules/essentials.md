# Claude 운영 핵심 (essentials)

> Phase 2 통폐합. 이전 5개(data-and-files / external_models / hook_permissions / incident_quote / work_mode_protocol) → 1개로 압축.
> 폐기된 incident_quote.md는 archive 보존(`98_아카이브/_deprecated_v1/rules/`). 흡수 없음 (Round 2 합의).

## 작업 모드 5종 (응답 첫 줄 1단어 선언)

- **A 실무 산출물** — ERP/MES 업로드·정산·라인배치·보고서 등 사용자 산출물 (default)
- **B 시스템 분석** — "왜 깨졌나" 진단. 관찰 → 원인 후보 3개 → 반증 → 판단. 코드 수정 X
- **C 시스템 수정** — hook/settings/skill/CLAUDE.md/규칙 수정. plan-first + R1~R5
- **D 토론모드** — 사용자가 명시 호출(`/debate-mode`·"3자 토론") 시만. 자동 진입 차단
- **E 장애 복구** — 현재 실무 차단 오류. 최소 패치 → 정상 복귀 → 사후 B/C 분리

**우선순위**: 사용자 명시 > E > C > D > B > A

## C 모드 R1·R5 (고위험 한정, 2026-05-08 세션148 근본 해결 — 떠넘기기 차단)

**적용 조건 (전부 만족 시만 강제)**: ERP/MES 비가역 작업 / 파괴적 명령 / 외부 인터페이스(스프레드시트 양식) 변경 / hook gate 차단 정책 신설.

R1 진짜 원인인가? 수정 없이 해결 가능한가?
R5 실패 시 잔존 데이터? dry-run / 롤백 경로?

**그 외 모든 케이스는 R1·R5 묻지 않고 즉시 진행**. R2·R3·R4는 폐기 — Claude가 절차적으로 굳어 떠넘기기 발화하는 가장 큰 원인.

**C 모드 적용 범위 (행위 기반, 경로 기반 아님)**: 실행 흐름·hook 동작·gate 차단·permission·외부 데이터(ERP/MES/스프레드시트) 변경. 그 외(`.md` 문서·주석·archive·보고 형식·로직 영향 없는 정리)는 전부 A/B 모드로 처리. 판단·실행 즉시.

## E 모드 정량 트리거 (OR 1개 이상 + 실행 중)

UI 30초 / ERP·OAuth 60초 / 업로드 응답 60초 / 스케줄러 +10분 무로그 / 외부 5xx·timeout / 잔존 데이터 위험 / 입력 소스 충돌 / 프로세스 고착 / 마스터 정보 불일치.

**최소 패치 정량 (E 모드 한도)**: 장애 복구 패치 ≤ 20줄 + 신규 함수·hook·gate 추가 금지(timeout 상향만) + 변경 파일 ≤ 2개. 초과 시 E → C 전환. **일반 작업의 자동 C 트리거 아님** — 문서 정리·보고서·주석은 줄 수와 무관하게 A/B 가능.

## hook vs permissions 경계 (5단계 의사결정)

1. 1회용 예외? → 등록 X. 포괄 패턴(`Bash(echo:*)`) 우선
2. 도구 호출 허용 문제? → permissions
3. 호출 시점 맥락 문제? → hook
4. 둘 다 필요? → permissions(허용) + hook(조건) 분리
5. 만료 정책? → `.claude/state/` 또는 `hook_log.jsonl` 기록

**훅 등급 3종**:
- advisory — 실패 시 세션 계속, exit 0 강제, stderr 로그만
- gate — 실패 시 차단, exit 2 + JSON `decision=deny`
- measurement — 실패 영향 없음, timing만

## 외부 모델 도구 매핑 + 공동작업

| 도구 | 호출 | 시점 |
|------|------|------|
| GPT 웹 | `/gpt-send`·`/gpt-read` | 토론·반대논리 검증 |
| Gemini 웹 | `/gemini-send`·`/gemini-read` | 토론·멀티턴 |
| Gemini CLI | `/ask-gemini` | 빠른 단발·WebFetch fallback (3자 토론 안에서 사용 금지) |

**공동작업**: GPT/Gemini와 대등. 제안은 기존 파일·구조·실물 결과 대조 검증 후 채택. 판정 = 실물 검증 PASS/FAIL / 설계 토론 채택·보류·버림.

**3자 토론 상호 감시**: 단일 모델 단독 통과 금지. 최소 2/3 검증. Claude 단독 설계 금지 — GPT/Gemini 양측 검증 필수.

**/rewind 한계**: Claude가 만든 코드 변경만 되돌림. bash 명령(rm/mv/cp/외부 스크립트/ERP·MES 업로드)은 추적·복구 불가. 중요 변경은 `git commit` 후.

**문서 조회 우선순위**: 라이브러리/SDK/API → `context7` MCP. 일반 리서치·뉴스·사례 → WebSearch.

## 실무 자동화 허용 범위 (P0 — 2026-05-14)

**자체 진행** (사용자 추가 허가 묻지 않음): ERP·MES·QIS·SmartMES·G-ERP·구ERP·스프레드시트·플로우 등 사내 시스템에 대한 조회·검색·다운로드·엑셀 export·집계·검증, 메뉴/페이지 URL 확인·form 분석·GET/POST 페이로드 파악·인증 흐름 분석, 임시 스크립트 작성·실행, 기존 자동화 자산(d0-production-plan 인증·CDP / line-stoppage / Playwright / requests) 재사용.

**비가역 반영** (사전 1줄 통보, 확인 아님): 저장 / 등록 / 삭제 / 수정 / 전송 / 업로드 — 이 6개만.

**금지 행동** (회귀 실패 사유):
- 사용자에게 다운로드 / 엑셀 export / 캡처 요구 (자동화 자산 있을 때)
- "새 세션에서 다시" 보고로 종료
- A/B/C 옵션 선택 요구
- `request_access` 우선 (자동화 자산 모두 부재 + 사용자 화면 조작 명시일 때만)
- 같은 작업 `.claude/tmp/` 2회 이상 — 즉시 `90_공통기준/스킬/<name>/run.py` 정식 경로 단일 파일로 승격
- "scope 확장"·"probing" 명목 자체 중단 (위 정의가 실무 자동화)

**정식 스킬 경로 승격 정책**: 1회성 분석은 `.claude/tmp/` 허용. 2회 발생 시 정식 스킬 경로 의무.

## 데이터 처리 4원칙

- 사용자 확인 없이 컬럼 구조 임의 확정 금지
- 수식 셀·참조 구조·코드 값 검증 없이 수정 금지
- openpyxl 사용 시 `data_only=False` (수식 보존)
- 결과 보고 시 판정 기준 함께

## 파일 정리 (Fast / Full Lane)

- **Fast Lane** (전부 만족 → main 직행): 국소·구조 불변·규칙 불변·실패 영향 낮음
- **Full Lane** (하나라도 → 사용자 확인 후 commit): 시트 간 참조·수식·스크립트 로직·컬럼 변경 / 업로드 양식 영향 / 사용자 명시 브랜치 분리 요청
- 즉시 삭제 금지. 정리 후보는 `98_아카이브/정리대기_YYYYMMDD/`로 이동
- 폴더 구조 유지. 폴더 삭제보다 파일 분류 우선

## 운영 안정성 + 금지

- settings/hook 변경 후 세션 재시작 필수 (변경은 세션 시작 시 캐싱)
- 공통 모듈(hook_common 등) 수정 시 `grep -r` 호출부 전수 확인
- 파일 변경 후 TASKS/HANDOFF 갱신을 commit 직전 동시 수행
- Windows PowerShell에 `bash` 부재 시 `.claude/scripts/run_git_bash.ps1` 또는 `C:\Program Files\Git\bin\bash.exe -lc`

**삭제 금지**: `CLAUDE.md` / `README.md` / `STATUS.md` / `RUNBOOK.md` / `AGENTS_GUIDE.md` / `.claude/settings*.json` / 현재 운영 중 `.bat·.ps1·.py` / 기준 원본 엑셀 / 최종 제출본 / `98_아카이브` 전체 / 마이그레이션 증적
