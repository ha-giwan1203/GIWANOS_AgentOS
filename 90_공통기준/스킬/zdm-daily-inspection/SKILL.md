---
name: zdm-daily-inspection
description: ZDM 시스템 일상점검 자동 입력 (SP3M3 라인)
version: v1.0
trigger: "일상점검", "ZDM", "ZDM 점검", "점검 입력", "일상점검 등록"
author: 하지완
last_updated: 2026-04-13
status: active
note: 통합 스킬 daily-routine/run.py에 포함됨. 단독 실행도 가능 (run.py)
grade: A
---

# ZDM 일상점검 자동 입력

## 대상 업무

| 업무 | 주기 | 시간 | 방식 |
|------|------|------|------|
| ZDM 시스템 일상점검 입력 | 매일 | 08:00 | API 직접 호출 (CDP 브라우저 경유) |

## 대상 라인
- **SP3M3** (19개 점검표, 75개 점검항목/일)
- 협력사: 오토리브 (전체 공정 동일)

## 시스템 정보

| 항목 | 값 |
|------|-----|
| URL | `http://ax.samsong.com:34010/` |
| 프레임워크 | Bootstrap 5.3.2 + vanilla JS |
| 메인 JS | `/static/js/main.js` |
| API 기본경로 | (루트, API_BASE 비어있음) |

## API 엔드포인트

| 용도 | 메서드 | 경로 |
|------|--------|------|
| 점검표 목록 | GET | `/api/daily-inspection` |
| 점검항목 조회 | GET | `/api/daily-inspection/{masterId}/items` |
| 점검기록 조회 | GET | `/api/daily-inspection/{masterId}/records?year_month=YYYY-MM` |
| 점검기록 저장 | POST | `/api/daily-inspection/{masterId}/record` |

### POST 요청 본문

```json
{
  "item_id": "UUID",
  "year_month": "2026-04",
  "check_day": 1,
  "check_result": "OK",
  "issue_desc": "",
  "action_taken": "",
  "manager_name": "",
  "worker_name": "작업자"
}
```

- `check_result`: `"OK"` / `"NG"` / `""` (삭제)
- `check_day`: 1~31 (해당 월의 일자)
- NG 입력 시 `issue_desc`(이상내용), `action_taken`(조치내용) 필수

## SP3M3 점검표 구조 (19개 공정)

| 점검표번호 | 공정번호 | 점검항목수 |
|-----------|---------|-----------|
| SP3M3-10-1 | 10 | 6 |
| SP3M3-30-1 | 30 | 7 |
| SP3M3-60-1 | 60 | 2 |
| SP3M3-80-1 | 80 | 3 |
| SP3M3-90-1 | 90 | 5 |
| SP3M3-120-1 | 120 | 2 |
| SP3M3-141-1 | 141 | 3 |
| SP3M3-180-1 | 180 | 4 |
| SP3M3-200-1 | 200 | 13 |
| SP3M3-210-1 | 210 | 3 |
| SP3M3-260-1 | 260 | 2 |
| SP3M3-290-1 | 290 | 2 |
| SP3M3-310-1 | 310 | 2 |
| SP3M3-320-1 | 320 | 2 |
| SP3M3-330-1 | 330 | 4 |
| SP3M3-360-1 | 360 | 5 |
| SP3M3-390-1 | 390 | 4 |
| SP3M3-400-1 | 400 | 4 |
| SP3M3-410-1 | 410 | 2 |
| **합계** | | **75** |

## 점검항목 주요 카테고리

| 카테고리 | 점검자 | 출현 빈도 | 설명 |
|---------|--------|----------|------|
| 설비청소상태 | 작업자 | 거의 전 공정 | 청소도구로 청소여부 확인 |
| 설비작동 작동상태 | 관리자 | 다수 공정 | 설비 정상작동 확인 |
| 자재 분류관 | 작업자 | 다수 공정 | 자재분류 확인 |
| 스크류 체결 값 세팅 "0" | 작업자 | 계측 공정 | LVDT 작동상태 |
| 리벳팅 압력 | 작업자 | 공정 200 | 60~80 bar |
| 그리스 도포량 | 작업자 | 공정 330 | 5~10mg |
| MGG 작동 시간 | 관리자 | 공정 200 | 1.7~2.3초 |

## 일요일 차단 (최우선 규칙)

**실행 전 반드시 요일 검사를 수행한다. 일요일이면 즉시 중단.**

```python
from datetime import datetime, date

def assert_not_sunday(target_date):
    """일요일이면 ValueError 발생. 모든 입력 전 필수 호출."""
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    if target_date.weekday() == 6:  # 6 = Sunday
        raise ValueError(f"{target_date} 은(는) 일요일 — 입력 금지")

# 사용 예시
assert_not_sunday(datetime.now().date())          # 당일 점검 시
assert_not_sunday(date(2026, 4, 5))               # 누락분 보정 시
```

- 당일 점검, 누락분 보정, 일괄 입력 등 **모든 경로**에서 이 함수를 거친다
- 일요일 데이터가 이미 입력된 경우: check_result="" POST로 삭제 후 보고
- cron 스케줄도 `* * 1-6` (월~토)이지만, 수동 실행 시에도 이 검사가 방어선

## 실행 절차

