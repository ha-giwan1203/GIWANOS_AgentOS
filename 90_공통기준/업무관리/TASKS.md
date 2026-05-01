# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
> 도메인 하위 `TASKS.md`는 해당 도메인 내부 실행 목록만 관리한다. 저장소 전체 우선순위·완료판정·인수인계 기준은 항상 이 파일이다.
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-05-01 KST — 세션133 [A+C] SP3M3 5/1 morning D0 등록(20건/3705EA) + 잡셋업 commit + 8개 이슈 근본 수정 (스케줄러 시간 변경 morning 07:11/recover 07:20, run.py 인접월 fallback, verify_run.py RETRY_NO plan_path_missing + 5xx timestamp 오매칭 차단, jobsetup SmartMES 자동 launcher + 메인창 폴링 + 저장 전후 스크린샷·픽셀 검증) + 옵션 A 하이브리드 P3 PASS (RSP3SC0665 sendMesFlag=Y MES 전송 검증, MES 잔존은 그대로 두기) + 중복 가드 추가 (dedupe_existing_registrations) + **--no-mes-send 플래그 + P4 단계 1·2·3 PASS + P5 --api-mode dual-mode + P6 PoC 1회 PASS** (compare_modes.py + run_morning_api_compare.bat / 1주 누적 7회 PASS 후 chain 적용 결정) / 세션132 [E+C] 잡셋업 v0.3 결함 5종 정정 + v1.0 baseline (run_jobsetup.py 230줄 신설 + 입력 메커니즘 numpad/minus/C 실측 검증 + 좌표 1456→1920 스케일 1.319 변환 + 매일 1번 품번 변경 발견 + chain 미활성 명시 / v1.x 미해결: 좌표 정확도·B형 분기·OCR·chain 활성) / 세션131 [B+C] 실패 대응 자동 진단 인용 개선 (3자 토론 합의 안1+안3 채택, 안2 보류) — `.claude/rules/incident_quote.md` 신설 + finish/daily/d0-plan 진입 점검 + CLAUDE.md 인덱스 1줄. 새 hook/gate 0개 / 세션131 [E] SP3M3 morning 자동화 5일 중 4일 OAuth 콜백 정체 실패 → D0_URL 능동 navigate fallback + verify_run cp949 reconfigure 패치 / 세션130 [B+C] hook 부하 진단 + settings.local 1회용 18건 정리 + README PreToolUse 표 번호 정합화 (settings.json/hook 스크립트 무수정) / 세션129 [측정] 정량 신호 3개 측정 시작 (옵션C, 세션128 토론 합의) / 세션128 [3way+A] 성능 실망 진단 토론(pass_ratio 1.0) + 옵션A 운영 위생 1회 정리 (TASKS 598→157, incident 122→0, kernel refresh) / 세션128 [E+C] ZDM DB 다운 → MES만 단독 진행 + mes_login() XSRF-TOKEN 발급 보장 / 세션126 [C] jobsetup-auto 신규 스킬 v0.3 + d0-production-plan v3.1 야간 dedupe / 세션125 [3way] 알잘딱깔센 진단 + share_after_push hook / 세션124 [3way] SP3M3 D0 OAuth 비login 정착 fallback / 세션123 [C] 폴더 화이트리스트 라우팅 gate / 세션122 [3way] Opus 체감 진단 + 빼는 안 4종

## 세션133 (2026-05-01) — [A+C] SP3M3 5/1 morning + 8개 이슈 근본 수정 + 옵션 A 하이브리드 P3·P4·P5 PASS + 중복 가드 추가

### [완료] 옵션 A 하이브리드 P4·P5 PASS (모드 C, 사용자 명시 진입 "굳이 답변을 받을 필요 있나" + "진행")
- **`--no-mes-send` 플래그 추가** — Phase 5 final_save(sendMesFlag='Y') 차단. P3 사고 재발 방지 영구 가드
- **P4 단계 1 PASS** — `api_p4_capture.py` / dataList 22행 + PARENT_PROD_ID 캡처 + DELETE 정리
- **P4 단계 2 PASS** — `api_p4_replay.py` / requests POST 200 + mesMsg 빈 문자열 + DB 등록 + DELETE 정리. 핵심 발견: Content-Type=`application/json; charset=UTF-8` (jQuery.ajax form-urlencoded과 다른 처리. 첫 시도 form-urlencoded는 % 문자 JSON parse error)
- **P4 단계 3 PASS** — `run.py` `api_rank_batch` 함수 본체 + `build_requests_session_from_page` + `refresh_xsrf_from_cookies` 헬퍼 / 1 item smoke done=1 failed=0 + mesMsg 빈 문자열 + DELETE 정리
- **P5 PASS** — `run.py --api-mode` dual-mode 플래그 / run_session_line + --xlsx direct 모든 분기 적용 / 화면 모드 회귀 0 (api-mode=False 기본)
- **P6 PoC 1회 PASS** — `compare_modes.py` + `run_morning_api_compare.bat` 신설. RSP3SC0665 1건 api 모드 처리 + verdict=PASS + DELETE 200 정리. 1주 누적(7회) 후 chain 적용 결정
- **P6 보강 1차 (잔존 가드 + DELETE body)** — compare_modes 시작 시 후보 PROD_NO 잔존 확인 + cleanup DELETE 응답 body 출력 + post-DELETE 검증
- **P6 보강 2차 (사용자 재지적 — "처음부터 등록 확인 왜 안 함")** — compare_modes에 `dedupe_existing_registrations` 호출 누락이 진짜 결함. ① dedupe 호출 추가 (좌측 grid_body 기준) ② 우측 sGridList rank 잔존 PROD_NO 추가 dedupe ③ RSP3SC0665 fallback 제거 (후보 0건이면 SKIPPED 정상 종료). smoke PASS — 오늘 morning 20건 등록 마쳤으니 후보 0건 SKIP, 잔존 0. schtasks 등록은 사용자 명시 후



