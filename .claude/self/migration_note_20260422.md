# Migration Note — 세션91 (2026-04-22)

## 배경

Plan glimmering-churning-reef 단계 V-4/V-5 합의에 따른 `protected_assets.yaml` Self-X/quota 블록 정리.

## 변경 사항

### V-4: Self-X 관련 보호 항목 제거

제거된 hook 항목:
- `health_check.sh` — 세션90 I-4에서 SessionStart 등록 해제 (Self-X Layer 1)
- `health_summary_gate.sh` — 세션90 II-1에서 UserPromptSubmit 등록 해제 (Self-X Layer 1)

추가된 hook 항목:
- `gate_boundary_check.sh` — 세션91 III-4 신설 (게이트 3종 경계 재절단 회귀 트립와이어)

### V-5: quota / ttl 블록 완전 제거

제거된 블록 (이전 line 135-156):
- `quota:` hook/command/agent glide_path 정원제 (Self-X Layer 4 B5)
- `ttl:` skill/memory 지식 표면 TTL

이유:
- Self-X Layer 4 B5 Subtraction Quota는 세션91 단계 I~III에서 정책 자체가 폐기됨
- 폐기된 정책의 보호 블록이 live 파일에 잔존하면 "보호 의도 없는데 보호"로 오해
- Round 5 GPT 지적: "live에 남아 있으면 archive 분리가 아니라 죽은 블록 보존"

## 원본 backup

`98_아카이브/session91_glimmering/protected_assets_quota_~session89.yaml`

## 복원 조건

이 변경은 Plan glimmering-churning-reef 전체 롤백 시에만 복원. 그 외 Self-X 재도입은 새 설계 근거 필요.
