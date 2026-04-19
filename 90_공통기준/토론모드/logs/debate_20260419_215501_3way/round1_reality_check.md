# Round 1 — Step C 실물 검증 결과

## C-1. commit_gate vs permissions_sanity 캐시 사양 대조 (주장 3 검증)

### permissions_sanity.sh
- L20: `CACHE_FILE="$PROJECT_ROOT/.claude/state/permissions_sanity_last.txt"`
- L21: `CACHE_TTL=3600  # 60분`
- L28: `if [ "$elapsed" -lt "$CACHE_TTL" ]` → 경과 체크 후 `skip_cache`로 스킵
- L99-100: `mkdir + date +%s > $CACHE_FILE`로 타임스탬프 갱신

→ **60분 캐시 = permissions_sanity.sh 사양 확정**

### commit_gate.sh
- **60분 캐시 관련 키워드 매칭 0건**
- L143: `should_suppress_incident "$_fingerprint" 60` — **60초 incident suppress grace window** (캐시 아님)
- L144: `hook_log "PreToolUse/Bash" "commit_gate: incident suppress (fingerprint=$_fingerprint, grace=60s)"`
- L16: 주석 "fingerprint suppress 함수 (세션46 GPT+Claude 합의: 2단 분리)"

→ **commit_gate.sh는 60분 캐시 없음. 60초 fingerprint suppress grace만 존재.**

### 결론
GPT 주장 3 "commit_gate.sh 60분 캐시로 재검증 민감도↓"는 **훅 혼동 확정**.
- permissions_sanity.sh의 CACHE_TTL=3600(60분 캐시) + commit_gate.sh의 60(60초 incident grace)을 섞어서 본 것.
- 두 기능은 완전 별개: 캐시(재실행 스킵) vs incident 중복 방지(기록 suppress).

**판정: GPT 주장 3 → 버림 (Claude + Gemini + GPT 3자 합의)**

---

## C-2. hook_common.sh sed/tr JSON 파싱 사용처 감사 (주장 4 검증)

### sed/tr/awk 전체 hit 위치 (11건)
- L29·L31·L33: `sha1sum | awk '{print $1}'`, `shasum | awk '{print $1}'`, `cksum | awk '{print $1}'` — **해시 추출** (JSON 무관)
- **L79-106: safe_json_get 구현 (JSON 파싱 핵심)**
  - L79 주석: `# 안전 JSON 값 추출 — sed 단독 파싱의 따옴표/줄바꿈 취약성 대체`
  - L90: `printf '%s' "$input" | tr '\n' ' ' | sed -n 's/.*"'"$key"'"[[:space:]]*:[[:space:]]*"\(\([^"\\]\|\\.\)*\)".*/\1/p'` — JSON string 값 추출
  - L95: `sed 's/\\\\/\x00BSLASH\x00/g; s/\\"/"/g; s/\\n/\n/g; s/\\t/\t/g; s/\x00BSLASH\x00/\\/g'` — escape 복원
  - L100: JSON object/array 값 추출 (sed chain)
  - L106: JSON number/bool/null 추출 (sed chain)
- L169: `echo "$text" | grep -oiE "$_COMPLETION_PATTERN" | head -3 | tr '\n' '; ' | sed 's/; $//'` — **완료 패턴 grep + 토큰 정리** (JSON 무관)
- L216: `sed '/^$/d' | sort -u` — 빈 라인 제거
- L268: `printf '%s' "$extra_json" | tr -d '\n'` — extra_json 줄바꿈 제거

### JSON 파싱 핵심 sed chain 4곳 분류
1. L90 string 값 추출
2. L95 escape 복원 (`\\ \"\ \n\ \t\ \\`)
3. L100 object/array 값 추출
4. L106 number/bool/null 추출

### 설계자 자각 증거
L79 주석 원문: **"안전 JSON 값 추출 — sed 단독 파싱의 따옴표/줄바꿈 취약성 대체"**
→ 설계자(Claude)가 sed 파싱 한계를 이미 인식하고 작성한 "개선 버전" — fragility를 알고 대응함.

### Incident Ledger 대조
- hook_common.sh sed 파싱 관련 incident: **0건**
- "safe_json_get" 키워드 포함 incident: **0건**

### 결론
Gemini 주장 4 "single point of fragility"는 **예방적 경고 수준**:
- 사실: sed 기반 JSON 파싱 4곳 존재
- 단, 설계자 자각 주석 + 장애 사례 0건
- 실증 강도 중간 → **보류 (Round 2 포함 검토 여지)**

---

## C-3. Incident 1027건 breakdown (Gemini Policy 현실성 지적 검증)

### 전체 집계
- 총 1027건 (파일: `.claude/incident_ledger.jsonl`)
- 미해결(False): **872건 (85%)**
- 해결(True): 155건 (15%)

### Hook별 상위 10 (71.4%가 2개 훅에 집중)

| Hook | Count | % |
|------|-------|---|
| **evidence_gate** | 474 | **46.2%** |
| **commit_gate** | 259 | **25.2%** |
| navigate_gate | 69 | 6.7% |
| completion_gate | 52 | 5.1% |
| skill_instruction_gate | 49 | 4.8% |
| harness_gate | 40 | 3.9% |
| final_check | 23 | 2.2% |
| (none) | 18 | 1.8% |
| date_scope_guard | 16 | 1.6% |
| instruction_not_read | 12 | 1.2% |

→ **상위 5종이 903건 (88%)** — 세션75 반복 미해결 정리 대상

### Classification reason별 상위 10

| Reason | Count | % |
|--------|-------|---|
| evidence_missing | 526 | 51.2% |
| pre_commit_check | 216 | 21.0% |
| send_block | 75 | 7.3% |
| structural_intermediate | 45 | 4.4% |
| harness_missing | 40 | 3.9% |
| python3_dependency | **31** | **3.0%** |
| (none) | 27 | 2.6% |
| meta_drift | 23 | 2.2% |
| **true_positive** | **12** | **1.2%** |
| scope_violation | 12 | 1.2% |

### Type
- gate_reject: 899 (87.5%)
- hook_block: 53 (5.2%)
- warn_recorded: 43 (4.2%)
- instruction_read_gate: 12 (1.2%)

### 핵심 인사이트 — Policy-Workflow Mismatch 실증

1. **true_positive = 12건 (1.2%)** — 시스템 스스로 "진짜 문제"로 라벨한 건 단 1.2%
2. **evidence_missing + structural_intermediate + send_block + harness_missing = 686건 (66.8%)** — 대부분이 "구조적 경고" 분류
3. **evidence_gate 단일 훅 46.2% 점유** — 특정 훅의 Policy가 과도하게 민감

### 결론
Gemini "Policy 현실성" 지적 **강력 실증**:
- 통제 기준(Policy)이 제조업 G-ERP 실제 워크플로우와 mismatch로 **False Positive를 대량 생성** 중
- 해결책은 훅 코드 수정(완화)이 아니라 **Policy 기준 재설계 + true_positive 라벨링 자동화 확대**
- GPT 세련화 표현: **"policy-workflow mismatch"** (전부 FP 단정은 과함 — 의심 표현)

**→ 신규 의제 승격 (Round 2) 정당화**
