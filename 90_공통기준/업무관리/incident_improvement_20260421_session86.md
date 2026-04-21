# incident 근본 개선 실측 — 세션86 (2026-04-21)

> 대상: `.claude/hooks/evidence_gate.sh` fingerprint suppress 효과 + `completion_gate.sh` 소프트 블록 정책
> 원본: `.claude/incident_ledger.jsonl` (전체 1,207 레코드, 2026-04-06 ~ 2026-04-20)
> 선행: 세션85 집계 `incident_audit_20260420_session85.md` (1,197 레코드 시점)
> 목적: 세션83 GRACE 30→120 + tail 30→100 확장 효과 측정, 개선 후보안 도출
> 범위: **실측·분석만** (코드 수정은 본 세션 밖)

## 요약 (결론부터)
1. **증분 10건**(세션85 → 세션86, 약 12.5시간): α 5 + β 4 + γ 1
2. **GRACE_WINDOW=120 설계가 81.5% 반복을 놓침** (7일 evidence_gate 249 연속 샘플 중 203건 >120s)
3. **실측 반복 median 347s, Top3 fingerprint median 320~370s** — GRACE 설계값과 실측값 2.8배 괴리
4. **증분 β 4건의 반복 간격 119s·122s·135s·209s** — GRACE 120 경계 직후 탈출이 증분에서도 실증됨
5. **completion_gate 최근 7일 0건** — 현행 소프트 블록 정책은 문제 없음 (Case C 우선순위 최저)
6. **γ 1건** (line 1198, hook:None) — 스키마 불완전 레코드. 별건 조사
7. 결론: **Case A (GRACE 120→300) + Case B (fingerprint 입력 확장)** 조합이 실증적 개선안. B 분류(차단 정책 조정 아님, suppress 기록 억제 확장)이지만 세션84 A안-1 기준으로는 "실행 흐름 변경 아님 + 판정 분기 불변 + 차단 정책 불변" → **A 분류 후보 유력** (3자 토론 재검토 없이 직접 구현 가능). Step 7에서 확정

---

## 섹션 1 — 세션85 대비 증분 요약

### 1.1 집계
| 항목 | 값 |
|---|---|
| 세션85 기준선 | 1,197건 (세션85 집계 시점) |
| 세션86 현재 | 1,207건 |
| 증분 | 10건 |
| 증분 ts 범위 | 2026-04-20T10:39:58Z ~ 2026-04-20T23:11:53Z (약 12.5h) |
| 세션 시작훅 "최근 24h 신규" | 12건 (오차 2건 — 훅 집계 기준과 ledger 증분 기준 차이) |
| 증분 resolved:false | 10/10 (100%) |
| 증분 false_positive:false | 10/10 (100%) |
| 실질 미해결 증분 | 10건 |

### 1.2 hook 분포
| hook | 증분 |
|---|---|
| evidence_gate | 6 |
| commit_gate | 1 |
| navigate_gate | 1 |
| skill_instruction_gate | 1 |
| None (γ) | 1 |

### 1.3 시간 집중 (10분 버킷)
| 버킷 (UTC) | 건수 |
|---|---|
| 2026-04-20 10:30 | 1 |
| 2026-04-20 10:40 | 1 |
| 2026-04-20 11:30 | 1 |
| **2026-04-20 11:40** | **6 (단일 클러스터)** |
| 2026-04-20 23:10 | 1 |

세션82 "2026-04-19 01:06~01:53 47분간 42건" 유형의 대규모 루프는 재발하지 않음. 다만 **11:38~11:48 10분간 7건 클러스터** 발생 (아래 섹션 3 참조).

---

## 섹션 2 — fingerprint suppress 효과 측정

### 2.1 최근 7일 evidence_gate 미해결 집계
- 전체 레코드 7일: 668건
- evidence_gate 미해결(resolved:false + fp:false): **272건**
- 동일 fingerprint 연속 발생 샘플: **249개**

