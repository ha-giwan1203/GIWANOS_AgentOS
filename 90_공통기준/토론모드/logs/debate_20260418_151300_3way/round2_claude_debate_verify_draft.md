# Round 2 — Claude 설계 초안: /debate-verify hook

> 설계 주체: Claude (3-tool 원칙)
> 검증: GPT + Gemini 양측 1줄 검증 병렬 수행

## 1. 목적
3자 토론(3way) 산출물 커밋 시, **Claude·GPT·Gemini 3자의 합의 서명이 실제 로그에 기록되어 있는지** 기계적으로 강제 검증한다. Claude 오케스트레이션 실수로 한쪽 모델을 누락한 채 "양측 통과" 선언하는 사고(세션68 실제 발생) 재발 방지.

## 2. 실행 지점

### 2-a. PreToolUse (Bash matcher) — 커밋 직전 차단형
- 매처: `Bash` + `git commit` 명령 감지
- 커밋 메시지에 `[3way]` 또는 `debate_.*_3way` 경로 언급 있을 때만 발동
- 검증 실패 시 → 커밋 차단, stderr로 누락 항목 출력

### 2-b. completion_gate 통합 — Stop 단계 최종 보고형
- 기존 completion_gate에서 마지막 커밋 범위 내 `debate_*_3way/` 변경 감지 시 호출
- 실패 시 → 경고 출력(차단 아님, 로그만)

**채택**: 2-a 차단형 우선. 커밋 전 막는 게 누락 재발 방지에 확실.

## 3. 파싱 대상

### 3-1. result.json (필수)
```
90_공통기준/토론모드/logs/debate_YYYYMMDD_HHMMSS_3way/result.json
```

### 3-2. 필수 필드 검증
```python
result.json.turns[*].cross_verification = {
  "gpt_verifies_gemini": {"verdict": "동의|이의|검증 필요", "reason": str},
  "gemini_verifies_gpt": {"verdict": "...", "reason": str},
  "gpt_verifies_claude": {"verdict": "...", "reason": str},
  "gemini_verifies_claude": {"verdict": "...", "reason": str},
  "pass_ratio_numeric": float,
  "round_count": int,
  "max_rounds": int
}
```

### 3-3. 최종 Step5 검증 (산출물 반영 시)
```
round*_claude_synthesis.md 또는 step5_final_verification.md에
"GPT 최종 판정" + "Gemini 최종 판정" 2개 섹션 모두 존재 +
각각에 "통과 / 조건부 통과 / 실패" 키워드 1개 포함
```

## 4. 통과 조건 (AND)

1. result.json이 존재하고 JSON 유효
2. `turns[]` 배열에 최소 1개 턴 존재
3. 각 턴의 `cross_verification` 객체 존재
4. 4개 verdict 키 모두 존재 + 값이 enum `{"동의","이의","검증 필요"}` 중 하나
5. 각 verdict에 `reason` 문자열 1개 이상
6. `pass_ratio_numeric >= 0.67` (또는 최종 round에서만 강제)
7. 산출물 커밋 시 step5_final_verification.md 존재 + 양측 판정 섹션 모두 포함
8. 최종 판정 양측 모두 "통과" (또는 "조건부 통과 → 통과 승격" 명시)

## 5. 실패 분기

| 실패 유형 | 처리 |
|----------|------|
| result.json 없음 | 커밋 차단, "3way 로그 누락" 에러 |
| JSON 파싱 실패 | 커밋 차단, 파싱 에러 줄 번호 출력 |
| cross_verification 누락 | 차단, 누락 필드 목록 출력 |
| 4키 중 일부 누락 | 차단, 누락 키 명시 |
| verdict 값 enum 위반 | 차단, 위반 값 + 허용 enum 출력 |
| pass_ratio < 0.67 | 차단, "합의 실패 — 재라운드 필요" |
| step5 파일 없음 | 차단, "Step 5 최종 검증 로그 생성 필수" |
| Gemini 판정 섹션 누락 | 차단, "3way에서 Gemini 누락 — SKILL.md 5-3 위반" |

## 6. 정규식 / 파싱 패턴

### 6-1. 커밋 메시지 3way 감지
```regex
(?:\[3way\]|3way|debate_\d{8}_\d{6}_3way|3-way|3자\s*토론)
```

### 6-2. verdict enum 매치
```regex
^(동의|이의|검증 필요)$
```

### 6-3. 최종 판정 섹션 매치 (step5_final_verification.md)
```regex
^##\s+(?:GPT|Gemini)\s+최종\s+판정\s*$
```

### 6-4. 판정 키워드 매치
```regex
\*\*(통과|조건부 통과|실패|통과 승격)\*\*
```

## 7. 구현 위치
- 신규 파일: `.claude/hooks/debate_verify.sh`
- settings.local.json hooks.PreToolUse 에 `"matcher": "Bash"` + `command: "bash .claude/hooks/debate_verify.sh"` 추가
- 차단 반환: exit 2 + stderr 메시지 (Claude Code 규약)

## 8. 단계적 적용
- **Phase 1**: 경고만 (stderr, exit 0) → 1주 검증
- **Phase 2**: 차단 전환 (exit 2) → 위반 incident 없을 경우
- **Phase 3**: step5 파일 자동 생성 스켈레톤 헬퍼 추가 (Claude 수동 작성 부담 감소)

## 9. 오탐 대응
- 커밋 메시지에 3way 언급 없지만 실제로 3way 산출물인 경우 → **false negative** → 매 커밋 git diff로 `debate_*_3way/` 경로 변경 확인하는 보조 감지 추가
- 토론 중 중간 커밋(잔여 쟁점 있음)은 `[WIP 3way]` 접두사로 검증 스킵 허용