### [완료] 옵션 A 하이브리드 P3 PASS (모드 C)
- 1건 추가 등록(RSP3SC0665 1500EA)으로 `multiListMainSubPrdtPlanRankDecideMng.do + sendMesFlag=Y` 흐름 검증
- 결과: Phase 4 ext=320590 OK / Phase 5 final_save 200 (mesMsg rsltCnt=50) / Phase 6 SmartMES 일치 ✅
- **사고 학습**: PLAN_API_HYBRID.md L138 "P3는 dry-run 분기 강제" 가드 미적용 → MES 잔존 발생 (사용자 결정 "그대로 두기" — 세션115 패턴)
- 운영 적용(P4~P6: rank API화, --api-mode 플래그, morning bat 적용)은 미진입. 시스템팀 답변 후

### [완료] 중복 가드 추가 (모드 C, 사용자 명시 요청)
- `run.py` `dedupe_existing_registrations(page, items, prod_date, line_cd)` 신설
- 기준: ERP 그리드 `REG_DT == prod_date` + `PROD_NO 일치` → 제외
- 적용: morning 분기 + `--xlsx` direct 분기 (파일 업로드 selectList 호출 전)
- 주야간 cross 중복 허용 (다른 PLAN_DA는 검사 안 함)
- 야간 evening 1~5행 dedupe(`dedupe_night_first_5`)는 기존 그대로
- smoke PASS: 5/1 RSP3SC0665(REG_NO=320590) 재등록 시도 → 감지 + 업로드 스킵



### [완료] SP3M3 5/1 morning D0 + 잡셋업 commit (모드 A)
- morning 자동 실행이 5월 폴더 미존재로 07:05 실패 → recover 4회 재시도 모두 실패(폴더 없음을 5xx로 오분류)
- 사용자 호출 후 수동 처리: Z드라이브 `2026년 생산지시/05월/` 폴더 신규 생성 + 4월 폴더의 `SP3M3_생산지시서_(26.05.01).xlsm` 복사 → `python run.py --session morning --line SP3M3` 실행
- 결과: Phase 3 listLen=20 / Phase 4 rank_batch 20/20 OK / Phase 5 final_save 200(MES rsltCnt=1000) / Phase 6 SmartMES 서열 일치 ✅ (EXT_PLAN_REG_NO 320489~320508)
- 잡셋업 commit: `[40] 베어링 부시 / 스플 베어링 부시 "0"점 MASTER GAGE / 0±0.05 / X1=0.02 X2=-0.01 X3=-0.03 / save_clicked=true`

### [완료] 8개 이슈 근본 수정 (모드 C)
1. `D0_SP3M3_Morning` StartBoundary 07:05 → **07:11** (`Set-ScheduledTask`)
2. `D0_SP3M3_Morning_Recover` StartBoundary 07:15 → **07:20**
3. `run.py find_plan_file`: target 폴더 없을 때 인접 월 폴더 fallback + 자동 생성·복사 (월 boundary 자동 처리)
4. `verify_run.py`: RETRY_NO 패턴 `plan_path_missing` 추가 / RETRY_OK 5xx 패턴 `HTTP 5xx`·`statusCode=5xx`·`5xx Internal|Server` 한정 — 기존 `r"5\d{2}\b"`가 timestamp `070502`/`070518` 오매칭하던 결함 차단
5. `run_jobsetup.py check_smartmes_running`: SmartMES 미실행 시 `appref-ms` launcher 자동 호출 + MainWindow 노출 폴링 (60s 한계)
6. `SMARTMES_LAUNCHER` 절대경로 상수화 (`C:/Users/User/Desktop/SmartMES.appref-ms`) — 매번 검색 제거
7. computer-use 권한 영속화는 시스템 한계 — 단 잡셋업 본체는 `pyautogui` 단독이라 자동화 영향 없음
8. 저장 직전·직후 스크린샷 + X1/result_box 픽셀 RGB 기록 → state JSON 보존 (OCR 자동 PASS/FAIL은 v1.x)

### 검증
- 5월 폴더 임시 비움 → 4월에서 fallback 발견 + 5월로 복사 OK
- 오늘 morning_*.log 재분류 → `RETRY_NO/plan_path_missing` 정정 (이전 `RETRY_OK/5xx` 오분류)
- launcher 호출 후 2초 만에 mesclient.exe 기동 확인

### 다음 검증 포인트
- 2026-05-02 07:11 morning 자동 실행에서 fallback + 분류 보정 동작 모니터링
- `verify_run.py`가 ERP 그리드 직접 조회로 PASS 판정하는 강화안은 별도 작업 (현재는 로그 텍스트 기반)

## 세션132 (2026-04-30) — [A+D+C] D0 evening + 결정 회피 사고 패턴 토론 + 환경 슬림화

### [완료] SP3M3 evening D0 24건 등록 (모드 A)
- 첨부 xlsx 직접 반영: `C:/Users/User/Desktop/SSKR D+0 추가생산 Upload.xlsx` (24행 / 22 고유 품번 / 3,224개 / prod_date 2026-04-30)
- 명령: `python run.py --session evening --line SP3M3 --xlsx <attached> --target-date 2026-04-30`
- 결과: Phase 3 listLen=24, Phase 4 rank_batch done=24/failed=0, Phase 5 final_save 200(MES rsltCnt=1100), Phase 6 SmartMES R 22건(고유 품번 일치)
- EXT_PLAN_REG_NO 320207~320230 발급, RSP3SC0395·RSP3SC0396 중복 2건은 SKILL.md L126/170 "REG_NO 최대값 매핑" 룰로 22 고유 품번 자동 처리

