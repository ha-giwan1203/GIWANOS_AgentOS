# Round 1 — Claude 독자 답안 (6-0 선행)

## 의제 요약
세션112 self-audit 후속 3건. 모두 B 분류(구조·정책 변경). 단독 결정 금지 → 3자 토론.

---

## 의제1 (P2-B): evidence_gate auth_diag.req / identifier_ref.req ok 발급 절차 명문화

### 결론 (1줄)
**ok 발급 트리거를 정상 OAuth/기준정보 작업 스크립트로 자동 확장 + req 발급 키워드를 좁힌다 (Option B+C 결합).** noise 감소와 보호 강도를 동시에 달성.

### 주장 (라벨/증거)
1. **현재 구조의 결함은 req 자동·ok 수동 비대칭** [실증됨, evidence-core ref] — `risk_profile_prompt.sh:54,63`이 키워드 감지로 req 자동 발급. `evidence_mark_read.sh:97-98`은 `auth_diag(\.sh)?` 명령 또는 `identifier_ref` 텍스트만 mark. 정상 OAuth 작업(`erp_oauth_login.py`, `erp_d0_*.py`)은 ok 미발급.
2. **세션112 35건 중 다수가 단일 fingerprint 반복 카운트** [실증됨, incident_ledger ref] — 5개 고유 fingerprint, 최다 `383f406a5519717b`(auth_diag)가 GRACE 300초 경계를 자주 넘어 누적. 세션86 측정: GRACE 120→300으로 81.5%→46.2% 억제, 그래도 절반이 넘침.
3. **deny 자체는 정상 작동** [실증됨] — `evidence_gate.sh:155-168` MES/OAuth 위험 명령 시 차단 정상. 문제는 정상 작업도 차단되어 noise.
4. **resolve_hint 단방향** [실증됨] — `evidence_gate.sh:117-120`이 "auth_diag 스크립트 실행" 안내. 그러나 D0 작업처럼 `auth_diag.sh`를 별도 실행하지 않는 정상 흐름은 ok 발급 경로 부재.

### 구체안 (Option B+C)
- **B**: `evidence_mark_read.sh`에 OAuth 성공 정상 스크립트 패턴 추가 — `erp_oauth_login\.py|chrome_login.*완료|OAuth.*200|cdp.*9222` 중 하나 PostToolUse 감지 시 `auth_diag.ok` mark
- **C**: `risk_profile_prompt.sh` 키워드 좁히기 — 현재 `mes|login|oauth|auth-dev|redirect|selenium|chrome` 중 `chrome`은 D0/일반 작업에서 너무 자주 매칭. `chrome` 단독 키워드 제거 + `chrome.*login` `chrome.*oauth` 조합으로 좁히기
- **identifier_ref**도 동일 접근: `라인배치_check.py|기준정보_대조.py|identifier_ref_check\.sh` 등 정상 도메인 스크립트 PostToolUse mark

### 약점 (반대 안 예상)
- **GPT 예상 반박**: "Option B는 보호 우회 위험 — 가짜 'OAuth 성공' 출력만으로 ok 발급되면 evidence-core 의미 무력화"
  - 반론: PostToolUse는 실제 명령 실행 후 트리거. 명령 자체가 실행됐다는 사실 = 사용자 의도 확인. evidence_mark_read의 기존 `mark "auth_diag"` 자체가 동일 모델
- **Gemini 예상 반박**: "Option C 키워드 좁히기는 false negative 위험 — 키워드 매칭 실패 시 진짜 위험 작업이 req 없이 통과"
  - 반론: 차단은 deny() 단계에서 별도 정책. req 발급은 "사용자에게 OAuth 진단 안내" 목적. 정상 OAuth 흐름이면 req 발급 자체 불요

