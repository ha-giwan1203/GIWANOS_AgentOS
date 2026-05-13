# Round 1 — Claude 독자 답안 (선행 작성, Step 6-0)

> 의제: kind-waddling-oasis PLAN(콘솔 fetch 가속) 사전 보강 4의제
> 시점: GPT·Gemini 답변 수령 전. 종속 방지.

## 결론 1줄

ChatGPT 콘솔 fetch는 **조건부 진입 (PoC 권장)**, Gemini는 **별도 PoC + 성공 확률 50% 가정**, ToS 위험 **낮음**, fallback 트리거에 **response schema 감지 추가 필요**.

## 의제 1. UI 자동화 병목 가설 검증

**주장**: 라운드 2~3분 중 모델 생성 시간은 **소수**(~30초), 나머지가 UI 자동화 overhead.
- (a) 모델 응답 생성: streaming 기준 5~30초 (실시간 토큰 표시)
- (b) chrome-devtools-mcp RPC 라운드트립: 각 호출 200~500ms × polling 수십 회 = 10~30초
- (c) stop-button polling 적응형 (3/5/8초 × 응답 길이): 1~2분 가능
- (d) 백그라운드 throttling 시 polling 응답 추가 지연: +30~60초
- (e) `select_page(bringToFront)` + 입력 fill + click overhead: 5~10초

콘솔 fetch 적용 시:
- (b) RPC 1회만 (evaluate_script 1콜)
- (c) polling 제거 — SSE reader가 응답 종료 직접 감지
- (d) throttling 무관 (콘솔 JS는 페이지 컨텍스트, throttling 영향 적음)
- (e) UI 자동화 0
- **예상 라운드 시간: 30~60초** (모델 생성 시간이 새 하한선)

**라벨**: 환경미스매치 — 현재 polling 방식 자체가 SPA streaming 패러다임과 안 맞음

**증거**: data-and-files/d0-production-plan `--http-only` 모드가 ERP 풀 자동화를 분~초로 단축한 동일 패턴

**예상 반대 약점**: 모델 생성 시간 측정치 없음. polling 분해 수치 추정. 실측 필요.

## 의제 2. PoC 실행 가능성 (ChatGPT + Gemini)

### ChatGPT
- `/backend-api/conversation` endpoint 실재 + SPA가 같은 endpoint 호출 중. **콘솔에서 fetch 호출 가능**
- 인증: `Authorization: Bearer <token>` — localStorage/쿠키에서 SPA helper 자동 주입. 같은 origin fetch는 브라우저가 헤더·쿠키 자동 첨부
- arkose challenge: ChatGPT Plus/Team에서 일부 요구. **SPA가 같은 페이지에서 이미 처리 중인 토큰**이므로 콘솔 fetch에도 자동 동봉됨
- SSE: `Accept: text/event-stream`. `r.body.getReader()` + `TextDecoder` 누적 — 표준 Web API
- **PoC 성공 확률: 80%+** (커뮤니티 스크립트 다수 실증)

### Gemini
- SPA 구조 다름. `/_/BardChatUi/data/...` 또는 새 endpoint 형태
- Google이 더 보수적 — POST payload protobuf 직렬화 또는 XSRF 토큰 동봉
- **PoC 성공 확률: 50%** — endpoint 캡처 + payload 형식 분석 부담 큼

**라벨**: 일부 실증됨 (ChatGPT) + 구현경로미정 (Gemini)

**예상 반대 약점**: ChatGPT 토큰 회전 빈도 자료 부족. arkose 자동 주입 실측 안 됨.

## 의제 3. ToS·계정 안전성

**주장**: 정지 위험 **낮음**.

근거:
- ChatGPT ToS 2.1 "automated/programmatic methods" 금지는 외부 스크립트·대량 호출·multi-account farming 대상
- 같은 origin·세션·쿠키·user-agent·IP → 외부에서 본 트래픽 패턴 = **사용자 화면 직접 입력과 동일**
- 호출 빈도: 토론 라운드 < 10회/세션, 라운드 간격 5~10초 → 인간 사용자 패턴 내
- 실제 정지 사례: 대부분 분당 수십~수백 호출 + 별도 IP 풀 + headless scraper. 단일 사용자 콘솔 fetch는 사실상 미검출

**위험 시나리오**:
- ChatGPT가 fingerprinting 강화 → `X-Requested-With` 헤더 분석 등 (현재는 SPA·fetch 둘 다 비송신이라 구분 안 됨)
- Gemini는 Google 보안 정책 더 엄격 — 향후 IP·디바이스 fingerprint 추가 가능

**완화책**:
- 라운드 간격 최소 5초 보장 (인간 타이핑 속도)
- 호출 빈도 모니터링 (`logs/console_fetch/call_rate.json`)
- 계정 정지 감지 시 즉시 UI fallback + 사용자 알림

**라벨**: 일반론 (구체적 정지 사례 자료 없음, 위험 평가만)

**예상 반대 약점**: Google ToS 별도 분석 안 됨. ChatGPT 향후 정책 변경 예측 불가.

## 의제 4. `--ui-fallback` 충분성

**제안 트리거 조건 (4종 + 1 보강)**:

1. **HTTP 4xx**: 401(인증 만료) → UI 경로로 토큰 재발급 + 재시도 / 403·429 → UI 즉시 전환
2. **HTTP 5xx**: 서버 오류 → 1회 재시도 → 실패 시 UI 전환
3. **SSE 타임아웃**: 30초 무수신 → 즉시 UI 전환
4. **404 endpoint**: SPA 변경 → UI 자동 복귀 + 사용자 알림 + 로그 critical
5. **(보강) Response schema 변화**: 응답 JSON 키 누락·타입 불일치 → schema_drift_count++ → 3회 도달 시 UI 자동 전환 + 사용자 알림

**임계값**:
- 세션 내 fallback 비율 > 30% → UI 모드 자동 전환
- 일주일 누적 fallback 비율 > 10% → 사용자 보고 (SPA 변경 가능성)

**로그 경로**: `logs/console_fetch/fallback_rate.json` + `schema_drift.json`

**라벨**: 보강 필요 — schema_drift 감지 추가 필수

**예상 반대 약점**: schema 변화 감지 로직 복잡도 증가. 임계값 30%·10%는 경험적 추정 (조정 가능).

## 종합 합의안 후보

**PoC 진입 권장 (조건부)**:
- Phase 1 ChatGPT PoC 먼저 — 성공 확률 80%
- Phase 2 Gemini PoC는 ChatGPT 성공 후 별도 — 성공 확률 50%
- Gemini 실패 시 부분 적용 (ChatGPT만 콘솔 fetch + Gemini는 기존 UI 유지)
- ToS 완화책 3종(라운드 간격·호출 빈도·정지 감지) 의무
- `--ui-fallback` 트리거 5종 (4 + schema_drift) + 임계값 30%/10%

**축소안 (Plan B)**:
- ChatGPT PoC FAIL 시 → 폴링 단축안(현재 3/5/8초 → 1/2/4초) + RPC 캐싱
- 가속폭 약 30~50% (분 단위 → 분 단위 절감)

**폐기 조건**: ChatGPT PoC FAIL + 폴링 단축 PoC FAIL 동시

## 착수·완료·검증 조건

**착수**: PoC Phase 1 ChatGPT endpoint 캡처 (10분)
**완료**: 라운드 시간 측정 < 60초 + 멀티턴 컨텍스트 유지 확인
**검증**: `--ui-fallback` 1회 강제 트리거 동작 확인 + 프로젝트방 채팅 히스토리 일치
