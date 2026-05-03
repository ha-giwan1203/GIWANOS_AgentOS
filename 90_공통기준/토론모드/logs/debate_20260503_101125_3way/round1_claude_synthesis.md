# Round 1 — Claude 종합·설계안 (Step 6-5)

> 입력: round1_claude.md(선행) + round1_gpt.md + round1_gemini.md + 2건 cross_verify (양측 모두 "동의")
> issue_class: **B** (구조 변경 — 메타 레이어 전면 리셋)
> skip_65: **false** (B 분류는 무조건 6-5 유지)
> claude_delta: **partial** (선행 답안 방향 일치, Gemini의 "독성" 진단 + GPT의 PR 통합 안 흡수)

---

## 4-way 합의 결론 (한 줄)

**현재 환경 실패의 본질은 "행동 교정형 메타 시스템 자체의 효과 부재 + 그것이 만든 인지적 부채"이며, 해법은 메타 레이어를 결정론적 도구·코드로 치환하고 도메인 자산을 보존·격리하는 Option 3 Hybrid이다. 진입 방식은 단일 PR로 골격·격리·측정 기준만 일괄 반영하고, 세부 이식은 8단계 Phase로 점진 적용한다.**

---

## 의제별 합의안

### 의제1. 실패 정의 = "관리비용 역전 + 인지적 부채"

