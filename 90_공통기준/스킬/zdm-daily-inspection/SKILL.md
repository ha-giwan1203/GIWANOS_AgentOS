---
name: zdm-daily-inspection
description: ZDM 일상점검 자동 입력 (SP3M3 19개 점검표 / 75개 항목). daily-routine 통합 또는 단독 실행
version: v1.0
trigger: "일상점검", "ZDM", "ZDM 점검", "점검 입력", "일상점검 등록"
grade: A
status: active
note: 통합 스킬 daily-routine/run.py 포함. 단독 실행도 가능
---

# ZDM 일상점검 자동 입력

> 점검표 19개 + API spec + 일요일 차단은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 시스템
- URL: `http://ax.samsong.com:34010/`
- 라인: SP3M3 (19개 점검표, 75항목/일)
- API: `GET/POST /api/daily-inspection/{masterId}/...`

## 절차 (요약)
1. **일요일 차단**: `assert_not_sunday(today)` 필수 호출
2. CDP `http://localhost:9223` 연결 (없으면 자동 실행)
3. `/api/daily-inspection` → SP3M3 19개 필터
4. 각 점검표 항목 조회 → `POST /record` check_result="OK", check_day=오늘
5. 검증: `/records` 재조회 = 75건

## verify
- records 재조회 75/75
- check_result 전부 "OK"
- check_day = 오늘
- SP3M3 19개 점검표 모두 처리

## 실패 시
- CDP 미연결 / ZDM 접속 불가 / 점검표 < 19 / 75건 불일치 → FAIL
- 일요일 시도 → 즉시 종료 (정상)
- 되돌리기: `check_result=""` POST → 해당일 삭제
- 상세 → MANUAL.md "실패 조건" + "되돌리기"

## 금지
- API 스펙 변경 없이 POST 본문 임의 변경
- NG 입력 시 issue_desc 없이 저장
- SP3M3 외 라인 임의 조작
- `taskkill //F //IM chrome.exe` 사용 (CDP 종료는 `Browser.close`)
