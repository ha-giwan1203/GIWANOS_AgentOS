---
name: daily-routine
description: >
  매일 반복 업무 통합 실행 (ZDM 일상점검 + MES 생산실적 업로드).
  "일상점검", "생산실적", "실적 올려", "매일 업무", "daily" 등을 언급하면 이 스킬을 사용할 것.
grade: A
version: 1.0
author: 하지완
last_updated: 2026-04-15
status: active
---

# 매일 반복 업무 통합 실행

## 목적
- 매일 아침 반복되는 ZDM 일상점검 + MES 생산실적 업로드를 하나의 스크립트로 자동 처리
- 누락분 자동 탐지 및 보정 포함
- 일요일 차단, KST 기준 시간 고정

## 트리거
- "일상점검", "ZDM 점검", "점검 입력"
- "실적 올려", "MES 업로드", "생산실적 등록"
- "매일 업무", "daily", "/daily"

## 스케줄
- **cron**: `7 8 * * 1-6` (월~토 08:07)
- **scheduled task ID**: `daily-routine`

## 구성

| 순서 | 업무 | 방식 | 시스템 |
|------|------|------|--------|
| 1 | ZDM 일상점검 | API 직호출 (requests) | ax.samsong.com:34010 |
| 2 | MES 생산실적 업로드 | 직접 HTTP OAuth + 3회 재시도 | mes-dev.samsong.com:19200 |

## 실행 방법

```bash
# 스케줄 태스크 (task_runner 경유 — 실행 로그 + 연속 실패 감지)
bash .claude/scripts/task_runner.sh daily-routine python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"

# 수동 실행 (직접 호출)
python3 "C:/Users/User/Desktop/업무리스트/90_공통기준/스킬/daily-routine/run.py"
```

## 실행 흐름

### 공통
- KST 기준 일요일이면 즉시 종료 (`is_sunday()` -> `sys.exit(0)`)
- 인코딩: em-dash 등 비ASCII 문자 사용 금지 (cp949 호환)

### 1단계: ZDM 일상점검
1. SP3M3 점검표 19개 조회
2. 당일 75개 항목 전부 OK 입력
3. 검증: records 재조회 75/75 확인
4. 누락분 보정: 1일~어제까지 중 일요일 제외 미입력일 자동 입력

### 2단계: MES 생산실적 업로드
1. BI 파일 갱신 (Z드라이브 -> 로컬)
2. 직접 HTTP OAuth 로그인 (CDP/Playwright 불필요)
3. MES 기등록 날짜 조회 -> 누락일 산출 (일요일 제외)
4. 누락일별: BI 추출 -> 품질검증 -> 업로드 -> 건수+합계 검증
5. 업로드 실패 시 최대 3회 재시도 (새 세션 재로그인)

## 입력
- 없음 (자동 실행, 날짜 자동 계산)
- 수동 실행 시 스크립트 직접 호출

## 출력
- 콘솔 출력: 각 단계별 성공/실패/검증 결과
- ZDM: `{일}일: {N}건 OK, 검증 {N}/75 PASS`
- MES: `{날짜}: {N}/{N}건(OK), qty {합계}/{합계}(OK)`

## 실패 조건

| 조건 | 판정 |
|------|------|
| ZDM API 접속 불가 | FAIL |
| SP3M3 점검표 != 19개 | FAIL |
| ZDM 입력 후 검증 != 75건 | FAIL |
| CDP 브라우저 연결 실패 (자동 시작 포함) | FAIL |
| MES 자동 로그인 실패 | FAIL |
| iframe/jQuery 미로드 | FAIL |
| BI 생산량 빈값 (데이터 미완성) | FAIL |
| 업로드 후 건수 또는 생산량 합계 불일치 | FAIL |

## 중단 기준
- 일요일 실행 시도 -> 즉시 종료 (정상)
- BI 파일에 대상 날짜 데이터 0건 -> STOP (정상)
- MES 중복 데이터 존재 -> STOP (정상)
- API 연속 실패 -> 사용자 보고

## 검증 항목
- [x] ZDM: records 재조회 75/75건 전수 확인
- [x] MES: 업로드 후 건수 + 생산량 합계 BI 원본과 대조
- [x] 일요일 데이터 입력/업로드 없음 확인

## 되돌리기 방법

| 범위 | 방법 |
|------|------|
| ZDM 특정 날짜 | check_result="" POST -> 해당일 기록 삭제 |
| MES 특정 날짜 | 올바른 데이터로 동일 날짜 재전송 (UPSERT) |
| MES 수동 삭제 | MES 화면에서 직접 삭제 |

## 의존성
- Python: requests, openpyxl
- 네트워크: ZDM 서버, MES 서버, Z드라이브
- ~~playwright, pyautogui, CDP 브라우저~~: 폐기됨 (직접 HTTP 전환)

## 관련 스킬 (개별)
- `zdm-daily-inspection/` - ZDM 단독 실행 시
- `production-result-upload/` - MES 단독 실행 시