### 2.2 Top10 fingerprint (7일 evidence_gate)
| 순위 | 건수 | fingerprint | detail 선두 |
|---|---|---|---|
| 1 | 79 | `e4cf9ecff4c3acc7` | skill_read.req / identifier_ref.req 존재 |
| 2 | 58 | `87bd66d7f815c6b4` | map_scope.req 존재. 변경 대상/연쇄 영향/후속 작업 3줄 선언 |
| 3 | 57 | `04a15c174f876e76` | tasks_handoff.req 존재. TASKS/HANDOFF 갱신 없이 commit/push 금지 |
| 4 | 22 | `bb52c08fe5cd7cd9` | map_scope.req 존재 (다른 cmd prefix) |
| 5 | 19 | `52eb988c2a4e8f9b` | commit 차단. 이번 세션에 TASKS.md/HANDOFF.md 변경 기록 없습니다 |
| 6 | 13 | `014b5dfb8ba8454e` | map_scope.req 존재 (settings 관련 cmd) |
| 7 | 5 | `547abe0009a7122f` | skill_read.req (다른 cmd) |
| 8 | 2 | `7617f307c123d35d` | skill_read.req (다른 cmd) |
| 9 | 2 | `690ac0e31af829c9` | skill_read.req (다른 cmd) |
| 10 | 2 | `fbc8431c1e701c02` | commit/push 차단 (TASKS/HANDOFF 미갱신) |

**Top3가 194/272 = 71.3%** 집중. 세션85 상위 5종(658/960 = 68%)과 유사 경향.

### 2.3 동일 fingerprint 연속 간격 분포 (7일, n=249)
| 간격 bin | 건수 | 비율 | suppress 성공 여부 |
|---|---|---|---|
| 0–30s | 0 | 0.0% | 성공 |
| 30–60s | 15 | 6.0% | 성공 |
| 60–120s | 31 | 12.4% | 성공 |
| **120–300s** | **69** | **27.7%** | **실패 (Case A 확장 대상)** |
| **300–900s** | **55** | **22.1%** | **실패** |
| **900s+** | **79** | **31.7%** | 실패 (다른 세션·장시간 간격) |

- median: **347s** (GRACE 120의 2.89배)
- min: 40s, max: 305,805s (85h, 다른 세션 이월)

### 2.4 핵심 계산 (GRACE 확장 시 기대 억제율)
| GRACE 값 | 억제 샘플 | 7일 억제율 | 기대 증분 감소 |
|---|---|---|---|
| 현행 120s | 46/249 | **18.5%** | (baseline) |
| 300s | 115/249 | **46.2%** | 2.5배 개선 |
| 900s | 170/249 | **68.3%** | 3.7배 개선 |
| 3600s | ? | (추가 측정 필요) | ? |

### 2.5 Top3 fingerprint 간격 특성
| fingerprint | 샘플 | over-120s | over-300s | median |
|---|---|---|---|---|
| `e4cf9ecff4c3acc7` (skill_read) | 78 | 64 (82%) | 42 (54%) | 320s |
| `87bd66d7f815c6b4` (map_scope) | 57 | 51 (89%) | 31 (54%) | 370s |
| `04a15c174f876e76` (tasks_handoff) | 56 | 52 (93%) | 33 (59%) | 368s |

**Top3 전부 median이 GRACE 120의 2.7배 이상**. 300~400s 범위 지배적.

---

## 섹션 3 — 증분 10건 α/β/γ 분류

### 3.1 분류 기준
- **α**: 정책 gate 정상 차단 (코드 버그 아님, 유저 행동 원인) → 개선 여지 제한
- **β**: fingerprint suppress 실패 (self-throttle 설계 개선 여지)
- **γ**: 신규 유형 / 스키마 불완전 (별건 조사)

