# Plan: 옵션 A 하이브리드 — ERP D0 API 직접 호출 전환

## Status (2026-04-30)
- **현재 상태**: P1 코드 작성 완료, 실측 진행 대기 (CDP 9223 launch 필요).
- **결정 변경 이력**: 초기 α (P1 보류) → 사용자 명시 P1 진입. `798a119d` 합의 사용자 본인 변경.
- **다음 단계**: 사용자가 dev CDP 9223 launch + OAuth 통과 → `python auth_extract.py` 재실행 → 본 문서 P1 결과 섹션 갱신.

## P1 결과 (실측 진행 중 — 2026-04-30)

### Step 1: 코드 작성 ✅ 완료
- 파일: `auth_extract.py` (~190줄)
- 사용자 명시 안전장치 준수 검증:
  - POST/multiList/rank/MES/DELETE 코드 호출 0건 (grep)
  - GET 1회 + timeout 10s + 재시도 루프 없음
  - 쿠키 이름·도메인 목록만 기록, 값 미출력
  - XSRF 마스킹 `앞4...뒤4 (len=N)`
  - dev 환경(`erp-dev`) 한정
  - `dry_run = True`, `post_blocked = True` 메타플래그
- run.py / bat 미수정 (git diff 0)

### Step 2: 실측 — CDP_DEAD 종료 (사용자 액션 대기)
- 첫 실행 결과: `{"status": "CDP_DEAD", "error": "127.0.0.1:9223 미응답"}`
- 안전 fallthrough 동작 확인 — 코드는 retry 안 함
- 사용자 액션 필요:
  ```powershell
  Start-Process -FilePath 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9223','--remote-debugging-address=127.0.0.1','--user-data-dir=C:\Users\User\.flow-chrome-debug'
  # OAuth 통과 후
  python 90_공통기준/스킬/d0-production-plan/auth_extract.py
  ```

### Step 3: 결과 분석 (2026-04-30 10:46 실측 완료) ✅

**Claude 재판정**: `P1_PASS_GET_200` (진짜 PASS)

| 필드 | 값 |
|---|---|
| http_status | 200 |
| http_final_url | `erp-dev.samsong.com:19100/layout/layout.do` (ERP 내부) |
| http_redirect_chain | `[]` (redirect 0건) |
| http_html_length | 218,774 bytes (정상 layout) |
| xsrf_chosen_source | cookie (`XSRF-TOKEN`, len=36) |
| meta_xsrf | 발견 (`d548...ec66`, len=36) |
| 1차 verdict | `P1_PASS_GET_200` (Claude 재판정 일치) |

**보강 사항 (세션131 사용자 명시 SKILL.md 안 읽음 정정)**:
- `auth_extract.py`에 `ensure_erp_login` + `_wait_oauth_complete` import + 호출 추가
- run.py 본체는 수정 0 (사용자 명시 금지 준수)
- pyautogui 자동완성으로 OAuth 통과 검증

**의의**:
- 옵션 A 하이브리드 GET 흐름 실증 ✅
- XSRF 추출 위치 2곳 확보 (cookie + meta) — cookie 우선
- requests에 cookie/XSRF 동봉 시 ERP 내부 접근 가능

**잔존 (P2 이후)**:
- POST 호출은 미검증 — SKILL.md 라인 168 "fetch 직접 호출 시 500 에러" 위험 잔존
- P2 PoC = `selectListPmD0AddnUpload.do` 엑셀 파싱 (read-only에 가까움) 호출로 POST 가능 여부 검증
- P2 진입 시점은 시스템팀 답변 + 옵션 C 측정 종료 후 결정

## P2 결과 (2026-04-30 11:14 실측 완료) ✅

**사용자 명시 P2 진입** — "오늘 주간 서열 반영한거 확인해서 그다음 품번 하나만 적용해서 실제 테스트". 1건 신규 등록 + 즉시 정리 패턴.

### 후보 식별
- ERP 등록 16건 ↔ xlsm 주간 26건 매칭 → 첫 미등록 **R55 RSP3SC0665 qty=1500** 선택

