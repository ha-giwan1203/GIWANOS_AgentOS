# zdm-daily-inspection — MANUAL

> 점검표 19개 + API spec + 일요일 차단 + 실행 절차. SKILL.md는 호출 트리거 + 80줄 요약.

## 대상 업무
| 업무 | 주기 | 시간 | 방식 |
|------|------|------|------|
| ZDM 일상점검 입력 | 매일 | 08:00 | API 직접 호출 (CDP 경유) |

## 대상 라인
- SP3M3 (19개 점검표, 75개 점검항목/일)
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
- `check_day`: 1~31
- NG 시 `issue_desc`(이상내용), `action_taken`(조치내용) 필수

## SP3M3 점검표 구조 (19개 공정, 합계 75)
| 점검표번호 | 공정 | 항목수 | | 점검표번호 | 공정 | 항목수 |
|--|--|--|--|--|--|--|
| SP3M3-10-1 | 10 | 6 | | SP3M3-260-1 | 260 | 2 |
| SP3M3-30-1 | 30 | 7 | | SP3M3-290-1 | 290 | 2 |
| SP3M3-60-1 | 60 | 2 | | SP3M3-310-1 | 310 | 2 |
| SP3M3-80-1 | 80 | 3 | | SP3M3-320-1 | 320 | 2 |
| SP3M3-90-1 | 90 | 5 | | SP3M3-330-1 | 330 | 4 |
| SP3M3-120-1 | 120 | 2 | | SP3M3-360-1 | 360 | 5 |
| SP3M3-141-1 | 141 | 3 | | SP3M3-390-1 | 390 | 4 |
| SP3M3-180-1 | 180 | 4 | | SP3M3-400-1 | 400 | 4 |
| SP3M3-200-1 | 200 | 13 | | SP3M3-410-1 | 410 | 2 |
| SP3M3-210-1 | 210 | 3 | | **합계** | | **75** |

## 점검항목 주요 카테고리
| 카테고리 | 점검자 | 빈도 | 설명 |
|---------|--------|------|------|
| 설비청소상태 | 작업자 | 거의 전 공정 | 청소도구 청소여부 |
| 설비작동 작동상태 | 관리자 | 다수 | 정상작동 |
| 자재 분류관 | 작업자 | 다수 | 자재분류 |
| 스크류 체결 값 세팅 "0" | 작업자 | 계측 공정 | LVDT 작동상태 |
| 리벳팅 압력 | 작업자 | 공정 200 | 60~80 bar |
| 그리스 도포량 | 작업자 | 공정 330 | 5~10mg |
| MGG 작동 시간 | 관리자 | 공정 200 | 1.7~2.3초 |

## 일요일 차단 (최우선)
모든 입력 전 필수 호출:
```python
from datetime import datetime, date

def assert_not_sunday(target_date):
    if isinstance(target_date, str):
        target_date = date.fromisoformat(target_date)
    if target_date.weekday() == 6:
        raise ValueError(f"{target_date} 은(는) 일요일 — 입력 금지")

assert_not_sunday(datetime.now().date())          # 당일
assert_not_sunday(date(2026, 4, 5))               # 누락분 보정
```
- 당일/누락분/일괄 입력 모든 경로에서 호출
- 일요일 데이터 이미 입력된 경우: `check_result=""` POST로 삭제 + 보고
- cron `* * 1-6` (월~토) + 수동 실행 시 본 검사 방어선

## 실행 절차

### 사전 조건
1. CDP 브라우저 `http://localhost:9223` 실행 중 (없으면 자동 실행)
2. ZDM 시스템 접속 상태
3. Chrome 프로필: `.flow-chrome-debug` (포트 9223)

### CDP 브라우저 실행/종료

실행:
```python
subprocess.Popen([
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--remote-debugging-port=9223",
    r"--user-data-dir=C:\Users\User\.flow-chrome-debug",
    "http://ax.samsong.com:34010/",
    "--no-first-run", "--no-default-browser-check"
])
```

종료 (필수):
```python
cdp = browser.contexts[0].pages[0].context.new_cdp_session(browser.contexts[0].pages[0])
cdp.send("Browser.close")
```

금지: `taskkill //F //IM chrome.exe` — 기존 브라우저 모두 종료 + 복구 팝업

### 실행 흐름
1. CDP 브라우저에 Playwright 연결
2. `/api/daily-inspection` → SP3M3 19개 필터
3. 각 점검표 `/api/daily-inspection/{id}/items` → 항목 목록
4. 각 항목 `POST /record` → check_result="OK", check_day=오늘
5. 결과 집계 (성공/실패)
6. 검증: records 재조회 = 75건

## UI 구조 (참고)

### 네비게이션
- 일상점검 메뉴: `switchSection('inspection')` (nav-link 5번째)

### 모달
| 모달 ID | 용도 | 트리거 |
|---------|------|--------|
| `inspectionModal` | 점검표 등록/수정 | `openAddInspectionModal()` |
| `inspectionItemsModal` | 점검항목 관리 | `openInspectionItemsModal(id)` |
| `inspectionRecordModal` | **일상점검 입력** | `openInspectionRecordModal(masterId)` |

### 점검 입력 화면
- 검사월: `#inspection-record-month`
- 검사일: `#inspection-record-date`
- 작업자: `#inspection-worker-name`
- 날짜 셀 클릭 → `toggleInspectionCheck(itemId, day, cell)`
- 토글: 빈칸 → OK → NG(이상내용) → 빈칸
- 자동 저장 (saveInspectionCheck)

### 필터 (목록)
- `#filter-insp-line` / `#filter-insp-vendor` / `#filter-insp-process-no` / `#filter-insp-process-name`

## 실패 조건
| 조건 | 판정 |
|------|------|
| CDP 미연결 (`localhost:9223` 무응답) | FAIL |
| ZDM 접속 불가 | FAIL |
| GET `/api/daily-inspection` 점검표 < 19개 | FAIL |
| POST 후 records 재조회 ≠ 75 | FAIL |
| API 4xx/5xx | FAIL |
| NG 입력인데 `issue_desc` 누락 | FAIL |

## 중단 기준
1. API 스키마 변경 (응답 필드명 불일치)
2. 연속 5건 이상 POST 실패 (서버 장애 의심)
3. CDP 크래시 또는 포트 무응답
4. 점검표 마스터 변경 (항목수 ≠ 75)
5. 이미 입력된 날짜 덮어쓰기 시도

## 검증 항목
- records 재조회 → 오늘 날짜 75건
- check_result 전부 "OK"
- check_day = 오늘
- SP3M3 19개 모두 처리
- API 에러 0건

## 되돌리기
| 범위 | 방법 |
|------|------|
| 특정 항목 | `check_result=""` POST → 해당일 기록 삭제 |
| 전체 롤백 | 19개 점검표 × 75건 전부 빈값 POST |
| 마스터 데이터 | 미변경 → 롤백 불필요 |

NG 잘못 입력 시: 빈값 POST 후 OK 재입력.

## 금지
- API 스펙 변경 없이 POST 본문 임의 변경
- NG 입력 시 issue_desc 없이 저장
- 점검표 마스터 조작 (등록/삭제) — 기록 입력만
- SP3M3 외 라인 임의 조작
