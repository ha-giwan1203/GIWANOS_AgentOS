---
name: line-stoppage
description: 월별 라인정지비(라인보상상세현황) G-ERP 자동 조회 + raw xlsx + 요약 md 생성. 대원테크(0109) default
trigger: "라인정지비 정리", "라인보상 정리", "월 라인정지", "라인정지 자동조회", "MM월 라인정지비"
grade: A
---

# 월별 라인정지비 자동 조회

> 도메인 규칙: `07_라인정지비용/CLAUDE.md` (산출 공식·메뉴 경로·작업폴더 관행)
> 데이터 원천: G-ERP 클레임관리 > 라인보상관리 > **라인보상상세현황**
> 인증·CDP 인프라: `90_공통기준/스킬/d0-production-plan/` (`erp_login_via_http`, `ensure_chrome_cdp` 재사용)

## 동기화 제한 ⚠️
매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53 G-ERP 조회 차단. 그 시간대 실행 시 결과 누락 가능 — `run.py` 자동 회피 (60초 대기 후 재시도).

## 사용

### 매월 표준 절차 (3단계)
```bash
# 1) G-ERP 라인보상상세현황 47건 → 라인정지_MM월_raw.xlsx
python 90_공통기준/스킬/line-stoppage/run.py --month 2026-04

# 2) QIS 4탭 (라인정지/재작업/선별작업/기타생산비용=라인교체) → QIS청구_MM월_raw.json
python 90_공통기준/스킬/line-stoppage/qis_extract.py --month 2026-04

# 3) 통합 — xlsx에 시트 추가(통합집계+QIS_기타생산비용) + md 통합 본문
python 90_공통기준/스킬/line-stoppage/merge_monthly.py --month 2026-04
```

### 부분 사용
```bash
# G-ERP만 (run.py)
python 90_공통기준/스킬/line-stoppage/run.py --month 2026-04 --cmpy 0110
python 90_공통기준/스킬/line-stoppage/run.py --month 2026-04 --line SP3M3

# QIS headless
python 90_공통기준/스킬/line-stoppage/qis_extract.py --month 2026-04 --headless
```

## 산출물
| 파일 | 위치 |
|------|------|
| raw 47건 + 집계 | `05_생산실적/조립비정산/{MM+1}월/라인정지_{MM}월_raw.xlsx` |
| 요약 보고 | `05_생산실적/조립비정산/{MM+1}월/라인정지_{MM}월_요약.md` |

## 절차 (요약)
1. d0 스킬의 `erp_login_via_http()` 호출 → ERP 세션 획득 (cookies + X-XSRF-TOKEN)
2. `ensure_chrome_cdp()` → Chrome CDP 9223 기동
3. Playwright `connect_over_cdp` → 쿠키 주입 → `/costCharge/viewListCostBillDetail.do` 진입
4. 검색조건 입력: `searchOcrnDaF`/`searchOcrnDaT` = 월 1일~말일, `searchCmpy` = 업체코드
5. `#btnSearch` 클릭 → pqgrid 로드 (3초)
6. `$('.pq-grid').pqGrid('instance').option('dataModel.data')` JS evaluate → JSON
7. raw xlsx + 요약 md 저장

## verify (사후 검증)
- 건수: G-ERP UI에서 직접 검색한 결과와 일치
- 합계 = `Σ COST_BILL_TOT`
- 미승인(APPROVAL_YN ≠ Y) / 미접수(ACCEPT_YN_NM ≠ 접수) 건수 보고
- 귀책 공란 / 차종 공란 건수 점검 출력

## 실패 시
- CDP 9223 안 뜸 → `_kill_zombie_chrome` 후 재시도
- OAuth 실패 → `.oauth.json` 확인 (d0 스킬 폴더)
- pqgrid 로드 0건 → 동기화 차단 시간대 회피 후 재시도
- 라인보상상세현황 메뉴 권한 없음 → ERP 사용자 권한 확인 (사용자 작업)

## 산출 공식 (참조)
```
라인정지비 = Σ COST_BILL_TOT
          = Σ (DAY_MINLY_STOP_COST × DAY_STOP_MINUTE
            +  NGT_MINLY_STOP_COST × NGT_STOP_MINUTE)
```

## 결과 예시 (4월)
- 47건 / 3,158,529원 / 전부 SP3M3 SP3 MAIN #03
- 귀책: 생산기술팀 36건(2,256,840), 협력사 5건(577,290), 품질관리팀 3건(181,384), 기타 3건(143,014)
- 발생유형: 설비이상 36 / 품질이상 10 / 자재이상 1

## 매월 반복 시 체크
1. 이전 월 미승인/미접수 건이 이번 달로 넘어와 중복 잡히지 않는지
2. 신규 라인·신규 귀책업체 등장 시 정산 본체와 매핑 확인
3. 조립품번 변경 시 도메인 문서 47건 사례 갱신
