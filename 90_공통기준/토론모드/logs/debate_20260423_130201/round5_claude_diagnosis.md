# Round 5 — Claude 독립 진단 (활성 패턴 근본 원인 분석)

## 시간 분포 실측 (2026-04-23 시점)

### harness_missing (44건)
- 5가지 detail 패턴 모두 9일 간 분산 발생
- 첫 발생: 2026-04-13T03:00, 마지막: 2026-04-22T07:21 (1일 전)
- 폭증 시점: 04-13~14 (25건), 04-18 (8건)
- 04-19 이후 산발적 → **학습 진행 중이나 완전 종료 X**

### evidence_missing (45건)
| 패턴 | 건수 | span | 마지막 발생 | 상태 |
|---|---|---|---|---|
| `instruction_not_read` (detail 빈) | 24 | 8일 | 2026-04-21 | **학습 완료**, 04-22 이후 0건 |
| `skill_instruction_gate` "MES access without SKILL.md read" | 11 | **0일** | 2026-04-23T05:02 | **활성**, D0 자동화 작업 시기 폭증 |
| `evidence_gate` "identifier_ref.req 존재" | 7 | **0일** | 2026-04-23T05:01 | **활성** |
| `evidence_gate` "auth_diag.req 존재" | 3 | **0일** | 2026-04-22 | 1일 자락 |

**핵심 발견**: evidence_missing 21건이 **04-22 이후 D0 자동화 작업(/d0-plan 스킬 개발) 부산물**

## hook 코드 분석

### harness_gate.sh (검출 로직)
- 활성 조건: `debate_preflight.req` 존재 (토론 도메인만)
- 차단 대상: Bash + (git commit|git push|share-result|finish)
- 4개 AND 마커 검사 (트랜스크립트 마지막 **20000자**):
  1. `채택:` 존재
  2. `보류:` 또는 `버림:` 존재
  3. 독립견해 마커 (반론|대안|내 판단|환경상|독립 대조|독립 의견|독립 견해|이견|내 입장)
  4. 실물근거 마커 (실증됨|Git|커밋|diff|실물|기준 미확인|일반론)

### skill_instruction_gate.sh (MES/ZDM)
- 트리거: 인라인 python (`python3 -c` / `python3 - <<EOF`)에서 mes-dev.samsong.com 또는 ax.samsong.com 접근
- 정식 스킬 run.py는 통과 (L17-21)
- SKILL.md 읽기 마커 없으면 차단 → `evidence_missing` 마킹

### evidence_gate.sh (.req/.ok 사이클)
- `identifier_ref.req` / `auth_diag.req` 등이 위험 작업 시점에 발행
- 대응 .ok 없으면 차단

## 근본 원인 가설

### 가설 H1: harness_gate 트랜스크립트 윈도우 협소 (20000자)
- 토론 응답이 길거나 후속 토론이 길면 라벨링이 윈도우 밖으로 밀림 → false positive
- 검증 가능: 차단된 시점의 트랜스크립트 길이 vs 20000자

### 가설 H2: harness_gate 라벨링 표현 다양성 미허용
- `채택:` 정확 매칭. "(채택)" / "채택 N건" / "**채택**" 등은 미검출
- 단 현재 detail 패턴이 정확히 누락 항목과 일치하므로 라벨링 자체를 안 한 것일 가능성도

### 가설 E1: skill_instruction_gate — 인라인 스크립트가 정식 스킬로 전환되면 자연 감소
- 04-22~23 발생 11건은 `.claude/tmp/erp_d0_*.py` 5종 (D0 개발 중)
- 세션95에서 `90_공통기준/스킬/d0-production-plan/run.py`로 정식화 완료 → **이미 자연 해소 경로**
- 잔존 incident는 정리만 하면 됨 (run.py 호출 시 통과)

### 가설 E2: evidence_gate identifier_ref/auth_diag .req 발행 트리거가 광범위
- `.req` 자동 발행 → 작업마다 사용자가 .ok 충족시켜야
- 7+3=10건 모두 04-22~23 D0 작업 시 발생
- D0 정식 스킬 사용 후 줄어들 가능성

## 개선안 후보

### A. harness_gate 개선 (44건)
- A-1: 트랜스크립트 윈도우 50000자로 확장 (단순)
- A-2: 라벨링 표현 정규식 다변화 (`채택:` → `(\\*\\*)?채택[:\\s\\)]`)
- A-3: 마커 기반 전환 — Claude가 라벨링 직후 `.claude/state/harness_done_<turn>.ok` 발행, gate가 마커 검사 (구조 변경)

### B. skill_instruction_gate 개선 (11건)
- B-1: 정식 스킬 run.py 호출은 이미 통과. **추가 변경 불필요**. 잔존 11건은 stale 정리(rule 추가)
- B-2: 인라인 tmp 스크립트도 SKILL.md 읽기 마커 있으면 통과 (이미 동작) — 마커 발행 경로 사용자 명시 문서화

### C. evidence_gate identifier_ref/auth_diag (10건)
- C-1: .req 발행 트리거 좁히기 (어떤 키워드로 발행되나 확인 필요)
- C-2: stale 정리 — D0 작업 종료 후 .req 자동 expire (24h TTL)
- C-3: .ok 발행 경로 사용자 문서화

## 의제 분리/순서 제안

**Wave 1 (즉시, 2자 토론 1건)** — 자연 해소 + stale 정리
- B-1 (skill_instruction_gate stale 11건 자동 해소 규칙)
- E1 가설 검증: D0 정식 스킬로 자연 해소되는지 24-48h 관찰

**Wave 2 (다음, 별 의제)** — 구조 개선
- A (harness_gate 검출 로직 개선) — 가설 H1/H2 검증 + 개선
- C (evidence_gate .req/.ok 사이클 개선)

Wave 1만 우선 처리해도 evidence_missing 21건 자연 해소 + skill_instruction_gate 11건 정리 가능.
