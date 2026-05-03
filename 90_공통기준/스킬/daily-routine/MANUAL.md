# daily-routine — MANUAL

> 상세 절차/실패조건/검증/되돌리기. SKILL.md는 호출 트리거 + 80줄 요약만.

## 목적
- 매일 아침 ZDM 일상점검 + MES 생산실적 업로드를 1 스크립트로 자동 처리
- 누락분 자동 탐지·보정 포함
- 일요일 차단, KST 기준 시간 고정

## 스케줄
- cron: `7 8 * * 1-6` (월~토 08:07)
- scheduled task ID: `daily-routine`

## 구성
| 순서 | 업무 | 방식 | 시스템 |
|------|------|------|--------|
| 1 | ZDM 일상점검 | API 직호출 (requests) | ax.samsong.com:34010 |
| 2 | MES 생산실적 업로드 | 직접 HTTP OAuth + 3회 재시도 | mes-dev.samsong.com:19200 |

## 실행 방법
```bash
# 스케줄 태스크 (task_runner 경유)
bash .claude/scripts/task_runner.sh daily-routine python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"

# 수동 실행
python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"
```

## 실행 흐름

### 공통
- KST 기준 일요일이면 즉시 종료 (`is_sunday()` -> `sys.exit(0)`)
- 인코딩: 비ASCII 문자 사용 금지 (cp949 호환)

### 1단계: ZDM 일상점검
1. SP3M3 점검표 19개 조회
2. 당일 75개 항목 전부 OK 입력
3. 검증: records 재조회 75/75 확인
4. 누락분 보정: 1일~어제 중 일요일 제외 미입력일 자동 입력

### 2단계: MES 생산실적 업로드
1. BI 파일 갱신 (Z드라이브 → 로컬)
2. 직접 HTTP OAuth 로그인 (CDP/Playwright 불필요)
3. MES 기등록 날짜 조회 → 누락일 산출
4. 누락일별: BI 추출 → 품질검증 → 업로드 → 건수+합계 검증
5. 실패 시 최대 3회 재시도 (새 세션 재로그인)

## 출력
- ZDM: `{일}일: {N}건 OK, 검증 {N}/75 PASS`
- MES: `{날짜}: {N}/{N}건(OK), qty {합계}/{합계}(OK)`

## 실패 조건
| 조건 | 판정 |
|------|------|
| ZDM API 접속 불가 | FAIL |
| SP3M3 점검표 != 19개 | FAIL |
| ZDM 입력 후 검증 != 75건 | FAIL |
| MES 자동 로그인 실패 | FAIL |
| BI 생산량 빈값 | FAIL |
| 업로드 후 건수/합계 불일치 | FAIL |

## 중단 기준
- 일요일 실행 → 즉시 종료 (정상)
- BI 대상 날짜 데이터 0건 → STOP (정상)
- MES 중복 데이터 존재 → STOP (정상)
- API 연속 실패 → 사용자 보고

## 검증
- ZDM: records 재조회 75/75건 전수
- MES: 업로드 후 건수+합계 BI 원본 대조
- 일요일 데이터 0건 확인

## 되돌리기
| 범위 | 방법 |
|------|------|
| ZDM 특정 날짜 | check_result="" POST → 해당일 기록 삭제 |
| MES 특정 날짜 | 올바른 데이터로 재전송 (UPSERT) |
| MES 수동 삭제 | MES 화면에서 직접 삭제 |

## 의존성
- Python: requests, openpyxl
- 네트워크: ZDM 서버, MES 서버, Z드라이브
- 폐기: playwright, pyautogui, CDP 브라우저

## 관련 스킬
- `zdm-daily-inspection/` — ZDM 단독 실행
- `production-result-upload/` — MES 단독 실행