### 착수·완료·검증 조건
- 착수: `evidence_mark_read.sh:97-98` 패턴 확장 + `risk_profile_prompt.sh:54,63` 키워드 좁히기
- 완료: 7일 incident_ledger evidence_missing 건수 50% 이상 감소
- 검증: `python3 .claude/hooks/incident_review.py --days 7 --threshold 3` 실행 + 단위테스트 (정상 OAuth + 위험 OAuth 모두 케이스 유지)

---

## 의제2 (P2-C): 죽은 보조 hook 4종 운영 경로 결정

### 결론 (1줄)
**4종 모두 폐기 아닌 "운영 경로 부여"로 결정. nightly_capability_check는 schtasks 등록, render_hooks_readme는 commit_gate 보조 호출, e2e_test/gate_boundary_check는 manual + final_check --full 통합.** 도입 합의 무력화 위험 회피.

### 주장 (라벨/증거)
1. **nightly_capability_check는 세션77 Round 2 Gemini 최우선 안전망 합의** [실증됨, 헤더 주석 ref] — 폐기 = 합의 무력화. 운영 경로 부여 필수.
2. **render_hooks_readme는 SSoT 자동 갱신 도구** [실증됨, 헤더 주석 + DESIGN_PRINCIPLES 원칙 7] — 수동 실행 의존이 SSoT 정신과 모순. commit_gate에서 dry-run 비교 후 차이 있으면 안내.
3. **e2e_test는 smoke_test의 동적 보완** [실증됨] — 정적 구조 검증 + E2E 병행이 본 의도. final_check --full 또는 weekly schedule 통합 적합.
4. **gate_boundary_check는 회귀 트립와이어** [실증됨, 헤더 주석 ref] — 헤더에서 "코드 리뷰 트리거"로 명시. PR 워크플로우 폐기로 트리거 위치 부재. commit_gate advisory 호출 가능.

### 구체안
- **nightly_capability_check.sh**: Windows schtasks 매일 02:00 `bash .claude/hooks/nightly_capability_check.sh` 등록 명령 문서화 + 사용자 1회 실행 안내
- **render_hooks_readme.sh**: `commit_gate.sh`에 `--dry` 호출 단계 추가 → 차이 감지 시 stderr 경고 (advisory)
- **e2e_test.sh**: `final_check.sh --full` 모드에 호출 통합 + scheduled-task `weekly-self-audit`에 추가
- **gate_boundary_check.sh**: `commit_gate.sh`에 advisory 호출 (실패해도 통과) + hook_log에 기록

### 약점
- **GPT 예상 반박**: "commit_gate에 4종 추가하면 commit 시간 증가, 사용자 답답"
  - 반론: render는 dry 모드(빠름), gate_boundary는 grep만(빠름). e2e는 `--full`만 호출. nightly는 schtasks 분리.
- **Gemini 예상 반박**: "schtasks 등록 명령 문서화로 충분한가? 실제 등록 검증 hook 없으면 또 silent"
  - 반론: schtasks 등록 후 첫 실행 결과를 incident_ledger에 기록 → 다음 self-audit에서 "최근 실행 흔적 없음" 감지 → 자동 재안내. 메타 안전망 1단계 더.

### 착수·완료·검증
- 착수: 위 4종 호출 경로 수정 + schtasks 등록 명령 문서 추가
- 완료: 4종 모두 호출 흔적이 hook_log 또는 schtasks에 1회 이상 기록됨
- 검증: 다음 weekly self-audit에서 "죽은 자산" 분류에서 모두 제거됨

---

## 의제3 (P3-E): agents 7종 진입 경로 명문화 vs 폐기

### 결론 (1줄)
**7종 모두 폐기 아닌 "AGENTS_GUIDE.md 진입 트리거 명문화" + 일부는 자동 호출 경로(skill 내장) 부여. 폐기 0건.** description 자체는 명확하므로 사용처가 문제.

