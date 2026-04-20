# Step 5 최종 검증 — 경로 회귀 테스트 체크리스트

> Phase 2-C 재평가 (2026-04-27 전후) 전 필수 회귀 테스트
> 세션81 debate_verify.sh 한글 경로 오탐지 수정 이후 영문/특수문자/한글 3종 경로에서 동일하게 작동 보증

## 배경
- 세션81 (2026-04-20): debate_verify.sh heredoc 인라인 삽입 취약 패턴 수정 — POSIX 경로 `/c/Users/...` + 쉘 `$RESULT` 인라인 전개 시 locale 경유 한글 경로 깨짐 해소
- 세션82 GPT A 제안: Phase 2-C 승격 판정 전에 영문·특수문자·한글 경로 3종 회귀 테스트로 커버리지 보강 필요

## 회귀 테스트 케이스 (3종)

### 1. 영문 경로
- 테스트 경로: `C:\Users\User\test_debate\logs\debate_20260427_000000_3way\round1_gpt.md`
- 검증: `debate_verify.sh` 실행 시 파싱 성공 + 해당 세션 서명 검증 통과
- 기대: `exit 0` + `PASS` 또는 정상 분석 결과

### 2. 특수문자 포함 경로
- 테스트 경로: `C:\Users\User\test-dir (backup)\logs\debate_20260427_000000_3way\round1_gpt.md`
- 공백·소괄호·하이픈 포함
- 검증: heredoc `<<'PY'` quoted + `os.environ['RESULT_ENV']` 경로 주입 동작 확인
- 기대: 셸 전개 중 quote 손실 없이 파싱 성공

### 3. 한글 경로
- 테스트 경로: `C:\Users\User\Desktop\업무리스트\90_공통기준\토론모드\logs\debate_20260427_000000_3way\round1_gpt.md`
- 검증: `cygpath -w` 변환 우선 + 범용 sed fallback + Python `os.path.normpath()` 2차 안전망 동작 확인
- 기대: "파싱 실패 [Errno 2]" 오탐지 미발생, 정상 검증 로직 진입

## 실행 절차 (수동)

```bash
cd "/c/Users/User/Desktop/업무리스트"

# 각 경로에 mock 토론 로그 생성 후
for test_path in \
    "/c/temp/debate_20260427_000000_3way" \
    "/c/temp/test-dir (backup)/debate_20260427_000000_3way" \
    "/c/Users/User/Desktop/업무리스트/tmp_debate_20260427_000000_3way"; do
  mkdir -p "$test_path"
  # 최소 mock 로그 (round1_gpt.md, round1_gemini.md, round1_claude_synthesis.md)
  cat > "$test_path/round1_gpt.md" << 'EOF'
## GPT Round 1 판정
- 채택: 1건 / 보류: 0건 / 버림: 0건
- 판정: 통과
EOF
  cat > "$test_path/round1_gemini.md" << 'EOF'
## Gemini Round 1 판정
- 채택: 1건 / 보류: 0건 / 버림: 0건
- 판정: 통과
EOF
  cat > "$test_path/round1_claude_synthesis.md" << 'EOF'
## Claude 종합
- pass_ratio: 2/2
- 최종 합의: 통과
EOF

  # debate_verify.sh 실행
  echo "=== TEST: $test_path ==="
  bash .claude/hooks/debate_verify.sh --dry-run --log-dir "$test_path" 2>&1 | head -10

  # 정리
  rm -rf "$test_path"
done
```

## 합격 기준

| 케이스 | 실측 결과 | 판정 |
|--------|----------|------|
| 영문 경로 | exit 0 + 정상 분석 | 필수 PASS |
| 특수문자 경로 | exit 0 + quote 손실 없이 파싱 | 필수 PASS |
| 한글 경로 | exit 0 + 한글 깨짐 없이 파싱 | 필수 PASS (세션81 수정 대상) |

**3건 모두 PASS**해야 Phase 2-C 승격 (advisory→gate 전환) 진행.

## Phase 2-C 승격 조건 (세션82 합의 재확인)

1. 위 회귀 테스트 3건 모두 PASS
2. 2026-04-27 이후 7일간 `type=debate_verify` incident 0건 (세션81 커밋 SHA `408c4856` 기준 재집계)
3. exit 2 + JSON `decision=deny` 전환 (기존 Phase 2-B 6종 준용)
4. 양측 모델(Gemini·GPT) 판정 PASS 교차 검증

## 변경 이력
- 세션83 (2026-04-20): 신규 작성. 세션82 GPT A 제안 반영
