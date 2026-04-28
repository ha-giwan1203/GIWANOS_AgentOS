# Round 1 — Claude 종합·설계안 (Step 6-5)

## 4-way 대조 요약 (round1_claude.md, GPT, Gemini, 양측 cross_verification)

| 안 | Claude 6-0 | GPT | Gemini | 합의 | 병합 사유 |
|----|-----------|-----|--------|------|-----------|
| (a) | 과잉설계 | 보류 | 보류 | **보류** | Claude=과잉설계는 즉각 버림 의향이지만 GPT·Gemini=보류는 Day 2+ 재검토 여지. 안전측 "보류"로 수렴 (DOM 의존 위험만 명시 + 즉시 채택 안 함) |
| (b) | 환경미스매치 | 버림 | 버림 | **버림** | 3자 일치 |
| (c) | (a)+(b) 단점 흡수 | 보류 | 보류 | **보류** | (a) 단점 + (b) 한계 결합 — 즉시 적용 불가 동일 |
| (d) | 채택 | 채택 통과 | 채택 | **채택** | 3자 만장일치 |

cross_verification:
- gemini_verifies_gpt: 동의 (불안정 DOM 의존성 배제, 실증된 _safe_goto 재사용 — 논리 지적)
- gpt_verifies_gemini: 동의 (최소성·실증성·잔존 차단 논리 정확 + 상태 동기화 재시도 보강)

## 채택 합의: (d) 단독

### 패치 범위 (run.py `navigate_to_d0` 168~177 수정)
```python
# OAuth 완료 명시 대기
if not _wait_oauth_complete(page, timeout_sec=30.0):
    print(f"[phase0] OAuth 완료 대기 30s 실패 — 현재 URL: {page.url}")
    if "auth-dev.samsong.com" in page.url and "/login" in page.url:
        print("[phase0] login 페이지 재도달 — 재로그인 1회 시도")
        ensure_erp_login(page)
        if not _wait_oauth_complete(page, timeout_sec=30.0):
            raise RuntimeError(f"OAuth 완료 2회 실패: {page.url}")
    elif "auth-dev.samsong.com" in page.url:
        # 신규: 클라이언트 선택 화면 등 비login auth-dev 정착 시 D0_URL 직접 이동 1회 시도 (오늘 수동 복구 패턴 코드화)
        print("[phase0] auth-dev 비login 정착 — D0_URL 직접 이동 1회 시도")
        _safe_goto(page, D0_URL)
        if not _wait_oauth_complete(page, timeout_sec=30.0):
            raise RuntimeError(f"OAuth 완료 실패: auth-dev 클라이언트 선택 화면에서 D0_URL 직접 이동 1회 시도 후에도 erp-dev 미도달 — 현재 URL {page.url}")
    else:
        raise RuntimeError(f"OAuth 완료 실패 (login 페이지 아님): {page.url}")
```

### 양측 답변 흡수 사항
- **GPT 보강**: 실패 메시지 구체화 ("OAuth 완료 실패: auth-dev 클라이언트 선택 화면에서 D0_URL 직접 이동 1회 시도 후에도 erp-dev 미도달")
- **Gemini 보강**: (d)는 단순 화면 우회를 넘어 내부망 통신 지연·브라우저 먹통으로 인증 콜백 상태가 누락된 경우 강제 재진입하는 "상태 동기화 재시도" 역할도 수행 — 가치 검증 보강
- **양측 일치**: D0_URL goto 후에도 auth-dev 잔류 시 즉시 실패 (DOM 자동 클릭 금지, 잔존 데이터 위험 회피)

### 변경 정량
- 변경 파일: 1개 (run.py)
- 변경 라인: 신규 elif 블록 ~5줄 (분기 1개 추가, 함수 신설 0)
- E 정량 적합 (≤20줄, ≤2파일, 신규 함수/hook/gate/settings 0)

### 약관/권한 부족 화면 처리 (critic WARN 보강)

신규 elif 블록 내 `_safe_goto(D0_URL)` 후 재대기 실패 시 raise 메시지에 현재 URL 동봉 → 후속 분석 시 약관/권한/타 클라이언트 화면 식별 가능. 별도 elif 분기로 약관·권한 화면을 자동 처리하지는 않음 — Gemini 지적 "잘못된 클라이언트/권한 상태 자동 진입은 잔존 데이터 위험" 원칙 준수. 사용자 수동 개입 트리거.

향후 약관/권한 화면이 반복 발생하면 별도 의제로 처리.

### claude_delta: partial
- 6-0 baseline 대비 양측 답변에서 추가 인사이트 흡수 (실패 메시지 구체화 + 상태 동기화 재시도 관점)
- 핵심 결정 (d) 단독은 동일

### issue_class: B
- 스킬 코드 실행 흐름·판정 분기 변경 (`_wait_oauth_complete` 실패 분기 내 신규 elif)
- B 분류이므로 6-5 수행 필수 (조건부 생략 불가)

### 검증 (다음 morning auto-run)
- 2026-04-30 07:10 `D0_SP3M3_Morning` LastResult=0
- `06_생산관리/D0_업로드/logs/morning_20260430.log` 정상 종료
- exit code = 0
