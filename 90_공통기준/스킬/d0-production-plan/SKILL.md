---
name: d0-production-plan
description: >
  ERP D0추가생산지시 생산계획 반영 자동화 (SP3M3 MAIN + SD9A01 OUTER).
  다음 키워드/표현이 나오면 반드시 이 스킬 사용:
  "생산계획 반영", "생산계획 등록", "생산계획 올려", "생산계획 업로드",
  "D0 반영", "D0 등록", "D0 업로드", "D0 올려",
  "야간 계획 반영", "야간 계획 등록", "야간 올려", "야간 업로드",
  "주간 계획 반영", "주간 계획 등록", "주간 올려", "주간 업로드", "주간계획 등록",
  "SP3M3 주간", "SP3M3 야간", "SP3M3 계획", "SP3M3 반영", "SP3M3 등록",
  "아우터 계획", "OUTER 계획", "SD9A01 계획", "SD9A01 등록", "SD9A01 반영",
  "생산지시 반영", "생산지시 등록", "생산지시 업로드".
  ❌ 엑셀 파일을 직접 열거나, 모니터를 전환하거나, ERPSet Client(javaw.exe)를 건드리지 말 것.
  ❌ computer-use/마우스/키보드 조작 사용 금지. 반드시 이 스킬의 run.py 실행으로 처리.
  ⛔ 사용자 메시지에 xlsx/xlsm 첨부가 있으면 자동 실행 차단 — 첨부 사용 vs Z드라이브 자동 탐색 명시 확인 필수 (2026-04-27 사고 재발 방지).
  Z 드라이브의 SP3M3 생산지시서 xlsm을 자동 추출 또는 `--xlsx` 옵션으로 직접 지정 가능.
  Phase 0~6: Chrome CDP + OAuth 자동 로그인 → D0 화면 진입 → 엑셀 업로드(selectList + multiList)
  → 야간/주간 서열 임시저장 → 최종 저장(MES 전송) → SmartMES 검증 자동 수행.
grade: B
---

# ERP D0추가생산지시 자동화 (SP3M3 / SD9A01)

## 개요

SP3M3 생산지시서 xlsm 단일 파일에서 라인별 계획을 추출해 ERP D0추가생산지시 화면에 업로드하고 서열 반영 + MES 전송까지 수행한다.

## 운영 세션 (하루 2회)

파일명 = OUTER 생산일 = D+1. SP3M3 야간은 시작일(오늘) 기준.

| 세션 | 실행 시점 | 파일명 날짜 | 처리 내용 | ERP 생산일 |
|------|---------|-----------|---------|-----------|
| 저녁 | 17~19시 (확정계획 확인 후) | 내일 | ① SP3M3 야간 (출력용 야간 섹션) | **오늘** (야간 시작일) |
|  |  |  | ② SD9A01 OUTER D+1 (OUTER 시트 SD9M01 블록) | **내일** (파일명 날짜) |
| 아침 | 07:10경 (계획 확정 후) | 오늘 (어제 저녁 저장) | ③ SP3M3 주간 (출력용 주간 섹션, 누적 ≥ 3600 컷) | **오늘** (파일명 날짜) |

## 사전 준비

- Chrome 디버깅 세션: `--remote-debugging-port=9223`, 프로필 `C:\Users\User\.flow-chrome-debug`
- ERP 로그인: 프로필에 저장된 자격증명(`0109`) 자동완성 (pyautogui)
- Python 의존성: `pyautogui`, `playwright`, `openpyxl`, **`pywin32`** (Excel COM, 업로드 xlsx 생성용 필수)
- Microsoft Excel 설치 필요 (업로드 xlsx 생성에 Excel.Application COM 호출)
- Z 드라이브 마운트: `\\210.216.217.180\zz-group`

## 파일 경로 규칙

```
Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서\{YYYY}년 생산지시\{MM}월\SP3M3_생산지시서_({YY.MM.DD}).xlsm
```

- 저장 시점 **전일 오후** → 파일명 = **D+1 (내일 날짜)**
- "수정본" 접미사 있으면 우선 (mtime 최신 기준)
- 저녁 세션: target_date = tomorrow → 파일명 날짜 = tomorrow
- 아침 세션: target_date = today → 파일명 날짜 = today (어제 저녁 생성)
- 파일 내 헤더 `◀ D+1` = 파일명 날짜, `◀ D+2` = 파일명 날짜+1

## 라인 설정

