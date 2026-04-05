# /settlement — 월말 조립비 정산

> 정산 대상 월을 입력하면 환경 세팅 → 파이프라인 실행 → 오류 리스트 → 검증 보고를 자동 수행한다.

## 사용법
```
/settlement 03        # 3월 정산 실행
/settlement 04        # 4월 정산 실행
/settlement 03 --from 5  # 3월 정산, step5부터 재실행
```

## 인수
- `$ARGUMENTS` — 첫 번째: 정산 대상 월 (01~12), 두 번째(선택): --from N (재시작 step)

## 실행 순서

### Phase 1: 환경 세팅
1. 도메인 CLAUDE.md 읽기 (`05_생산실적/조립비정산/CLAUDE.md`)
2. `setup_month.py {월}` 실행
   - 월별 폴더 생성 (XX월/실적데이터/, _cache/)
   - 04_실적데이터/에서 해당 월 GERP/구ERP 파일 탐색 → 복사
   - _pipeline_config.py 자동 수정 (경로, MONTH, OLDERP_SHEET)
3. 파일 존재 검증 — 실패 시 중단하고 사용자에게 보고

### Phase 2: 파이프라인 실행
4. `run_settlement_pipeline.py` 실행 (step 1~8 순차)
   - --from 인수가 있으면 `--start-from N --use-cache` 적용
   - step 1: 파일 검증
   - step 2: GERP 처리 (0109 필터, RSP 역변환)
   - step 3: 구ERP 처리 (전체업체 피벗, 지원분)
   - step 4: 기준정보 매칭
   - step 5: 정산 계산 (야간 ×1.3 통일)
   - step 6: 합계 검증
   - step 7: 보고서 생성 (정산결과_MM월.xlsx)
   - step 8: 오류 리스트 (오류리스트_MM월.xlsx)
5. 실패 step 있으면 로그 확인 후 원인 보고

### Phase 3: 결과 검증 + 보고
6. step6 검증 결과 파싱 (PASS/WARNING/FAIL 항목)
7. 라인별 정산 금액 요약표 출력:
   ```
   | 라인 | GERP 합계 | 구ERP 합계 | 차이 | 오류 건수 |
   ```
8. 오류 리스트 요약 (유형별 건수 + 금액)
9. 산출물 목록:
   - 정산결과_MM월.xlsx (13개 시트)
   - 오류리스트_MM월.xlsx (오류리스트 + 유형별요약)

### Phase 4: 상태 갱신 (선택)
10. 사용자 확인 후 STATUS.md 업데이트

## 파이프라인 경로
- 진입점: `05_생산실적/조립비정산/03_정산자동화/run_settlement_pipeline.py`
- 설정: `05_생산실적/조립비정산/03_정산자동화/_pipeline_config.py`
- 세팅: `05_생산실적/조립비정산/03_정산자동화/setup_month.py`

## 전제 조건
- 04_실적데이터/에 해당 월 GERP/구ERP 파일이 존재해야 함
- 기준정보 파일: 01_기준정보/기준정보_라인별정리_최종_V1_20260316.xlsx
- Python 3.12 + pandas + openpyxl 설치

## 주의사항
- 기준정보 파일은 수동 갱신 (단가 변경 시 사용자 확인 필수)
- 구ERP 시트명은 파일마다 다를 수 있음 (setup_month이 추정하지만 확인 필요)
- 파이프라인 실패 시 RUNBOOK.md 참조
