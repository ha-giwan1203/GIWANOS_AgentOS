# Round 1 — 의제 정의

## 배경
세션90 Plan glimmering-churning-reef 단계 0+I+II 8커밋 누적. GPT 재검증 FAIL 판정("settings.json 여전히 옛 상태") 수령 후 로컬 Git 상태 실물 점검에서 이상 발견.

## 확인된 사실
1. **로컬 `refs/heads/main` 손상**
   - `git show-ref`: `refs/heads/main` = `0000000000000000000000000000000000000000`
   - `git reflog main`: `c99c9a16 main@{0}: commit: docs(session90)...` (정상)
   - `git symbolic-ref HEAD`: `refs/heads/main` (branch symlink 정상)
   - 현상: HEAD는 정상 커밋 가리키고 reflog도 살아있으나 ref 파일 값만 null

2. **원격 fetch 실패**
   - `git fetch origin main`: `fatal: bad object refs/heads/main ... did not send all necessary objects`
   - origin/main (cached): `ddcb252ae0d34c3b42894c25cb814f66c73e6d3a`
   - 로컬 HEAD와 무관한 SHA — 원격 상태 미확인

3. **Working tree 상태**
   - 대량 modified·deleted·untracked (별개 작업, 커밋 안 됨)

## 의제 2건

### 의제 1: 로컬 main ref 손상 복구 + 원격 push 방법
**선택지**:
- A. `git update-ref refs/heads/main c99c9a16` (reflog 값으로 loose ref 복원) → `git push origin main`
- B. 먼저 GitHub 웹 UI로 원격 refs 상태 확인 → ref 수리 방식 결정
- C. `git push --force-with-lease origin main` (원격에 로컬 HEAD 강제 push, 손상 ref 우회 시도)

**판정 요청**: 가장 안전한 경로 + 근거 1문장

### 의제 2: `.claude/commands/gpt-read.md` Step 1 drift 수정
**현재 상태** (10행):
> "ChatGPT 탭이 없으면: `.claude/state/debate_chat_url` 읽기 → navigate"

**문제**:
- `debate_chat_url`은 이전 토론 의제("토론모드 코드 분석")로 stale
- 사용자 피드백 메모리 `feedback_debate_mode_first_room.md` ("최신 대화로 바로 입장") 미반영
- 토론모드 CLAUDE.md 27행 규칙: "매 세션 시작 시 프로젝트 URL에서 최상단(최신) 채팅방을 자동 탐지하여 `debate_chat_url` 갱신" — 지금 gpt-read에 해당 로직 없음

**제안 변경안**:
1. 탭 없음 → 프로젝트 URL (`.../project`) navigate
2. DOM에서 `main a[href*="/c/"]` 최상단 href 추출
3. 해당 URL로 navigate + `.claude/state/debate_chat_url` 갱신
4. 최상단 탐지 실패 시 기존 `debate_chat_url` fallback

**판정 요청**:
- 이 수정안이 Step 절차 분기 변경(B 분류 — 3자 토론 승격 대상)인가?
- 변경안 자체 적절성 (통과/조건부/실패) + 근거