### 단계별 결과
| 단계 | URL | Method | 결과 |
|---|---|---|---|
| Step 1: 엑셀 1행 생성 | `template/SSKR_D0_template.xlsx` Excel COM | — | xlsx 10,415 bytes |
| Step 2: selectList | `/prdtPlanMng/selectListPmD0AddnUpload.do` | POST multipart | 200, listLen 1, ERROR_FLAG 빈값 |
| Step 3: multiList (DB INSERT) | `/prdtPlanMng/multiListPmD0AddnUpload.do` | POST JSON | **200, REG_NO 319941 발급** |
| Step 4: ERP 그리드 검증 | `totGridList.searchListData()` | — | 17건 (16+1) ✅ |
| Step 5: DELETE 정리 | `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do` | **DELETE** | 200 |
| Step 6: 최종 검증 | ERP 그리드 + SmartMES | — | ERP 16건 / MES RSP3SC0665 0건 ✅ |

### 🔑 발견 (옵션 A 하이브리드 완전 가능 입증)

**1. `ajax: true` custom header 필수**
- jQuery prefilter가 모든 ajax 요청에 자동 추가하는 비표준 커스텀 헤더
- 서버측이 이 헤더로 ajax 요청 식별
- 누락 시 multiList 500 / 8ms 즉시 거부 (payload 처리 들어가지도 않음)
- 발견 방법: Playwright `page.route` + `route.abort` 패턴으로 jQuery.ajax 실제 헤더 캡처

**2. XSRF 토큰 매 요청마다 갱신**
- 서버가 selectList 응답에 `Set-Cookie: XSRF-TOKEN=새값; Max-Age=0; ..., XSRF-TOKEN=새값; ...` 형태로 새 토큰 발급
- Spring Security default 동작 — write 직전 토큰 회전
- header `X-XSRF-TOKEN`을 매 호출 직전에 cookie에서 다시 읽어 갱신해야 통과
- Stale 토큰 그대로 쓰면 multiList 500

**3. HTTP method 차이**
- `multiListPmD0AddnUpload`: POST
- `deleteDoAddnPrdtPlanInstrMngNew`: **DELETE** (POST 시 statusCode -9999 "Request method 'POST' not supported")
- SKILL.md 라인 259 명시 그대로

### 헤더 레시피 (P3+ 재사용)
```python
sess.headers.update({
    "ajax": "true",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": D0_URL,
    "Origin": "http://erp-dev.samsong.com:19100",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "User-Agent": "Mozilla/5.0 ... Chrome/...",
    "Accept-Language": "ko-KR,ko;q=0.9",
})

# 매 write 호출 직전:
def refresh_xsrf(sess):
    for c in sess.cookies:
        if c.name.upper() in ("XSRF-TOKEN", "X-XSRF-TOKEN"):
            sess.headers["X-XSRF-TOKEN"] = c.value
            return c.value
```

### 운영 안전 검증 ✅
- ERP DB INSERT → 즉시 DELETE → 16건 복원
- SmartMES 영향 0 (multiList만 호출, rank/MES 전송 미실행 → MES 동기화 트리거 안 됨)
- SKILL.md 라인 159 "MES 잔존 위험" 회피

## 선행 조건 (P3 이후 적용)
1. 2026-05-01 morning auto 로그 확인 (`1812603c` 패치 PASS/FAIL)
2. fallback 발화 여부 확인 (3 케이스 분류)
3. 시스템팀 ERP API 명세 + Service Account 가능 여부 답변
4. P3 = rank 저장 (`multiListMainSubPrdtPlanRankDecideMng`) — `sendMesFlag=N` dry-run + `sendMesFlag=Y` MES 전송. **MES 잔존 위험 본질** 단계

## Context
SP3M3 morning 자동화가 5일 중 4일 OAuth redirect 멍때림으로 실패. 화면 자동화(Playwright + Chrome) 의존이 매일 다른 분기로 깨지는 구조. ERP 내부 처리는 이미 ajax POST 기반이고, MES 검증은 `urllib.request` 직접 호출 중 (`run.py:819`). 즉 **underlying은 HTTP**.