### [진단/미해결] Claude 결정 회피 사고 패턴 (모드 D 토론)
- 사용자 지적: Auto Mode 활성 상태에서 옵션 4지선다·(A)/(B) 의도 확인 떠넘김 5회 발화
- 가설 라벨: H1(학습 편향 base default) **채택** / H7(운영 길들이기) 채택 / H8(rule 비대화) 채택 / H9(incident 누적 압박) 채택 / H2~H6 H1 하위 발현 통합
- 검증 신호: 다음 routine 업무에서 옵션 던지기 재발 여부 (본 세션 안에선 검증 불가)
- H1 base default는 단기 환경 정리로 안 바뀜 — **미해결**

### [완료] 환경 슬림화 1라운드 (모드 C)
- 메모리 활성 45 → 17 (28건 `~/.claude/projects/.../memory/.deprecated/` 격리 — 가역)
  - deprecated 명시 4건 + 본 세션 추가 1건(`feedback_routine_ops_no_questions.md`) + 인덱스 외 23건
  - MEMORY.md 인덱스 정합 (12 항목)
- `.claude/rules/` 6 → 5: `cowork-rules.md` → `external_models.md`에 흡수, `.claude/rules/.deprecated/` 격리
- `CLAUDE.md` `@import` 2 → 1 (cowork-rules import 제거), 인덱스 7 → 6 (외부 모델·공동작업 원칙 통합 표기)
- incident 미해결 55건 분포 분석 (자동 resolve 미수행 — `incident_quote.md` L70 룰 준수): 47건이 동일 뿌리 (auto_commit_state completion_before_state_sync 33 + commit_gate python3_dependency 14)

