# 외부 모델 호출 (3-tool 합의안)

> 루트 `CLAUDE.md`에서 분리 (debate_20260428_201108_3way 빼는 안 1 / 세션122).
> 합의 원본: 2026-04-18 3-tool workflow 합의. 메모리 `project_three_tool_workflow.md`.

워크플로우 설계 주체는 항상 Claude. GPT/Gemini는 입력 제공자로만 호출.

## 도구 매핑

| 도구 | 호출 경로 | 사용 시점 |
|------|----------|----------|
| GPT (웹) | `/gpt-send`, `/gpt-read` | 토론, 추론·창의·아이디어 다변화, 반대논리 검증 |
| Gemini (웹) | `/gemini-send`, `/gemini-read` | 토론, 멀티턴 대화 |
| Gemini (CLI minion) | `/ask-gemini` | 빠른 단발 질의, WebFetch fallback, 대용량/멀티모달 |

## 원칙

- Claude가 호출 시점·입력·검증 절차를 설계
- GPT/Gemini 응답은 무결성 검증 후 채택 (실물 파일/Git/실증 데이터 대조)
- 도메인 한정 발상 금지 — 강점 기반 분담
- **상호 감시**: 3자 토론 시 단일 모델 단독 통과 금지 — GPT 답은 Gemini 검증, Gemini 답은 GPT 검증, Claude 설계는 양측 검증 (`90_공통기준/토론모드/CLAUDE.md` "상호 감시 프로토콜")

## /rewind 한계 (2026-04-18 3자 토론 합의)

- `/rewind`(Esc×2)는 **Claude가 만든 코드 변경만** 되돌린다. Git 대체재가 아니다.
- bash 명령으로 수행한 변경(`rm`, `mv`, `cp`, 외부 스크립트 실행, ERP/MES 업로드)은 **추적·복구 불가**.
- 저장소는 Bash 훅·외부 스크립트·G-ERP 연동이 많으므로, 중요한 변경은 반드시 `git commit` 후 작업한다.

## 문서 조회 우선순위 (2026-04-18 3자 토론 합의)

- **라이브러리/SDK/API 문서 조회**: `context7` MCP 우선 사용 (`mcp__context7__query-docs`, `resolve-library-id`). WebSearch는 fallback.
- **일반 리서치·최신 뉴스·사례 조사**: WebSearch 우선.
- 이유: context7은 공식 저장소에서 최신 버전별 문서를 가져와 학습 데이터 오래됨 문제를 해소한다.

## 설계 원칙 (Plan glimmering-churning-reef 안전안)

자기유지형 시스템의 7원칙은 `.claude/self/DESIGN_PRINCIPLES.md` 단일 원본을 따른다.
이전 Self-X Layer 1/2/4 + B5 Subtraction Quota 정책은 전면 폐기 (안전안 채택).
자세한 맥락: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` Part 2.

- 활성 hook 자동 집계: `bash .claude/hooks/list_active_hooks.sh`
- 주 1회 수동 점검: `bash .claude/self/selfcheck.sh`
- 보호 자산: `90_공통기준/protected_assets.yaml` (Self-X/quota 블록 제거됨)

## 운영 안정성

- settings/hook 파일 변경 후 반드시 세션 재시작 (변경사항은 세션 시작 시 캐싱됨)
- 장시간 세션 방치 금지 — 도메인/의제 전환 시 세션 재시작 권장
- 공통 모듈(hook_common 등) 수정 시 `grep -r` 호출부 전수 확인 선행
- 파일 변경 후 TASKS/HANDOFF 갱신을 커밋 직전에 함께 수행 (completion_gate 반복 방지)
- Windows PowerShell 세션에서는 `bash`가 PATH에 없을 수 있다. Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'` 또는 `C:\Program Files\Git\bin\bash.exe -lc '<command>'`를 사용한다.