| 라인 | ERP 코드 | LINE_DIV_CD | 시트 | 라인 필터 | 품번 컬럼 | 수량 컬럼 | 저장 URL |
|------|---------|------------|------|----------|---------|---------|---------|
| MAIN | SP3M3 | 02 | `출력용` | R1 `◀ D+1 야간계획`, R35 `◀ D+2 주간계획` | I (신MES 품번, 정제) | K (지시) | `/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do` |
| OUTER | SD9A01 | 01 | `OUTER 생산계획` | B열 `== 'SD9M01'` (D+1 블록) | D (품번 그대로, 접미사 포함) | E (수량) | `/prdtPlanMng/multiListOuterPrdtPlanRankDecideMng.do` |

## 사용법

```bash
# dry-run (추출 + 업로드 시뮬레이션, 서버 저장 안 함)
python run.py --session evening --dry-run

# 저녁 세션 (SP3M3 야간 + SD9A01 OUTER)
python run.py --session evening

# 아침 세션 (SP3M3 주간 3600컷)
python run.py --session morning

# 시간대 자동 판정
python run.py --session auto

# 대상 날짜 명시 (파일명 기준)
python run.py --session evening --target-date 2026-04-24

# 라인 제한
python run.py --session evening --line SP3M3     # SP3M3만
python run.py --session evening --line SD9A01    # SD9A01만
```

## 실행 절차

### Phase 0: 환경 준비
1. Z 드라이브 접근 확인
2. Chrome CDP 9223 기동 (이미 있으면 재사용)
3. ERP OAuth 자동 로그인 (pyautogui 저장 자격증명)
4. D0추가생산지시 화면 진입: `http://erp-dev.samsong.com:19100/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do`

### Phase 1: 파일 해석
5. target_date 계산 (session + 현재시각 기반)
6. SP3M3 생산지시서 xlsm 탐색 (수정본 우선)
7. 세션별 시트 추출:
   - 저녁: 출력용 야간 섹션 + OUTER 시트 SD9M01 D+1 블록
   - 아침: 출력용 주간 섹션 (누적 ≥ 3600 도달 행까지 컷)

### Phase 2: 업로드 파일 생성
8. 라인별 임시 엑셀 생성 (생산일 | 제품번호 | 생산량)
   - SP3M3: target_date
   - SD9A01: target_date (저녁 세션), target_date+1 (아침 세션 해당 없음)
9. 저장 경로: `06_생산관리/D0_업로드/d0_{line}_{date}.xlsx`
10. **⚠ 엑셀 생성은 반드시 `win32com.client`(Excel COM)으로 수행** (2026-04-24 세션104 실증)
    - `openpyxl`로 새로 생성하거나 `load_workbook → save` 한 파일은 ERP 서버 파서가
      **COL2(제품번호)를 빈값으로 파싱** (OOXML 내부 구조 호환 안 됨)
    - Excel이 직접 저장한 xlsx만 서버 파서 통과
    - 흐름: `shutil.copy(template, out)` → `Excel.Application` 열기 → R2~last
      `ClearContents` → 새 데이터 R2부터 작성 → `wb.Save()` → `Excel.Quit()`
    - 템플릿 경로: `90_공통기준/스킬/d0-production-plan/template/SSKR_D0_template.xlsx`
      (ERP `/js/workspace/pm/prdtPlanMng/SSKR D+0 추가생산 Upload.xlsx` 양식 다운로드본)

