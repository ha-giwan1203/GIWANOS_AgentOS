# 잡셋업 하이브리드/API 전환 — 시나리오 판정

> 상위 plan: `C:\Users\User\.claude\plans\wiggly-gliding-sundae.md`
> 캡처 산출물: `state/traffic_capture_20260501.md`
> 작성일: 2026-05-01
> 상태: **시나리오 3 강력 후보 (페이로드 미확인 단서 1건 잔존)** — 2026-05-01 17:36~17:38 KST 실측 (사용자 권한 TCP 폴링)

## 0. 비교 기준 (생산계획 하이브리드 PoC)

| 항목 | 생산계획 (확정) |
|------|---------------|
| 핵심 함수 | `build_requests_session_from_page()` `refresh_xsrf_from_cookies()` `api_rank_batch()` (`d0-production-plan/run.py:830-977`) |
| 인증 | OAuth → Playwright cookie + XSRF-TOKEN → `requests` Session 동봉 |
| 필수 헤더 | `ajax: true`, `Content-Type: application/json; charset=UTF-8`, `X-XSRF-TOKEN` |
| 안전 가드 | `sendMesFlag='N'` 강제, `mesMsg` 비면 break, `--no-mes-send`, timeout=30 |
| Fallback | `--legacy-mode` 화면 모드 즉시 복귀 |

이 패턴을 잡셋업이 따를 수 있는지가 판정 핵심.

---

## 1. 시나리오 1 — 완전 하이브리드 가능

**조건 (전부 만족 시 채택)**:
- [ ] mesclient.exe → 표준 HTTP/HTTPS 트래픽 관찰됨
- [ ] 인증 토큰/세션쿠키 추출 가능 (Cookie 헤더 또는 Authorization Bearer)
- [ ] 잡셋업 저장(검사항목 등록) endpoint 식별됨
- [ ] Request body 구조 사람이 읽을 수 있는 JSON/XML/form

**구현 개요**:
1. mesclient 로그인 후 인증 정보 추출 경로 확정 (3가지 후보):
   - (a) mesclient 가 system proxy 따른다면 Fiddler 통해 토큰 sniff 후 환경변수 주입
   - (b) SmartMES 웹 포털 별도 존재 시 → Playwright 로그인 → cookie 흡수 (생산계획과 동일)
   - (c) 둘 다 안 되면 mitmproxy 상시 운영 (운영 부담 큼 → 시나리오 2 격하 권고)
2. `requests` Session 구성 (`build_smartmes_session()` 신규 함수)
3. 잡셋업 저장 호출 (`api_jobsetup_save()`) 구현
4. 안전 가드 (생산계획과 동일):
   - dry-run 모드 기본값 유지
   - 저장 직전 1줄 사용자 확인 (`--commit` 시에만)
   - timeout=30, 응답 검증

**예상 공수**: 3~5일

**판정**: ⬜ 채택 / ⬜ 보류 / ⬜ 기각

판정 근거 (캡처 라인 인용):

---

## 2. 시나리오 2 — 부분 하이브리드 (조회만 API)

**조건**:
- [ ] HTTP 트래픽은 관찰되나 저장은 RPC/암호화/.NET Remoting
- [ ] 또는 저장 endpoint는 보이나 request body 가 직렬화된 binary blob (재현 위험)

**구현 개요**:
1. 제품·공정·검사항목 마스터 조회만 `requests` 화 (`api_smartmes_query()`)
2. 입력은 기존 좌표 자동화 유지 (`run_jobsetup.py:169-194`)
3. 효과: 멀티 공정·검사항목 확장 시 마스터 데이터 준비 속도 향상. 좌표 의존성은 남음.

**예상 공수**: 2~3일

**판정**: ⬜ 채택 / ⬜ 보류 / ⬜ 기각

판정 근거:

---

## 3. 시나리오 3 — 하이브리드 불가

**조건 (하나라도 해당 시)**:
- [ ] 트래픽 dump 에 HTTP 요청 0건
- [ ] 통신이 .NET Remoting / WCF NetTcpBinding / gRPC + 클라이언트 인증서
- [ ] Application-level 암호화로 request body 재현 불가

**대안 작업**:
- `pywinauto` (UI Automation framework) PoC — 좌표 의존성 제거. 컨트롤 ID/AutomationId 기반 입력
- mesclient.exe가 WPF/WinForms 인지에 따라 가능 여부 갈림
- 본 plan 종료. 별도 plan `PLAN_PYWINAUTO_POC.md` 작성

**판정**: ⬜ 채택 / ⬜ 보류 / ⬜ 기각

판정 근거:

---

## 4. 최종 판정 (2026-05-01 실측)

- **채택 시나리오**: 시나리오 3 강력 후보 (페이로드 미확인 단서 1건 잔존 → B 옵션 선택 시 시나리오 1/2 재평가 가능)
- 판정일: 2026-05-01 17:38 KST
- 판정자: Claude (실측 데이터 기반)
- 근거 요약:
  - 표준 HTTP/HTTPS endpoint 0건 (생산계획 하이브리드 전제 미성립)
  - 단일 사내 서버 + 비표준 포트 3개(6379/18100/19220)만 사용
  - Redis 직접 연결 + 단발 RPC 패턴
  - 상세: `state/traffic_capture_20260501.md`
- 다음 plan 경로 (사용자 결정 대기):
  - A. `pywinauto` PoC plan 작성 (좌표 의존성 제거)
  - B. 관리자 권한 PktMon 1회 추가 캡처 (페이로드 형태 확정)
  - C. 현 좌표 자동화 유지, 하이브리드 포기
