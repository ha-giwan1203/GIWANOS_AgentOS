# Round 2 Consensus — 보류 쟁점 4건 종결

> 토론: Round 2 / pass_ratio 4/4 = 1.0
> 일시: 2026-05-03 12:00 KST 전후
> 입력: Round 1 consensus.md + R5_dry_run_report.md + 사용자 결정(세트 A 안전 우선)
> 검증: gemini_verifies_gpt=동의 / gpt_verifies_gemini=동의(+4파일→단일파일 양보) / gpt_verifies_claude=동의 / gemini_verifies_claude=동의(+다음 행동 Phase 1 즉시 개시 권고)

---

## 합의 결론 (한 줄)

**4지표 목표 수치 채택 + 행동 교정 메타 0은 Gemini "출력의 건조함" 강화 + GLOSSARY 단일 플랫 파일 + RAG 영구 보류 가까운 기준. Phase 1 단일 PR 즉시 개시 권고.**

---

## 보류 쟁점 4건 종결 (Round 1 미합의)

### 쟁점 1. 사용자 생존 필수 3가지 (Gemini 질문) → **세트 A 안전 우선**
- 핵심 5개 hook (block_dangerous + protect_files + commit_gate + session_start_restore + completion_gate) 만 보존
- 31개 폐기 후보 전부 폐기

### 쟁점 2. 헤비유저 4지표 목표선 → **8지표 모두 확정**

| 지표 | 현재 | 목표 |
|------|------|------|
| Always-loaded 토큰 | ~7,100 | < 1,000 |
| rules/* | 300줄 5개 | 100줄 1개 |
| Slash command | 33개 | 5개 |
| Skill 평균 | 305줄 | 80줄 |
| Hook | 36개 | 5개 |
| Subagent | 9개 | 5개 |
| Permissions | 130개 | 15개 (포괄 패턴) |
| Worktree | 17개 | active 3개 |

### 쟁점 3. "행동 교정 메타 0" 경계 → **Gemini 강화 입장 채택**
- incident_quote.md는 흡수 없이 archive로만 (`98_아카이브/_deprecated_v1/rules/`)
- session_start_restore.sh는 deterministic 데이터(incident N건 / 24h 신규 N건 / git status)만 출력. 자연어 조언 금지
- completion_gate.sh는 통과/실패 + 누락 실물(staged file)만 보고. "반성하라"·"다음엔 이렇게 하라" 가이드 금지
- 핵심 원칙: **"출력의 건조함"** = 도구는 상태와 데이터만 말함, 판단·반성은 Claude가 MANUAL 보고 스스로

### 쟁점 4. GLOSSARY + RAG → **단일 플랫 시작 + RAG 영구 보류 가까움**
- GLOSSARY: 단일 파일 `90_공통기준/glossary/GLOSSARY.json`로 시작
- 비대화 트리거 시(500줄+ OR grep 누락 빈번) 4파일 분리 별건 plan
- RAG 보류 해제 트리거 4개 모두 만족까지 영구 보류 가까움

---

## Phase 8단계 확정 (Round 1 + Round 2)

| Phase | 작업 | 측정값 |
|-------|------|--------|
| 0 | R5 dry-run | ✅ 완료 |
| 1 | 단일 PR (동작 무변경 / baseline + _proposal_v2 골격 + main 태그) | 다음 |
| 2 | rules/* 5→1 통폐합 | 300→100줄 |
| 3 | hook 36→5 (카테고리 D 즉시 archive) | -31개 |
| 4 | Slash 33→5 (skill-rules.json 자동 매칭 엔진) | -28개 |
| 5 | Skill 평균 305→80 + GLOSSARY.json 신설 + MANUAL 분리 + verify 치환 | -4,725줄 (21개 평균) |
| 6 | Subagent 9→5 + Permissions 130→15 | -4 / -115 |
| 7 | Worktree 17→active 3 (archive→prune→verify) | -14 |
| 8 | 7일 측정 + 1차 평가 + 2차 조정 | 4지표 모두 목표선 진입 |

---

## 추가 강제 장치

1. **삭제 목표 수치를 PR 첫 커밋에 박기** (이후 추가 시 PR 거부)
2. **출력의 건조함 점검**: Phase 진행 중 hook/script가 자연어 가이드 출력하는지 매번 확인
3. **token_threshold_check.sh 활용**: always-loaded > 1,000 토큰 시 경고

---

## R1+R2 합산 검증 결과

| 라운드 | 검증 | 결과 |
|-------|------|------|
| R1 | gemini_verifies_gpt | 동의 |
| R1 | gpt_verifies_gemini | 동의 (+PR 통합) |
| R1 | gpt_verifies_claude_v2 | 동의 (v1 검증필요 → v2) |
| R1 | gemini_verifies_claude_v2 | 동의 |
| R2 | gemini_verifies_gpt | 동의 |
| R2 | gpt_verifies_gemini | 동의 (+4파일 양보) |
| R2 | gpt_verifies_claude | 동의 |
| R2 | gemini_verifies_claude | 동의 |

**전체 8/8 동의. pass_ratio 1.0**.

---

## 다음 행동 (양측 권고)

**Gemini**: "합의된 8단계 Phase에 따라 Phase 1(단일 PR 및 골격 구축) 작업을 즉시 개시하십시오."

**GPT**: 동의 (Round 1 v2부터 일관 권고).

**사용자 결정 사항**: Phase 1 단일 PR 작성 진행 여부.