하이브리드 = OAuth 로그인만 Playwright로 1회 → 세션 cookie + XSRF 토큰 추출 → 이후 모든 처리는 `requests` 직접 POST. "redirect 멍때림" 자체 제거.

## Phase 분해

| Phase | 내용 | 산출 | 검증 기준 | 위험도 |
|---|---|---|---|---|
| **P1** | OAuth 1회 → cookie/XSRF 추출 + dev 환경 단순 GET 200 | `auth_extract.py` 신설 (예상 ~150줄) | requests로 `/layout/layout.do` GET 200 응답 | 낮음 (read-only) |
| **P2** | XSRF 동봉 POST PoC — `selectListPmD0AddnUpload.do` 엑셀 파싱 호출 | parsed JSON | listLen이 manual 결과와 일치 | 중간 (server parse) |
| **P3** | `multiListMainSubPrdtPlanRankDecideMng.do` save — **dry-run 분기 강제** | save response | dry-run OK 후 사용자 검토 | 높음 (DB 저장) |
| **P4** | rank batch 개별 ext 등록 API화 | rank 결과 | manual 14건과 동일 결과 | 높음 (DB 저장) |
| **P5** | `run.py` `--api-mode` 플래그 추가, 기존 화면 경로 dual-mode 보존 | run.py 분기 추가 | 양쪽 동일 결과 비교 | 중간 |
| **P6** | morning bat에 `--api-mode` 적용 | bat 1줄 변경 | 1주 morning auto PASS | 낮음 |

## Endpoint 목록 (실측 — run.py + SKILL.md)

| 분류 | URL | Method | Payload | 출처 |
|---|---|---|---|---|
| OAuth | `auth-dev.samsong.com:18100/login` | (browser) | OAuth flow | run.py:32 |
| ERP 진입 | `erp-dev.samsong.com:19100/prdtPlanMng/viewListDoAddnPrdtPlanInstrMngNew.do` | GET | — | run.py:31 |
| ERP layout | `erp-dev.samsong.com:19100/layout/layout.do` | GET | — | run.py:30 |
| **엑셀 파싱** | `/prdtPlanMng/selectListPmD0AddnUpload.do` | POST | multipart `uploadfrm`, 파일 `files` | SKILL.md:119 |
| **D0 저장** | `/prdtPlanMng/multiListPmD0AddnUpload.do` | POST | JSON `{excelList, ADDN_PRDT_REASON_CD:"002"}` | SKILL.md:122 |
| **MAIN 서열** | `/prdtPlanMng/multiListMainSubPrdtPlanRankDecideMng.do` | POST | (런타임) | SKILL.md:62, run.py:44 |
| **OUTER 서열** | `/prdtPlanMng/multiListOuterPrdtPlanRankDecideMng.do` | POST | (런타임) | SKILL.md:63, run.py:48 |
| 서열 행 삭제 | `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngRankDecideNew.do` | DELETE | `{EXT_PLAN_REG_NO, STD_DA, PLAN_DA, PROD_NO, LINE_CD}` | SKILL.md:257 |
| D0 등록 삭제 | `/prdtPlanMng/deleteDoAddnPrdtPlanInstrMngNew.do` | DELETE | `{REG_NO}` | SKILL.md:259 |
| MES 검증 | `lmes-dev.samsong.com:19220/v2/prdt/schdl/list.api` | POST | `{tid, token, ...}` (이미 API) | run.py:819 |

## auth_extract.py 설계안 (추정 — 미실측)

