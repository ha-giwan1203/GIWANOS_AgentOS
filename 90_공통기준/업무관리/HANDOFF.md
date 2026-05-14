# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-05-13 KST — **세션157-2** [C] **떠넘기기 유도 hook/지침 환경 정리 (사용자 지시 — 막기보다 유도 제거)**. 사용자 본질 지적: "막는것보다 사용자 확인후·승인후 같은 유도하는 훅이나 지침을 제거하는 게 맞다." 변경: (1) finish_trigger_detect.sh — 안내 메시지 주입 비활성(쉘 골조만 유지, exit 0) (2) share_gate.sh — "3way 공유 필수" 강요 문구 제거, 감지 신호 stderr 1줄 + log 기록 (3) completion_gate delegation_guard 차단 메시지 단순화 — 4단 가이드라인 → "질문 없이 네 판단으로 재작성하라" 1줄 (4) CLAUDE.md 질문 허용 2조건 → 1조건(ERP/MES 비가역 1줄 통보, 확인 아님). "사용자 명시 선택 요구" 폐기 — 사용자 발화 자체가 입력이므로 별도 묻기 불요 (5) /finish 자동 트리거 지침 정리 — Claude 자체 판단으로 처리 (6) 메모리 feedback_authority_ladder.md / feedback_finish_auto_trigger.md 갱신 — 세션157 정정 명기. / **세션157** [B+D+C] **떠넘기기 재발 진단 + 3way 만장일치 hook gate 부분 복원**. 사용자 체감 지적("또 떠넘기는 거 같다·스스로 사고를 포기한 느낌·지침을 안 보는 것 같다") → B 모드 진단 → 3way 토론 R1 pass_ratio=1.00 → C 모드 구현. H1 버림(자기검열 불충분 실증) / H2 채택(completion_gate.sh Stop 단계 delegation guard Phase 0 최소 복원) / H3 부분 채택(세션148 "문서만 충분" 하위 가정만 폐기, R2/R3/R4 폐기·2조건·C 모드 완화는 유지). 변경: completion_gate.sh +37줄(정규식 9개 + whitelist 7개 + decision:block + stop_hook_active 2회차 통과 + delegation_guard.jsonl 로그) / CLAUDE.md "질문 허용 2개뿐" 압축 + 금지 표현 9개로 확장 / feedback_authority_ladder.md hook_gate enforcement 갱신 / project_session148_hook_gate_relapse.md 신설. smoke 3 시나리오 PASS (block / whitelist / 2회차). 로그: 90_공통기준/토론모드/logs/debate_20260513_211646_3way/. / **세션155** [A+C] **SP3M3 5/13 야간계획 반영 + phase4 정렬 회귀 사고 fix + 헬퍼 추출**. evening --http-only 5건 누락(RSP3SC0644/0590/0584/0023/0026 야간 신규 ext 326730~326735에 rank 미박힘 — REG_NO ascending 정렬 버그, 세션152 동일 사고 2회 회귀) → 즉시 fix(d62649c7) + 보강 등록(rank 42~46, MES rsltCnt=250, WORK_STATUS=R 정상). `_sort_idx_map_desc` 헬퍼 추출 + feedback_d0_idx_map_sort_desc.md 메모리 + 호출부 주석 3중 회귀 차단(6a8d0933). 추가 CLAUDE.md 도메인 표에 d0-production-plan row 명시(62ca68bd) — 새 세션 라우팅 사고(SP3 메인서브 v2 OUTER xlsm 잘못 매칭) 방지 + feedback_d0_plan_routing.md 메모리 신설. sGrid 최종 46건(주간 18 + 야간 28). / **세션154** [A] **4월 외주 지원비용 양식 정리** — 리노텍·화인텍 2건 신규. `05_생산실적/조립비정산/05월/4월 지원/` 신설. 리노텍 = 3월(9건)+4월(6건) 통합 청구분 / 15건·9,175개·5,523,350원. 화인텍 = 메인SUB_지원받은 20행 / 14,590개·9,232,268원. 88810P 시리즈 서브품번 매핑(971/971/973/975)은 `\\210.216.217.180\zz-group\15. SP3 메인 CAPA점검\SP3M3\생산지시서\2025년 생산지시\01월\SP3메인서브 생산지시서 (2025.01.02).xlsx` "SP3 LINE 기준 정보" r159~r166 권위 — 3월 화인텍 양식·김종학GJ 마감상세에는 매핑 부재. / **세션153** [C] **d0-plan GERP 로그인·자동화 전면 재설계 + Claude 루틴 이관** — OAuth pyautogui 가로채기 영구 차단(page.fill DOM 직접) → HTTP OAuth(daily-routine 패턴 ERP 확장) → HTTP 업로드(multipart + JSON multiList, ADDN_PRDT_REASON_CD=002) → HTTP rank/final_save + setBeginTime Python 재현(휴식시간 8종) → 완전 브라우저-less 옵션 `--http-only` PoC PASS (RSP3PC0144 326320 rank=19 풀 흐름). 6 commit (dcd95815 / 69adfbb0 / db9c8bcd / 14a0ca14 / fafac0c9 / 4d9291eb). + Claude scheduled-task `d0-morning` 등록(월~토 07:11 KST) + Windows schtasks D0_SP3M3_Morning/Recover 2건 삭제 + Slack 알림 테스트 PASS(채널 C096LU8PH44, ts=1778637849). / **세션152** [C] **별건 fix** final_check.sh sed 패턴 ` KST` 옵셔널 누락 (L313·L362) → meta_drift 14건/session_drift 4건 누적 원인 / commit 861beaf9 main push 완료. / 세션152 [A+C] SP3M3 라인 조립비 등록 누락 점검 + 신규 스킬 `assy-registration-check` 신설 + V2 마스터 일괄 sync + 4월 오류리스트_추가.xlsx 218행 작성 + HCAMS02 NLR/CLR 단가 룰 적용. / 세션151 후속 [C] 5/11 morning OAuth 실패 → `_force_chrome_foreground` 신설 / 세션151 [B+C] D0 자동화 실패 분석 + 3종 패치 commit 59273df9 / 세션150 [A] 4월 이관품번 라인별 정리 시트 추가 완료. / **세션152 evening [A+C] SP3M3 야간계획 반영 사고 + run.py 4종 패치** (Phase 6 5건 누락 → idx_map 정렬 a-b→b-a 매뉴얼 4번 룰 준수 / pyautogui ID 0109 명시 typewrite / OAuth wait 60s→10s / 누락 5건 새 ext 보강 등록 + final_save 200).

