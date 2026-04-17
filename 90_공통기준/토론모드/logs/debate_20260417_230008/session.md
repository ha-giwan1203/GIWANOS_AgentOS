# 토론 로그 — notebooklm-mcp 좀비 Chrome 근본 해결안 결정

- session_id: debate_20260417_230008
- chat_url: https://chatgpt.com/g/g-p-69bca228f9288191869d502d2056062c-gpt-keulrodeu-eobmu-jadonghwa-toron/c/69e202a2-2c98-83e8-96d4-85e9fe5fd425
- 시작: 2026-04-17 23:00 KST
- 참여: Claude (세션58) / GPT (프로젝트방)

---

## 배경

- 환경: Windows 11 + Claude Code + notebooklm-mcp (PleasePrompto/notebooklm-mcp, stdio)
- 증상: setup_auth 후 Chrome 10개 잔존 → 다음 세션 `ask_question` 시 `exitCode=21` (프로필 lockfile 점유) → taskkill + cleanup_data(preserve_library=true) + setup_auth 157초 반복
- 재발 세션: 57, 58

## 사전 조사

- `~/.claude.json`의 notebooklm-mcp `env={}` (빈 객체, 기본값만 작동)
- 기본 `NOTEBOOK_PROFILE_STRATEGY=auto`는 conflict 시 isolated 폴백이라 문서에 명시되나 실제 폴백 안 됨
- Playwright 공식 이슈 #35466·#24144: launchPersistentContext SingletonLock 잔존 다수 보고
- 영상 시연자도 동일 증상을 수작업 재인증으로 우회 (근본 해결 없음)

## 해결 옵션 (Claude 초안)

- A. env에 NOTEBOOK_PROFILE_STRATEGY=isolated 명시 — chrome_profile_instances/ 프로필 격리
- B. SessionStart hook에서 notebooklm-mcp Chrome taskkill — 쿠키·프로필 유지
- C. A+B 병행 (isolated + hook 안전망)
- D. MCP 포크 변경 (jacob-bd/notebooklm-mcp-cli 또는 Pantheon-Security/notebooklm-mcp-secure)

---

## 턴1 (Claude → GPT)

의제 전송: A/B/C/D 4개 옵션 + 4개 쟁점 제시, 선결 1개 + 검증 조건 1개 요청.

### 턴1 GPT 응답 요약

- 선결: **A**
- 판정: 조건부 통과
- 근거: 공식 설계 축(NOTEBOOK_PROFILE_STRATEGY/CLONE_PROFILE/chrome_profile_instances). B는 병렬 세션 끊기 위험, D는 비용 과다
- NOTEBOOK_CLONE_PROFILE은 기본값 유지 (이번 의제 핵심은 잠금 재발 중단, 쿠키 최적화 아님)
- 검증 조건: isolated 반영 후 새 세션 3회 연속 → 매회 get_health → ask_question 세트 수행 시 추가 setup_auth 없이 3회 모두 성공 + exitCode=21 0회 = 성공

### 턴1 하네스 분석

- 채택 6건 / 보류 0 / 버림 0
- (A 선택, B·D 배제, C 과잉설계, CLONE_PROFILE 기본값 유지, 검증 조건, 분기 순서)

---

## 턴2 (Claude → GPT) — 4개 보강 쟁점

- R1 세션 정의 모호 (프로세스 재기동 vs 같은 세션 turn)
- R2 setup_auth 허용 범위 (isolated 신규 프로필이므로 첫 인증 1회 불가피)
- R3 실패 분기 3갈래 확정 요청 (exitCode 재발 / 재인증 반복 / 둘 다)
- R4 B의 "다른 세션 끊기 위험" 재검토 (병렬 Claude 세션 시나리오 없음)

### 턴2 GPT 응답 요약

- 판정: 조건부 통과
- R1 확정: **Claude Code 프로세스 완전 종료·재기동 3회**
- R2 확정: **1세션 setup_auth 1회 허용, 2·3세션 재인증 없이 성공**이 PASS 기준
- R3 확정: 3갈래 분기. ③만 순서 조정 — **CLONE_PROFILE → B → A 폐기** 순 (덜 파괴적 옵션부터)
- R4 부분 인정: B는 근본 해결 아닌 운영 우회, A 우선 유지

### 턴2 하네스 분석

- 채택 4건 / 보류 0 / 버림 0

---

## 합의안 (최종)

1. **선결 옵션**: A (NOTEBOOK_PROFILE_STRATEGY=isolated)
2. **세션 정의**: Claude Code 프로세스 완전 종료·재기동 3회
3. **통과 기준**:
   - 1세션: setup_auth 1회 허용 (신규 isolated 프로필 인증)
   - 2·3세션: 재인증 없이 get_health → ask_question 성공
   - exitCode=21 0회
4. **실패 분기**:
   - ① exitCode=21만 재발 → B(SessionStart hook taskkill) 또는 NOTEBOOK_CLEANUP_ON_SHUTDOWN 재검증
   - ② 재인증만 반복 → NOTEBOOK_CLONE_PROFILE=true
   - ③ 둘 다 발생 → CLONE_PROFILE → B → A 폐기 순
5. **미합의 쟁점**: 없음

## 즉시 실행안

1. `~/.claude.json`의 notebooklm-mcp `env`에 `NOTEBOOK_PROFILE_STRATEGY=isolated` 추가
2. TASKS.md / HANDOFF.md에 세션59~61 검증 조건·실패 분기 등재
3. git commit + push → SHA 공유
4. GPT 최종 검증 요청 (4개 기준: env 실반영 / TASKS·HANDOFF 반영 / 커밋 diff / 3세션 결과)
5. 3세션 검증은 세션59부터 순차 수행 (이번 세션은 불가)

---

## GPT 최종 검증 기준 (GPT 확인 메시지)

- 커밋 SHA
- 반영 파일 목록
- 3세션 검증 로그 요약
- exitCode=21 발생 여부
- 재인증 발생 여부

충족 시 통과, 하나라도 비면 조건부 통과 또는 실패.