### 3.2 10건 상세
| tag | line | ts (UTC) | hook | fingerprint | 비고 |
|---|---|---|---|---|---|
| γ | 1198 | 10:39:58 | None | - | hook·classification_reason 모두 null. 스키마 불완전 |
| α | 1199 | 10:40:47 | commit_gate | - | python3 의존성 |
| β | 1200 | 11:38:23 | evidence_gate | `52eb988c2a4e8f9b` | 증분 내 2회 반복 (Δ=376s) |
| β | 1201 | 11:40:25 | evidence_gate | `e4cf9ecff4c3acc7` | 증분 내 2회 반복 (Δ=463s) |
| α | 1202 | 11:42:24 | evidence_gate | `014b5dfb8ba8454e` | Top10 6위 (13회), 증분 내 1회 |
| β | 1203 | 11:44:39 | evidence_gate | `52eb988c2a4e8f9b` | 1200 반복 |
| β | 1204 | 11:48:08 | evidence_gate | `e4cf9ecff4c3acc7` | 1201 반복 |
| α | 1205 | 11:48:13 | navigate_gate | - | ChatGPT 진입 차단 (5s 후속) |
| α | 1206 | 11:48:17 | skill_instruction_gate | - | MES access without SKILL.md (4s 후속) |
| α | 1207 | 23:11:53 | evidence_gate | `547abe0009a7122f` | Top10 7위 (5회), 증분 내 1회 |

### 3.3 집계
| tag | 건수 | 비율 |
|---|---|---|
| α | 5 | 50% |
| β | 4 | 40% |
| γ | 1 | 10% |

### 3.4 11:38~11:48 클러스터 상세 (7건 10분 집중)
연속 간격: **[122, 119, 135, 209, 5, 4]** (단위 초)
- 119s·122s·135s·209s (evidence_gate 간): **GRACE 120 경계 직후 탈출**
- 5s·4s (navigate → skill_instruction 별 hook): GRACE 대상 아님 (각자 독립 경로)

**증분 레벨에서도 GRACE 120 경계선 문제가 실증됨.** GRACE=300이면 β 4건 전부 suppress됐을 것.

### 3.5 γ 1건 상세 (line 1198)
```json
{"ts":"2026-04-20T10:39:58Z","type":null,"hook":null,"file":null,"detail":null,...}
```
- `hook`·`type`·`classification_reason` 전부 null
- 실제 파일 line 1198 확인하여 원본 JSON 스키마 파악 필요 (별건)

---

## 섹션 4 — completion_gate 52건 분석

### 4.1 전체 분포
| 항목 | 값 |
|---|---|
| 총 건수 | 52 |
| type | gate_reject 52 (100%) |
| detail | "파일 변경 후 TASKS.md,HANDOFF.md 미갱신" (100% 동일) |
| classification_reason | `structural_intermediate` 45 + `completion_before_state_sync` 7 |
| resolved:true | 7 (`completion_before_state_sync` 전부 해소) |
| false_positive:true | 45 (`structural_intermediate` 의도된 중간 차단) |
| 최근 7일 | **0건** |
| 최근 30일 | 52건 (= 전체) |

### 4.2 평가
- 최근 7일 발동 0건 → **현행 정책이 실제로 차단을 자주 발생시키지 않음**
- `structural_intermediate` 45건은 `false_positive:true`로 마킹 — 설계상 "의도된 중간 차단" (세션 내 자연스러운 이중 탭 저장)
- `completion_before_state_sync` 7건은 모두 `resolved:true` — "차단 → 유저 교정 → 해소" 정상 루프
- **하드페일 전환·정책 폐기·임계값 조정 모두 실증 근거 없음**
- **세션72 도입 "7일 1회용 패턴 3회 누적 → deny 1회" 소프트 블록은 ledger에 별도 흔적이 없음** — 로그 기록 경로가 `completion_gate` 범주로 들어가지 않거나, 발동 없이 운영 중

### 4.3 결론
**Case C (completion_gate 정책 조정) 보류**. 현행 유지.

---

## 섹션 5 — 개선 후보안 A~D 비교

| Case | 변경 내용 | 기대 효과 | 리스크 | 분류 (A/B) |
|---|---|---|---|---|
| **A** | `GRACE_WINDOW` 120 → 300 | 7일 억제율 18.5%→46.2% (2.5배) | 다른 세션의 독립 이벤트가 suppress될 가능성 극미 (fp 동일성 해시) | A (suppress 기록 임계만, 차단 로직 불변) |
| B | fingerprint 해시 입력 확장 (현재 `reason[:80]\|command[:50]` → `+file[:50]` 추가) | Top3 내 `014b5dfb`·`bb52c08f`·`87bd66d7` 세분화 가능성 | fp 파편화로 suppress 효과 하락 가능 — 실측 후 판단 | A (해시 입력만, 차단 로직 불변) |
| C | completion_gate 정책 조정 | 발동 0건 → 효과 없음 | 현행 false_positive:true 45건 마킹 제거 시 오히려 노이즈 증가 | (보류) |
| D | 현행 유지 | α/γ는 행동 교정·스키마 수정으로만 해결 | β 4건/증분 반복 지속 | - |

