# 토론 세션 debate_20260417_235521

의제: 세션59 notebooklm-mcp 검증 — 좀비 Chrome 해결(isolated PASS) / ask_question 셀렉터 실패 분리 대응

## Turn 1

### Claude (의제 + 독립 판단)

사실 10건:
- NOTEBOOK_PROFILE_STRATEGY=isolated 반영
- 첫 setup_auth 2회 실패(브라우저 안 뜸)
- 좀비 Chrome 아님(lockfile 없음)
- cleanup_data(preserve_library=true)로 41MB 삭제, Legacy+Current 둘 다 포함
- cleanup 후 setup_auth 103.74초 성공
- list_notebooks 빈 배열 → library.json 소실
- 노트북 2개 수동 재등록
- ask_question "chat input 찾지 못함" 오류(타임아웃/show_browser/단순 질문 모두 실패)
- MCP 1.2.1 = 최신
- exitCode=21 관측 안 됨

Claude CLAIM:
- A. isolated 1세션 검증은 부분 PASS(cleanup 선행 조건 발생)
- B. 세션60·61 재인증 없음은 다음 세션에서 확인 필요
- C. ask_question 실패는 좀비 Chrome과 별개(list_notebooks 성공이 증거)
- D. preserve_library 부작용은 MCP 1.2.1 자체 버그

### GPT (조건부 통과)

- Q1: 조건부 통과 — isolated+cleanup 후 인증·라이브러리 회복, ask_question 본검증 미완료
- Q2: 별건 분리 맞음 — list_notebooks 성공은 통신·인증 정상 증거
- Q3: ① show_browser DOM 실물 확보 → ④ 다른 노트북 교차 테스트 → ② GitHub 이슈 검색 → ③ 1.2.0 롤백(마지막)
- Q4: 별도 안건화 필요 — cleanup 보호 범위와 실동작 불일치

실무 구분:
- 세션59 판정: 조건부 통과
- TASKS 분리 3건: 좀비 Chrome 3세션 검증 계속 / ask_question 입력창 탐지 실패 / preserve_library 보호 누락
- 다음 액션: DOM/화면 실물 확보 → 다른 노트북 URL 교차 테스트 → 이슈 검색/리포트 → 필요 시 1.2.0 롤백

### Harness

- 채택 4 / 보류 0 / 버림 0
- Claude CLAIM A~D ↔ GPT Q1~Q4 전부 일치, 1턴 조기 합의

## 최종 합의

1. 세션59 조건부 통과 기록
2. TASKS에 분리 등록 3건
3. 다음 액션 우선순위 ①→④→②→③
