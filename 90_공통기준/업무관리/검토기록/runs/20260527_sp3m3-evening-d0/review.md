# SP3M3 야간계획 D0 반영

## 결과
- PASS: `d0-production-plan` 단일 진입으로 SP3M3 야간계획을 반영했다.
- SD9A01 OUTER 보류 잠금 활성 확인, SP3M3만 처리했다.
- Phase 3 ERP D0 업로드, Phase 4 서열, Phase 5 MES 전송, Phase 6 SmartMES 대조까지 완료했다.

## 실행
- 사전검증: `python 90_공통기준/스킬/d0-production-plan/run.py --session evening --line SP3M3 --http-only --parse-only`
- 본실행: `python 90_공통기준/스킬/d0-production-plan/run.py --session evening --line SP3M3 --http-only`
- 후속검증: `python 90_공통기준/스킬/d0-production-plan/verify_run.py --session evening --line SP3M3`
- 호환 재시도: `python 90_공통기준/스킬/d0-production-plan/verify_run.py --session night --line SP3M3`

## Phase 결과
| Phase | 결과 |
|---|---|
| Phase 0 | HTTP OAuth PASS |
| Phase 1 | `SP3M3_생산지시서_(26.05.28).xlsm` 선택 |
| Phase 1 원본 | 36건 |
| 한글 PROD_NO skip | `구형바코드사용` 6건 제외 |
| Phase 1.5 dedupe | 30건 중 3건 제외 |
| 최종 등록 대상 | 27건 |
| Phase 2 | `06_생산관리/D0_업로드/d0_SP3M3_20260527.xlsx` 생성, 27행 |
| Phase 3 | HTTP 업로드 status=200, statusCode=200, 27건 저장 |
| Phase 4 | 서열 27건 등록, failed=0, missing=0 |
| Phase 5 | final_save status=200, MES `statusCode=200`, `rsltCnt=1350` |
| Phase 6 | SmartMES 서열 순서 엑셀 일치 PASS, 27건 |

## 등록 대상
| 구분 | 값 |
|---|---|
| 파일명 날짜 | 2026-05-28 |
| 생산일 | 2026-05-27 |
| 라인 | SP3M3 |
| 세션 | evening |
| 최종 ext 범위 | 334260~334286 |
| 최종 rank 범위 | 20~46 |

## 주요 로그
- `RSP3PC0144 ext=334260 -> OK (rank=20)`
- `RSP3SC0410 ext=334286 -> OK (rank=46)`
- `[SP3M3:http] api_rank_batch: {'done': 27, 'failed': 0, 'missing': 0, ...}`
- `[phase5:http final_save] status=200 statusCode=200 mesMsg={"statusMsg":"성공하였습니다.lmes","rslt":{"rsltCnt":1350},"statusCode":200}`
- `[phase6] SP3M3 서열 순서 엑셀 일치 ✅ (27건, 카운트·중복·순서 모두 일치)`

## 보정 사항
- Excel COM pywin32 캐시 손상으로 1차 parse-only가 중단되어 `Temp/gen_py/3.12`의 Excel typelib 캐시만 삭제 후 재생성했다.
- `--http-only --parse-only` 분기가 브라우저용 `page`를 호출하는 버그를 수정했다.
- 야간 추출 경로에도 한글 PROD_NO skip을 적용했다.

## verify_run 결과
- `--session evening`은 현재 verify_run 인자에서 미지원이라 argparse 실패.
- `--session night --line SP3M3`는 실행됐으나 스케줄러 로그 기반 검증 구조라 수동 실행 로그를 찾지 못해 `RETRY_NO / log_missing`으로 종료.
- 본 실행의 Phase 6 SmartMES 직접 대조는 PASS다.
