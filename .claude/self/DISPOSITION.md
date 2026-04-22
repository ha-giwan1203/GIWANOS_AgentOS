# .claude/self/ Disposition 표 (세션91 단계 IV-4)

> 2026-04-22 작성. Plan glimmering-churning-reef 단계 IV-4 산출물.
> 각 파일의 처리 방침 명시. 단계 V~VII 진행 시 참조.

## 현행 파일

| 파일 | 역할 | Disposition | 근거 |
|------|------|-------------|------|
| `selfcheck.sh` | 주 1회 수동 실행 묶음 (신규, 세션91 IV-2) | **유지** (유일한 자기유지 실행 경로) | 원칙 1 Meta Depth=0, 계획 IV-2 |
| `summary.txt` | 1줄 health summary (selfcheck 출력 타깃) | **유지** | 계획 IV-3 |
| `HEALTH.md` | 상세 health 리포트 (diagnose.py 생성) | **유지** | 수동 selfcheck 출력 타깃 |
| `last_selfcheck.txt` | 마지막 수동 실행 타임스탬프 (신규) | **유지** (SessionStart 정보 표시용) | 계획 보강안 B |
| `diagnose.py` | invariants 평가 (Self-X Layer 1 원본) | **selfcheck.sh로 흡수 후 archive** (단계 V-1/V-2 완료 후) | 계획 IV-4. 현재 selfcheck가 호출 중이므로 즉시 archive 불가 |
| `quota_diagnose.py` | 실행 표면 정원 카운트 (Self-X Layer 4 B5 원본) | **selfcheck.sh로 흡수 후 archive** (단계 V 완료 후) | 계획 IV-4 |
| `last_diagnosis.json` | diagnose.py 캐시 | **diagnose.py archive 시 동반 제거** | 계획 IV-4 |
| `circuit_breaker.json` | Self-X Layer 4 런타임 상태 | **삭제** (세션90 I-3 완료 후 dead) | 계획 IV-4 |
| `meta.json` | Layer 4 메타 invariant 상태 | **삭제** (세션90 I-3 완료 후 dead) | 계획 IV-4 |
| `auto_recovery.jsonl` | Self-X Layer 2 T1 자동 수리 로그 | **archive** (세션90 I-2 완료 후 dead) | 계획 IV-4 |

## 실행 순서 (세션92 이후)

1. **단계 V-1/V-2 완료** (README/STATUS 자동 생성) → settings_drift WAIVER 해제
2. **단계 V-4/V-5 완료** (protected_assets.yaml 정리)
3. **단계 IV-4 후반**:
   - `circuit_breaker.json` / `meta.json` / `auto_recovery.jsonl` 삭제 or archive
4. **단계 IV-5**: `90_공통기준/invariants.yaml` → `98_아카이브/invariants_~session89.yaml`
5. **IV-4 마무리**: `diagnose.py` / `quota_diagnose.py` / `last_diagnosis.json` archive
   - selfcheck.sh에서 호출 코드 제거 (흡수 완료 후)

## 보존 원칙

- **삭제 금지**: `selfcheck.sh`, `summary.txt`, `HEALTH.md`, `last_selfcheck.txt`
- **archive 이동**: `diagnose.py`, `quota_diagnose.py`, `last_diagnosis.json`, `auto_recovery.jsonl`, `invariants.yaml`
- **완전 삭제 허용**: `circuit_breaker.json`, `meta.json` (런타임 상태, 복원 불필요)

## 의존 그래프

```
selfcheck.sh
  ├─ smoke_fast.sh (HOOKS_DIR)
  ├─ doctor_lite.sh (HOOKS_DIR)
  ├─ diagnose.py → invariants.yaml → HEALTH.md / summary.txt
  ├─ quota_diagnose.py
  └─ last_selfcheck.txt
```

단계 V 완료 후 selfcheck.sh는 diagnose/quota 의존 없이 동작하도록 리팩터링 필요 (단계 IV-4 후반).
