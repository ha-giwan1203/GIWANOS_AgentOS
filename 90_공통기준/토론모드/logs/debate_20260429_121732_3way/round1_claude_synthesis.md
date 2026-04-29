# Round 1 — Claude 종합안 (Step 6-5)

## 4-way 대조 (Claude 6-0 / GPT / Gemini / 양측 1줄 검증)

| 항목 | Claude 6-0 | GPT | Gemini | 합의 |
|------|-----------|-----|--------|------|
| 원인 분류 5종 | 충분 | 동의 + RETRY_BLOCK 신설 | 보류 + timeout 시점(전/후) 구분 | **통합** — 입력 전/후 시점으로 RETRY_BLOCK·RETRY_NO 동등 처리 |
| 백오프 즉시/5/15/30 | 적정 | 동의 | 부분동의, 1분 유예 권장 | **Gemini 채택** — 1/5/15/30분, 누적 51분 |
| UNKNOWN 1회 vs 2회 | 2회 권장 | 반대(1회) | 반대(1회) | **양측 1회 채택** — Claude 2회안 폐기 |
| schtasks 강제 종료 | Running 5분 대기 후 종료 | Phase 0/1/2 한정 | Phase 2까지만 | **합의** — Phase 2 종료 시점 이전만 허용. Phase 3 이후 종료 금지 + 알림 |
| lock O_EXCL | 단순 | 동의 + PID·시각·stale 정리 | 동의 + PID·시각·stale 정리 | **만장일치** — atomic + stale 처리 |

## 채택안 (5종 + Gemini 신규 1종)

### 1. 원인 분류 (재정의 — GPT/Gemini 통합)
- **RETRY_OK** (백오프 재시도 가치 있음):
  - timeout/5xx/네트워크/Chrome CDP 미기동 — **단 입력 단계(Phase 0/1/2 = 로그인·xlsx 로드·dedupe) 한정**
  - OAuth 정착 (b4ab2fea fallback 1차 시도 후)
- **RETRY_BLOCK** (재실행 차단 + 알림 — GPT/Gemini 통합 신설):
  - timeout이 **데이터 전송 후 응답 대기 중**(Phase 3 업로드 이후 = ext 채번/rank_batch/mesMsg 단계)에 발생
  - dedupe 결과 기존 등록·부분 등록 의심
  - 즉 "이미 일부 등록됐을 가능성"이 의심되는 모든 경우
- **RETRY_NO** (즉시 알림, 0회 재시도):
  - xlsx 미존재 / 권한 오류 / 마스터 정보 불일치
- **UNKNOWN** (1회 즉시 재시도만, 양측 합의):
  - 분류 실패 → 1회 재시도 → 실패 시 즉시 Slack 알림 + 로그 30줄

### 2. 백오프 정책 (Gemini 채택)
- 검증 시점: 07:30 (morning 20분 후) / 야간 verify 별도
- RETRY_OK 백오프: **1분 / 5분 / 15분 / 30분** (누적 51분)
- 매 시도 전 dedupe + schtasks 상태 확인 선행

### 3. schtasks 상태 확인 + 강제 종료 (양측 합의)
- 검증 시점에 `schtasks /query /TN "D0_SP3M3_Morning" /v` 결과 확인
- **Status="Running" + Phase 분석**:
  - Phase 0/1/2(로그인·xlsx 로드·dedupe) 단계: 5분 추가 대기 → 그래도 Running이면 `schtasks /end` 강제 종료 OK + 알림
  - Phase 3 이상(업로드·rank_batch·mesMsg 단계): **강제 종료 금지** + 알림으로 즉시 종결 + 사용자 수동 결정
- Phase 판정: morning_<date>.log 끝부분 grep ("Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5", "Phase 6")

### 4. dedupe 선행 (필수)
- 매 재시도 전: `python .claude/tmp/erp_d0_dedupe.py --line SP3M3 --date <today> --execute`
- 결과 분석: dedupe가 "기존 등록 N건 발견 + 정리"라면 **RETRY_BLOCK 트리거** → 재실행 중단 + 알림
- "0건 정리"라면 정상 dedupe 통과 → 재실행 진행

### 5. lock 파일 (양측 합의 보강)
- 경로: `.claude/state/d0_verify_<date>_<session>.lock`
- 생성: `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)` (atomic)
- 내용 JSON: `{"pid": <int>, "started": "<ISO>", "session": "morning|night"}`
- stale 정리: 시작 시간 + 60분 경과 시 무시하고 락 재획득
- 정상 종료 시 lock 파일 삭제