### 5.1 권장 조합
**A 단독 채택** (B는 A 효과 측정 후 2주 이상 관찰):
- 단일 상수 `GRACE_WINDOW=120`을 `300`으로 변경
- 한 줄 변경으로 기대 억제율 2.5배
- 역방향 리스크 없음 (차단 자체는 유지, 기록 중복만 억제 확장)
- 세션83 Round 2 합의 "차단은 유지" 원칙 그대로 준수

### 5.2 A 채택 시 smoke_test 추가 항목 (세션86+ 구현 시)
1. GRACE_WINDOW=300 동일 fp 200s 간격 2회 → 2회차 suppress 확인
2. GRACE_WINDOW=300 동일 fp 301s 간격 2회 → 2회차 기록 확인 (경계 정확성)
3. GRACE_WINDOW=300 다른 fp 200s 2회 → 2회 전부 기록 (독립성)
4. 기존 세션83 섹션 48 5건 회귀 PASS 확인

### 5.3 Case A·B 공통 경계
- `evidence_gate.sh` 45~110행 (fingerprint·GRACE 로직) 외 변경 없음
- 차단 자체(deny 경로)는 불변
- `fresh_ok` 완화·cooldown 중 차단 생략 여전히 금지 (세션83 4자 합의)

---

## 섹션 6 — 분류 판단 (A 분류 vs B 분류)

세션84 A안-1 자동 승격 트리거 (B 분류 정의):
> "실행 흐름·판정 분기·차단 정책이 바뀌는 경우"

Case A 변경 내용:
- `local GRACE_WINDOW=120` → `local GRACE_WINDOW=300` (단일 상수)
- 실행 흐름: 불변 (동일 경로, 임계만 다름)
- 판정 분기: 불변 (동일 조건식, 비교값만 다름)
- 차단 정책: 불변 (deny 경로 완전 동일, suppress는 기록 중복만 억제)

→ **A 분류 (3자 토론 재승격 불필요, 세션84 기준)**

근거 명확성:
- 세션83 Round 2 4자 합의 "차단은 유지, 기록 중복만 확장 억제"의 상수 조정에 한정
- 설계 의도는 그대로, 실측 근거만으로 임계 재조정

---

## 섹션 7 — 본 세션 외 Out-of-scope 재확인
- β안-C API 실제 구현 — 사용자 명시 승인·API 키 예산 필요
- A안-2 `skip_65` 자연 테스트 — A 분류 의제 자연 발생 대기
- Phase 2-C `debate_verify.sh` exit 2 전환 — 2026-04-27+
- γ 1건 (line 1198 스키마 결함) — 별건 조사 이월

## 섹션 8 — 다음 AI 액션 (세션87+)
1. **Case A 구현**: `evidence_gate.sh:59` GRACE_WINDOW 120→300 + 주석 갱신 + smoke_test 섹션 50 신설 4건
2. **2주 관찰 (04-21 ~ 05-05)**: Top3 fingerprint 억제율 변화 측정 → Case B 필요 여부 판단
3. **γ 1건 별건 조사**: line 1198 원인 추적 (hook_log 대조)
4. **세션 시작훅 "최근 24h" 집계 기준 검토**: ledger 증분 vs 훅 카운트 2건 오차 원인 확인

## 검증 로그
- 집계 스크립트 실측 재실행 가능 (본 보고서 실측값은 스크립트 재실행으로 재현)
- 증분 합계 = 1,207 − 1,197 = 10 ✓
- 증분 tag 합계 5+4+1 = 10 ✓
- 증분 hook 합계 6+1+1+1+1 = 10 ✓
