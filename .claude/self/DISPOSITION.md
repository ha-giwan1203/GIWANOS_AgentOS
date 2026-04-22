# .claude/self/ Disposition 표 (세션91 단계 IV-4 / 세션92 완결)

> 2026-04-22 작성, 2026-04-22 세션92 갱신. Plan glimmering-churning-reef 단계 IV 산출물.
> 세션92에서 IV-5 + IV-4 마무리 완료 — Self-X Layer 1/4 원본 파일 전부 archive 완료.

## 현행 파일 (세션92 archive 완료 반영)

| 파일 | 역할 | Disposition | 상태 |
|------|------|-------------|------|
| `selfcheck.sh` | 주 1회 수동 실행 묶음 (세션91 IV-2) | **유지** (유일한 자기유지 실행 경로) | live |
| `summary.txt` | 1줄 health summary (selfcheck 출력 타깃) | **유지** | live |
| `HEALTH.md` | 상세 health 리포트 (과거 diagnose.py 생성본) | **유지** (historical 스냅샷, 수동 갱신) | live |
| `last_selfcheck.txt` | 마지막 수동 실행 타임스탬프 | **유지** (SessionStart 정보 표시용) | live |
| `migration_note_20260422.md` | 세션91 V-4/V-5 제거 근거 기록 | **유지** | live |
| `DESIGN_PRINCIPLES.md` | 자기유지 설계 원칙 7종 (세션91 VI-1) | **유지** (CLAUDE.md 포인터 대상) | live |
| ~~`diagnose.py`~~ | invariants 평가 (Self-X Layer 1 원본) | **archive 완료** (세션92) | `98_아카이브/session91_glimmering/self_state/diagnose.py` |
| ~~`quota_diagnose.py`~~ | 실행 표면 정원 카운트 (Self-X Layer 4 B5) | **archive 완료** (세션92) | 동 `self_state/quota_diagnose.py` |
| ~~`last_diagnosis.json`~~ | diagnose.py 캐시 | **archive 완료** (세션92) | 동 `self_state/last_diagnosis.json` |
| ~~`circuit_breaker.json`~~ | Self-X Layer 4 런타임 상태 | **archive 완료** (세션91 VII-2) | 동 `self_state/circuit_breaker.json` |
| ~~`meta.json`~~ | Layer 4 메타 invariant 상태 | **archive 완료** (세션91 VII-2) | 동 `self_state/meta.json` |
| ~~`auto_recovery.jsonl`~~ | Self-X Layer 2 T1 자동 수리 로그 | **archive 완료** (세션91 VII-2) | 동 `self_state/auto_recovery.jsonl` |

## 90_공통기준/invariants.yaml (세션92 IV-5 완료)

- 원본 위치: ~~`90_공통기준/invariants.yaml`~~
- archive: `98_아카이브/session91_glimmering/invariants_~session89.yaml`
- 이유: Self-X Layer 1 명세 원본. diagnose.py archive와 동반 제거.

## 실행 순서 (완료 기록)

1. ✅ **단계 V-1/V-2** (세션91): README/STATUS 자동 생성 → settings_drift WAIVER 해제
2. ✅ **단계 V-4/V-5** (세션91): protected_assets.yaml 정리
3. ✅ **단계 VII-2** (세션91): `circuit_breaker.json` / `meta.json` / `auto_recovery.jsonl` archive 이동
4. ✅ **단계 IV-5** (세션92): `90_공통기준/invariants.yaml` → archive
5. ✅ **IV-4 마무리** (세션92): `diagnose.py` / `quota_diagnose.py` / `last_diagnosis.json` archive. selfcheck.sh 수정 불필요(optional 체크 구조가 `"archive 상태"` 출력으로 자연 흡수).

## V-2 드리프트 감지 경로 교환 (세션92 명시)

세션91 V-2에서 invariants.yaml의 `settings_drift` invariant 원본 블록을 복원하고 WAIVER를 해제했다. 세션92 IV-5로 invariants.yaml이 archive되면서 이 invariant의 live 평가 경로가 사라진다. **대체 경로**:

- `.claude/hooks/render_hooks_readme.sh` — settings.json 기반 README/STATUS 자동 생성(세션91 V-2 신설). 수동 실행으로 드리프트를 **원천 차단**.
- 감지(사후) → 생성(사전)으로 정책 전환. 드리프트는 render 도구 1회 실행으로 해소되며, 미실행 대비 감지는 수용 가능한 공백으로 판단.
- 근거: 원칙 1 "Meta Depth = 0 (안전안)" — 관측/감지 레이어보다 생성 도구 단일화 우선.

## 보존 원칙

- **삭제 금지**: `selfcheck.sh`, `summary.txt`, `HEALTH.md`, `last_selfcheck.txt`, `migration_note_20260422.md`, `DESIGN_PRINCIPLES.md`
- **archive 완료** (7건): `diagnose.py`, `quota_diagnose.py`, `last_diagnosis.json`, `circuit_breaker.json`, `meta.json`, `auto_recovery.jsonl`, `invariants.yaml`
- **재도입 금지**: 30일 TTL 관찰 기간(2026-04-22 ~ 2026-05-22) 동안 위 archive 파일의 live 경로 재생성 감시(단계 VIII 지표 #6)

## 의존 그래프 (세션92 반영)

```
selfcheck.sh
  ├─ smoke_fast.sh (HOOKS_DIR)
  ├─ doctor_lite.sh (HOOKS_DIR)
  ├─ diagnose.py (archive됨 → "archive 상태" 문구만 출력)
  ├─ quota_diagnose.py (archive됨 → "archive 상태" 문구만 출력)
  ├─ incident_ledger 요약
  └─ last_selfcheck.txt 갱신
```

단계 IV 완료. 다음: **단계 VIII 30일 관찰** (2026-05-22까지).
