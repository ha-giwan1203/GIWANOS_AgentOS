# Round 1 — Claude 종합 설계안

> 의제5 (hook vs permissions 중복 감사) + 신규 쟁점 G(settings 계층 분리), H(훅 에러 전파 고립)를 통합한 최종 설계안. GPT와 Gemini가 Round 1에서 1줄 교차 검증 모두 **동의**.

---

## 1. 최종 채택 사항 (8개 쟁점)

### A. 1회용 permissions 16건 정리 — **소프트 블록 방식** (Gemini 수정 + GPT 수용)
- **즉시**: 16건 제거 (PID 8 + URL 3 + rm 3 + rmdir 1 + sed 1)
- **재발 방지**: `.claude/hooks/permissions_sanity.sh` 신설 → PID/URL/rm/sed 1회용 패턴 + 완전 중복 자동 탐지 → **stderr 경고** + `hook_log.jsonl` 기록
- **소프트 블록 (세션71 후속)**: `completion_gate.sh` 연동. 동일 1회용 패턴 3회 이상 누적 탐지 시 사용자 명시적 확인 프롬프트 요구 → 마찰 추가로 재발 차단. **하드페일은 사용하지 않음** (제조업 급한 세션 중단 리스크 회피)

### B. 완전 동일 중복 2건 제거
- `Bash(cat:*)` 중복 1건, `Bash(echo:*)` 중복 1건 즉시 제거 (무손실)
- sanity hook이 중복 검출 로직 기본 포함

### C. dedicated tool 중첩 10건 유지 + CLAUDE.md 명문화
- ls/wc/find/grep/cat/head/tail/echo 유지 (실무 편의 > 보안 이득)
- CLAUDE.md: "포괄 Bash 허용은 Read/Grep/Glob의 fallback. 우선순위는 dedicated tool"

### D. PreToolUse Bash 매처 7개 — timing 실측 후 통합 평가
- `hook_common.sh`에 `hook_timing_start` / `hook_timing_end` 래퍼 함수 추가
- 각 hook 실행 시간 → `hook_timing.jsonl` 수집 (1주일)
- **의제4(세션72)**: 누적 데이터 기반 통합 후보 평가
- 순서 의존성(block_dangerous → commit_gate → debate_verify)은 고정

### E. Stop hook 4개 유지
- 각 책임 분리 명확(stop_guard/gpt_followup_stop/completion_gate/evidence_stop_guard)
- `.claude/hooks/README.md`에 책임 매트릭스 섹션 추가

### F. hook vs permissions 역할 경계 명문화 (5단계 의사결정 트리)
- CLAUDE.md 루트에 "hook vs permissions 역할 경계" 섹션 신설
- 5단계 의사결정 트리 (GPT 보강 1단계 선행 질문 포함):
  1. **전역 규칙인가 일회성 예외인가** (1회용 쓰레기 원천 차단)
  2. 도구 호출 허용 문제인가 (on/off 게이트 → permissions)
  3. 호출 시점 맥락 문제인가 (조건부 게이트 → hook)
  4. 둘 다 필요한가
  5. 기록/만료 정책이 필요한가

### G. settings.local.json vs settings.json 계층 분리 — **신규 채택 (GPT 제안, Gemini 전적 동의)**
- 현재 문제: `.claude/settings.local.json`을 팀 공용 정책 저장소처럼 운영 → Git 추적과 로컬 환경 간 꼬임
- 계층 분리:
  - **팀 공용 정책** (permissions·hook 전역 규칙): `.claude/settings.json` 또는 기준 문서 (Git 커밋)
  - **개인/세션성 허용** (1회용, 탭 ID, 임시 파일): `.claude/settings.local.json` (gitignore 또는 최소 범위)
- **선제조건 검토**: 현재 settings.json 전역 3개 항목(mcp_telegram_reply, Edit/Write 포괄)과 settings.local.json 110개 항목의 소속 재분류 — 세션71 후속 작업으로 분리

### H. 훅 체이닝 에러 전파 고립 정책 — **신규 채택 (Gemini 제안, GPT 정당성 확인)**
- 현재 문제: 36개 .sh hook 중 특정 훅 exit 1 발생 시 전파 정책 제각각. `debate_verify.sh`도 `set -u`만 켜고 `|| true` 개별 완화 → 실패 고립 방식 비일관
- **훅 등급 3종 + exit code 표준**:
  - **경고성 훅** (advisory): 실패해도 세션 계속. exit 0 강제, stderr 로그만. `|| true` 허용 명시
  - **차단성 훅** (gate): 실패 시 상위 도구 호출 차단. exit 2 전파. `|| true` 금지. 예: block_dangerous, commit_gate, debate_verify
  - **계측 훅** (measurement): 실패 영향 없음. exit 0 강제, timing만 기록. 예: timing 래퍼, hook_log
- **hook_common.sh 공통 래퍼**:
  - `hook_advisory <hook_path>` → 실패 시 stderr 로그 + exit 0
  - `hook_gate <hook_path>` → 실패 시 exit 2 전파
  - `hook_measure <hook_path>` → trap ERR 예외 무시, timing만
- `.claude/hooks/README.md`에 등급 분류 + 전파 정책 섹션 추가

---

## 2. 실행 Phase 분리

### Phase 2-A. 세션71 즉시 (1커밋)
- settings.local.json permissions 18건 제거 (A·B)
- `permissions_sanity.sh` 신설 (경고만)
- CLAUDE.md "hook vs permissions 역할 경계 + 5단계 의사결정 트리" 섹션 신설 (F + C 원칙)
- `hook_common.sh` timing 래퍼 함수 추가 (D 수집 시작)
- `hook_common.sh` 훅 등급 3종 공통 래퍼 함수 추가 (H 표준)
- `.claude/hooks/README.md` 책임 매트릭스 + 훅 등급 분류 (E + H 문서화)

### Phase 2-B. 세션71 후속 (2커밋 또는 세션72 분리)
- `completion_gate.sh` 소프트 블록 추가 (A 재발 방지 마찰 설계 — 1회용 패턴 3회 누적 시 사용자 확인)
- 기존 훅 전수 등급 재분류 → 공통 래퍼 호출 전환 (H 실행)

### Phase 3. 의제3 Phase A (2커밋)
- `.claude/hooks/skill_drift_check.sh` 신설 (commit 시점 래퍼/실물 정합성)
- 5종 래퍼(debate-mode/settlement/line-batch-management/line-batch-outer-main/daily) 정합성 재검증

### 세션72 이월
- 의제4 `/debate-verify` 실행 순서 재평가 (D timing 수집 1주일 후)
- 쟁점 G settings 계층 분리 실물 이행

---

## 3. Round 1 종합 수치
- 합의 채택: 8 (A·B·C·D·E·F·G·H)
- 보류/이의: 0
- 버림: 0

## 4. 최종 검증 요청 (양측)
- GPT에 이 설계안 원문 전체 + `[설계안 검증] 동의/이의/검증 필요 + 근거 1문장`
- Gemini에 동일 내용으로 동시 송부
- 양측 모두 동의 시 `pass_ratio_numeric = 4/3 = 1.33` → 채택 조건 충족 (≥ 0.67)
- 한쪽 이의 시 Round 2 진입 (최대 3회)

---

## 부록 — 설계 원칙 요약 (GPT 지적 반영)
"이번 라운드의 중심은 '찌꺼기 정리'보다 **재발 방지 마찰 설계 + 훅 실패 고립 규칙 표준화**다."
