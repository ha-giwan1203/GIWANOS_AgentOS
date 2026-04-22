# Round 1 — Claude 독립 점검 (단계 III 게이트 3종 범위 재절단)

**의제**: Plan glimmering-churning-reef 단계 III — `commit_gate` / `evidence_gate` / `completion_gate` 재절단 + III-4 신설 + III-5 동반 정리
**토론 모드**: 2자 (Claude × GPT), 사용자 명시 지시
**계획 원문**: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` Part 3 단계 III
**세션91 진입 계획**: `C:/Users/User/.claude/plans/cosmic-jingling-toast.md`
**기준 시간**: 2026-04-22 11:01 KST

---

## 1. 현 상태 팩트 시트 (실측)

### 1-A. 선결 조건
- settings_drift invariant → `invariants.yaml` L68-70 **WAIVER 적용** (V-1/V-2 후 복원 예정)
- settings.json 활성 hook 31개 ↔ `.claude/hooks/README.md` L9 언급 31개 (동기)
- STATUS.md 파일 부재 (V 단계에서 자동 생성 예정)
- smoke_fast.sh 10/10 ALL PASS (2026-04-22 11:01 베이스라인)
- doctor_lite OK / health_check summary.txt 부재 (IV 단계 전제)
- `.claude/hooks/gate_boundary_check.sh` 미존재 (III-4 신규 설계)

### 1-B. 게이트 3종 현 책임 범위 (코드 실측)
| 게이트 | 등록 | 현 책임 | 원칙 5 목표 | 경계 위반 |
|--------|------|---------|------------|----------|
| commit_gate.sh | PreToolUse/Bash | final_check 강제 + **write_marker 존재 시 TASKS/HANDOFF staged 검증** (L81-98) | Git/staging만 | **위반** |
| evidence_gate.sh | PreToolUse/Bash\|Write\|Edit | req 파일 존재 시 ok 마커 확인 + 300s GRACE_WINDOW suppress | 사전 근거만 | 없음 |
| completion_gate.sh | Stop | Git 미반영 변경 + write_marker mtime vs TASKS/HANDOFF/STATUS mtime 비교 (L37-46, 69-79) | 최종 완료 선언만 | 없음 |

### 1-C. III-5 동반 훅 3종
| 훅 | 등록 | 현 역할 |
|-----|------|---------|
| write_marker.sh | PostToolUse/Write\|Edit | 파일 변경 마커 생성 + `after_state_sync=true` 플래그 생산 |
| evidence_mark_read.sh | PostToolUse/Read\|Grep\|... | 읽기 증거 `.ok` 마커 적립 |
| evidence_stop_guard.sh | Stop | 근거 없는 최종 결론 차단 (exit 2) |

---

## 2. Claude 독립 점검 의제 5개

### 의제 1: commit_gate write_marker 동봉 로직의 이전 방향

**쟁점**: commit_gate.sh L81-98이 `write_marker` 존재 시 TASKS/HANDOFF staged 검증까지 수행. 원칙 5대로 "commit_gate = Git/staging만"으로 축소하면 이 검증은 어디로?

**선택지**:
- **A**: completion_gate로 이관 (Stop 시점 staged 비교 + mtime 비교 병행)
- **B**: 삭제 (write_marker는 문서 갱신 일치만 보증, commit 시점 강제는 없애고 completion_gate의 mtime만으로 충분)
- **C**: commit_gate에 유지 (원칙 5 완화)

**Claude 초안 판정**: **A**. 근거:
1. completion_gate L69-79 FILE_EPOCH 비교가 이미 "상태문서 갱신 강제"의 본거지
2. commit 시점과 Stop 시점 모두 검증이면 "1 Problem 2 Hook" — 원칙 5 직접 위반
3. staged 비교(현재 commit_gate 방식)는 완료 시점엔 의미가 다름(이미 커밋 후이므로 last commit의 파일 목록으로 치환 필요)
4. 구현 비용: completion_gate에 `git log -1 --name-only HEAD` 기반 추가 ~10줄

**리스크**: push 단독 경로는 이미 L113-117에서 skip됨 → completion_gate로 이관 시 push 후 Stop이 있는 세션에서만 효력. commit 후 즉시 세션 종료 없이 다음 작업으로 넘어가면 검증 누락 가능.

**GPT 의견 구함**: A vs B. B(삭제)가 더 단순하지만 체감 품질 저하 가능성. A 이관 방식의 풋건(footgun) 추가 지적 바람.

---

### 의제 2: evidence_gate의 300s GRACE_WINDOW suppress가 "사전 근거만"을 위반하는지

**쟁점**: 300s suppress 로직(최근 근거 있으면 중복 체크 통과)은 "사전"이 아니라 "이미 충족된 근거"로 해석될 여지 있음. 원칙 5 "사전 근거만"에 부합?

**Claude 초안 판정**: **미위반**. 근거:
1. 300s는 동일 fingerprint 중복 검증 억제일 뿐, 근거 자체를 완료 선언으로 승격하지 않음
2. req/ok 마커 시스템은 "사전에 준비된 근거"의 표준 구현
3. 단, suppress 로그 분류 라벨을 `"evidence_recent"` 같은 명시 라벨로 고정해 의미 혼란 방지 권고

**GPT 의견 구함**: 300s 임계값 적정성 + suppress 로그 라벨 명시화 필요성.

---

### 의제 3: III-4 gate_boundary_check.sh 금지 토큰 grep 방식의 오탐 위험

**쟁점**: 계획서 III-4에서 "금지 토큰 검사"로 commit_gate.sh에 `grep "TASKS\|HANDOFF\|STATUS"` → 경로 리터럴이 **주석·로그 메시지**에만 있어도 FAIL. 오탐 높음.

**Claude 초안 대안**:
- **대안 1** (정밀): 금지 토큰 대신 **함수/변수명 기반 검사**. 예: commit_gate에 `_has_tasks` 변수나 `TASKS.md` 경로 사용이 **shell 변수 대입 또는 실제 명령어 인자**로 있을 때만 FAIL. 주석/echo 문자열은 pass. 구현 복잡(정규식 조건 다수).
- **대안 2** (실용): grep 기반 유지하되 `# [gate-boundary-allow]` **주석 화이트리스트**로 의도된 언급 표시. 단순.
- **대안 3** (간접): 직접 검사 대신 각 게이트의 **책임 범위 주석 헤더**(`# SCOPE: git-staging-only` 등)를 요구하고 smoke_fast가 해당 주석과 실제 검사 로직 간 상관을 확인. 높은 구현 비용.

