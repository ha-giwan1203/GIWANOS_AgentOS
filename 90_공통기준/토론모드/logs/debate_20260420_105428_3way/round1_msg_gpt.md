=== 신규 의제 (3자 토론 Round 1) ===

앞서 지적한 훅 과밀·상태 분산의 **실증 사례** 하나 띄웁니다. 별개 의제로 판정 요청.

**의제**: `.claude/hooks/debate_verify.sh` 한글 경로 Python3 오탐지 수정 (hook 구조 변경 = B 분류, 3자 승격 대상)

**증상**
- `[3way] 커밋` 시 "result.json 파싱 실패: [Errno 2] No such file or directory" 오탐지
- 실물 파일 정상 존재: `/c/Users/User/Desktop/업무리스트/90_공통기준/토론모드/logs/debate_20260420_010101_3way/result.json` (JSON valid, turns=1)
- incident_ledger에 `debate_verify` 태그 18건 누적 (Phase 2 승격 보류 근거)

**Claude 실증한 근본 원인** (사용자가 제시한 surrogate escape와 다름)
주원인: Git Bash POSIX 경로 `/c/Users/...` → Windows 네이티브 Python3 비호환 (os.path.exists False)
부원인: 쉘 `$RESULT` 인라인 전개 시 Python 소스가 한글을 CP949로 깨뜨림 (`업무리스트` → `??????????`)

재현 결과:
- `p='/c/Users/.../업무리스트/.../result.json'` → exists False, 한글 깨짐
- `p=r'C:\Users\...\업무리스트\...\result.json'` → exists True
- `cygpath -w` + `os.environ[]` + `PYTHONUTF8=1` 조합 → exists True, JSON load 성공

**Claude 수정안**
```
# debate_verify.sh 80-85행
RESULT_WIN=$(cygpath -w "$RESULT" 2>/dev/null || echo "${RESULT/#\/c\//C:/}")
VALIDATE=$(RESULT_ENV="$RESULT_WIN" PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 <<'PY' 2>&1
import json, sys, os
try:
    with open(os.environ['RESULT_ENV'], encoding="utf-8") as f:
        d = json.load(f)
# (이하 동일. 변경 3점: <<PY→<<'PY', r"$RESULT"→os.environ, cygpath+bash fallback)
```

**Claude 독립 관찰 (중요)**
incident 18건 잔존 = Phase 2 승격 보류 근거였는데, 그 18건은 **3way 검증 로직 버그가 아니라 이 인코딩/경로 버그 때문**일 가능성 매우 높음. 즉 훅이 한 번도 제대로 작동한 적 없음. 이 fix 후 incident 0 달성하면 Phase 2-C 승격 타이밍 재산정 가능.

**GPT에 요청하는 판정 5개**
1. 근본 원인 진단 맞는가? (POSIX 경로 + 쉘 인라인 CP949, surrogate escape 아님)
2. 수정안 3점 변경(`<<'PY'` quote, `os.environ[]`, cygpath+bash fallback)이 충분한가? 다른 python3 heredoc 훅에도 동일 패턴 전수 점검해야 하는가?
3. 170행 `printf "${ERRORS[@]}" | python3 -c` 파이프 stdin 전달 구간은 수정 대상 아닌가? (Claude 판정: 수정 불필요)
4. Phase 2-C 승격 타이밍 — 이 fix 후 incident 재집계를 며칠 관찰해야 하는가? (기존 7일 유지 vs 3일 단축)
5. cygpath 의존도 — 순수 bash substring fallback만으로 충분한가, 아니면 Python 측에서도 경로 정규화 필요한가?

응답 형식: 본론 답변 → 마지막에 5개 항목 각각 "통과 / 조건부 통과 / 실패 — 근거 1문장"
