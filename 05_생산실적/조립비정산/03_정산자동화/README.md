# 조립비 정산 파이프라인 — 운영 패키지

> 기준: 2026-03-24 실행 결과 (02월 정산)
> 경로: `C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\03_정산자동화\`
> Python: `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`

---

## 1. 실행 명령어

> **PYTHONUTF8=1 필수.** bash(Git Bash) 환경에서 실행 권장.

### 전체 실행 (기본)
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --month MM
```
예) 03월 정산:
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --month 03
```

### 특정 Step부터 재시작
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --start-from N --month MM
```
예) Step 5부터 재시작 (앞 단계 캐시 활용):
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --start-from 5 --use-cache --month 03
```

### 캐시 활용 실행 (이미 처리된 Step 건너뜀)
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --use-cache --month MM
```

### 옵션 요약

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--month MM` | 대상 월 (두 자리) | config 기본값 (MONTH 변수) |
| `--start-from N` | Step N부터 시작 (1~7) | 1 |
| `--use-cache` | 출력 JSON이 있는 Step은 SKIP | False |

---

## 2. 입력 파일

### 위치

```
C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\
  01_기준정보\
    기준정보_라인별정리_최종_V1_20260316.xlsx   ← MASTER_FILE
  04_실적데이터\
    GERP_실적현황_20260311.xlsx                ← GERP_FILE
    구ERP_실적현황_20260311.xlsx               ← OLDERP_FILE
```

### 필수 파일 목록

| 파일 | config 변수 | 필수 내용 |
|------|------------|-----------|
| 기준정보_라인별정리_최종_V1_*.xlsx | `MASTER_FILE` | 10개 라인 시트, 품번·단가·Usage 컬럼 |
| GERP_실적현황_*.xlsx | `GERP_FILE` | 23열 이상, 주야구분(정상/추가), 업체코드 0109 행 포함 |
| 구ERP_실적현황_*.xlsx | `OLDERP_FILE` | Sheet1, 14열 이상, LOTNO 끝자리 A/B/C/S |

> 파일명이 바뀌면 `_pipeline_config.py`의 경로 변수를 수정한다.

### Step 1 통과 기준 (02월 참조값)

| 검증 항목 | 참조값 |
|-----------|--------|
| 기준정보 라인 시트 | 10개 |
| GERP 전체 데이터 | 10,870행 |
| GERP 대원테크(0109) | 2,885행 |
| 구ERP 전체 데이터 | 11,433행 |
| 구ERP 대원테크(0109) | 1,116행 |

---

## 3. 출력 파일

### 정산결과 Excel

```
C:\Users\User\Desktop\업무리스트\
  정산결과_MM월.xlsx
```

**시트 구성 (총 13개):**

| 시트 | 내용 |
|------|------|
| 00_정산집계 | 라인별 GERP/구ERP 합계 및 차이 요약 |
| SD9A01 | 아우터 상세 (629행, 02월 기준) |
| SP3M3 | 메인 상세 (1,455행) |
| WAMAS01 | 웨빙 ASSY 상세 (10,318행) |
| WABAS01 | 웨빙 스토퍼 상세 (1,349행) |
| ANAAS04 | 앵커 상세 (614행) |
| DRAAS11 | 디링 상세 (398행) |
| WASAS01 | 웨빙 스토퍼2 상세 (245행) |
| HCAMS02 | 홀더 CLR ASSY 상세 (1,282행) |
| HASMS02 | 홀더센스 ASSY 상세 (40행) |
| ISAMS03 | 이너센스 ASSY 상세 (225행) |
| 01_차이분석 | GERP vs 구ERP 차이 항목 (529건, 02월) |
| 02_미매핑품번 | 기준정보 미매핑 품번 목록 (정상 시 0건) |

### 주요 수치 (02월 기준)

| 항목 | 수치 |
|------|------|
| GERP 정산 합계 | 194,591,630원 |
| 구ERP 정산 합계 | 110,364,430원 |
| GERP vs 구ERP 차이 | +84,227,200원 |

---

## 4. 로그 위치

```
03_정산자동화\
  run_logs\
    YYYY-MM-DD_HHmmSS.log             ← 전체 실행 로그
    YYYY-MM-DD_HHmmSS_summary.json    ← 요약 JSON
  _cache\
    step1_validation.json
    step2_gerp.json
    step3_olderp.json
    step4_matched.json
    step5_settlement.json
    step6_validation.json
```

**summary.json 주요 필드:**

| 필드 | 설명 |
|------|------|
| `pipeline_status` | `"SUCCESS"` 또는 `"FAILED at Step N"` |
| `failed_step` | 실패 Step 번호 (성공 시 `null`) |
| `total_elapsed_sec` | 전체 소요시간 (초) |
| `steps[].status` | 각 Step의 `SUCCESS` / `FAILED` / `SKIPPED` |

---

## 5. 월마감 체크리스트

### ① 입력 파일 준비

- [ ] GERP 실적현황 파일 다운로드 → `04_실적데이터\` 저장
- [ ] 구ERP 실적현황 파일 다운로드 → `04_실적데이터\` 저장
- [ ] 신규 품번 발생 시 기준정보 파일에 단가 등록
- [ ] `_pipeline_config.py` 파일 경로 변수 확인 (GERP_FILE, OLDERP_FILE, MASTER_FILE)
- [ ] `_cache/` 삭제 (새 월 정산 시작 시)

### ② 파이프라인 실행

```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --month MM
```

- [ ] 전체 7 Step SUCCESS 확인
- [ ] `run_logs/` 최신 `_summary.json`에서 `"pipeline_status": "SUCCESS"` 확인
- [ ] 실패 시 RUNBOOK.md 참조하여 조치 후 재실행

### ③ Step 6 검증 확인

- [ ] `_cache/step6_validation.json` 열어 `"overall": "PASS"` 확인
- [ ] `fail` 항목 = 0 확인
- [ ] INFO 항목 내용 확인 (차단 아님, 이상 여부만 확인)
  - WABAS01 단가=0 품번 현황
  - GERP vs 구ERP 라인별 차이 내역

### ④ 보고서 확인

- [ ] `정산결과_MM월.xlsx` 열기
- [ ] `00_정산집계` 시트 합계 확인
- [ ] `02_미매핑품번` 시트 행 수 = 0 확인
- [ ] 시트 총 13개 확인

### ⑤ DB 업데이트

- [ ] 정산 합계 금액 DB 입력 (GERP 기준)
- [ ] 구ERP 참조값 기록

### ⑥ 파일 아카이브

- [ ] `정산결과_MM월.xlsx` → 지정 아카이브 폴더 이동/복사
- [ ] `run_logs/` 해당 월 로그 백업
- [ ] `_cache/` 정리 (다음 월 정산 전 삭제 예정)

---

## 6. 관련 문서

| 문서 | 용도 |
|------|------|
| `RUNBOOK.md` | 실패 복구 절차, 인코딩 오류, Step별 재시작 기준 |
| `pipeline_contract.md` | Step별 입출력 JSON 스키마 정의 |
| `AGENTS_GUIDE.md` | 도메인 에이전트 판정 기준 및 검수 기준표 |
| `_pipeline_config.py` | 경로, 월, 컬럼 인덱스 등 공통 설정 |
