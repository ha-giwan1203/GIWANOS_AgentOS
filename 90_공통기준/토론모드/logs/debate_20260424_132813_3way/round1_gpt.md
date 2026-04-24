# Round 1 — GPT (gpt-5-5-thinking)

Q1. A안 선택
기존 Stop 계열 블록에 추가하는 게 맞습니다. auto_commit_state.sh는 Stop 5번째 hook이고, 성격도 세션 종료 상태문서 처리라 별도 계열 신설은 문서 구조만 복잡하게 만듭니다.

Q2. B안 선택
final_check --fast 실패 시 자동 push 차단은 이미 들어갔으니, incident 기록까지 남기는 게 낫습니다. 나중에 "왜 자동 커밋 안 됐지?" 추적하려면 stderr 한 줄보다 incident가 훨씬 덜 짜증납니다.

Q3. A안 선택
hook_advisory 래핑이 맞습니다. auto_commit_state는 Stop hook이지만 정책상 advisory이고, hook_gate로 올리면 Stop 자체 차단 의미가 생겨 기존 "실패해도 세션 계속" 계약과 충돌합니다.

Q4. B안 선택
문서 보강(P-1/P-2)과 hook_common 래핑은 분리 커밋이 맞습니다. 앞의 둘은 계약 문서 수정이고, wrapper 적용은 실행 파일 변경이라 회귀 추적 단위가 다릅니다.
