# `.claude/_proposal_v2/` — Phase 1 골격

> **이 디렉토리는 활성 환경 영향 0.** 활성 hook/settings/commands/skills 어떤 파일도 본 디렉토리를 로드하지 않음.
> 합의안 v2 Phase 1 = "동작 무변경 보장". `_proposal_v2/`는 Phase 2~8에서 점진 이식할 새 메타 구조의 격리된 초안.

## 디렉토리 구조

```
.claude/_proposal_v2/
├── README.md                       (이 파일)
├── baseline.json                   (Phase 1 시작 시점 정량 측정)
├── delete_target.json              (Phase 2~8 삭제 목표 수치, 첫 커밋에 박힘)
├── CLAUDE.md.draft                 (Boris 100줄 룰 적용 초안, .draft 확장자로 비활성)
├── settings.json.draft             (5개 hook + 15 포괄 permissions 초안)
├── hooks/
│   ├── block_dangerous.sh          (활성 .claude/hooks/ 사본 — 격리)
│   ├── protect_files.sh
│   ├── commit_gate.sh
│   ├── session_start_restore.sh
│   └── completion_gate.sh
└── glossary/
    └── GLOSSARY.json.draft         (단일 플랫 파일 빈 스키마)
```

## Phase 진행 시 절차

각 Phase는 별도 PR + 측정값 비교 + 롤백 가능:

| Phase | 작업 | 활성 영향 | 롤백 |
|-------|------|---------|------|
| 1 (이 PR) | 골격 생성 + tag | 0 | git reset --hard stable-before-reset |
| 2 | rules/* 5→1 통폐합 | rules/ 변경 | tag checkout |
| 3 | hook 36→5 (D 카테고리 6 즉시 archive) | hook archive | tag checkout |
| 4 | Slash 33→5 (skill-rules.json 자동 매칭 엔진) | commands/ 변경 | tag checkout |
| 5 | Skill 압축 + GLOSSARY 신설 + MANUAL 분리 | skills/ 변경 | tag checkout |
| 6 | Subagent 9→5 + Permissions 130→15 | agents/ + settings | tag checkout |
| 7 | Worktree 17→active 3 | worktree prune | git worktree restore |
| 8 | 7일 측정 + 평가 | 0 (검증만) | - |

## 핵심 원칙 (Round 1+2 합의)

1. **출력의 건조함** — 도구는 상태와 데이터만 말함. 자연어 가이드 금지.
2. **결정론적 도구·코드 치환** — 행동 교정 명제 → Permission/Hook/Python verify
3. **메타는 최소, 도메인은 보존**
4. **삭제 목표 수치 강제** — `delete_target.json`에 박힘. 이후 추가 시 PR 거부.

## 롤백

```bash
git reset --hard stable-before-reset
git push --force-with-lease origin main  # 사용자 명시 발화 시만
```

또는 단순 골격만 폐기:
```bash
rm -rf .claude/_proposal_v2/
git commit -am "revert: Phase 1 골격 폐기"
```

## 참조

- 합의 원본: `90_공통기준/토론모드/logs/debate_20260503_101125_3way/`
- 자료 노트: `C:/Users/User/.claude/plans/luminous-skipping-teapot.md`
- baseline 측정: `baseline.json` (이 디렉토리)
