# d0-production-plan — MANUAL

> Phase 0~7 절차 / 모드 분기 / 핵심 주의사항 / 변경 이력. SKILL.md는 호출 트리거 + 80줄 요약.

## 개요
SP3M3 생산지시서 xlsm 단일 파일에서 라인별 계획을 추출해 ERP D0추가생산지시 화면에 업로드 + 서열 반영 + MES 전송 + 자동 검증.

## 운영 세션 (하루 2회)

파일명 = OUTER 생산일 = D+1. SP3M3 야간은 시작일(오늘) 기준.

| 세션 | 실행 시점 | 파일명 날짜 | 처리 내용 | ERP 생산일 |
|------|---------|-----------|---------|-----------|
| 저녁 | 17~19시 | 내일 | ① SP3M3 야간 (출력용 야간 섹션) | **오늘** (야간 시작일) |
|  |  |  | ② SD9A01 OUTER D+1 (OUTER SD9M01 블록) | **내일** (파일명 날짜) |
| 아침 | 07:10경 | 오늘 (어제 저녁 저장) | ③ SP3M3 주간 (출력용 주간 섹션, 누적 ≥ 3600 컷) | **오늘** (파일명 날짜) |

## 사전 준비
- Chrome 디버깅: `--remote-debugging-port=9223`, 프로필 `C:\Users\User\.flow-chrome-debug`
- ERP 로그인: `0109` pyautogui 자동완성
- Python 의존성: `pyautogui`, `playwright`, `openpyxl`, **`pywin32`** (Excel COM 필수)
- Microsoft Excel 설치 (xlsx 생성 COM 호출)
- Z 드라이브 마운트: `\\210.216.217.180\zz-group`

## 파일 경로 규칙
```
Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서\{YYYY}년 생산지시\{MM}월\SP3M3_생산지시서_({YY.MM.DD}).xlsm
```
- 저장 시점 전일 오후 → 파일명 = D+1 (내일 날짜)
- "수정본" 접미사 우선 (mtime 최신)
- 저녁 세션: target_date = tomorrow → 파일명 = tomorrow
- 아침 세션: target_date = today → 파일명 = today (어제 저녁 생성)
- 파일 헤더 `◀ D+1` = 파일명 날짜, `◀ D+2` = 파일명 날짜+1

## 라인 설정
| 라인 | ERP 코드 | LINE_DIV_CD | 시트 | 라인 필터 | 품번 컬럼 | 수량 컬럼 | 저장 URL |
|------|---------|------------|------|----------|---------|---------|---------|
| MAIN | SP3M3 | 02 | `출력용` | R1 `◀ D+1 야간계획`, R35 `◀ D+2 주간계획` | I (신MES, 정제) | K (지시) | `/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do` |
| OUTER | SD9A01 | 01 | `OUTER 생산계획` | B열 `== 'SD9M01'` (D+1 블록) | D (접미사 포함) | E (수량) | `/prdtPlanMng/multiListOuterPrdtPlanRankDecideMng.do` |

## 사용법
```bash
# 기본값 = 옵션 A 하이브리드 (--api-mode default=True, 세션133)
python run.py --session morning              # 아침 (주간 3600컷, 하이브리드)
python run.py --session evening              # 저녁 (야간 + OUTER, 하이브리드)
python run.py --session auto                 # 시간대 자동 판정

# 회귀 fallback — 화면 모드
python run.py --session morning --legacy-mode

# dry-run (서버 저장 안 함)
python run.py --session evening --dry-run

# 대상 날짜 명시
python run.py --session evening --target-date 2026-04-24

# 라인 제한
python run.py --session evening --line SP3M3
python run.py --session evening --line SD9A01

# 1건 PoC (xlsm 21번째 등 미등록 후보)
python run.py --session morning --line SP3M3 --xlsx <1건xlsx> --target-date YYYY-MM-DD

# Phase 5 final_save 차단 (P3 사고 재발 방지)
python run.py --session morning --no-mes-send
```

## 모드 분기 (세션133)
| 옵션 | 동작 | 용도 |
|------|------|------|
| 기본 (--api-mode default=True) | Phase 4 rank를 requests 직접 POST | 운영 |
| `--legacy-mode` | Phase 4 jQuery.ajax (화면 모드) | 회귀 fallback |
| `--no-mes-send` | Phase 5 final_save 차단 | PoC/검증 |
| `--dry-run` | Phase 2까지만 | 추출 검증 |
| `--parse-only` | Phase 3 selectList까지 | 파싱 검증 |
| `--xlsx <path>` | Phase 1 추출 건너뛰고 외부 xlsx 직접 업로드 | 1건 PoC, 첨부 처리 |