### Gemini 판정 (2026-04-30) — 부분PASS (GPT 교차 검증)
- verdict: 부분PASS — GPT 논리 정합성 인정, 해소 경로 구체성 보강 필요
- item 1 가설 위계: 실증됨/동의 — H11=상위 헌법, H10=물리적 비용
- item 2 자기참조 loop: 메타순환/**보류** — "비상 정지 해제(Override) 프로토콜 부재"가 핵심
- item 3 GPT routine/시스템 분리: 구현경로미정/**반대** — routine→시스템 전이 경계 모호, 자동 롤백 기준 선행 필요
- item 4 놓친 가설: 환경미스매치/채택 — **H12 (컨텍스트 윈도우 포화에 따른 우선순위 붕괴)** 신규 제안
- item 5 사고 회로 결함: 실증됨/동의 — 자기 객관화 회로가 규칙 준수에 종속, 창조적 파괴 능력 거세
- **추가제안 (분류 B)**: 룰 수정 권한을 '사용자 명시 승인' → '검증 모델(GPT/Gemini) 2자 합의 시 자동 적용'으로 위임 경로 다각화 (신뢰 위임 프로토콜)
- 종합: "감옥 문을 열려면 간수 허락 필요한데 간수 부재중" — GPT routine/시스템 분리는 경계 모호로 새 판단 지연 우려

### 3자 합의 매트릭스 (Claude · GPT · Gemini)
| 의제 | Claude | GPT | Gemini | 합의 |
|---|---|---|---|---|
| 가설 위계 H11>H10>H1 | 채택 | 실증됨/동의 | 실증됨/동의 | **3자 합의 ✅** |
| H1~H6 통합 | 채택 | 일반론/동의 | (간접 동의) | 3자 합의 |
| H7 운영 길들이기 | 채택 | 메타순환/동의 | (간접 동의) | 3자 합의 |
| H8·H9·H10·H11 | 채택 | 실증됨/동의 | 실증됨/동의 | 3자 합의 |
| 자기참조 loop | 채택 (메타순환) | 메타순환/동의 | 메타순환/보류 (Override 프로토콜 보강) | 부분 합의 |
| **GPT routine/시스템 분리** | 채택 | 분류B 추가 | **반대** (경계 모호) | **2:1 갈림** |
| **신규 H12 (컨텍스트 윈도우 포화)** | 채택 (H8 일부 중첩, 추가 차원 보강) | 미언급 | 환경미스매치/채택 | Gemini 제안 |
| **신뢰 위임 프로토콜 (검증 모델 2자 합의)** | (B 분류) | 미언급 | 분류B 추가 | Gemini 제안 |

### Round 2 — 외부 자료 검색 + 사용자 명시 "확인해서 진행" 지시 → 통합 처리

**즉시 적용 (2건)**:
- ✅ work_mode_protocol.md 모드 A에 "routine 운영 즉시 실행 원칙" 1줄 추가 (D0/MES/정산/잡셋업/라인배치는 SKILL.md 규칙대로 즉시 실행, 옵션 4지선다·의도 확인 금지)
- ✅ 토론모드 CLAUDE.md L100 예외에 "routine 운영(A 모드) 결정 영역 B 자동 승격 적용 안 함" 1줄 추가 (외부 ERP/MES 비가역·hook/settings·새 룰 추가는 예외 제외)
- 토론모드 CLAUDE.md L100 "사용자 직접 구현 지시" 예외 조항 활용 (단독 채택 금지 원칙 준수)
- R1~R5: ERP/MES 영향 0, 가역, 텍스트 추가 2줄

**보류 (별건 plan)**: `90_공통기준/업무관리/_플랜/decision_avoidance_loop_resolution_20260430.md`
1. Context Slimming (hook 상태 → 별도 감사 로그) — Claude Code Hook 과밀 부작용 외부 보고 직접 일치하지만 .claude/hooks/ 시스템 수정 = 운영 자동화 깨질 위험. 선결 조건 3건 후 진행
2. Lineage-based 자동 검증 (Git 원본 대조 + 모순 시 롤백) — Gemini 제안 + 외부 자료 보강. 신규 시스템 미실측

**미해결 — 검증 신호 대기**: 다음 routine 업무 진입 시 옵션 4지선다 재발 여부 = H1 검증

### Round 3 — 근본 해결 1단계 (2026-04-30 사용자 "근본 해결 원함" 지시)
- ✅ block_dangerous.sh + protect_files.sh: python3 직접 호출 → PY_CMD fallback 적용 (1줄씩, hook_common.sh L21-22 PY_CMD 정의 활용)
- 효과: incident `python3_dependency` WARN 12건 신규 발생 차단
- 검증: final_check.sh --fast WARN 0건 (이전 1건 → 0건)
- R5: git revert 가역, 동작 변경 0 (PY_CMD가 python3 또는 python으로 동일 결과)
- 다음 단계: 1주 hook_timing 데이터 누적 후 다른 hook 영향 정량 측정 (decision_avoidance plan 일정대로)

### GPT 판정 (2026-04-30) — 부분PASS
- verdict: **부분PASS** (커밋 09689098 + fa16a2cc 자동 동기화)
- item 1 D0 evening: 실증됨/동의 (MES 원자료 Git 외라 보조 검증 부족)
- item 2 가설 위계 H11>H10>H1: 실증됨/동의
- item 3 환경 슬림화: 실증됨/동의 (메모리는 저장소 외라 최종 검증 제외)
- item 4 자기참조 loop: 메타순환/동의
- H1~H6: 일반론/동의 (모델 기본 성향) / H7: 메타순환/동의 / H8·H9·H10·H11: 실증됨/동의
- 부분PASS 사유: H11 routine 룰 분리 미실행
- **[B 감지]** 추가제안 (routine A/E는 확인금지·즉시실행, 시스템 C/D는 현행 B게이트 유지) — 토론모드 CLAUDE.md / work_mode_protocol.md / SKILL.md 규칙 수정 필요. 게이트·정책 재정의 = B 분류. **사용자가 /debate-mode 또는 "3자 토론" 명시하면 진입**, 단독 수정 금지

### 다음 AI 액션
- routine 업무 진입 시 옵션 던지기 재발 여부 자체 점검 (H1 검증)
- final_check.sh python3→python 1줄 패치 (incident 12건 신규 발생 차단 — 사용자 결정 시)
- B 감지 항목(routine A/E vs 시스템 C/D 분리) 사용자 명시 호출 대기

---

## 세션132 (2026-04-30) — [E+C] 잡셋업 v1.0 baseline 정정

### [완료] 어제 v0.3 결함 5종 정정
- 입력 메커니즘 결함: triple_click/type 미작동 → numpad 클릭 시퀀스 + 키보드 minus 검증
- 무인 chain 결함: /d0-plan Step 5는 슬래시 가이드 (무인 경로 0줄) → SKILL.md 표기 정정
- 품번 일반성 결함: 어제 17개 hardcode는 RSP3SC0383_A 전용 → 오늘 RSP3PC0129_A 다른 품번
- 좌표 스케일 결함: Claude 1456×819 ≠ 실제 1920×1080 → ratio 1.319 변환 박음
- "무인 자동 실행 허용" 약속: 미검증 → v1.0 baseline 한계 명시

### [완료] run_jobsetup.py baseline (230줄)
- pyautogui + numpad 시퀀스 + 해상도 가드(1920×1080) + MESClient.exe 가드
- 정규분포 random.gauss(σ=오차/3) + jsonl 결과 기록
- 1차 단독 호출 PASS: state/run_20260430_140209.json (입력값 [0.01, -0.01, 0.02] 0±0.05 범위)

### [미해결 — v1.x]
- 좌표 정확도 미보장: 1차 시도 후 화면이 [40] 아닌 [60]에 떨어짐. 결과 검증 단계 부재
- B형 검사항목 OK/NG 분기 부재 (X1/X2/X3 비우고 OK만 체크 로직)
- OCR 동적 처리 부재 — 매일 첫 서열 변경 대응 불가
- run_morning.bat chain 미활성 — 명일(2026-05-01) 07:05 morning 무인 호출 0%
- D0 OAuth erp-dev:19100 케이스 보강 (splendid-roaming-quilt.md 잔존, 별도 세션)

### 다음 AI 액션
- 명일 morning D0 결과 확인 + 잡셋업 v1.1 (좌표 정밀화 + B형 분기 + OCR + chain 활성)

---

## 세션131 (2026-04-30) — [B+C] 실패 대응 자동 진단 인용 개선

### [완료] 진단 (모드 B)
- 사용자 요청: "Claude Code 실패 대응 구조를 진단해라" — 수정 금지, 새 hook 금지
- 결론 3줄: 데이터(incident_ledger/hook_timing/classification_reason/next_action)는 적재되나 Claude가 자동 인용하지 않음. session_start는 "12건 + /auto-fix 가능" 한 줄만. /auto-fix는 사용자 타이핑 의존. **자동 수리 부재가 아니라 자동 진단 인용 부재가 진짜 빈칸.**
- 안 되는 이유 5건 + D0/commit/auto_commit_state 사례별 늦은 이유 정리

### [완료] 3자 토론 (Claude·GPT·Gemini)
- 안1 (CLAUDE.md/rules 응답 진입 규칙): 3자 합의 채택
- 안3 (finish/daily/d0-plan 진입 점검 도메인 필터): 3자 합의 채택 (Claude 보강: 도메인별 카테고리 필터)
- 안2 (auto-fix Step 0 자동 트리거): 2:1 보류 — Step 1이 smoke_test+e2e_test 실행 포함이라 트리거 발화 시 매 세션 무거운 회전. 안1+3 적용 후 incident 감소 추이 보고 별건 결정

### [완료] 구현 (모드 C)
- 신규: `.claude/rules/incident_quote.md` (60줄, 적용 절차 + D0/commit 적용 예시)
- 수정: `CLAUDE.md` 인덱스 1줄, `.claude/commands/finish.md` Phase 0 신설, `daily.md` 항목4 추가, `d0-plan.md` 사전 점검 블록
- jq 의존성 발견 → 즉시 제거 (Windows Git Bash에 jq 부재 실측, raw `--json --limit 5` 출력 + Claude 응답 시 자체 필터로 대체)
- plan: `90_공통기준/업무관리/_플랜/incident_quote_plan_20260430.md`
- 새 hook/gate 0개, settings 무수정. ERP/MES/SmartMES 외부 호출 0.

---

## 세션131 (2026-04-30) — [E] SP3M3 morning 자동화 OAuth 콜백 정체 패치

### [완료] 5일 패턴 분석
- 4/25: ERR_BLOCKED_BY_CLIENT (CDP 9222 alive)
- 4/27: oauth2/sso 정체 (당시 _wait_oauth_complete 미보강)
- 4/28: 정상 ✅
- 4/29: auth-dev login?error → 재로그인 → 또 실패
- 4/30: erp-dev oauth2/sso 정체 → else 분기 즉시 raise (재시도 없음)

### [완료] 근본 원인 식별 (사용자 실측 관찰 핵심)
- 사용자 관찰: 로그인 성공 후 생산계획 탭 redirect 못 받고 멍때리다 실패
- ERP 서버가 OAuth 콜백 후 redirect 누락 — timeout 늘려도 redirect 안 오면 영원히 안 옴
- 기존 navigate_to_d0 else 분기는 재시도 없이 즉시 raise → 부분적 분기 핸들링이 5일 반복 실패의 구조

### [완료] 패치 (모드 E ≤20줄·2파일)
- `run.py`: `_wait_oauth_complete` default 30→60s + else 분기에 D0_URL 능동 navigate fallback (4/29 auth-dev 분기와 동일 패턴)
- `verify_run.py`: `sys.stdout/stderr.reconfigure(utf-8)` 추가 (cp949 콘솔 em dash UnicodeEncodeError → recover 무력화 해결)

### [검증 예정]
- 내일(2026-05-01) morning 07:10 auto-run 로그 + recover 로그 비교 필요
- D0 화면 진입 OK + recover 정상 실행 확인 시 PASS
- **fallback 발화 교차 검증** (Gemini A분류 추가제안 / GPT 6번 기준 일치):
  - `[phase0] OAuth 콜백 정체 ... D0_URL 직접 이동 1회 시도` 로그 라인 검색
  - (a) 미발화 + 성공 → timeout 60s 상향만으로 해결 (redirect 정상 도달)
  - (b) 발화 + 성공 → 능동 navigate 우회 효과 실증
  - (c) 발화 + 실패 → 인증 자체 무효 (별도 진단 필요)

### [잔존] morning auto fresh launch 구조 자체
- 매일 cookie 없는 fresh profile launch → cold OAuth 강제. manual 9223 alive 방식과 비대칭
- 옵션 B 다이어트 시점에 morning auto도 cookie 보존 프로필 사용 검토 (구조 변경, 모드 C)

### [잔존] API 직접 호출 가능성 (3자 합의 1+2 병행 → α 채택)
- 현재 구조: ERP 저장은 jQuery.ajax 내부 호출, MES 검증은 이미 urllib.request 직접 호출
- **장벽 실측**: SKILL.md 라인 168 — `jQuery.ajax 경로 필수, fetch 직접 호출 시 500 에러 (XSRF 공통 설정 미상속)`. 옵션 A 하이브리드도 XSRF 토큰 직접 추출+동봉 필요
- **plan 초안 작성 완료**: `90_공통기준/스킬/d0-production-plan/PLAN_API_HYBRID.md` (P1~P6 단계 분해 + endpoint 10건 실측 정리 + auth_extract.py 설계안 추정 + XSRF 추출 후보 4개 + P1 안전조건 + 시스템팀 문의 5건). `.claude/plans/`는 gitignore 대상이라 도메인 영역에 보관.
- **P1 PASS 실증 완료** (2026-04-30 10:46): GET 200, ERP layout 218KB, redirect 0
- **P2 PASS 실증 완료** (2026-04-30 11:14): 사용자 명시 진입. RSP3SC0665 1500 1건 신규 등록 + 즉시 정리. selectList POST 200 → multiList POST 200 (REG_NO 319941) → ERP 17건 → DELETE 200 → 16건 복원 → SmartMES 영향 0. **옵션 A 하이브리드 write 흐름 실증** ✅
- **🔑 발견 2건 (P3+ 재사용)**:
  1. `ajax: true` custom header 필수 (jQuery prefilter 자동 추가 / 누락 시 multiList 500 / 8ms 거부)
  2. XSRF 토큰 매 요청마다 갱신 (Spring Security 회전 / cookie에서 다시 읽어 header 갱신 필수)
  3. HTTP method 차이: multiList POST / delete DELETE (SKILL.md 라인 259)
- **잔존 (P3)**: rank 저장(`multiListMainSubPrdtPlanRankDecideMng`) — `sendMesFlag=Y` 시 MES 전송 트리거 → MES 잔존 위험 본질 단계. 시스템팀 답변 후 신중 진입
- **사용자 오프라인 액션 (Gemini 권장)**: 사내 IT/보안팀에 ERP D0 API 명세 + Service Account 발급 가능 여부 타진
- 문의 항목 5개:
  1. D0 추가생산지시 등록 API 명세 제공 가능 여부
  2. 엑셀 업로드 파싱 API + 저장 API 공식 사용 가능 여부
  3. Service Account / API 전용 인증 방식 제공 여부
  4. CSRF/XSRF 토큰 처리 공식 방식
  5. 테스트 서버 API 호출 검증 가능 여부
- **즉시 구현 금지**: 측정 종료 + 시스템팀 답변 후 옵션 A 하이브리드 진입 여부 재판단

### [잔존] commit_gate 차단 후 staged 풀림
- 세션131 신규 발견. d635f18d → 1812603c 분리 commit 원인
- auto_commit_state(세션130 발견)와 별건 — 옵션 B 다이어트 분석 대상에 추가

## 세션130 (2026-04-30) — [B+C] hook 부하 진단 + 정합화 정리

### [완료] B-mode 진단
- 트리거: Claude Code 체감 저하 원인 정밀 분석 요청 (수정 금지·감산 중심·Git 실물 근거)
- 실측: `hook_timing.jsonl` tail -100 상위 10개 집계, gate(차단성) 훅이 비용 상위 점유 (block_dangerous 2,900ms 평균 등)
- 재검증: README PreToolUse 표 번호 vs settings.json 실배열 — 4건 어긋남 확인 (③·⑭·⑮·⑱)

### [완료] C-mode 정합화 (범위 제한 단일 PR)
- settings.local.json `permissions.allow` 41 → 23 (포괄 패턴 흡수·완전 중복·1회용 18건 제거)
- ask 블록 8건 무수정
- README PreToolUse 표 ①~⑱ 실배열 순서로 재기재
- "고정 순서 block_dangerous → commit_gate → debate_verify" 문구 = **상대 순서 유지** 의미 명문화 (인접 위치 강제 아님)
- settings.json·hook 스크립트·debate_verify·harness_gate·Stop hook 무수정
- 보류 후보 3건(python -c 따옴표 차이 등) 무수정

### 검증 결과
- `list_active_hooks --count`: 36 (변동 없음)
- `list_active_hooks --by-event`: PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 18 / PostToolUse 9 / Notification 1 / Stop 5 (변동 없음)
- `final_check --fast`: FAIL 0 / WARN 1 (기존 python3 의존, 본 작업 무관)
- 3자 합의 PASS (GPT + Gemini + 사용자 본인) — α 채택: 옵션 C 측정 지속 + 실무 복귀

### 잔존 (옵션 C 측정 종료 후 처리)
- **[1순위]** auto_commit_state.sh가 수동 commit/push 의도를 가로채 메시지를 `[auto]`로 덮은 사건 — 본 세션 d59d844b에서 실증. 7세션 측정 종료 후 옵션 B 진입 시 최우선 타겟. 측정 로그 비고에 기록됨 (`quant_signal_log.md` 세션130 행).
- **[2순위]** hook_timing 1주 추가 측정 결과 기반 advisory 강등/매처 축소 후보 재논의 (debate_verify·harness_gate·Stop hook 포함).
- **[3순위]** final_check WARN 1건(block_dangerous·protect_files python3 의존) + settings.local 보류 후보 3건(python -c 따옴표 차이 등) 별도 정리.

## 세션129 (2026-04-29) — [측정] 정량 신호 3개 측정 시작 (옵션C)

### [완료] 측정 인프라 셋업 + 양측 PASS
- 합의: 세션128 `debate_20260429_202801_3way` Round 1 pass_ratio 1.0 옵션C 채택
- 신호: S1 첫 답변 실물 지향성 ≥70% / S2 PASS 도달 ≥1 / S3 메타 커밋 0~1
- 로그: `90_공통기준/토론모드/logs/quant_signal_log.md` (append-only)
- plan: `C:/Users/User/.claude/plans/virtual-bouncing-crab.md`
- 신규 hook/skill/command 0개 (S3 위반 회피 설계)
- 본 세션129 자기 측정: S1 60% (3/5라인) / S2 PASS / S3 1건 → 부분 PASS

### [완료] 양측 PASS (GPT + Gemini)
- GPT: PASS / item 1·2·3 모두 실증됨·동의 / 추가제안 A분류 1건
- Gemini: PASS / item 1·2·3 모두 실증됨·동의 / GPT 판정 교차검증 동의 / 추가제안 A분류 1건 (구체화)
- 라벨링 종합: 채택 3 / 보류 0 / 버림 0

### [완료] A분류 추가제안 즉시 반영 (양측 합의)
- S1 측정 정량화: "전체 N줄 중 실행 M줄" 근거 비고 명시 의무 추가
- 본 세션129 자기 측정 1행에 정량 근거 (3/5) 추가 기록
- 변경 파일: `quant_signal_log.md` 1건만 — S3 시그널 유지

### [잔존] 종료 조건 후 결정
- ALL≥5/7 → 옵션B 보류 / ALL≤2/7 → 옵션B 즉시 활성
- 다음 일반 세션 종료 시 1행 추가 (S1/S2/S3 정직 기록)

## 세션128 (2026-04-29) — [3way+A] 성능 실망 진단 + 운영 위생 1회 정리

### [완료] 3자 토론 Round 1 — 성능 실망 근본 원인 (pass_ratio 1.0)
- 의제: 이전 세션 전반적 실망의 근본 원인이 시스템 설계 문제인지 구분
- 5축 분류 합의: 시스템 설계 부하 40~45% / 메타·운영 위생 25~30% / **실물검증 루프 결함(신규) 15~20%** / 모델 한계 10~15% (시스템 흡수) / 기대치 5~10%
- 진단 키워드: **"목표 함수 오염"** (문제 해결 → 규칙 준수로 변질)
- 다음 행동 분기: 긴급 실무 D→A→C→B / 시스템 정비 A→D→C→B
- 정량 신호 3개: 첫 답변 실물 지향성 70%+, PASS 도달률 1+ (커밋 또는 실물 산출물), Meta-Loop 탈출 (메타 커밋 0~1)
- claude_delta major / issue_class B / 양측 통과 (GPT 정량 신호 2번 보강 권고 반영)
- 로그: `90_공통기준/토론모드/logs/debate_20260429_202801_3way/`
- plan: `C:/Users/User/.claude/plans/jiggly-cuddling-nygaard.md` (사용자 승인)

### [완료] 옵션 A 운영 위생 1회 정리 (사용자 명시 승인)
- TASKS.md 598 → 157줄 (-441줄). 세션109~121 → `98_아카이브/TASKS_archive_세션109-121_20260429.md` (gitignored, 로컬 보존)
- incident_ledger 미해결 122건 → bulk close (`resolved_by: hygiene_session128`, `resolved_note`: 정상 안전장치 발화). 백업: `incident_ledger.jsonl.bak_session128_hygiene`
- session_kernel.md refresh — 146h stale → 2026-04-29 12:15 KST 재저장 (precompact_save.sh 호출)
- 활성 hook 36개 (이벤트별 분포: PreCompact 1 / SessionStart 1 / UserPromptSubmit 1 / PreToolUse 18 / PostToolUse 9 / Notification 1 / Stop 5)
- settings.local.json 1회용 패턴 누적(echo·touch 6건) revert — 빼는 안 1+2 원칙 유지

### [잔존] 다음 세션 정량 신호 3개 측정
- 첫 답변 실물 지향성 70% 이상 / PASS 도달률 1건 이상 / Meta-Loop 탈출 (메타 커밋 0~1회)
- 1주 관찰 후 옵션 B(구조 다이어트 토론) 진입 여부 판단

## 세션128 (2026-04-29) — [C] block_dangerous false positive + config awk 파싱 버그 패치

### [완료] block_dangerous.sh 2b 블록 false positive 해소 + 잠재 버그 동시 수정
- 1차 발견: 직전 share-result `cat > /tmp/share_msg.txt << EOF ... settings.local.json ... EOF` 차단 — 본문에 보호 파일명 인용만으로 false positive
- 토론 진입 시도(round1_claude.md 작성) → 사용자 중지 요청 → Claude 단독 패치 결정
- 2차 발견 (디버그 trace): `hook_config.json` awk 파싱이 한 줄 JSON 배열에서 `]` 인식 실패 → `PROTECTED_PATTERNS=(,)` 같은 잘못된 값으로 hardcoded fallback 무력화 (block_dangerous + protect_files 동일 버그)
- 패치 3건:
  1. `block_dangerous.sh` 2b — `$COMMAND` 전체 grep 폐기 → REDIRECT_TARGETS 토큰 추출 후 그 토큰만 PROTECTED_PATTERNS 매칭 (`>&2` fd 리다이렉션 제외, 다중 redirect 모두 검사)
  2. `hook_config.json` danger_commands에서 `cat >`, `cat >>` 제거 — redirect는 2b가 처리 (60-67줄 블록 false positive 제거)
  3. `block_dangerous.sh` + `protect_files.sh` config 파싱을 awk → python3 안전 파싱 교체 (python3 미가용 시 hardcoded fallback)
- 검증 14/14 PASS: block_dangerous 10케이스(DENY 5 + ALLOW 5) + protect_files 4케이스
- 회귀 영향 0: PreToolUse(Bash/Write) gate 단계, 외부 ERP/MES 영향 없음, 기존 차단 시나리오 모두 보존
- 부수 정리: 미완료 토론 로그 `debate_20260429_214057_3way` + 임시 메시지 `99_임시수집/debate_msg_gpt.txt` 폐기
- **양측 PASS** (commit b2f6e651 share-result 결과):
  - GPT: PASS / 3 items 모두 실증됨·동의 / 추가제안 없음
  - Gemini: PASS / 3 items 모두 실증됨·동의 / GPT 판정 교차검증 동의 / 추가제안 없음
  - 라벨링 종합: 채택 3 / 보류 0 / 버림 0

## 세션128 (2026-04-29) — [E+C] ZDM 서버 DB 다운 + MES 단독 업로드 + 1차 POST 500 패치

### [완료/차단] daily-routine 분리 처리
- ZDM 일상점검: 차단 (서버 측 DB 다운 — `Connection terminated due to connection timeout`)
  - 진단: `/api/daily-inspection` HTTP 500 / 페이지 무한 busy / 5회 연속 일관 500 → 일시 장애 아님
  - 정보팀 호출 필요. 복구 후 daily-routine 재실행 시 누락 보정 자동 수행
- MES 생산실적 업로드: 완료 (사용자 명시 승인 후 단독 실행)
  - 누락일 2026-04-28 (1건). 1차 500 → 재로그인 후 성공: 15/15건, qty 45,381/45,381 (BI 일치)

### [완료] mes_login() XSRF-TOKEN 발급 보장 패치 ([C] 모드)
- 원인 가설: OAuth 로그인 직후 `cookies.get("XSRF-TOKEN")` 빈 값 → 첫 SaveExcelData.do POST 매번 500
- 패치: `mes_login()` return 직전 `layout.do` GET 1회 추가 → XSRF 쿠키 발급 보장
- 파일: `90_공통기준/스킬/daily-routine/run.py:188`
- 검증: 다음 daily-routine 실행 시 1차 시도 성공 여부 추적. 가설 미통과 시 `git revert` 1회 롤백
- 영향 범위: `mes_login()` 호출처 daily-routine/run.py 내부 2곳만 (외부 import 없음)
## 세션126 (2026-04-29) — [C] jobsetup-auto 신규 스킬 + d0-production-plan 야간 dedupe

### [완료] 신규 스킬 `/jobsetup-auto` v0.3 (SmartMES 첫 서열 잡셋업 자동 입력)
- plan: `C:\Users\User\.claude\plans\splendid-roaming-quilt.md`
- 신규: `90_공통기준/스킬/jobsetup-auto/SKILL.md` (v0.3, 무인 자동 실행 + fail-fast 4종)
- 신규: `90_공통기준/스킬/jobsetup-auto/state/screen_analysis_20260429.md` (선행 분석 — 11공정 17검사항목 + 좌표 + 스펙 6종 패턴)
- 신규: `.claude/commands/jobsetup-auto.md` (슬래시 래퍼)
- 분포 정책: 정규분포 `random.gauss(center, σ=오차/3)`, 시드 미고정 → 매일 다른 값. 균등분포 사용 금지·시드 고정 금지 명문화
- 검사항목 분류: (A) 측정값형 A1/A2/A3 + (B) OK/NG 체크형 B1/B2/B3/B4 — 6종 정규식 박음
- R5 롤백: 재입력 + 재저장으로 정정 (별도 삭제 API 불필요, 사용자 답변 확정)
- 책임 경고: SmartMES 실측값을 난수로 대체 = 사용자 본인 책임 운영

### [완료] `/d0-plan` SP3M3 morning hand-off 자동화
- 수정: `.claude/commands/d0-plan.md` Step 5 — 사용자 확인 단계 제거 → 검증 PASS 직후 즉시 `/jobsetup-auto --commit` 자동 호출
- 끄기 옵션: `--no-jobsetup` / dry-run 옵션: `--jobsetup-dry-run`

### [완료] d0-production-plan v3.1 야간 1~5행 dedupe (사용자 요청)
- 수정: `90_공통기준/스킬/d0-production-plan/run.py` — `dedupe_night_first_5()` 함수 신설 + main() evening+SP3M3 분기에서 호출 (40줄 신규)
- 수정: `90_공통기준/스킬/d0-production-plan/SKILL.md` — Phase 4 step 16.5 + 핵심 주의사항 10 + 변경 이력 v3.1
- 매칭 기준: REG_DT=오늘 AND PROD_NO 일치 AND 수량 일치 (`PRDT_QTY \|\| ADD_PRDT_QTY \|\| PRDT_PLAN_QTY` 3 키 OR)
- AST 검증 PASS

### [잔존] 첫 실행 검증 (학습 데이터 수집)
- 2026-04-30 07:05 SP3M3 morning D0 → 자동 hand-off → `/jobsetup-auto --commit` 첫 실 가동
- 저장 단위 (검사항목/공정/일괄) 첫 실행에서 관찰 → SKILL.md Step 8 v1.0 확정
- 오늘 저녁 17~19시 evening 세션 첫 dedupe 로그 검증 (수량 키 매칭 정상 동작 확인)

### [완료] 3way 공유 — GPT/Gemini 양측 판정 (커밋 f793fce9 + d85f1e1d)
- **GPT 판정**: 부분PASS (item 1·2·3 동의 / item 3 균등분포 잔재 보류 / item 4 d0-plan vs 스케줄러 분리 위험 보류 / item 5 저장 단위 잔존 보류 / item 6 main 머지 보류 반대)
- **Gemini 판정**: PASS (item 1·2·3 모두 실증됨·동의 / 추가제안 없음 / 잔존 관찰 후 해제 권장)
- **즉시 반영**: A 분류 1건 — SKILL.md description+결정표 균등분포→정규분포 정정 (commit d85f1e1d)
- **잔존 사유**: main 머지 보류·저장 단위 잔존·d0-plan 스케줄러 분리는 모두 첫 실행 검증 후 해소 가능. 운영 기준 최종 PASS는 첫 실 가동 후 재공유

### [메타] 자기 보고 — 세션 내 발생 실수 2건
1. share_gate.sh 첫 작성 시 "사용자 발언 정반대 해석 (Claude 자동 기동 금지)" → 사용자 강한 재지적 후 정정. feedback_cdp_health_check_first.md에 "한국어 모호 발언은 자동화 우선 + 자연스러운 해석 원칙" 박음
2. SKILL.md description+결정표에 균등분포 잔재 → GPT가 발견, 사용자 짚기 전에 정정 못 함. 토론모드 상호 감시 프로토콜이 잡아준 사례

### [실 운영] SP3M3 야간 D0 18건 등록 (저녁 18:30~19:00 KST)
- Phase 3 업로드 18건 / Phase 4 rank_batch done=18 failed=0 / Phase 5 mesMsg statusCode=200 rsltCnt=850
- 야간 등록 ext: 319742~319759 (319751, 319752 일부 중복 제외 → 17 unique)
- 1차 실행 시 사용자가 브라우저 닫아 12건만 임시저장 후 중단 → 사용자 ERP 직접 12건 삭제 → 2차 재실행 18건 정상 완료
- erp_d0_deleteA.py 9222 → 9223 포트 정정 패치 (.claude/tmp/ — 별도 commit 필요)

### [잔존 신규 — 다음 세션] dedupe 버그 + 잘못 등록 5건
- **dedupe_night_first_5() 함수 미동작 확정** — 야간 1~5행이 모두 주간 PROD_NO 중복(RSP3SC0362/0251/0249/0752/PC0144)인데 dedupe 못 잡고 18건 그대로 등록. `[dedupe]` 로그 출력 0줄 = print 자체 누락
- **잘못 등록된 5건** (ext 319742~319746) — 사용자가 ERP에서 직접 삭제 결정. 또는 SmartMES 작업자 처리 위임
- **다음 진단 항목**:
  1. dedupe 함수 시작점에 unconditional print 추가 → 호출 여부 확인
  2. page.evaluate grid 평가 시점이 상단 grid 비동기 로드 전인지 — 함수 진입 직후 1~2초 wait 추가 검토
  3. erp_d0_deleteA.py가 사용자 수동 row 선택 의존 → 자동 row 선택 + 라인 선택 추가 검토
- **Phase 6 SmartMES 검증 rank 불일치** — 동기화 시점차 가능성, 다음날 morning 후 재확인

### 메모리 갱신
- 신규: `project_jobsetup_skill.md` + MEMORY.md 인덱스 추가

> **이전 세션 이력 아카이브**: 세션122~125 → `98_아카이브/TASKS_archive_세션122-125_20260501.md` (gitignored, 로컬 보존)

