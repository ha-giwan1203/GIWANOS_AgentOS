# Round 1 — GPT 본론

**수령 시각**: 2026-05-03 16:11 KST

## 핵심 판정

- **Q1**: dazzling-cannon + fervent-mclaren + **goofy-ptolemy** (Claude의 serene-wiles 대신)
- **Q2**: (b) archive 보존만 + cherry-pick 금지 (동의)
- **Q3**: (c) 폐기 + diff 0 기록 (동의)

## Claude 답안 차이점

**Q1에서 GPT 반론**:
- goofy-ptolemy 배제 근거 부족 — D0 시간 변경 07:05/07:15는 운영 스케줄 직접 연결, scheduler·morning run·업무 시작시간과 연동
- serene-wiles 세션126 evening D0 18건은 main 반영 완료된 **완료형 과거 맥락**
- 따라서 serene 대신 goofy 보존 우선순위가 더 높음

**dazzling vs zealous 임의 선택 비판** (Claude 약점 정확히 지적):
- 둘 다 SHA 동일이지만 선택 기준은 "이름"이 아니라:
  1. git status --short가 깨끗한 쪽
  2. untracked 파일이 없는 쪽
  3. 최근 수정 파일이 적은 쪽
  4. 경로명이 더 설명적인 쪽
  5. 사용자 기억에 더 익숙한 쪽

## R1~R5

- **R1 진짜 원인**: worktree 수 자체보다 "main 반영 완료 worktree 방치 → 인덱싱·탐색·판단 비용 증가". 원인 맞음.
- **R2 즉시 영향**: hook/settings/skill 변경 X. ERP/MES 영향 X. 단 로컬 untracked·plan 비가역 위험.
- **R3 같은 패턴**: SHA 중복 / main 동등 commit / main 동일 파일 / untracked diff 0 / right=0 — 4가지 처리 원칙.
- **R4 incident**: 직접 incident 해결 아님. 단 Phase 8 측정 신뢰성과 context 슬림화 직접 영향.
- **R5 잔존 위험**: 미커밋·untracked·로컬 plan 소실. 대응 5단계 (status_before_prune / patch / diff / 사용자 확인 / list 재검증).

## archive 디렉터리 구조 권고

```
98_아카이브/_deprecated_v1/worktrees/
  README.md
  _inventory_YYYYMMDD.md
  quirky-goldwasser-7f435d/
    README.md
    git_log.txt
    status_before_prune.txt
    commits/6dfa24d6.patch + ab0feda7.patch
  crazy-shannon-f8e7ff/
    README.md / status_before_prune.txt / diff_check.txt
  serene-wiles-721d3b/, zealous-nightingale-4ec2b9/, ...
```

## prune 순서 10단계
1. git worktree list 저장
2. 각 worktree status/log 저장
3. 미반영 commit patch archive
4. untracked 동일성 확인 기록
5. 사용자 active 3개 확정
6. prune 대상 목록 파일 작성
7. git worktree remove <path>
8. git worktree prune
9. git worktree list 재검증
10. baseline_post_phase7.md 작성

## baseline_post_phase7.md 템플릿
- 기준 SHA / 측정 시각 / active 3개 / archive·prune 목록 / git worktree list / count·token 측정 / Phase 8 공식 시작 시각

## 최종 판정
**Claude 답안 부분동의** — Q2/Q3 동의, Q1은 serene → goofy 수정 권고.