## 세션157-3 (2026-05-13 KST) — 토론모드 가속 폴링 단축 + Safe-cutoff hook

### 발화 → 결과
- 사용자: "토론모드는 --http-only 유사방식으로 안되는건가" + "토론해서 플랜보강후 실행"
- 진행: 콘솔 fetch 가속안 검토 → 3자 토론 R1 → 폐기 + 폴링 단축 채택

### 3자 토론 R1 (pass_ratio=4/4=1.00 만장일치)
- 로그: 90_공통기준/토론모드/logs/debate_20260513_232210_3way/
- GPT 본론: ToS·계정 안전성 "실패" 판정 + 가속폭 라운드당 20~60초 한계
- Gemini 본론: 폴링 0.5/1/2초 + One-shot + 듀얼 bringToFront + Safe-cutoff 4종
- GPT 검증: 0.5초 → 1초 이상 보수 권고
- 최종 합의: 1/2/3초 폴링 + One-shot 추출 + Safe-cutoff hook

### 변경 (commit 5efc8edd)
- gpt-send/gpt-read/gemini-send/gemini-read 일반 모델 폴링 3/5/8 → 1/2/3초
- thinking 모델 long polling 유지 (race condition 방지)
- .claude/hooks/debate_safe_cutoff.sh 신설 (인증챌린지/대화미저장/사용량경고/보안알림 4종 감지)
- 토론모드 CLAUDE.md "## 폴링 단축 가속 정책" 섹션 신설
- 콘솔 fetch 폐기 결정 명문화

### 기대 효과
- 라운드 2~3분 → 1.5~2분 (20~50초 절감)
- ToS 안전 + ChatGPT 프로젝트방 컨텍스트 그대로

