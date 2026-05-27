# SP3M3 화인텍 5월 지원수량 추출 실행 기록

## 결론
- 결과: FAIL
- run.py 작성: 완료
- run.py 실행: 완료
- xlsx 산출물 생성: 실패
- 원인: 현재 Codex 셸에서 UNC 및 Z: 매핑 공유 폴더 모두 `WinError 5 Access is denied`
- 자동회신: FAIL (`Claude window not found; GUI_ACCESS_UNAVAILABLE`). 현재 권한 정책상 `require_escalated` 재시도 불가

## 산출물 경로
- 스크립트: `C:\Users\User\Desktop\업무리스트\99_임시수집\화인텍_5월\run.py`
- 목표 xlsx: `C:\Users\User\Desktop\업무리스트\99_임시수집\화인텍_5월\화인텍_지원수량_05월_20260527.xlsx`

## 실행 stdout 요약
| 항목 | 값 |
|---|---:|
| RESULT | FAIL |
| INPUT_DIR_SELECTED | NONE |
| SOURCE_FILES | 0 |
| ROWS | 0 |
| TOTAL_QTY | 0 |
| CROSSCHECK_EXPECTED_COUNT | 32 |
| CROSSCHECK_PASS | 0 |
| CROSSCHECK_FAIL | 32 |
| OUTPUT_CREATED | false |

## 입력 접근 오류
| 후보 경로 | 결과 |
|---|---|
| `\\210.216.217.180\zz-group\15. SP3 메인 CAPA점검\SP3M3\생산지시서\2026년 생산지시\05월` | `PermissionError: [WinError 5] 액세스가 거부되었습니다` |
| `Z:\15. SP3 메인 CAPA점검\SP3M3\생산지시서\2026년 생산지시\05월` | `PermissionError: [WinError 5] 액세스가 거부되었습니다` |

## Cross-check 불일치 전체
| 날짜 | 서브품번 | 기대 | 실제 |
|---|---:|---:|---|
| 05-14 | 971 | 160 | NO_INPUT |
| 05-14 | 975 | 120 | NO_INPUT |
| 05-14 | 978 | 120 | NO_INPUT |
| 05-19 | 971 | 120 | NO_INPUT |
| 05-19 | 975 | 120 | NO_INPUT |
| 05-19 | 972 | 120 | NO_INPUT |
| 05-19 | 978 | 96 | NO_INPUT |
| 05-20 | 971 | 140 | NO_INPUT |
| 05-20 | 972 | 216 | NO_INPUT |
| 05-20 | 973 | 60 | NO_INPUT |
| 05-20 | 975 | 220 | NO_INPUT |
| 05-20 | 978 | 144 | NO_INPUT |
| 05-21 | 971 | 330 | NO_INPUT |
| 05-21 | 972 | 180 | NO_INPUT |
| 05-21 | 973 | 90 | NO_INPUT |
| 05-21 | 975 | 150 | NO_INPUT |
| 05-21 | 976 | 120 | NO_INPUT |
| 05-21 | 978 | 120 | NO_INPUT |
| 05-22 | 971 | 300 | NO_INPUT |
| 05-22 | 972 | 210 | NO_INPUT |
| 05-22 | 973 | 120 | NO_INPUT |
| 05-22 | 974 | 30 | NO_INPUT |
| 05-22 | 975 | 150 | NO_INPUT |
| 05-22 | 976 | 120 | NO_INPUT |
| 05-22 | 978 | 150 | NO_INPUT |
| 05-23 | 971 | 260 | NO_INPUT |
| 05-23 | 972 | 120 | NO_INPUT |
| 05-23 | 973 | 100 | NO_INPUT |
| 05-23 | 974 | 48 | NO_INPUT |
| 05-23 | 975 | 120 | NO_INPUT |
| 05-23 | 976 | 72 | NO_INPUT |
| 05-23 | 978 | 192 | NO_INPUT |

## 다음 액션
- 같은 `run.py`를 공유 폴더 접근이 가능한 일반 Windows PowerShell 또는 Claude 측 실행 채널에서 재실행한다.
- 산출물은 원본 접근 성공 시에만 지정 xlsx 경로에 생성되도록 되어 있다.
