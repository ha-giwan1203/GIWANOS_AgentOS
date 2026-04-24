# Round 1 — GPT (웹 UI)

Q1: **B안: 조건부 격상**

근거: final_check FAIL = 무조건 exit 2는 과합니다. 현재 구조는 이미 commit/push를 차단하므로 데이터 오염은 막고 있습니다. 다만 동일 원인 반복, 상태문서 미갱신 반복, TASKS/HANDOFF/STATUS 불일치 같은 명확한 상태 원본 불일치가 누적되면 Stop 차단으로 격상하는 게 맞습니다.

Q2: **B안: 그렇지 않다 — advisory + 가시성 강화가 우선**

근거: Stop hook exit 2는 세션 종료를 막는 강한 조치라, 일시적 final_check 오류나 로컬 환경 문제까지 세션 블록으로 이어질 수 있습니다. 현 단계에서는 exit 0 유지 + incident/hook_log/timing 기록 + stderr 가시성 강화가 더 안전합니다.

결론: 즉시 hook_gate 격상 반대. 조건부 격상 설계는 채택.
