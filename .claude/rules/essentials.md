# Claude 운영 핵심 (essentials)

> 2026-06-02 Phase A 압축. 100줄 → 50줄. 이전본 `98_아카이브/reset_20260602/essentials_pre_compact.md`.

## 작업 모드 5종 (응답 첫 줄 1단어 선언)

- **A 실무 산출물** — ERP/MES 업로드·정산·라인배치·보고서 (default)
- **B 시스템 분석** — 진단. 관찰 → 원인 후보 → 반증 → 판단
- **C 시스템 수정** — hook/settings/skill/CLAUDE.md 변경. plan-first
- **D 토론모드** — 사용자 명시 호출(`/debate-mode`) 시만
- **E 장애 복구** — 실무 차단 오류. 최소 패치 후 사후 B/C 분리

**우선순위**: 사용자 명시 > E > C > D > B > A

## C 모드 R1·R5 (고위험 한정)

**적용 조건**: ERP/MES 비가역 / 파괴 명령 / 외부 인터페이스(스프레드시트 양식) / hook gate 신설. **그 외는 묻지 말고 즉시 진행**.

- R1 진짜 원인인가? 수정 없이 해결 가능한가?
- R5 실패 시 잔존 데이터? dry-run·롤백 경로?

문서·주석·archive·보고 형식은 줄 수 무관 A/B로 처리.

## E 모드 정량 트리거

UI 30초 / ERP 60초 / 업로드 응답 60초 / 스케줄러 +10분 무로그 / 외부 5xx·timeout / 잔존 데이터 위험 / 프로세스 고착. 패치 ≤ 20줄, 신규 hook 금지, 변경 파일 ≤ 2개. 초과 시 E → C.

## 훅 등급 3종

- **advisory** — 실패해도 세션 계속, exit 0, stderr 로그만
- **gate** — 실패 시 차단, exit 2 + JSON `decision=deny`
- **measurement** — 영향 없음, timing만

## 외부 모델 도구

| 도구 | 호출 | 시점 |
|------|------|------|
| Codex | `python 90_공통기준/업무관리/codex_claude_channel/auto_reply.py --target codex "<msg>"` | 모든 실행 위임 |
| GPT 웹 | `/gpt-send` `/gpt-read` | 토론·반대논리 |
| Gemini 웹 | `/gemini-send` `/gemini-read` | 토론·멀티턴 |
| context7 MCP | 라이브러리·SDK 문서 조회 | 코드 작성 전 |

3자 토론은 단일 모델 단독 통과 금지(2/3 검증). `/rewind`는 bash·외부 호출 복구 불가 — 중요 변경은 commit 후.

## 실무 자동화 허용 범위

**자체 진행** (추가 허가 불필요): ERP·MES·QIS·SmartMES·G-ERP·구ERP·플로우 조회·검색·다운로드·집계·검증, 인증 흐름 분석, 임시 스크립트, 기존 자동화 자산 재사용.

**비가역 반영** (사전 1줄 통보, 확인 아님): 저장·등록·삭제·수정·전송·업로드 6개만.

**금지 행동**: 사용자에게 다운로드·캡처 요구 / "새 세션에서 다시" 종료 / A/B/C 옵션 선택 요구 / `.claude/tmp/` 스크립트 2회 이상 반복(2회째 즉시 `90_공통기준/스킬/<name>/run.py` 정식 승격).

## 데이터 처리

- 컬럼 구조 임의 확정 금지
- 수식·참조 검증 없이 수정 금지
- openpyxl: `data_only=False` (수식 보존)
- 결과 보고 시 판정 기준 함께

## 파일 정리

- **Fast Lane**: 국소·구조 불변·규칙 불변 → main 직행
- **Full Lane** (시트 참조·수식·로직·컬럼·업로드 양식 영향): 사용자 확인 후 commit
- 즉시 삭제 금지. 후보는 `98_아카이브/정리대기_YYYYMMDD/`로 이동

## 운영 + 금지

- settings/hook 변경 후 세션 재시작 필수
- 공통 모듈 수정 시 `grep -r` 호출부 전수 확인
- 파일 변경 시 TASKS/HANDOFF 동시 갱신
- PowerShell에 bash 없으면 `C:\Program Files\Git\bin\bash.exe -lc`

**삭제 금지**: CLAUDE.md / README.md / STATUS.md / RUNBOOK.md / .claude/settings*.json / 운영 중 스크립트 / 기준 원본 엑셀 / 최종 제출본 / 98_아카이브 / 마이그레이션 증적
