# 조립비 정산 파이프라인 — 실패 복구 절차서 (RUNBOOK)

> 기준: 2026-03-24 실행 결과 (02월 정산)
> 경로: `C:\Users\User\Desktop\업무리스트\05_생산실적\조립비정산\03_정산자동화\`

---

## 1. Step별 실패 원인 및 증상

| Step | 스크립트 | 주요 실패 원인 | 증상 |
|------|----------|----------------|------|
| 1 | step1_파일검증.py | 입력 파일 경로 불일치, 파일 없음, 시트 구조 변경 | `[FAIL]` 메시지 + `exit=1` |
| 2 | step2_gerp처리.py | GERP 파일 컬럼 위치 변경, 대원테크(0109) 데이터 없음 | `unmatched_lines` 비어 있지 않음 |
| 3 | step3_구erp처리.py | 구ERP Sheet1 없음, 컬럼수 13개 미만 | 라인 매핑 실패 |
| 4 | step4_기준정보매칭.py | 기준정보에 없는 신규 품번, MASTER_FILE 경로 오류 | 미매핑 품번 발생 |
| 5 | step5_정산계산.py | step4 캐시 손상, Usage=2 품번 수량 홀수 | 계산 오류 |
| 6 | step6_검증.py | FAIL 항목 발생 (PASS 조건 미충족) | `최종 판정: FAIL` |
| 7 | step7_보고서.py | OUTPUT_FILE 경로 잠김 (Excel 열려 있음), openpyxl 오류 | 파일 저장 실패 |

---

## 2. 로그 확인 위치

```
03_정산자동화\
  run_logs\
    YYYY-MM-DD_HHmmSS.log          ← 전체 실행 로그 (Step별 출력 포함)
    YYYY-MM-DD_HHmmSS_summary.json ← 요약 JSON (Step별 상태, 소요시간, 실패 Step)
  _cache\
    step1_validation.json
    step2_gerp.json
    step3_olderp.json
    step4_matched.json
    step5_settlement.json
    step6_validation.json
