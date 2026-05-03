# Round 2 — Claude 종합·설계안 (Step 6-5)

> 입력: round2_claude.md(선행) + round2_gpt.md + round2_gemini.md + round2_cross_verify.md
> issue_class: B (구조 변경)
> skip_65: false
> claude_delta: partial (선행 답안 방향 일치, GPT의 completion_gate 축소 + Gemini의 흡수 반대·단일 플랫 흡수)
> round_count: 2 / max_rounds: 3

---

## Round 2 4-way 합의 결론 (한 줄)

**4지표 목표 수치는 그대로 채택. 행동 교정 메타 0은 Gemini 입장(흡수 반대 + 출력의 건조함)으로 강화. GLOSSARY는 단일 플랫 파일로 시작 + 비대화 트리거 시 분리. RAG는 영구 보류 가까운 기준.**

---

## 합의 사항

### R2-1. 헤비유저 4지표 목표선 (전부 동의)

| 지표 | 현재 | 목표 | 실행 절차 |
|------|------|------|---------|
| Always-loaded 토큰 | ~7,100 | **< 1,000** | rules/* + CLAUDE.md 통폐합 |
| rules/* | 300줄 5개 | **100줄 1개** | 5→1 통폐합 |
| Slash command | 33개 | **5개** | skill-rules.json 자동 매칭 엔진 활용 |
| Skill 평균 | 305줄 | **80줄** | MANUAL.md + GLOSSARY + verify script 분리 (GPT 조건부) |
| Hook | 36개 | **5개** | 핵심 5개만 보존 (사용자 세트 A) |
| Subagent | 9개 | **5개** | 도메인 검증 위주 |
| Permissions | 130개 | **15개** | 포괄 패턴 중심 |
| Worktree | 17개 | **active 3개** | archive/backup → prune → verify (GPT 절차) |

**실행 순서 (양측 모두 동의)**:
1. baseline 기록
2. archive/backup
3. prune
4. verify

### R2-2. 행동 교정 메타 0 — Gemini 강화 입장 채택

**보존 (안전·기능 deterministic 장치만)**:
- block_dangerous.sh — 위험 명령 차단
- protect_files.sh — 보호 파일 차단
- commit_gate.sh — final_check 통과 후 commit/push
- session_start_restore.sh — **deterministic 데이터만 출력** (incident N건 / 24h 신규 N건 / git status / TASKS·HANDOFF 상단). **자연어 조언 출력 금지**
- completion_gate.sh — **통과/실패 + 누락 실물(staged file)만 보고**. **"반성하라"·"다음엔 이렇게 하라" 가이드 금지**

**폐기 (행동 교정·자연어 가이드)**:
- 카테고리 D 권위 명제 강제 6개 — 즉시 폐기 (instruction_read_gate / skill_instruction_gate / r1r5_plan_check / risk_profile_prompt / permissions_sanity / skill_drift_check)
- 카테고리 A 토론모드 6개 — 토론 SKILL.md 자체 검증으로 대체
- 카테고리 B 도메인 의무 검증 6개 — write_router_gate만 핵심 5개에 통합 가능 검토
- 카테고리 C 자동 후속 7개 — 사용자 명시 발화 시만 수행
- 카테고리 E 외부 알림 3개 — 수동 호출
- 카테고리 F stop guard 잔여 2개 — completion_gate 흡수
- 카테고리 G PreCompact·Date 2개 — date_scope_guard 폐기, precompact_save 보존(토론 손실 방지)

**incident_quote.md 처리** (Gemini 입장 채택):
- rules/*에서 폐기
- **흡수 없이 archive로만** 보존 (`98_아카이브/_deprecated_v1/rules/incident_quote.md`)
- session_start_restore.sh에 자연어 조언 추가 금지
- 필요 시 incident_repair.py 출력 결과를 사용자가 읽고 직접 판단

**핵심 원칙**: 시스템 어떤 출력물에서도 **"AI 행동을 훈계하는 자연어"**가 섞이지 않도록 '**출력의 건조함**' 유지. 도구는 오직 **상태와 데이터**만 말함. 판단·반성은 Claude의 순수 추론 엔진이 MANUAL을 보고 스스로 수행.

### R2-3. GLOSSARY 단일 플랫 파일 + RAG 영구 보류 가까운 기준

**GLOSSARY 채택 안** (Gemini 단일 + GPT 트리거 조건 절충):
- 시작: 단일 플랫 파일 `90_공통기준/glossary/GLOSSARY.json`
- 내용: 제조 용어 / 라인 약어 / 공정명 / ERP·MES 필드명 / 품번 suffix 규칙 / SUB·OUTER·ASSY 관계 / 자주 헷갈리는 한국어·영문 표현
- **넣지 말 것**: 업무 절차 / Claude 행동 규칙 / 토론 규칙 / 완료 판정 / 세션 이력
- 형식: 짧고 기계가 읽는 데이터. 설명형 풀이 금지

**비대화 트리거 시 4파일 분리** (GPT 안 보존):
- 트리거 조건: GLOSSARY.json 500줄 초과 OR 도메인 검색 시 grep 누락 빈번
- 분리 안: GLOSSARY.json + LINE_CODES.json + PROCESS_CODES.json + PARTNO_RULES.json
- 분리 결정 시 별건 plan

**RAG 영구 보류 가까운 기준** (양측 동의):
- 보류 해제 트리거 (모두 만족 시):
  - manual/glossary 50개 이상으로 증가
  - grep/read 검색 시간 반복적으로 3분 이상
  - 용어 오판 incident 7일간 5건 이상
  - 동기화/색인/권한 관리자 명확
- 그 전에는 Grep + Glob + Read + manual로 충분

---

## R5 통과 확정 (사용자 세트 A 결정 + Round 2 강화)

R5 dry-run 통과 기준 3개 모두 충족:
1. ✅ 핵심 5개 hook 부재 시 깨지는 동작이 사용자 세트 A 결정 안에 100% 포함
2. ✅ 도메인 스킬 5개 dry-run 성공 (.claude/hooks 의존도 0회)
3. ✅ session_start hook 새 골격 전환 가능

**Round 2 강화**: session_start_restore.sh + completion_gate.sh도 **자연어 가이드 출력 금지**로 추가 제약. 보존하되 "출력의 건조함" 유지.

---

## Phase 8단계 (consensus.md + Round 2 확정)

| Phase | 작업 | 목표 측정값 | 양측 동의 |
|-------|------|-----------|---------|
| 0 | R5 dry-run | (완료) | ✅ |
| 1 | 단일 PR (동작 무변경) | baseline 기록 + _proposal_v2/ 골격 + main 태그 | ✅ |
| 2 | rules/* 5→1 통폐합 | 300줄 → 100줄 | ✅ |
| 3 | hook 36→5 | 31개 archive (카테고리 D 즉시) | ✅ |
| 4 | Slash 33→5 | skill-rules.json 자동 매칭 엔진 도입 | ✅ |
| 5 | Skill 평균 305→80 + GLOSSARY 분리 + MANUAL 분리 + verify 치환 | 단일 GLOSSARY.json 신설 | ✅ |
| 6 | Subagent 9→5 + Permissions 130→15 | 포괄 패턴 통폐합 | ✅ |
| 7 | Worktree 17→active 3 | archive/backup → prune → verify | ✅ |
| 8 | 7일 측정 + 1차 평가 + 2차 조정 | 4지표 모두 목표선 진입 | ✅ |

---

## 미합의·보류 (Round 3 의제 후보)

> Round 2 합의로 모든 보류 쟁점 해소. Round 3 신규 의제는 발생 시점에 결정.

검증 후 발생 가능 의제:
- Phase 5 진행 시 Skill 80줄 압축 실패 케이스 (line-batch-management 714줄 같은 큰 파일)
- Phase 7 Worktree 활성/비활성 분류 기준 (사용자 결정 영역)
- 단일 GLOSSARY 비대화 시 4파일 분리 결정 (보류 트리거 만족 시)

---

## 즉시 실행안 5개 (Round 1 4개 + Round 2 신규 1개)

1. **R5 dry-run report 양측 검증** (신규)
2. R5 통과 후 **단일 PR 작성** (Phase 1)
3. **Phase 2-8 순차 진행**
4. **삭제 목표 수치를 PR 첫 커밋에 박기** (이후 추가 시 PR 거부)
5. **출력의 건조함 점검** — Phase 진행 중 hook/script가 자연어 가이드 출력하는지 매번 확인 (Gemini 강조 원칙)
