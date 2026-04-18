# Round 1 — GPT 응답 (의제1 /schedule 분류 매트릭스)

## 요약
1. **매트릭스 반쯤 맞음**. 4칸 현 초안은 "원격 Cloud /schedule 전용 분류"로는 대체로 맞음. Desktop 스케줄은 로컬 파일·도구 직접 접근 가능. "로컬=불가"는 원격 기준에서만 맞음. 제목을 "원격 Cloud /schedule 분류표"로 변경 필요.

2. **4칸 앞에 1차 게이트 추가**: Cloud / Desktop / /loop (실행 모드 게이트) → 2차 4칸(GitHub-only/커넥터/로컬실물/사내망). 5번째 "하이브리드" 축 신설보다 실행 모드 게이트가 정확.

3. **Phase 1 3건 더 보수적으로**:
   - self-audit, doc-check 가장 안전
   - memory-audit: 읽기 전용이면 포함, MEMORY 수정·정리·커밋 흐름이면 Phase 1 제외
   - Cloud 작업은 fresh clone + 기본 브랜치 시작 + `claude/` 접두 브랜치에만 push 허용 → 읽기 위주/리포트 위주부터

4. **커넥터 Phase 2로**. NotebookLM은 "Cloud connector 실증 후 편입" 명시.

## 최종 권고안
- 매트릭스 제목 변경: "원격 Cloud /schedule 분류표"
- 1차 실행 모드 게이트 추가: Cloud / Desktop / /loop
- Phase 1: 읽기 전용 3종 (/doc-check, /self-audit, /review-claude-md 또는 읽기 전용 memory-audit)
- 커넥터는 Phase 2로
- 자동 수정·반영류는 원격 1차 파일럿에서 제외 (fresh clone + 브랜치 제약 + main 직행 상충)

## 한 줄 결론
4칸 자체보다 "원격이냐 로컬이냐" 1차 게이트 누락이 핵심 구멍. Phase 1은 읽기 전용 GitHub-only 3종으로 시작이 가장 안전.