### Phase 3: D0 업로드 (라인별)
10. 엑셀업로드 팝업 오픈 (#btnExcelUpload)
11. `jQuery.ajax` POST `/prdtPlanMng/selectListPmD0AddnUpload.do` (multipart, form `uploadfrm`, 파일 필드 `files`)
12. 응답 data.list로 팝업 그리드 채우기 (excelUploadCallBack)
13. 오류 행 검증 (ERROR_FLAG 확인)
14. `POST /prdtPlanMng/multiListPmD0AddnUpload.do` JSON `{excelList, ADDN_PRDT_REASON_CD:"002"}` → DB 저장
15. 상단 그리드 자동 반영 확인

### Phase 4: 야간 서열 배치 (저녁 세션만)
16. 엑셀 순서대로 상단 행 idx 매핑 (동일 품번 여러 건이면 REG_NO 최대값)

16.5. **야간 1~5행 dedupe** (2026-04-29 사용자 요청 — 주간과 2중 등록 방지)
   - 적용 대상: SP3M3 야간만 (OUTER 영향 없음)
   - 검사 범위: 야간 추출 결과의 **첫 5행** (서열 1~5번)
   - 매칭 기준 (v3.2 정정): 같은 `REG_DT`(=오늘) ERP 기등록 행과 **PROD_NO 일치만** (수량 무관)
     - v3.1까지는 PROD_NO+수량 동시 매칭이었으나, 같은 품번이면 수량 다르더라도 작업자 입장에서 중복 작업 위험 동일 → 품번만으로 단순화 (사용자 결정 2026-04-29)
   - 처리: 매칭된 행은 야간 등록에서 **제외** (skip=True). 나머지 행은 정상 등록
   - 데이터 소스: ERP D0 상단 그리드 GET (이미 Phase 0/3에서 로드됨) — 주간 D0 등록분이 REG_DT=오늘으로 이미 들어가 있는 상태
   - 로그: 제외된 행은 `[dedupe] 야간 N행 PROD_NO=<X> 야간qty=<a> 주간qty=<b> → 품번 일치, 제외` 1줄씩 (수량은 참고용 표시만)
   - 6행 이후는 검사 안 함 (실무 기준 — 주간 종료 시점과 야간 시작 서열이 겹치는 1~5행만 위험)

17. 각 품번 (16.5에서 skip 안 된 행만):
    - rowClick 로직 재현 (totSelectRowData 세팅 + mGridList.searchListData)
    - 좌하단 로드 대기 → 해당 라인 코드 선택 (SP3M3 또는 SD9A01)
    - sGridList.searchListData → 우하단 로드 대기
    - addRow 직접 호출 (내장 중복 체크 우회, 주간/야간 중복 허용 — 단 16.5 dedupe 통과한 행 한정)
    - multiList API 임시저장 (sendMesFlag=N)
18. 라인별 저장 URL 분기

### Phase 5: 최종 저장 + MES 전송
19. 라인별 sendMesFlag=Y로 multiList POST
20. 응답 statusCode=200 + mesMsg statusCode=200 확인

### Phase 6: 검증
21. SmartMES API 조회: `POST http://lmes-dev.samsong.com:19220/v2/prdt/schdl/list.api`
    - body: `{lineCd, prdtDa}` (lineCd="SP3M3" 또는 "SD9A01")
22. rank 순서와 엑셀 순서 대조

## 핵심 주의사항

⛔ **사용자 첨부 파일 가드** (세션115 사고 실증, 2026-04-27)
   - 사용자가 메시지에 xlsx/xlsm을 첨부했는데 스킬이 그걸 무시하고 Z 드라이브 원본 자동 추출 → ERP+MES에 중복 등록 사고
   - MES는 ERP에서 삭제해도 잔존 (이전 증명) → 정정 매우 어려움
   - **규칙**: 첨부 발견 시 자동 실행 금지. 사용자에게 (A) 첨부 사용(`--xlsx <path>`) (B) Z드라이브 자동 탐색 중 명시 선택 받은 후 진행

0. **⚠ 업로드 xlsx는 Excel COM으로만 생성** (세션104 실증, 2026-04-24)
   - openpyxl 생성 파일 → ERP 서버 파서가 COL2="" 반환, 15건 전부 ERROR_FLAG="Y"
   - 증상: `[phase3 parse]` 응답의 listLen은 정상이지만 각 행 COL2 빈값 → multiList 저장 단계에서 `오류 행 N건 존재` 에러
   - 원인: OOXML 내부 구조(sharedStrings.xml, cell type 속성, 시트 XML 네임스페이스) 차이
   - **근본 해결**: `win32com.client.Dispatch("Excel.Application")`로 편집·저장
   - 템플릿 `template/SSKR_D0_template.xlsx` 복사 후 Excel COM으로 데이터 덮어쓰기
1. **jQuery.ajax 경로 필수** — fetch 직접 호출 시 500 에러 (XSRF 공통 설정 미상속)
2. **파일 필드명 `files` (복수형)** — `fileHelper.js` allSave 규칙
3. **EXT_PLAN_REG_NO 최대값 매핑** — 동일 품번 상단에 여러 건 (기존 주간 + 신규 야간) 시 최대값 선택
4. **주간/야간 중복 품번** — 서버가 서로 다른 EXT_PLAN_REG_NO로 P + A 공존 허용. 반드시 신규 REG_NO 사용
5. **s_grid 폴링 필수** — 기존 P/R 행 로드 완료 후 addRow (미완 상태에서 addRow하면 payload에 기존 행 유실)
6. **OUTER 품번 접미사 포함** — G열 "품번정제" 사용 금지, D열 그대로 사용
7. **OUTER 시트 7개 라인 혼재** — B열 정확 매칭 `== 'SD9M01'` (헤더 `◀ SD9M01 D+1` 등 제외)
8. **주간 3600 컷 규칙** — 누적 ≥ 3600 되는 첫 행까지 포함 (초과 1건 포함)
9. **중복 실행 방지** — 같은 날짜 이미 저장된 건 스킵 (EXT_PLAN_REG_NO 기준)
10. **야간 1~5행 주간 중복 dedupe** (2026-04-29 사용자 요청, v3.2 정정) — Phase 4 step 16.5 참조. 야간 첫 5행 **PROD_NO만** 같은 REG_DT(=오늘) 주간 등록분과 매칭 시 제외 (수량 무관). 이전엔 "주간/야간 중복 허용"이었으나 1~5행만 예외 처리

## 실패 조건

- Chrome CDP 9223 미응답
- ERP OAuth 실패 (저장 자격증명 미사용 시 pyautogui 자동완성 불가)
- Z 드라이브 미접근
- 생산지시서 xlsm 파일 미존재
- 출력용 시트 헤더 `◀ D+1 야간계획` / `◀ D+2 주간계획` 미발견
- OUTER 시트 B열 `SD9M01` 행 0건
- selectList 서버 500 에러
- multiList 서버 에러
- MES 전송 statusCode != 200

## 중단 기준

- 상단 그리드 등록 0건 (파싱 실패)
- 서열 배치 중 임시저장 실패 (첫 실패 즉시 중단)
- 최종 저장 실패

## 검증 항목

- 라인별 엑셀 건수 = ERP 상단 그리드 저장 건수
- 야간 서열 A 행 수 = 엑셀 건수 (주간 중복 품번도 신규 REG_NO로 추가 확인)
- SmartMES rank 순서 = 엑셀 순서
- MES 응답 rsltCnt > 0

## Phase 7 — 사후 검증 + 자동 재실행 (verify_run.py, debate_20260429_121732_3way 합의)

> **목적**: D0_SP3M3_Morning(07:05) / Night Windows 작업 스케줄러 실행 후 결과 자동 검증 (verify는 07:15, morning 10분 후).
> 실패 감지 시 원인 분류 → RETRY_OK 백오프 / RETRY_BLOCK·RETRY_NO 즉시 알림.

### 호출 (사용자 작업 스케줄러 등록 후 자동)
```
python verify_run.py --session morning --line SP3M3
python verify_run.py --session night --line SP3M3
python verify_run.py --session morning --line SP3M3 --dry-run    # 점검만
```

### 원인 분류
- **RETRY_OK**: timeout / 5xx / 네트워크 / Chrome CDP 미기동 / OAuth 정착 — Phase 0/1/2(로그인·xlsx 로드·dedupe) 한정
- **RETRY_BLOCK**: timeout이 Phase 3+(업로드·rank_batch·mesMsg)에 발생, 또는 dedupe 결과 N건 정리 시 (이미 등록 의심)
- **RETRY_NO**: xlsx 미존재 / 권한 / 마스터 정보 불일치 — 즉시 알림 + 재시도 0회
- **UNKNOWN**: 분류 실패 — 1회 재시도 후 알림

### 백오프 정책 (RETRY_OK)
- **1분 / 5분 / 15분 / 30분** — 누적 51분 한계
- 매 시도 전 dedupe 선행 (`erp_d0_dedupe.py --execute`) — N건 정리 시 RETRY_BLOCK 트리거
- schtasks 상태 확인 — Running 시 5분 대기 후 Phase 분석:
  - Phase 0/1/2 → `schtasks /end` 강제 종료 OK
  - Phase 3+ → 종료 금지 + 알림 즉시 종결

### 안전장치 (R5)
- **lock 파일** atomic — `os.O_EXCL` + JSON `{pid, started, session}` + 60분 stale 정리
- **누적 시간 한계**: 51분 도달 시 자동 재시도 종료
- **dedupe 선행**: 매 시도 — 기존 등록 의심 시 RETRY_BLOCK
- **Phase 3+ 강제 종료 금지**: ERP 트랜잭션 단절 방지
- **롤백 도구**: `erp_d0_dedupe.py --execute` 즉시 실행 가능

### 알림 (현재 stub — Slack MCP 통합은 Phase 2 이월)
- **현재**: `.claude/state/d0_verify_notify.jsonl`에 알림 레코드만 기록 (jsonl append)
- **DOM/스크린샷 저장**: 미구현 — Phase 2 이월 (chrome-devtools-mcp CDP 9222 의존)
- **Phase 2 통합 예정**: Slack `mcp__8d2abc6d-...__slack_send_message` + DOM snapshot + 스크린샷 첨부

### 알림 정책
- 성공: 무알림
- 재시도 후 성공: 1건 알림 (재시도 N회, 누적 M초)
- RETRY_BLOCK / RETRY_NO / UNKNOWN 실패: 즉시 + 로그 끝 30줄
- 누적 한계 도달: 즉시 + 로그 끝 30줄

### Windows 작업 스케줄러 등록 (사용자 수동, admin 권한 필요할 수 있음)
```
schtasks /create /TN "D0_SP3M3_Morning_Recover" /TR "C:\Users\User\Desktop\업무리스트\90_공통기준\스킬\d0-production-plan\run_morning_recover.bat" /SC DAILY /ST 07:15 /RU <USER>
```

> **기존 `run_morning_verify.bat`(Phase 3까지 parse-only 사전 점검)와 별개**.
> 본 verify_run.py는 morning 종료 후 사후 검증·재실행이며 wrapper는 `run_morning_recover.bat`.

## 되돌리기 방법

- **서열 행 삭제 API** (야간 A 행): `DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do` payload `{EXT_PLAN_REG_NO, STD_DA, PLAN_DA, PROD_NO, LINE_CD}`
  - `.claude/tmp/erp_d0_deleteA.py --all` 로 A 행 일괄 삭제 후 재업로드 가능
- **D0 등록 삭제 API** (상단 그리드 1건, 세션110 발견 — UI 미노출): `DELETE /prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do` payload `{REG_NO: <번호>}`
  - 호출처: `totGridList.deleteRow(rowData)` (코드에는 있으나 UI 버튼 미노출)
  - 식별: SmartMES `sewmacLabelScanQty` 필드 = ERP `REG_NO` 매핑 (필드명 misleading)
  - **중복 등록 자동 정리 도구**: `.claude/tmp/erp_d0_dedupe.py --line SP3M3 --date YYYYMMDD [--execute]`
    - SmartMES rank 작은 쪽(위) 보존 / rank 큰 쪽(아래) 삭제 자동 식별
    - 기본 dry-run, `--execute`로 실 DELETE
    - 세션110 실증: 7건 중복 1분 내 깨끗하게 정리 완료 (2026-04-27)

## 변경 이력

| 일자 | 버전 | 내용 |
|------|------|------|
| 2026-04-23 | v1 | 초기 스킬 패키징. 오늘 SP3M3 야간 실검증 완료. OUTER/주간은 구조 완비하되 실운영 검증 후 활성화 권장 |
| 2026-04-24 | v2 | SP3M3 주간/야간 실운영 검증 완료. 버그 수정: (a) make_upload_xlsx openpyxl→win32com(Excel COM) 교체 — openpyxl 생성 xlsx는 ERP 파서가 COL2 빈값 인식, (b) 팝업 재사용 로직 우선 배치(reload 분기보다 먼저), (c) run_session_line에 verify_prod_date 파라미터 추가 — SmartMES 검증 시 야간 생산일(target_file_date-1) 전달. Windows 작업 스케줄러 `D0_SP3M3_Morning` 자동 운영 개시 |
| 2026-04-27 | v3 | 세션110: (1) 숨겨진 D0 등록 삭제 API 발견 (`deleteDoAddnPrdtPlanInstrMngNew.do`, payload `{REG_NO}`), (2) SmartMES `sewmacLabelScanQty` ↔ ERP `REG_NO` 매핑 식별, (3) 신규 도구 `.claude/tmp/erp_d0_dedupe.py` (SmartMES rank 기준 자동 중복 식별 + 안전 삭제 dry-run/execute 모드), (4) 7건 중복 1분 내 깨끗 정리 실증. **morning batch는 OAuth 자동완성 잔존 위험 — 수동 등록 후 batch 자동 재실행 시 중복 발생 시나리오 주의** |
| 2026-04-29 | v3.1 | **야간 1~5행 주간 중복 dedupe 추가** (사용자 요청). Phase 4 step 16.5 신설 — SP3M3 야간 첫 5행 중 같은 REG_DT(=오늘) 주간 등록분과 PROD_NO+수량 일치 시 등록 제외. **run.py 코드 패치 완료**: `dedupe_night_first_5()` 함수 신설 + main() evening+SP3M3 분기에서 `extract_sp3m3_night()` 직후 호출. AST 검증 PASS. 매칭 키: `PRDT_QTY \|\| ADD_PRDT_QTY \|\| PRDT_PLAN_QTY` (3개 후보 OR). 첫 저녁 세션 실행 시 dedupe 로그 검증 필요 |
| 2026-04-29 | v3.2 | **dedupe 매칭 단순화** (사용자 결정) — PROD_NO+수량 → **PROD_NO만**. 같은 품번이면 수량 다르더라도 작업자 중복 작업 위험 동일하므로 수량 무관 제외. run.py + SKILL.md 동시 정정. 로그에는 야간qty/주간qty 둘 다 표시 (참고용) |