### 주장 (라벨/증거)
1. **각 agent description은 명확** [실증됨, agents/*.md ref] — `evidence-reader`(컨텍스트 보호 경량 reader), `debate-analyzer`(GPT 하네스), `artifact-validator`(반영 후 검증), `settlement-validator`(정산 Step1~7), `code-reviewer`(읽기 전용 검증), `critic-reviewer`(허점 발굴), `self-audit-agent`(자기진단)
2. **이미 일부는 자동 호출됨** [실증됨] — `self-audit-agent`는 `/self-audit` 스킬에서, `critic-reviewer`는 `debate-mode/SKILL.md` Step 4b에서, `settlement-validator`는 `/settlement` 또는 `/settlement-validate`에서 호출. 진단의 "참조 미발견"은 grep 누락.
3. **진짜 미참조는 일부**: `evidence-reader`, `debate-analyzer`, `artifact-validator`, `code-reviewer` 4종은 description에 트리거가 명시되어 있으나 자동 호출 위치 부재.
4. **AGENTS_GUIDE.md 분산 명문화 부재**: CLAUDE.md 진입 테이블에 도메인 전문가 2종(line-batch, settlement)만 명시. 나머지는 분산.

### 구체안
- **AGENTS_GUIDE.md**: 9종 모두 표로 정리 (이름 / 트리거 / 자동 호출 위치 / 모델). 누락 4종(evidence-reader/debate-analyzer/artifact-validator/code-reviewer)에 명시적 트리거 추가
- **evidence-reader 자동 호출**: 세션 시작 시 `session_start_restore.sh`가 도메인 전환 감지 시 호출 권장 (advisory 안내)
- **artifact-validator 자동 호출**: `/share-result` 5-0 단계에서 자동 위임
- **debate-analyzer 자동 호출**: `debate-mode` Step 3 하네스 분석 위임 옵션
- **code-reviewer 자동 호출**: `/finish` 또는 `/auto-fix` 후처리 단계
- **폐기 0건** — 모두 description이 명확하고 사용 시점이 정의 가능

### 약점
- **GPT 예상 반박**: "subagent 자동 호출 추가는 토큰 비용 증가. ROI 불확실"
  - 반론: agents는 모두 haiku/sonnet (저비용). 메인 컨텍스트 보호 효과가 더 큼. 7일 incident `harness_missing` 7건도 debate-analyzer 자동 호출로 해소 가능
- **Gemini 예상 반박**: "AGENTS_GUIDE.md 한 곳에 집중하면 도메인 CLAUDE.md와 충돌"
  - 반론: AGENTS_GUIDE는 인덱스, 도메인 CLAUDE.md는 도메인 한정 트리거 — 직교

### 착수·완료·검증
- 착수: AGENTS_GUIDE.md 표 작성 + 4종 자동 호출 위치 추가
- 완료: 다음 self-audit에서 "참조 미발견" 0건
- 검증: 1주 후 hook_log/skill_usage.jsonl에서 7종 모두 호출 흔적 1회 이상 (단, evidence-reader는 도메인 전환 시점 한정)

---

## 종합 (Round 1 Claude 종합 답안)

| 의제 | 안 | 핵심 변경 | B 분류 |
|------|----|----------|---------|
| P2-B | Option B+C 결합 | evidence_mark_read 패턴 확장 + risk_profile_prompt 키워드 좁히기 | YES |
| P2-C | 운영 경로 부여 (폐기 0) | 4종 모두 호출 경로 신설 | YES |
| P3-E | 명문화 + 자동 호출 (폐기 0) | AGENTS_GUIDE 표 + 4종 자동 호출 추가 | YES |

**모두 B 분류이므로 6-5 종합 단계 유지 (생략 불가)**. 양측 본론 + 1줄 검증 후 Claude 종합 → 양측 검증 → pass_ratio ≥ 2/3 시 채택.

**claude_delta**: 이 답안은 6-0 선행 작성. 6-5에서 양측 답변 수령 후 `none/partial/major` 자체 선언 예정.
