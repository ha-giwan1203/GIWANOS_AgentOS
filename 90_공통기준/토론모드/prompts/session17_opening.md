## 세션17 의제: 문서 정비 + smoke_test 확장 + 취약점 모니터링

세션16 재평가(9.1/10)에서 도출된 다음 세션 안건 3개 + 추가 1건을 공유한다.

### 의제 1: CLAUDE.md 상태 원본 경로 명시
현재 CLAUDE.md "상태 원본" 섹션에 TASKS.md/HANDOFF.md가 파일명만 적혀있고 실제 경로(90_공통기준/업무관리/)가 없다. 매 세션 시작마다 파일 위치를 찾느라 헛돌게 되는 문제.
- 제안: 경로를 명시적으로 추가 (TASKS: 90_공통기준/업무관리/TASKS.md 등)
- 영향 범위: CLAUDE.md 1개 파일, 5줄 수정

### 의제 2: local_hooks_spec.md 아카이브 + 리다이렉트
90_공통기준/agent-control/local_hooks_spec.md가 Phase 1 미구현 훅(pre_write_guard, post_write_dirty, pre_finish_guard) 기준으로 멈춰있어 현행 19훅 체계와 완전히 불일치. .claude/hooks/README.md가 이미 현행 기준 문서 역할을 하고 있음.
- 제안: 구 spec을 98_아카이브/정리대기_20260411/로 이동, 원래 위치에 README.md 참조 리다이렉트 스텁 남김
- 판단 근거: README.md가 19훅 전체 + 실패 계약표 포함하므로 재작성은 중복

### 의제 3: smoke_test json_escape payload 테스트 3건 추가
현행 102개 테스트 중 grep 존재검사 68건, payload 기반 11건. json_escape()가 세션16에서 추가됐지만 실질 검증이 없음.
- 추가 대상:
  1. Windows 경로 백슬래시 (C:\Users\test\new를 C:\\Users\\test\\new로)
  2. 제어문자 LF+TAB+CR이 단일 라인 출력되는지 확인
  3. 혼합 입력(백슬래시+따옴표+개행) 동시 이스케이프 확인
- 예상: 102에서 105 테스트로 증가

### 의제 4: 동결 취약점 3건 모니터링 (읽기 전용)
- TOCTOU (handoff lock): 단일 스레드 가정 유효 확인
- execCommand: send_gate 차단 로직 유지 확인
- classification 소급: .req 파일이 UserPromptSubmit에서만 생성 확인

4건 모두 구현 전 의견을 구한다. 특히 의제 2(아카이브 vs 재작성)와 의제 3(테스트 케이스 적절성)에 대한 검토를 요청한다.
