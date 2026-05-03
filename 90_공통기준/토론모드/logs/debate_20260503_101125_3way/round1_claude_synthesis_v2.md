# Round 1 — Claude 종합안 v2 (양측 보완 요청 흡수)

> v1 대비 변경:
> 1. 단일 PR 범위 명확화 — **hook/settings 동작 변경 없이** 태그·백업·격리·측정 베이스라인·폴더 골격까지만 (GPT)
> 2. R5 실물 검증(dry-run) 단계를 단일 PR 작성 **이전**으로 명시 — `.claude → _deprecated_v1/` 이동이 활성 환경을 즉시 깨뜨리는지 사전 확인 (GPT + Gemini 공통)

## v2 변경 패치

### 의제4 PR 통합안 — 단일 PR 범위 명확화

**단일 PR (1회 일괄, hook/settings 동작 무변경 보장)**:
1. main에 `stable-before-reset` 태그 생성
2. `.claude/` 통째 백업 (별도 위치에 사본 보존)
3. 새 폴더 골격 생성 (`.claude/_proposal_v2/` 같은 격리 영역에 새 메타 구조 초안만)
4. 측정 베이스라인 기록 (현재 always-loaded 토큰·rules/* 줄 수·Slash 수·Skill 평균·Hook 수·Worktree 수·incident 누적)
5. **활성 hook/settings/commands/skills 파일은 한 줄도 수정·이동하지 않음**

**Phase별 점진 8단계 (실제 동작 변경)**:
- Phase 1: rules/* 5개 → 1개 통폐합 (always-loaded 토큰 측정값 1차 검증)
- Phase 2: hook 약 45개 → 핵심 5개로 (위험차단 + formatter + sessionstart + 측정 + completion)
- Phase 3: Slash 33개 → 5개 (자동 매칭 엔진으로 이전)
- Phase 4: Skill 21개 평균 305줄 → 80줄 압축
- Phase 5: Subagent 9개 → 5개
- Phase 6: Permissions 130개 → 15개 포괄 패턴
- Phase 7: Worktree 17개 → 사용자 결정 후 prune (사용자가 선언한 "생존 필수 3가지"만 유지)
- Phase 8: 7일 측정 + 1차 평가 + 2차 조정

각 Phase는 별도 PR + 측정값 비교 + 롤백 가능.

### R5 실물 검증 (dry-run) — 단일 PR 작성 이전 강제 단계

> 양측 모두 요청. "**`.claude → _deprecated_v1/` 이동이 활성 환경을 즉시 깨뜨리는지**" 사전 확인.

**검증 절차**:
1. 별도 worktree 생성 (`.claude/worktrees/dry-run-reset/`)
2. 해당 worktree 안에서만 `.claude/` 통째 → `_deprecated_v1/` 이동 시뮬레이션
3. session_start hook 실행 → 동작 여부 확인
4. 핵심 5개 hook (위험차단 + formatter + sessionstart + 측정 + completion) **부재 시 어떤 동작이 깨지는지** 목록화
5. 도메인 스킬 (settlement / line-batch / d0-plan / jobsetup-auto) 5개 dry-run 호출 → 의존성 깨짐 여부
6. 결과를 `R5_dry_run_report.md`로 출력 + 양측 검증 받음

**검증 통과 기준**:
- 핵심 5개 hook 부재 시 깨지는 동작이 사용자가 사전 정의한 "생존 필수 3가지" 안에 없음
- 도메인 스킬 5개 모두 dry-run 성공
- session_start hook 출력이 새 골격(`.claude/_proposal_v2/`)으로 정상 전환

**검증 실패 시**:
- 깨지는 동작 추가 보강 후 재검증
- 또는 메타 0 폭을 줄여 "행동 교정 메타 0"으로만 한정 (Option 4 부분 적용)

### 즉시 실행안 4개로 갱신 (v1의 3개 + R5 dry-run 추가)

1. **R5 dry-run 실측** (단일 PR 작성 이전 강제 단계, 별도 worktree)
2. R5 통과 후 **단일 PR 작성** (골격 + 격리 + 태그 + 측정 베이스라인 / hook·settings 동작 무변경)
3. Round 2 의제 정리 (생존 필수 3가지 + 보류 쟁점 3건)
4. 삭제 목표 수치 합의 (Phase별)

---

## v2 cross_verification (Step 6-5 v2 양측 검증 대기)

```json
{
  "round": 1,
  "synthesis_version": "v2",
  "v1_to_v2_delta": {
    "patches": [
      "단일 PR 범위 = hook/settings 동작 무변경 (태그+백업+격리 폴더+측정 베이스라인까지)",
      "R5 dry-run을 단일 PR 작성 이전 강제 단계로 격상",
      "Phase 8단계 안에 측정값 비교·롤백 명시",
      "즉시 실행안 4개로 확장 (R5 dry-run 추가)"
    ],
    "drivers": ["GPT 검증 필요 + Gemini 동의 반응에서 양측 일치한 보완 요청"]
  },
  "expected_v2_pass": "양측 모두 '동의' 예상 (보완 요청 1:1 흡수)"
}
```