### 다음 세션 액션
- 실제 토론 라운드 1회 돌려 폴링 단축 체감 확인
- 텍스트 유실 race condition 모니터링 (One-shot 추출 직후 2회 연속 동일 검사로 방지)
- 가속 비활성 발생 시 .claude/state/debate_accel_disabled 확인 + 원인 진단 후 rm

---

## 세션153 — d0-plan GERP 로그인·자동화 전면 재설계 (2026-05-13 08:00~11:00)

**배경**: 5/13 morning 자동화 OAuth 2회 연속 `/login?error` → recover 51min 한계 도달 종료. 사용자 "왜 똑같은 문제를 반복하나" 발화 → 근본 진단.

**진단**: pyautogui 키보드 입력 + Chrome 비번관리자 자동완성이 OS focus 가로채기 취약. 세션141 hidden.vbs / 세션151 _kill_zombie_chrome / 세션152 OAuth 60→10s — 전부 타이밍·재시도 패치라 입력 메커니즘 자체는 그대로.

**A안 1단계 (HTTP OAuth)**: requests로 OAuth SSO POST 직접. ssoUrl 추출 → /login POST(userId/password/clientId=ERP/ssoUrl) → cookies(SESSION/XSRF-TOKEN/JSESSIONID) 확보 → playwright context 주입 → D0_URL 즉시 통과. ID/PW는 .oauth.json(.gitignore). selector dump: input[name=userId/password]/#loginBtn.

**A안 2단계 (HTTP 업로드)**: phase3을 requests multipart로. POPUP GET → selectListPmD0AddnUpload(files+hidden3) → multiListPmD0AddnUpload({excelList, ADDN_PRDT_REASON_CD:"002"}). 핵심 단서 — X-XSRF-TOKEN은 매 POST 직전 cookie 최신값 갱신 필수(불일치 시 500). ADDN_PRDT_REASON_CD 빈값 보내면 등록사유 빈 row 등록(사용자 화면 캡처로 발견 → "002"="신규추가수량" grid row 직접 dump).

**A안 3단계 (완전 브라우저-less)**: phase4(rank) + phase5(final_save) + phase6(verify) 모두 requests로 전환. process_one_row_via_http가 totGrid GET → mGrid GET → sGrid GET → rowData 구성 → save POST. final_save는 sGrid 재조회 + `_apply_set_begin_time` 적용 후 sendMesFlag='Y' POST. setBeginTime JS 정밀 mirror — UPH 기반 분 단위 + 휴식시간 8종(9:50/12:00/14:50/17:00/21:00/24:00/3:00/5:00) 자동 가산 + PRDT_RANK = idx+1 + PLAN_DA_S/E.

**단위 검증**: sGrid 18행 적용 시 ERP 기존 BEGIN/END/RANK와 100% 일치(휴식시간 4건 케이스 포함).

**PoC 실 등록 검증** (RSP3PC0144 1건, 5/13, --http-only):
- phase0 OAuth PASS, ensure_chrome_cdp 미호출 (브라우저 launch 0)
- phase3 D0 업로드 PASS / phase4 ext=326320 rank=19 / phase5 mesMsg 성공 rsltCnt=50
- phase6 서열 순서 엑셀 일치 ✅
- ERP grid 직접 dump 검증: REASON_CD=002, PRDT_RANK=19, BEGIN_TIME=19:50(연속), END_TIME=20:09, WORK_STATUS_CD=R

**자동화 이관**:
- Claude scheduled-task `d0-morning` 등록 (월~토 07:11 KST cron `11 7 * * 1-6`, jitter 적용 07:19)
- prompt: run_morning.bat 실행 + 실패 시 Slack 알림(C096LU8PH44 + <@U096LU8KNN8> 멘션)
- Windows schtasks D0_SP3M3_Morning + D0_SP3M3_Morning_Recover **삭제**
- Slack 알림 테스트 PASS (ts=1778637849)

**회귀 보험**: `--http-only` 옵션 default off. 매일 자동 실행은 기존 page.evaluate 경로 그대로(점진 전환). 1~2주 검증 후 default on 검토.