### 사전 조건
1. CDP 브라우저가 `http://localhost:9223`에서 실행 중 (없으면 자동 실행)
2. ZDM 시스템(`http://ax.samsong.com:34010/`)에 접속된 상태
3. Chrome 프로필: `.flow-chrome-debug` (포트 9223, `--remote-debugging-port=9223`)

### CDP 브라우저 실행/종료

**실행:**
```python
subprocess.Popen([
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--remote-debugging-port=9223",
    r"--user-data-dir=C:\Users\User\.flow-chrome-debug",
    "http://ax.samsong.com:34010/",
    "--no-first-run", "--no-default-browser-check"
])
```

**종료 (필수 — 아래 방식만 사용):**
```python
cdp = browser.contexts[0].pages[0].context.new_cdp_session(browser.contexts[0].pages[0])
cdp.send("Browser.close")
```

**금지:** `taskkill //F //IM chrome.exe` 사용 금지 — 기존 브라우저까지 종료되고 복구 팝업 발생

### 실행 흐름
1. CDP 브라우저에 Playwright로 연결
2. `/api/daily-inspection` 호출 → SP3M3 점검표 19개 필터
3. 각 점검표의 `/api/daily-inspection/{id}/items` 호출 → 점검항목 목록
4. 각 항목에 `POST /api/daily-inspection/{id}/record` → check_result="OK", check_day=오늘
5. 결과 집계 (성공/실패 건수)
6. 검증: records 재조회하여 입력 건수 = 75건 확인

### 브라우저 없이 실행 (향후)
- API가 세션 인증 불필요 시, `requests` 라이브러리로 직접 호출 가능
- 현재는 CDP 브라우저 세션의 쿠키/인증을 활용

## UI 구조 (브라우저 조작 시 참고)

### 네비게이션
- 일상점검 메뉴: `switchSection('inspection')` (nav-link 5번째)

### 주요 모달
| 모달 ID | 용도 | 트리거 |
|---------|------|--------|
| `inspectionModal` | 점검표 등록/수정 | `openAddInspectionModal()` |
| `inspectionItemsModal` | 점검항목 관리 | `openInspectionItemsModal(id)` |
| `inspectionRecordModal` | **일상점검 입력** (전체화면) | `openInspectionRecordModal(masterId)` |

### 점검 입력 화면 (inspectionRecordModal)
- 검사월: `#inspection-record-month` (type=month)
- 검사일: `#inspection-record-date` (type=date)
- 작업자: `#inspection-worker-name` (text)
- 날짜 셀 클릭 → `toggleInspectionCheck(itemId, day, cell)`
- 토글 순서: 빈칸 → OK → NG(이상내용 입력) → 빈칸
- 각 클릭마다 자동 저장 (saveInspectionCheck)

### 필터 (목록 화면)
- 라인: `#filter-insp-line`
- 협력사: `#filter-insp-vendor`
- 공정번호: `#filter-insp-process-no`
- 공정명: `#filter-insp-process-name`

## 실패 조건

다음 중 하나라도 해당하면 **실행 실패**로 판정한다:

| 조건 | 판정 |
|------|------|
| CDP 브라우저 미연결 (`localhost:9223` 무응답) | FAIL |
| ZDM 시스템 접속 불가 (`ax.samsong.com:34010`) | FAIL |
| GET `/api/daily-inspection` 반환 점검표 < 19개 | FAIL |
| POST 저장 후 records 재조회 시 입력 건수 ≠ 75 | FAIL |
| API 응답 4xx/5xx 에러 | FAIL |
| NG 입력인데 `issue_desc` 누락 | FAIL (API 거부) |

## 중단 기준

다음 상황에서는 **즉시 중단**하고 사용자에게 보고한다:

1. API 스키마 변경 감지 — 응답 필드명이 문서와 불일치
2. 연속 5건 이상 POST 실패 (서버 장애 의심)
3. CDP 브라우저 크래시 또는 포트 무응답
4. 점검표 마스터(ID/구조) 변경 감지 — 항목수가 기존 75와 불일치
5. 이미 입력된 날짜에 덮어쓰기 시도 감지

## 검증 항목

실행 완료 후 반드시 확인:

- [ ] records 재조회 → 오늘 날짜 기준 75건 전수 확인
- [ ] check_result 전부 `"OK"` 확인
- [ ] check_day = 오늘 일자 일치
- [ ] SP3M3 19개 점검표 전부 처리 확인 (누락 공정 없음)
- [ ] API 에러 로그 0건

## 되돌리기 방법

| 범위 | 방법 |
|------|------|
| 특정 항목 | 해당 점검표의 record POST API에 `check_result=""` (빈값) 전송 → 해당 일자 기록 삭제 |
| 전체 롤백 | 19개 점검표 × 해당일 75건 전부 `check_result=""` POST |
| 마스터 데이터 | 변경하지 않으므로 구조 롤백 불필요 |

> NG로 잘못 입력한 경우: 빈값 POST 후 OK로 재입력

## 금지사항
- API 스펙 변경 없이 POST 본문 구조 임의 변경 금지
- NG 입력 시 issue_desc 없이 저장 금지
- 점검표 마스터(등록/삭제) 조작 금지 — 점검 기록 입력만 허용
- 다른 라인(SP3M3 외) 데이터 임의 조작 금지