### 6. Gemini 신규 — 브라우저 DOM/스크린샷 저장 (수동 복구 지원)
- 실패 시 chrome-devtools-mcp로 마지막 페이지 DOM(text snapshot) + 스크린샷 캡처
- 저장 경로: `06_생산관리/D0_업로드/logs/morning_<date>_failure_<timestamp>.{txt,png}`
- Slack 알림에 경로 포함 + 마지막 30줄 로그
- 단 chrome-devtools-mcp는 verify_run.py가 실행될 때 CDP 9222 포트 살아있을 때만 가능. CDP 미기동이면 스킵

### 7. 알림 정책
- **성공**: stdout에 "OK" 1줄, Slack 알림 없음 (스팸 방지)
- **재시도 후 성공**: Slack 정보 알림 1건 ("재시도 N회 후 성공, 누적 M분")
- **RETRY_BLOCK / RETRY_NO / UNKNOWN 실패**: Slack 즉시 알림 + 로그 끝 30줄 + DOM/스크린샷 경로
- **누적 51분 도달**: Slack 알림 + 자동 재시도 종료 + 사용자 수동 결정 대기

## 구현 단위 (Phase 1 — 즉시)

### 신규 파일
1. `90_공통기준/스킬/d0-production-plan/verify_run.py` (~280줄)
   - argparse: `--session morning|night --line SP3M3 [--max-elapsed-min 51] [--dry-run]`
   - 함수 분리: `check_schtasks_status()` / `analyze_phase()` / `classify_failure()` / `do_dedupe()` / `acquire_lock()` / `notify_slack()` / `capture_dom_screenshot()`
   - main 루프: lock → schtasks 확인 → 로그 분석 → 분류 → 재시도(백오프) → 알림 → unlock

### 변경 파일
2. `90_공통기준/스킬/d0-production-plan/SKILL.md` — Phase 7 verify 섹션 추가 (~30줄)
3. `06_생산관리/D0_업로드/README.md` (또는 신설) — schtasks /create 등록 명령 안내

### 사용자 수동 작업 (자동화 안 함)
- Windows 작업 스케줄러 등록:
  ```
  schtasks /create /TN "D0_SP3M3_Morning_Verify" /TR "python ... verify_run.py --session morning --line SP3M3" /SC DAILY /ST 07:30 /RU <USER>
  ```
- 야간 verify는 야간 스케줄러 시간 + 30분 후

## R1~R5 보강 (모드 C)

**R1 (진짜 원인)**: 스케줄러 실패 인지 + 자동 복구 부재. 사용자 수동 부담. 본 안건 사유

**R2 (직접 영향)**:
- 새 작업 스케줄러 2개 (외부 시스템) — 사용자 수동 등록
- run.py 재호출 = ERP 등록 비가역. dedupe 선행 필수
- Slack 알림 빈도 ↑ (재시도 후 성공도 알림)
- chrome-devtools-mcp DOM 캡처 (CDP 9222 의존)

**R3 (간접 영향·grep)**:
- 같은 패턴: D0_SP3M3 morning/night. 야간 verify는 Phase 1 이월
- 다른 ERP 자동화: 라인배치·MES 업로드 — 별도 의제
- run.py가 verify에서 호출될 때 verify의 lock과 morning 작업의 lock(있다면) 충돌 가능성 점검

**R4 (선례)**:
- 세션115: dedupe 도구 만들어짐 — 재사용
- 세션121: timeout 60→120 상향 — 같은 패턴
- 세션124: OAuth fallback (d) 패치 — 검증 미도래
- 본 안건은 수동 절차 자동화 (새 패러다임 아님)

**R5 (롤백·잔존 데이터 — 가장 중요)**:
- **자동 재실행 = ERP 비가역**. 핵심 안전장치:
  - dedupe 선행 (매 시도)
  - Phase 3 이상 schtasks 강제 종료 금지
  - timeout 발생 시점 분류 → 입력 후 = RETRY_BLOCK
  - lock atomic + stale 처리
  - 누적 51분 한계 + 재시도 횟수 + 카운터 파일
- **롤백 도구**: `erp_d0_dedupe.py --execute` 즉시 실행 가능 (세션115 도구)
- **race condition 방지**: schtasks Status="Running" 5분 대기 + Phase 분석
- **무한 루프 방지**: lock 파일 + 카운터 + 누적 시간 한계 3중 차단

## claude_delta: **partial → major**
- UNKNOWN 1회로 변경 (Claude 2회안 폐기)
- 1분 유예 추가 (Gemini 채택)
- timeout 시점 분류 추가 (RETRY_BLOCK 신설 — GPT/Gemini 통합)
- schtasks 강제 종료 Phase 2 한정 (양측 합의)
- lock에 PID·시각·stale (양측 합의)
- DOM·스크린샷 저장 (Gemini 신규)

## issue_class: **B**
- skip_65 = false (B + delta major)

## 양측 최종 검증 요청
종합안 원문 전체를 양측에 동봉하여 1줄 검증 요청 (동의 / 이의 / 검증 필요 + 근거).