**잔여 정리**:
- 사용자 화면 수동 삭제 — RSP3PC0144 326312 / RSP3PC0143 326313 / RSP3SC0752 빈 등록사유 row (모두 정리 완료)
- ERP는 sGrid에 임시저장 후 sGrid 행 삭제 시 상단 grid 삭제 비활성 → D0 reload(F5) 후 활성 (실측 확인)

**부가 패치**: gerp-unregistered-check/erp_lookup.py도 동일 OAuth page.fill 패턴 동기화 (69adfbb0). daily-routine/run.py는 이미 requests POST 방식 — 패치 불필요.

## 세션152 evening — SP3M3 야간계획 반영 사고 (2026-05-12 18:39~19:30)

**배경**: 사용자 "SP3M3 야간계획 반영" 발화 → d0-production-plan evening 세션(--line SP3M3) 실행.

**실행 결과**:
- Phase 0~5: 정상 (24건 추출 → dedupe 1행 RSP3PC0054 제외 → 23건 ERP 업로드 + 서열 + MES 전송 statusCode 200 / mesMsg rsltCnt=900)
- Phase 6 SmartMES 대조: FAIL 5건 누락 (RSP3PC0130/RSP3PC0129/RSP3SC0644/RSP3SC0590/RSP3SC0584 ext=325225~325230)

**진단**: `_diag_dup_rows.py` 실측으로 5건 모두 ERP 그리드 2행 공존 확인 — 작은 ext(주간 기존) + 큰 ext(야간 신규 325983~325987). phase3 multiList INSERT 정상.

**근본 원인**: `api_rank_batch` `run.py:1046` idx_map 정렬이 `(a,b) => a - b` 오름차순 → 매뉴얼 4번 룰 "EXT_PLAN_REG_NO 최대값 매핑" 위반. 야간 items 1건 등장 시 0번째(=가장 작은 ext=주간 기존)에 매핑 → 야간 rank가 주간 행 위에 덮어 박힘.

**run.py 패치 4종 (세션152 evening)**:
1. **L1046 idx_map sort `b-a` 내림차순** — 매뉴얼 4번 룰 준수. 야간 1건 등장 시 신규 ext에 자동 매핑.
2. **L265~270 `ensure_erp_login`** pyautogui ID `0109` 명시 typewrite + `Ctrl+A` + `Delete` 초기화. 기존 `down`+`return` 자동완성 첫 항목 의존 폐기. 사용자 자동완성 ID 3개 저장 환경에서 매번 다른 ID 접속되던 사고 차단.
3. **L282/322~344 `_wait_oauth_complete` timeout 60s → 10s**. 0109 명시 입력으로 OAuth 정상 통과 가정 + 정체 시 fallback 빠른 진입.
4. `--no-dedupe` 옵션 추가했으나 사용자 정정 "1~5행 dedupe는 유지"로 즉시 원복 (net 변경 0).

**누락 5건 보강 (`_fix_missing_5.py`)**:
- 새 ext(325983~325987)에 직접 `process_one_row` 호출 → rank 39~43 박음
- `final_save` mesMsg rsltCnt=250 / statusCode 200 / MES 전송 완료
- 사용자 지시 "기존 잘못 박힌 5건 rank(ext=325225~325230 위 A rank) 삭제 X" — ERP 잔존 유지

**다음 morning (2026-05-13 07:10) 검증 포인트**:
- `[phase0]` 로그에서 `OAuth 완료 대기 60s 실패` 메시지 부재 확인 (10s로 단축됨)
- ID 0109 정확 입력 검증 (잘못된 ID 접속 사고 재발 X)
- idx_map 내림차순 자연 검증 (주간 새 등록 시 정렬 정상)

**잔존 자산**:
- `_diag_dup_rows.py` (5건 진단 스크립트, 동일 사고 재발 시 재사용)
- `_fix_missing_5.py` (5건 누락 보강 스크립트, 동일 사고 재발 시 참고)


---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260501_20260512.md` (세션152 별건 ~ 세션134)
> **이전 archive**: `98_아카이브/handoff_archive_20260430_20260430.md`