## 실행 절차

### Phase 0: 환경 준비
1. Z 드라이브 접근 확인
2. Chrome CDP 9223 기동 (재사용)
3. ERP OAuth 자동 로그인 (pyautogui)
4. D0 화면 진입: `http://erp-dev.samsong.com:19100/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do`

### Phase 1: 파일 해석
5. target_date 계산
6. SP3M3 생산지시서 xlsm 탐색 (수정본 우선)
7. 세션별 시트 추출:
   - 저녁: 출력용 야간 섹션 + OUTER 시트 SD9M01 D+1 블록
   - 아침: 출력용 주간 섹션 (누적 ≥ 3600 도달 행까지 컷)

### Phase 2: 업로드 파일 생성
8. 라인별 임시 엑셀 생성 (생산일 | 제품번호 | 생산량)
9. 저장 경로: `06_생산관리/D0_업로드/d0_{line}_{date}.xlsx`
10. **⚠ 엑셀 생성은 반드시 `win32com.client`(Excel COM)** (세션104 실증)
    - openpyxl 생성 또는 `load_workbook → save` 한 파일 → ERP 서버 파서가 COL2 빈값 인식
    - 흐름: `shutil.copy(template, out)` → `Excel.Application` → `ClearContents` → 새 데이터 → `wb.Save()` → `Excel.Quit()`
    - 템플릿: `90_공통기준/스킬/d0-production-plan/template/SSKR_D0_template.xlsx` (ERP `/js/workspace/pm/prdtPlanMng/SSKR D+0 추가생산 Upload.xlsx` 다운로드본)

