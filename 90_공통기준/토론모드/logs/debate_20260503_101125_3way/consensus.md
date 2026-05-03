# Round 1 Consensus — Claude Code 환경 리모델링

> 토론: Claude × GPT × Gemini 3자 / Round 1 / pass_ratio 4/4 = 1.0
> 일시: 2026-05-03 10:11 KST 시작
> 입력자료: `C:/Users/User/.claude/plans/luminous-skipping-teapot.md`
> 검증 통과: gemini_verifies_gpt=동의 / gpt_verifies_gemini=동의 / gpt_verifies_claude_v2=동의 / gemini_verifies_claude_v2=동의

---

## 한 줄 합의 (4-way)

**현재 환경 실패의 본질은 행동 교정형 메타 시스템 자체의 효과 부재 + 그것이 만든 인지적 부채. 해법은 메타 레이어를 결정론적 도구·코드로 치환하고 도메인 자산을 보존·격리하는 Option 3 Hybrid. 진입은 R5 dry-run 선행 → 단일 PR(동작 무변경) → Phase별 점진 8단계.**

---

## 합의 사항

### 1. 실패 정의
- incident 1346건 자체가 실패 아님
- 실패의 본질 = "**관리비용 역전** + **인지적 부채**" (사용자 개입량·운영 에너지 > 자동화 이득)
- 측정 지표 4개:
  - Always-loaded 토큰 (현재 ~7,100 → 목표 < 1,000)
  - 사용자 판단 생략 횟수
  - 지침 문서 삭제량
  - 분노 사이클(같은 지적 반복 빈도)

### 2. 모델 한계 vs 셋팅 한계
- spec drift / 장기 지침 준수 / 자기교정 / 결정 회피 = 모델 한계 영역. 셋팅 보완 불가.
- 행동 교정 메타 추가 = Claude에게 **독(Poison)**으로 작용해 인지적 마비 유발.
- **셋팅으로 박아도 되는 영역**: 파일 접근 / 원본 보호 / 위험 명령 차단 / 실행 표준화 / 검증 자동화 / worktree·sandbox 분리
- **박는 것 금지 영역**: 장기 규칙 준수 명제 / 행동 성향 교정 / 자기반성 자동 개선 / 의도 추론 / 메타 우선순위 충돌 해소 / "결정 위임 금지" 같은 명제형
- 치환 원칙: 행동 교정 문구 → **결정론적 도구·코드** (Permission / Hook / Python verify)

### 3. 헤비유저 컨센서스 도메인 적합성
- 100줄 룰·hook 4-5개·subagent 5개·slash 5개는 **메타 계층에만** 적용
- 도메인(제조 ERP·MES)은 별도 manual / verify / rollback (또는 GLOSSARY.json + RAG) 분리

**메타 계층 목표선**:
- CLAUDE.md 100~200줄
- Hook 4-5개 (위험차단 + formatter + sessionstart + 측정 + completion)
- Subagent 5개 이하
- Slash command 5개 이하
- Permissions 15개 이하 (포괄 패턴만)
- Always-loaded < 1,000 토큰

**도메인 계층 (보존·결정론화)**:
- MANUAL.md 길이 자유 (사용자 지식 보존)
- SKILL.md = 절차 + verify 호출만
- ERP/MES 등록 = dry-run / list-only / commit / verify / rollback 5단계 강제
- Claude는 판단자 아닌 **실행 대행자** (판단 근거는 verify.py 리턴값)
- 한국어 제조업 용어·품번·라인·공정코드 → glossary 분리 (RAG 식 호출)

### 4. Option 우선순위
1. **Option 3 Hybrid 2-Layer** (1순위 채택)
2. Option 5 부분 채택 (ERP/MES 핵심 자동화는 순수 Python)
3. Option 4 장기 목표 ("행동 교정 메타 0"으로 재정의 — 안전 기능은 보존)
4. Option 1 임시 완충안
5. Option 2 폐기 (도메인 자산 손실 위험)

### 5. PR 진입 방식 (양측 보완 흡수)

**Phase 0 — R5 dry-run 강제 단계** (단일 PR 작성 이전):
1. 별도 worktree 생성 (`.claude/worktrees/dry-run-reset/`)
2. `.claude` 통째 → `_deprecated_v1/` 이동 시뮬레이션
3. session_start hook 실행 + 핵심 5개 hook 부재 시 깨지는 동작 목록화
4. 도메인 스킬 5개 (settlement / line-batch / d0-plan / jobsetup-auto + 1) dry-run
5. 결과를 `R5_dry_run_report.md`로 출력 + 양측 검증
6. 통과 기준: 깨지는 동작이 사용자 사전 정의한 "**생존 필수 3가지**" 안에 없음 + 도메인 스킬 5개 dry-run 성공 + session_start 새 골격 정상 전환
7. 실패 시: 보강 후 재검증 또는 Option 4 부분 적용으로 폭 축소

