# evidence_gate 04-19 집중 발화 분석 (안건 B)

- 생성: 2026-04-20 14:30 KST (세션83)
- 원천: `.claude/incident_ledger.jsonl` (1177행)
- 필터: `classification_reason="evidence_missing"`, 2026-04-13 ~ 2026-04-19 (7일)

## 1. 수치 확정

| 지표 | 값 |
|------|----|
| 7일 evidence_missing 총합 | **332건** (세션82 기록 "333건" 일치) |
| 2026-04-19 건수 | **165건** (7일의 49.7%) |
| hook 분포 (7일) | evidence_gate 272 / skill_instruction_gate 56 / instruction_not_read 4 |
| 04-19 hook 분포 | evidence_gate 129 / skill_instruction_gate 36 |
| 04-19 해소율 | **0 / 165 (resolved:false 전원, false_positive:false 전원)** |

## 2. 일별 매트릭스 (evidence_gate만, 7일)

```
date         map_scope  skill_read  tasks_handoff  commit_tasks  auth_diag  date_check  TOTAL
2026-04-13      28          1            8             0           0          0          37
2026-04-14      26         15           12             0           2          2          57
2026-04-15       4          5            4             0           0          0          13
2026-04-17       3          7            3             0           2          0          15
2026-04-18       9          6            6             0           0          0          21
2026-04-19      46         43           32             8           0          0         129
--------------------------------------------------------------------------------
TOTAL          116         77           65             8           4          2         272
```

04-13은 ledger에 있으나 04-16은 0건(세션 단절 추정). 04-19 129건이 evidence_gate 7일 총합 272건의 **47.4%**.

## 3. 04-19 시간대 분포 (evidence_gate)

```
01:00 KST  42건 ← 집중 구간 (47분 사이)
03:00       9
05:00       9
06:00       6
08:00       6
09:00       6
10:00       9
11:00       6
13:00      12
15:00       6
16:00       5
22:00      10
23:00       3
```

**01:00 세부 (01:06:16 ~ 01:53 UTC = KST 10:06 ~ 10:53)**: 분당 1~3건씩 47분 연속 — 단일 세션의 commit/push 재시도 루프로 판단.

## 4. fingerprint 분포 (evidence_gate 7일, 상위 3종)

| fingerprint | 건수 | 패턴 |
|-------------|-----|------|
| `e4cf9ecff4c3acc7` | 65 | skill_read.req / identifier_ref.req (SKILL.md·기준정보 대조 signal 없음) |
| `87bd66d7f815c6b4` | 58 | map_scope.req (변경대상/연쇄영향/후속작업 3줄 선언 없음) |
| `04a15c174f876e76` | 57 | tasks_handoff.req (TASKS/HANDOFF 갱신 없이 commit/push) |
| 그 외 14종 | 92 | 변종 경로/파일/commit 메시지 |

**상위 3종 = 180건 / 272건 = 66%**. 17종 unique fingerprint 중 3종에 집중 → **동일 상황 반복 발화**.

## 5. 가설 후보 (3자 토론 의제 1 Round 2 입력)

### 가설 α — `.ok` 마커 수명 부정합
- map_scope 한 번 선언해도 후속 커밋마다 재요구되는 구조 의심
- 해소 신호(`.claude/state/*.ok`) TTL·scope(세션 vs 커밋 vs 작업단위)가 불명확
- **검증 방법**: `evidence_mark_read.sh`·`map_scope.sh` 등 `.ok` 생성 훅과 `evidence_gate.sh` 소비 훅의 경로·TTL 일치 여부 코드 비교

### 가설 β — 01:00 KST 단일 세션 42건 = 학습루프 진단 구간
- 세션80 HANDOFF 기록상 "학습루프 진단 + 4단계 보정" 작업이 2026-04-19 전후로 집중
- commit이 tasks_handoff/map_scope/skill_read 3종 gate에 연쇄 차단되며 재시도 → 42건
- **검증 방법**: git log `--since=2026-04-19T01:00Z --until=2026-04-19T02:00Z` 대조

### 가설 γ — fingerprint 중복 억제 부재
- 동일 fp 연속 발화에 대한 self-throttle(쿨다운) 없음
- 같은 사유로 1분 내 3번 차단되면 4번째부터 ledger 기록 스킵 or warn 강등이 합리적
- **검증 방법**: `evidence_gate.sh`에 rate-limit 로직 존재 여부 grep

### 가설 δ — skill_instruction_gate 36건 별개 경로
- evidence_gate(129)와 다른 hook(skill_instruction_gate 36)이 병행 차단
- 세션 시작 시 SKILL.md read 신호 없이 진입한 `/skill` 호출 시점 차단 추정
- **검증 방법**: `skill_instruction_gate.sh` 발화 조건과 SessionStart SKILL read 타이밍 상관 분석

## 6. 즉시 조치 권고 (A Round 2 이전)

1. **수치 확정 완료** — 세션82 기록 정정 불필요 (332≈333 반올림 차)
2. **가설 α·γ가 최우선**: 구조적 반복 발화 차단이 효과 큼
3. **가설 β는 운영 맥락**: "기록되는 게 정상", 억제 대상 아님 (실제 문제 세션은 해결됨)
4. **가설 δ는 별건**: A 의제 분기 필요 여부는 GPT·Gemini 판단에 맡김

## 7. A 3자 토론 의제 1 Round 2 입력으로 쓸 3문항

1. 가설 α(`.ok` 마커 수명·scope 불일치) 실증 경로와 조치안은?
2. 가설 γ(fingerprint self-throttle) 도입 시 advisory→gate 등급 차별화는?
3. 가설 δ(skill_instruction_gate 36건)는 의제 1에 포함할지 별건 분리할지?