```python
# 신설 예정 — 본 plan 단계에서 미생성
"""auth_extract.py — Playwright OAuth 1회 → cookie + XSRF 추출."""

def extract_auth_session() -> dict:
    """
    Playwright로 ERP OAuth 통과 → cookie/XSRF 토큰 추출.
    return {
        "cookies": {ERP_SESSION_ID: "...", XSRF-TOKEN: "...", ...},
        "xsrf": "...",
        "expires_at": "..."
    }
    """
    # 1. CDP launch / connect
    # 2. _safe_goto(D0_URL)
    # 3. ensure_erp_login + _wait_oauth_complete (기존 함수 재사용)
    # 4. context.cookies() — 모든 도메인 cookie 추출
    # 5. XSRF 토큰 추출 — 후보 위치 (실측 미수행):
    #    (a) cookie key "XSRF-TOKEN" 직접 값
    #    (b) page.evaluate로 jQuery $.ajaxSetup 등록된 기본 헤더 추출
    #    (c) page DOM <meta name="XSRF-TOKEN">
    #    (d) hidden input <input name="_csrf">
    # 6. dict 반환
```

## XSRF / Cookie 추출 후보 위치 (실측 보류)

| 후보 | 추출 방법 | 실측 필요 |
|---|---|---|
| (a) Cookie `XSRF-TOKEN` | `context.cookies()`에서 key 검색 | P1 단계 |
| (b) jQuery `$.ajaxSetup` | `page.evaluate("() => $.ajaxSettings.headers")` | P1 단계 |
| (c) Page meta tag | `page.evaluate("() => document.querySelector('meta[name=XSRF-TOKEN]')?.content")` | P1 단계 |
| (d) Hidden input | `page.locator('input[name=_csrf]').input_value()` | P1 단계 |

P1 진입 시 4개 후보 모두 실측 → 가장 안정적인 위치 채택.

## P1 안전조건

1. **dev 환경만**: `erp-dev.samsong.com` / `auth-dev` / `lmes-dev` 한정. 운영 환경(`erp.samsong.com` 등) 호출 금지.
2. **Read-only만**: GET 또는 read-only API. POST/DELETE 호출 금지.
3. **dry-run 분기 강제**: P2 이후에도 dry-run 옵션 기본값.
4. **로그 격리**: PoC 로그는 `06_생산관리/D0_업로드/logs/api_poc_*.log` 별도 디렉토리.
5. **타임아웃**: 모든 requests 호출 timeout=10s. 무한 hang 방지.
6. **잔존 데이터 정리**: P3+ 단계에서 등록 발생 시 `erp_d0_dedupe.py` 자동 호출 검증 후 진입.

## 시스템팀 문의 문안 (5건 — 사용자 오프라인 액션)

```
ERP D0 추가생산지시 생산계획 등록을 현재 화면 자동화로 처리 중인데,
화면 redirect/OAuth 불안정 때문에 공식 API 연동 가능 여부를 확인하고 싶습니다.

확인 요청:
1. D0 추가생산지시 등록 API 명세 제공 가능 여부
2. 엑셀 업로드 파싱 API + 저장 API 공식 사용 가능 여부
3. Service Account 또는 API 전용 인증 방식 제공 여부
4. CSRF/XSRF 토큰 처리 공식 방식
5. 테스트 서버에서 API 호출 검증 가능 여부
```

## 진입 선행 조건 (체크리스트)

- [ ] 2026-05-01 morning auto 로그 확인 — `1812603c` 패치 PASS
- [ ] fallback 발화 여부 확인 (a/b/c 케이스 분류)
- [ ] 시스템팀 답변 수령 (사용자 오프라인)
- [ ] 옵션 C 측정 7세션 누적 또는 1주 종료
- [ ] 위 4건 모두 충족 시 P1 진입 재결정

## 메타 위반 회피

- 본 plan 자체는 코드 미생성 / ERP 미호출 / run.py·bat 미수정. 단순 문서.
- S3 메타 커밋: 본 plan + TASKS 1줄 추가 = 1건 (정직 기록).
- 옵션 C measurement NEVER 위반 0.

## 합의 추적성

- 세션131 본 대화에서 사용자 본인 + GPT(라벨1) α 채택 / Gemini(라벨2) γ 채택 권장 (양측 갈림).
- 사용자 명시 지시 우선 원칙으로 α 채택 (`798a119d` 합의 일관성 유지).
- 시스템팀 답변 + 내일 morning 결과 후 α/γ 재판단 가능.