**Claude 초안 판정**: **대안 2** 우선 채택 — 구현 비용 낮음 + 오탐 허용 장치 명시적. 대안 1은 파일 파서(awk/sed) 없이는 정확도 한계.

**GPT 의견 구함**: 대안 1/2/3 중 실무 적정성 + 금지 토큰 grep의 결정적 한계(Claude 미인지 부분) 지적.

---

### 의제 4: III-5 동반 3개의 실제 수정 필요 여부

**쟁점**: 계획서 III-5는 "동반 정리 필수"로 명시했지만, 실측 결과 3개 다 정상 배선 상태. 실질 수정이 필요한가, 아니면 재절단 후 회귀 테스트만 통과하면 되나?

**Claude 초안 판정**:
- **write_marker.sh**: 소비자 이전에 따라 내용 수정 필요. `after_state_sync` 플래그 **의미는 그대로**, commit_gate.sh가 이 플래그를 읽는 코드(L86-98) 제거. write_marker 자체 로직 불변.
- **evidence_mark_read.sh**: evidence 범위 유지(의제 2에서 미위반 판정 시) → 수정 불필요. smoke_fast 통과 확인만.
- **evidence_stop_guard.sh**: completion_gate의 책임이 "Stop 시점 상태문서 + Git 미반영 검증"으로 명확해지면 stop_guard와 completion_gate 사이의 책임 중복 재점검 필요. 현재 stop_guard는 `req 기반 활성` — completion_gate와 다른 축(evidence 잔존 vs 완료 선언)이므로 충돌 없음 예상.

**GPT 의견 구함**: stop_guard와 completion_gate의 Stop 시점 중복 가능성 재검증.

---

### 의제 5: 커밋 단위 (III-1~5 순차 5커밋 vs 묶음)

**Claude 초안**: **4커밋**
- 커밋 A: III-1 commit_gate 축소 + III-5 write_marker 소비자 이전 (생산-소비 쌍 한 단위)
- 커밋 B: III-2 evidence_gate suppress 라벨 명시화 (미위반 판정 전제)
- 커밋 C: III-3 completion_gate write_marker 동봉 검증 이관 (의제 1 A안 채택 시)
- 커밋 D: III-4 gate_boundary_check.sh 신설 + smoke_fast 편입

**근거**: B4 "1커밋 1논리단위"의 논리단위는 "경계 재절단"이므로 생산-소비 쌍(A)이 한 단위. 각 커밋 직후 smoke_fast 10/10 검증.

**GPT 의견 구함**: 커밋 A 묶음의 합리성 + 커밋 C가 의제 1 A안 의존이라 토론 결과에 따라 순서 뒤집힐 가능성.

---

## 3. 응답 형식 요청

각 의제별로:
1. **GPT 판정**: 채택 / 보류 / 버림
2. **근거 1~2문장**
3. **Claude 초안 수정 제안 (있으면)**

의제 간 의존(의제 1이 의제 3/5를 결정)을 명시해 주십시오. 한국어만 사용.

---

## 4. 토론 진행 조건

- 최대 4라운드. 의제 5개 전부 채택/버림 확정 + 구현 경로 확정 시 종결
- 구현은 본 토론 종결 후 별도 세션에서 착수 (세션91은 토론까지)
- GPT 응답 → Claude 하네스 분석(4라벨 + 메타순환/구현경로미정 2라벨 확장) → round2 반박