**Phase 1 — 단일 PR (동작 무변경)**:
- main에 `stable-before-reset` 태그 생성
- `.claude/` 통째 백업 (별도 위치 사본)
- 새 폴더 골격 생성 (`.claude/_proposal_v2/` 격리 영역에 새 메타 구조 초안만)
- 측정 베이스라인 기록 (현재 always-loaded 토큰 / rules/* 줄 수 / Slash 수 / Skill 평균 / Hook 수 / Worktree 수 / incident 누적)
- **활성 hook/settings/commands/skills 파일은 한 줄도 수정·이동하지 않음**

**Phase 2-9 — 점진 8단계 (실제 동작 변경, 각 단계 별도 PR + 측정값 비교 + 롤백 가능)**:
- Phase 2: rules/* 5개 → 1개 통폐합
- Phase 3: hook 약 45개 → 핵심 5개
- Phase 4: Slash 33개 → 5개 (자동 매칭 엔진으로 이전)
- Phase 5: Skill 21개 평균 305줄 → 80줄 압축
- Phase 6: Subagent 9개 → 5개
- Phase 7: Permissions 130개 → 15개 포괄 패턴
- Phase 8: Worktree 17개 → 사용자 결정 후 prune
- Phase 9: 7일 측정 + 1차 평가 + 2차 조정

### 6. R5 롤백 계획
- main `stable-before-reset` 태그 + `.claude` 백업 + `_deprecated_v1/` 이동
- 도메인 코드 (`05_생산실적/조립비정산/`, `10_라인배치/` 등) 직접 수정 금지
- 리모델링 기간 ERP/MES 실등록은 dry-run / list-only 우선
- 운영 등록 script는 기존 stable 경로 유지
- 실패 시 `.claude` 백업 복원 + tag checkout

### 7. 시스템적 강제 장치
- 측정 hook 1개 신설 (예: 기존 `token_threshold_check.sh` 활용)
  - always-loaded 토큰 > 1,000 시 경고
- 점진 적용 안티패턴 차단: "삭제 목표 수치"를 PR 첫 커밋에 박고 그 이후 추가 시 PR 거부

---

## 미합의·보류 쟁점 (Round 2 의제)

1. **사용자 답변 필요**: 17개 worktree와 약 45개 hook 중 "**이게 없으면 당장 내일 업무 마비**"라고 확신하는 **생존 필수 기능 딱 3가지** (Gemini가 사용자에게 던진 질문)
2. 헤비유저 4지표 목표선 구체 수치 — 사용자 답변 후 결정
3. "행동 교정 메타 0"의 경계 — `incident_quote.md` 같은 안전 가이드는 어느 쪽인지
4. **GLOSSARY.json + RAG 도입 여부** — Gemini만 명시 제안. GPT는 manual + verify로만

---

## 즉시 실행안 4개

1. **R5 dry-run 실측** (단일 PR 이전 강제, 별도 worktree)
2. **R5 통과 후 단일 PR 작성** (골격 + 격리 + 태그 + 측정 베이스라인 / 동작 무변경)
3. **Round 2 의제 정리** (생존 필수 3가지 + 보류 쟁점 4건)
4. **삭제 목표 수치 확정** (Phase별)

---

## 검증 결과 요약

| 검증 | 결과 | 검증자 → 대상 |
|------|------|---------------|
| 1 | 동의 | Gemini → GPT 본론 |
| 2 | 동의 | GPT → Gemini 본론 (+ PR 통합 자동 도출) |
| 3 v1 | 검증 필요 → v2 동의 | GPT → Claude 종합 |
| 4 v1 | 동의 → v2 동의 | Gemini → Claude 종합 |

**pass_ratio (전체 4건)**: 4/4 = **1.0**
**pass_ratio (Claude 종합 v2 검증만)**: 2/2 = **1.0**

→ Round 1 합의 종결. Round 2는 사용자 답변(생존 필수 3가지) 수신 후 진행.

---

## 핵심 메시지 (양측 합의)

> **"새 규칙이 아니라 새 구조가 필요하다."** (GPT)
> **"7,000토큰 시스템 프롬프트는 Claude를 인지적 마비 상태로 몰아넣는다. 잔소리를 지워내어 순수 추론 엔진에 깨끗한 공기를 불어넣어야 한다."** (Gemini)
> **합의: 행동 교정 문구 추가는 누적 부패의 시작점. 결정론적 도구·코드로 치환.**