### Phase 3: D0 업로드 (라인별)
10. 엑셀업로드 팝업 오픈 (#btnExcelUpload)
11. `jQuery.ajax` POST `/prdtPlanMng/selectListPmD0AddnUpload.do` (multipart, 폼 `uploadfrm`, 파일 필드 `files`)
12. 응답 data.list로 팝업 그리드 채우기 (excelUploadCallBack)
13. 오류 행 검증 (ERROR_FLAG)
14. `POST /prdtPlanMng/multiListPmD0AddnUpload.do` JSON `{excelList, ADDN_PRDT_REASON_CD:"002"}` → DB 저장
15. 상단 그리드 자동 반영 확인

### Phase 1.5: dedupe (세션133)
- `dedupe_existing_registrations(page, items, prod_date, line_cd)` — selectList 호출 전
- 검사: ERP 좌측 grid_body `REG_DT == prod_date AND PROD_NO 일치` → items에서 제외
- 주야간 cross 중복 허용 (다른 PLAN_DA 검사 X)
- 야간 evening 1~5행 dedupe(`dedupe_night_first_5`)는 별도 (16.5 참조)
- 결과 0건 → selectList/multiList/rank/final_save 모두 스킵

### 해당일 파일 없으면 작업 패스 (세션133)
- `find_plan_file()` `FileNotFoundError` → `[skip] 해당일 파일 없음 — 작업 패스` + exit 0
- `verify_run.py check_log_success` `skip_no_file` 마커 인식 → recover 알림 0
- 토요일/공휴일 자동 skip

### Phase 4: 서열 배치
- **하이브리드 (기본 `args.api_mode=True`)**: `api_rank_batch(page, items, target_line, save_url, sess)` — process_one_row(dry_run=True)로 sGridList 채움 + dataList 추출 + **requests 직접 POST** `multiListMainSubPrdtPlanRankDecideMng.do` (sendMesFlag='N' 강제)
  - Content-Type: `application/json; charset=UTF-8` (P4 단계 2)
  - 헤더: `ajax: true` + `X-XSRF-TOKEN` 매 호출 직전 갱신
  - mesMsg 비어있지 않으면 즉시 break (sendMesFlag='N'인데 MES 의심 차단)
- **레거시 (`--legacy-mode`)**: 기존 `rank_batch` (jQuery.ajax POST)

16. 엑셀 순서대로 상단 행 idx 매핑 (동일 품번 여러 건이면 REG_NO 최대값)

16.5. **야간 1~5행 dedupe** (사용자 요청 2026-04-29, v3.2 정정)
   - 적용: SP3M3 야간만 (OUTER 영향 없음)
   - 검사 범위: 야간 첫 5행 (서열 1~5번)
   - 매칭 (v3.2): 같은 `REG_DT`(=오늘) ERP 기등록 행과 **PROD_NO 일치만** (수량 무관)
     - v3.1까지 PROD_NO+수량 매칭 → 같은 품번이면 수량 다르더라도 작업자 입장 중복 위험 동일
   - 매칭 행 → `skip=True` (야간 등록 제외)
   - 데이터 소스: ERP D0 상단 그리드 GET (Phase 0/3에서 로드)
   - 로그: `[dedupe] 야간 N행 PROD_NO=<X> 야간qty=<a> 주간qty=<b> → 품번 일치, 제외`

17. 각 품번 (16.5에서 skip 안 된 행만):
    - rowClick 로직 재현 (totSelectRowData + mGridList.searchListData)
    - 좌하단 로드 대기 → 라인 코드 선택
    - sGridList.searchListData → 우하단 로드 대기
    - addRow 직접 호출 (내장 중복 체크 우회, 주간/야간 중복 허용)
    - multiList API 임시저장 (sendMesFlag=N)
18. 라인별 저장 URL 분기

### Phase 5: 최종 저장 + MES 전송
19. 라인별 sendMesFlag=Y multiList POST
20. 응답 statusCode=200 + mesMsg statusCode=200 확인

### Phase 6: 검증
21. SmartMES API: `POST http://lmes-dev.samsong.com:19220/v2/prdt/schdl/list.api`
    - body: `{lineCd, prdtDa}` (lineCd="SP3M3" 또는 "SD9A01")
22. rank 순서와 엑셀 순서 대조

## 핵심 주의사항

⛔ **사용자 첨부 파일 가드** (세션115 사고 실증, 2026-04-27)
- 첨부 발견 시 자동 실행 금지
- (A) 첨부 사용(`--xlsx <path>`) (B) Z드라이브 자동 탐색 중 명시 선택 받은 후 진행
- MES는 ERP 삭제해도 잔존 → 정정 매우 어려움

0. **⚠ 업로드 xlsx는 Excel COM으로만 생성** (세션104, 2026-04-24)
   - openpyxl 생성 → ERP 파서 COL2 빈값, 15건 전부 ERROR_FLAG="Y"
   - 원인: OOXML 내부 구조 차이 (sharedStrings.xml, cell type, 시트 XML 네임스페이스)
   - 근본 해결: `win32com.client.Dispatch("Excel.Application")` 편집·저장
1. **jQuery.ajax 경로 필수** — fetch 직접 호출 시 500 (XSRF 공통 설정 미상속)
2. **파일 필드명 `files` (복수형)** — `fileHelper.js` allSave 규칙
3. **EXT_PLAN_REG_NO 최대값 매핑** — 동일 품번 상단 여러 건 시 최대값
4. **주간/야간 중복 품번** — 서버가 다른 EXT_PLAN_REG_NO로 P + A 공존. 신규 REG_NO 사용
5. **s_grid 폴링 필수** — 기존 P/R 행 로드 완료 후 addRow (미완 시 payload 유실)
6. **OUTER 품번 접미사 포함** — G열 "품번정제" 사용 금지, D열 그대로
7. **OUTER 시트 7개 라인 혼재** — B열 정확 `== 'SD9M01'` (헤더 `◀ SD9M01 D+1` 등 제외)
8. **주간 3600 컷** — 누적 ≥ 3600 도달 첫 행까지 포함 (초과 1건 포함)
9. **중복 실행 방지** — 같은 날짜 저장된 건 스킵 (EXT_PLAN_REG_NO 기준)
10. **야간 1~5행 주간 중복 dedupe** (v3.2) — Phase 4 step 16.5 참조

## 실패 조건
- Chrome CDP 9223 미응답
- ERP OAuth 실패 (저장 자격증명 미사용)
- Z 드라이브 미접근
- 생산지시서 xlsm 미존재
- 출력용 시트 헤더 `◀ D+1 야간계획` / `◀ D+2 주간계획` 미발견
- OUTER 시트 B열 `SD9M01` 행 0건
- selectList 서버 500
- multiList 서버 에러
- MES 전송 statusCode != 200

## 중단 기준
- 상단 그리드 등록 0건 (파싱 실패)
- 서열 배치 중 임시저장 실패 (첫 실패 즉시 중단)
- 최종 저장 실패

## 검증 항목
- 라인별 엑셀 건수 = ERP 상단 그리드 저장 건수
- 야간 서열 A 행 수 = 엑셀 건수
- SmartMES rank 순서 = 엑셀 순서
- MES 응답 rsltCnt > 0

## Phase 7 — 사후 검증 + 자동 재실행 (verify_run.py)

목적: D0_SP3M3_Morning(07:05) / Night Windows 작업 스케줄러 실행 후 결과 자동 검증.

### 호출
```
python verify_run.py --session morning --line SP3M3
python verify_run.py --session night --line SP3M3
python verify_run.py --session morning --line SP3M3 --dry-run    # 점검만
```

### 원인 분류
- **RETRY_OK**: timeout / 5xx / 네트워크 / Chrome CDP 미기동 / OAuth — Phase 0/1/2 한정
- **RETRY_BLOCK**: timeout이 Phase 3+에 발생, 또는 dedupe N건 정리 시
- **RETRY_NO**: xlsx 미존재 / 권한 / 마스터 불일치 — 즉시 알림 + 재시도 0
- **UNKNOWN**: 분류 실패 — 1회 재시도 후 알림

### 백오프 (RETRY_OK)
- 1분 / 5분 / 15분 / 30분 — 누적 51분 한계
- 매 시도 전 dedupe 선행 (`erp_d0_dedupe.py --execute`)
- schtasks Running 시 5분 대기 후 Phase 분석:
  - Phase 0/1/2 → 강제 종료 OK
  - Phase 3+ → 종료 금지 + 즉시 종결

### 안전장치 (R5)
- lock 파일 atomic — `os.O_EXCL` + JSON `{pid, started, session}` + 60분 stale
- 누적 51분 도달 → 자동 재시도 종료
- dedupe 선행 매 시도
- Phase 3+ 강제 종료 금지 (트랜잭션 단절 방지)
- 롤백: `erp_d0_dedupe.py --execute`

### 알림 (현재 stub)
- 현재: `.claude/state/d0_verify_notify.jsonl` jsonl append만
- DOM/스크린샷 저장: 미구현 (Phase 2 이월)
- Phase 2 통합 예정: Slack MCP + DOM snapshot + 스크린샷

### 알림 정책
- 성공: 무알림
- 재시도 후 성공: 1건 (재시도 N회, 누적 M초)
- RETRY_BLOCK / RETRY_NO / UNKNOWN: 즉시 + 로그 끝 30줄
- 누적 한계 도달: 즉시 + 로그 끝 30줄

### Windows 작업 스케줄러 등록
```
schtasks /create /TN "D0_SP3M3_Morning_Recover" /TR "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning_recover.bat" /SC DAILY /ST 07:15 /RU <USER>
```
기존 `run_morning_verify.bat`(Phase 3까지 parse-only)와 별개. 본 verify_run은 morning 종료 후 사후 검증, wrapper는 `run_morning_recover.bat`.

## 되돌리기

- **서열 행 삭제 API** (야간 A 행): `DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do` payload `{EXT_PLAN_REG_NO, STD_DA, PLAN_DA, PROD_NO, LINE_CD}`
  - `.claude/tmp/erp_d0_deleteA.py --all` 일괄 삭제
- **D0 등록 삭제 API** (상단 그리드 1건, 세션110, UI 미노출): `DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do` payload `{REG_NO}`
  - 호출처: `totGridList.deleteRow(rowData)` (코드 있음, UI 버튼 X)
  - 식별: SmartMES `sewmacLabelScanQty` = ERP `REG_NO` (필드명 misleading)
  - **중복 등록 자동 정리**: `.claude/tmp/erp_d0_dedupe.py --line SP3M3 --date YYYYMMDD [--execute]`
    - SmartMES rank 작은 쪽 보존 / 큰 쪽 삭제 자동 식별
    - 기본 dry-run, `--execute`로 실 DELETE
    - 세션110 실증: 7건 중복 1분 내 정리 (2026-04-27)

## 변경 이력
| 일자 | 버전 | 내용 |
|------|------|------|
| 2026-04-23 | v1 | 초기. SP3M3 야간 실검증. OUTER/주간 구조 완비 |
| 2026-04-24 | v2 | 주간/야간 실운영. (a) make_upload_xlsx openpyxl→win32com, (b) 팝업 재사용, (c) verify_prod_date 파라미터. D0_SP3M3_Morning 자동 운영 개시 |
| 2026-04-27 | v3 | 세션110: 숨겨진 D0 삭제 API + sewmacLabelScanQty↔REG_NO 매핑 + erp_d0_dedupe.py + 7건 정리 실증 |
| 2026-04-29 | v3.1 | 야간 1~5행 주간 중복 dedupe. `dedupe_night_first_5()` + main() evening+SP3M3 분기 |
| 2026-04-29 | v3.2 | dedupe 매칭 단순화 — PROD_NO+수량 → PROD_NO만 (수량 무관) |
| 2026-05-01 | v4.0 | 세션133 옵션 A 하이브리드 chain. Phase 4 requests 직접 POST(sendMesFlag='N'), `--legacy-mode` fallback. dedupe 사용자 명시 보강. `--no-mes-send`, 해당일 파일 없으면 패스, 인접 월 fallback, verify_run RETRY_NO 추가 |