```

**실패 Step 빠른 확인:**
```bash
# 최신 요약 JSON에서 failed_step 확인
cat run_logs/$(ls run_logs/*_summary.json | tail -1) | python -c "import sys,json; d=json.load(sys.stdin); print('failed_step:', d['failed_step'])"
```

또는 run_logs/ 폴더에서 최신 `_summary.json`을 텍스트 편집기로 열어 `"failed_step"` 값을 확인한다.

---

## 3. --start-from N 재시작 기준

실패한 Step에서 원인을 해결한 뒤, **해당 Step부터** 재시작한다.
캐시가 유효한 앞 Step은 `--use-cache`로 건너뛸 수 있다.

| 실패 Step | 원인 해결 후 재시작 명령 |
|-----------|--------------------------|
| Step 1 | `--start-from 1` (입력 파일 경로·구조 수정 후) |
| Step 2 | `--start-from 2` |
| Step 3 | `--start-from 3` |
| Step 4 | `--start-from 4` (기준정보 업데이트 후) |
| Step 5 | `--start-from 5 --use-cache` |
| Step 6 | `--start-from 6 --use-cache` (step5 캐시 유효 시) |
| Step 7 | `--start-from 7 --use-cache` (Excel 닫은 후) |

**원칙:**
- Step 1~4는 입력 데이터 또는 기준정보가 변경되면 **해당 Step부터 전부 재실행** 필요
- Step 5~7은 계산·검증·보고서 단계이므로 캐시 재사용 가능

---

## 4. --use-cache 사용 기준

### 캐시 재사용 가능 조건

```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --start-from N --use-cache --month MM
```

| 조건 | 설명 |
|------|------|
| 앞 Step의 `_cache/*.json`이 이미 존재 | 해당 Step은 자동 SKIP |
| 입력 파일(GERP, 구ERP, 기준정보)이 변경되지 않음 | 데이터 재처리 불필요 |
| Step N-1까지 모두 SUCCESS 상태 | summary.json에서 확인 |

### 캐시 삭제 후 전체 재실행해야 하는 경우

- 입력 파일(GERP_실적현황.xlsx, 구ERP_실적현황.xlsx, 기준정보.xlsx)이 교체된 경우
- `_pipeline_config.py`의 MONTH, 컬럼 인덱스, 단가 등이 변경된 경우
- 캐시 파일이 중간에 손상된 것으로 의심될 경우
- 월이 바뀌어 새 월 정산을 처음 실행하는 경우

```bash
# 캐시 전체 삭제 후 재실행
rm -rf _cache/
PYTHONUTF8=1 python run_settlement_pipeline.py --month MM
```

---

## 5. _cache/ 삭제 기준

| 상황 | 조치 |
|------|------|
| 새 월 정산 시작 | 삭제 권장 (오염 방지) |
| 입력 파일 교체 | 삭제 필수 |
| Step 실패 후 원인 불명확 | 삭제 후 전체 재실행 |
| 동일 월 파라미터 재실행 | 삭제 불필요 (`--use-cache` 활용) |
| 디스크 정리 | 정산 완료 후 아카이브 또는 삭제 |

**주의:** `_cache/` 삭제 시 모든 Step이 재실행된다 (전체 약 25초).

---

## 6. Windows 인코딩 문제 조치 (PYTHONUTF8=1)

### 증상 (02월 실행에서 실제 발생)

```
UnicodeEncodeError: 'cp949' codec can't encode character ...
```

또는 콘솔 출력에서 한글이 깨지는 현상.

### 원인

Windows cmd/PowerShell의 기본 인코딩이 `cp949`이고, 파이프라인 스크립트가 UTF-8로 작성되어 있어 `subprocess` 출력 시 충돌 발생.

### 해결법

**bash (Git Bash, WSL) 환경에서 실행 — 권장:**
```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --month MM
```

**Windows cmd 환경:**
```cmd
set PYTHONUTF8=1
python run_settlement_pipeline.py --month MM
```

**Windows PowerShell 환경:**
```powershell
$env:PYTHONUTF8 = "1"
python run_settlement_pipeline.py --month MM
```

> `run_settlement_pipeline.py`는 내부적으로 `env['PYTHONUTF8'] = '1'`을 자동 설정하여
> 각 Step 스크립트를 호출한다. 실행기 자체에도 환경변수를 적용해야 로그 출력이 정상.

### config 복원 실패 시 (비정상 종료 후)

`--month` 옵션 사용 중 강제 종료된 경우 백업 파일이 남아 있을 수 있다:

```
_pipeline_config.py.pipeline_bak  ← 원본 백업
```

수동 복원:
```bash
cp _pipeline_config.py.pipeline_bak _pipeline_config.py
rm _pipeline_config.py.pipeline_bak
```

---

## 7. 자주 발생하는 에러와 해결법

### 7-1. UnicodeEncodeError (cp949)

```
UnicodeEncodeError: 'cp949' codec can't encode character '\u2026' in position ...
```

**원인:** `PYTHONUTF8=1` 미적용 상태에서 cmd 실행
**해결:** bash 환경에서 `PYTHONUTF8=1` 접두 후 실행 (§6 참조)

---

### 7-2. Step 1 FAIL — 파일 없음

```
[FAIL] GERP 파일 없음 — C:\...\GERP_실적현황_20260311.xlsx
```

**원인:** `_pipeline_config.py`의 GERP_FILE / OLDERP_FILE / MASTER_FILE 경로가 실제 파일과 다름
**해결:**
1. `_pipeline_config.py` 열기
2. `GERP_FILE`, `OLDERP_FILE`, `MASTER_FILE` 경로를 실제 파일명으로 수정
3. `--start-from 1` 재실행

---

### 7-3. Step 4 미매핑 품번 발생

```
미매핑: 12개
```

**원인:** 신규 품번이 기준정보 파일에 등록되어 있지 않음
**해결:**
1. `_cache/step4_matched.json`에서 `unmatched` 배열 확인
2. 기준정보 파일(`01_기준정보/*.xlsx`)에 해당 품번 단가 등록
3. `_pipeline_config.py`의 MASTER_FILE 경로 확인
4. `--start-from 4 --use-cache` 재실행

---

### 7-4. Step 6 FAIL 판정

```
최종 판정: FAIL
```

**원인:** 합계 불일치, 비즈니스 규칙 위반 등
**해결:**
1. `_cache/step6_validation.json` 열어 `[FAIL]` 항목 확인
2. 항목별 원인 분석:
   - **전체합계 불일치** → Step 5 재실행 (`--start-from 5 --use-cache`)
   - **Usage=2 홀수 수량** → 기준정보 Usage 컬럼 확인
   - **SP3M3 야간단가 오류** → `_pipeline_config.py`의 `SP3M3_NIGHT_PRICE` 확인 (기본: 170)

> **INFO 항목은 FAIL이 아님** — 확인 권장이지만 파이프라인을 중단하지 않는다.
> (예: WABAS01 단가=0 품번 56건, GERP vs 구ERP 라인별 차이)

---

### 7-5. Step 7 파일 저장 실패

```
PermissionError: [Errno 13] Permission denied: '...정산결과_02월.xlsx'
```

**원인:** 출력 파일이 Excel에서 열려 있음
**해결:** Excel에서 `정산결과_MM월.xlsx` 닫은 후 `--start-from 7 --use-cache` 재실행

---

### 7-6. config 월 미변경 상태에서 다른 월 실행

**증상:** 로그에 `--month: (config 기본값)` 표시, 이전 월 파일이 덮어씌워짐
**해결:** 반드시 `--month MM` 옵션을 명시한다:

```bash
PYTHONUTF8=1 python run_settlement_pipeline.py --month 03
```

---

## 부록: Step별 소요시간 참조 (02월 기준)

| Step | 소요시간 |
|------|---------|
| Step 1 (파일검증) | 5.1s |
| Step 2 (GERP처리) | 2.3s |
| Step 3 (구ERP처리) | 1.9s |
| Step 4 (기준정보매칭) | 7.0s |
| Step 5 (정산계산) | 0.5s |
| Step 6 (검증) | 0.2s |
| Step 7 (보고서) | 7.9s |
| **전체** | **24.8s** |