- **합의**: incident 1346건 자체가 실패 아님. 실패의 본질은 (a) 사용자 개입량과 운영비용이 줄지 않은 상태(GPT) + (b) 시스템 유지보수 에너지 > 자동화 이득이 된 상태(Gemini "인지적 부채").
- **공통 측정 지표**:
  1. Always-loaded 토큰 (현재 ~7,100 → 목표 < 1,000)
  2. 사용자 판단 생략 횟수 (incident에 사용자가 개입해 정정한 빈도)
  3. 지침 문서 삭제량 (rules/* / Slash / Skill 평균 줄 수)
  4. 분노 사이클 (사용자가 같은 지적을 반복한 빈도)
- **놓칠 위험**: incident 수치 하락만 보고 성공 착각 (Gemini 지적). incident 0이라도 사용자 개입량이 그대로면 실패.

### 의제2. 모델 한계 vs 셋팅 한계 — "지침 인플레이션 종말"

- **합의**: spec drift, 장기 지침 준수, 자기교정, 결정 회피는 사용자 셋팅으로 보완 불가능한 모델 한계 영역(GPT). 메타 지침 추가는 Claude에게 **독(Poison)** 으로 작용해 인지적 마비 유발(Gemini).
- **셋팅 보완 가능 영역** (계속 박아도 됨):
  - 파일 접근 범위 / 원본 보호 / 위험 명령 차단 / 실행 경로 표준화 / 검증 명령 자동화 / worktree·sandbox 분리
- **셋팅 보완 불가능 영역** (박는 것 금지):
  - 장기 규칙 준수 / 행동 성향 교정 / 자기반성 후 자동 개선 / 의도 추론 / 메타 우선순위 충돌 해소 / "질문하지 말라"·"결정 위임 금지" 같은 명제형 행동 교정
- **치환 원칙**: 행동 교정 문구 → **결정론적 도구·코드** (Permission/Hook/Python verify)로 치환.
- **놓칠 위험**: "조금 더 명확한 CLAUDE.md를 쓰면 된다"는 이성적 낙관주의 (양측 모두 지적).

### 의제3. 헤비유저 컨센서스 도메인 적합성 — "메타는 룰, 도메인은 SOP"

- **합의**: 100줄 룰·hook 4개·subagent 5개 컨센서스는 **메타 계층에만** 적용. 도메인(제조 ERP·MES)은 별도 manual/verify/rollback (GPT) 또는 GLOSSARY.json + RAG + Python 호출 구조 (Gemini)로 분리.
- **메타 계층 (Anthropic 디폴트 + 최소 레이어)**:
  - CLAUDE.md 100~200줄
  - Hook 4-5개 (위험차단 + formatter + sessionstart + 측정)
  - Subagent 5개 이하 (도메인 검증 위주)
  - Slash command 5개 이하
  - Permissions 15개 이하 (포괄 패턴만)
  - Always-loaded < 1,000 토큰
- **도메인 계층 (보존·결정론화)**:
  - 도메인 MANUAL.md 길이 자유 (사용자 지식 보존)
  - SKILL.md는 절차 + verify 명령 호출만
  - 한국어 제조업 용어 / 품번 / 라인 / 공정코드 → glossary 분리 (RAG 식 호출)
  - ERP/MES 등록은 operator skill에서만 / dry-run·list-only·commit·verify·rollback 5단계 경로 보유
  - Claude는 판단자 아닌 **실행 대행자**, 판단 근거는 verify.py 리턴값
- **놓칠 위험**:
  - Claude: 헤비유저 컨센서스를 도메인 문서까지 확장 적용 → 도메인 자산 유실
  - Gemini: 슬림화를 단순 "짧게 쓰기"로 오해. 진짜 슬림화는 **자연어 지침 → 코드 치환**

### 의제4. Option 3 Hybrid + 단일 PR 골격 + 점진 세부 이식

- **우선순위 (양측 합의)**: **Option 3** (1순위) > Option 5 부분 채택 (ERP/MES 핵심 Python) > Option 4 장기 목표 (행동 교정 메타 0) > Option 1 임시 완충 > Option 2 폐기
- **PR 방식 통합 안 (자동 도출)**:
  - **단일 PR (1회 일괄)**: 폴더 골격 + `.claude → _deprecated_v1/` 이동 + main `stable-before-reset` 태그 + 측정 기준 (토큰 / 분노 사이클 / incident) 베이스라인
  - **Phase별 점진 (8단계)**: hook 축소 / settings 슬림화 / commands·skills 재배치 / TASKS·HANDOFF archive / 도메인 manual·verify 코드 작성 / 7일 측정 / 1차 평가 / 2차 조정
- **R5 롤백 계획**:
  - main `stable-before-reset` 태그 생성
  - `.claude/` 통째 백업 → `_deprecated_v1/` 이동
  - 도메인 코드 (`05_생산실적/조립비정산/`, `10_라인배치/` 등) **직접 수정 금지**
  - 리모델링 기간 ERP/MES 실등록은 dry-run / list-only 우선
  - 운영 등록 script는 기존 stable 경로 유지
  - 실패 시 `.claude` 백업 복원 + tag checkout

### 추가 합의 (양측 거론 / Claude 흡수)

- **삭제 목표 수치를 시스템적으로 강제**: 측정 hook 1개 신설 (예: 기존 `token_threshold_check.sh` 활용). always-loaded 토큰 > 1,000 시 경고.
- **Gemini가 사용자에게 던진 질문**: "현재 17개 worktree와 수많은 hook 중 '이게 없으면 당장 내일 업무 마비'라고 확신하는 **생존 필수 기능 딱 3가지**" → **Round 2 의제 1번**으로 보존.
- 점진 적용의 안티패턴 차단: "삭제 목표 수치"를 PR 첫 커밋에 박고 그 이후 추가 시 PR 거부.

---

## 미합의·보류 쟁점

1. **헤비유저 4지표 목표선** (rules/* / Slash / Skill 평균 / Worktree)을 "헤비유저 범위 안"으로 진입시키는 구체 수치 — Round 2에서 사용자 답변(생존 필수 3가지) 후 결정
2. **의제2 "행동 교정 메타 0"의 경계** — Option 4가 장기 목표라는 데는 합의했으나, 어디까지가 "행동 교정"인지 (예: `incident_quote.md`는 행동 교정인가 안전 가이드인가)
3. **GLOSSARY.json + RAG 도입 여부** — Gemini만 명시 제안. GPT는 manual + verify로만. Round 2에서 결정

---

## 즉시 실행안 3개 (Round 1 종결 후)

1. **단일 PR 작성**: 골격 + `_deprecated_v1/` 이동 + `stable-before-reset` 태그 + 측정 기준 베이스라인
2. **사용자 결정 대기 의제 정리**: Round 2 의제 1번(생존 필수 3가지) + 보류 쟁점 3건
3. **삭제 목표 수치 합의**: always-loaded < 1,000 토큰, rules/* 5개 → 1개, Slash 33개 → 5개, Skill 평균 305줄 → 80줄, Hook 약 45개 → 5개, Worktree 17개 → 사용자 결정 후 prune

---

## cross_verification JSON (Step 6-5 종합 후 시점, 양측 검증 전)

```json
{
  "round": 1,
  "round_count": 1,
  "max_rounds": 3,
  "issue_class": "B",
  "skip_65": false,
  "skip_65_reason": "B 분류 (메타 레이어 전면 리셋)는 6-5 무조건 유지",
  "claude_delta": "partial",
  "claude_delta_reason": "선행 답안 방향과 일치, Gemini '독성' 진단 + GPT PR 통합 안을 종합안에 흡수",
  "gemini_verifies_gpt": {
    "verdict": "동의",
    "reason": "모델 한계를 더 많은 지침으로 해결하려 한 것이 시스템 비대화 원인이라는 분석과 도메인 실행 경로를 결정론적 코드로 분리하자는 제안에 전적으로 동의"
  },
  "gpt_verifies_gemini": {
    "verdict": "동의",
    "reason": "Gemini의 메타 독성·도구/검증 중심 전환 판단은 GPT 판정과 정합하며, 단일 PR은 폴더 골격·deprecated 이동·측정 기준까지만 허용하고 실제 hook/settings/업무 세부 이식은 Phase별 점진 적용이 안전"
  },
  "gpt_verifies_claude": null,
  "gemini_verifies_claude": null,
  "pass_ratio_before_claude_verify": "2/2 (양측 cross verify, Claude 종합 검증 대기)",
  "pass_ratio_target": "2/3 이상 (Claude 종합에 대해 GPT·Gemini 양측 중 2 이상 동의)"
}
```
