# Claude 독립 사전 분석 (Round 1 전)

**일시**: 2026-04-20 10:54 KST
**의제**: `.claude/hooks/debate_verify.sh` 한글 경로 Python3 오탐지 수정 (hook 구조 변경 = B 분류)
**원칙**: 독립의견 유지 — GPT/Gemini 응답 수령 전 Claude 자체 판정 선기록

## 1. 근본 원인 (실증 완료)

사용자 제시 원인 "surrogate escape"과 **다름**:

| 테스트 | 결과 |
|--------|------|
| `python3 -c "p='/c/Users/.../업무리스트/.../result.json'; os.path.exists(p)"` | False, 한글 `��������Ʈ` 깨짐 |
| `python3 -c "p=r'C:\Users\...\업무리스트\...\result.json'; os.path.exists(p)"` | True |
| `cygpath -w` + `os.environ[]` + `PYTHONUTF8=1` | True, JSON load 성공 |

**주원인**: Git Bash POSIX 경로(`/c/...`) → Windows 네이티브 Python3 비호환
**부원인**: 쉘 `$RESULT` 인라인 전개 시 Python 소스 파싱에서 locale(CP949) 기반 해석 → 한글 깨짐

> 주의: `PYTHONUTF8=1`은 런타임 파일 I/O만 UTF-8로 바꾼다. 소스 인라인 전개 시 bash heredoc body의 리터럴은 Python이 파일 인코딩(PYTHONUTF8) 적용 전에 이미 해석됨.

## 2. 더 깊은 관찰 (Claude 독립 추론)

**관찰 A**: incident_ledger에 `debate_verify` 18건 잔존 → 그 18건은 **3way 로직 버그 때문이 아니라 이 인코딩/경로 버그 때문**일 가능성 높음. 즉 "검증 자체가 한 번도 제대로 작동하지 않음"이 유력. Phase 2 승격 보류의 숫자 근거가 훅 자체 내부 결함이었다.

**관찰 B**: 이 버그는 다른 훅도 감염됐을 가능성. `grep -l 'python3 <<PY' .claude/hooks/*.sh` 결과가 2개 이상이면 공통 래퍼(`hook_common.sh`의 `py_read_utf8` 같은)로 추상화 필요.

**관찰 C**: cygpath 의존은 Git-for-Windows 결합. WSL/Cygwin/msys2 등 다른 환경 호환성 리스크. 순수 bash fallback(`${RESULT/#\/c\//C:/}` + `${RESULT//\//\\}`) 병기가 안전.

## 3. Claude 수정안 (사전)

```bash
# debate_verify.sh 80-85행 수정안
RESULT_WIN=$(cygpath -w "$RESULT" 2>/dev/null || echo "${RESULT/#\/c\//C:/}")
VALIDATE=$(RESULT_ENV="$RESULT_WIN" PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 <<'PY' 2>&1
import json, sys, os
try:
    with open(os.environ['RESULT_ENV'], encoding="utf-8") as f:
        d = json.load(f)
# (이하 동일 — heredoc은 <<'PY' quote로 변수 전개 차단)
```

핵심 3변경:
1. `<<PY` → `<<'PY'` (쉘 변수 전개 차단)
2. `r"$RESULT"` → `os.environ['RESULT_ENV']` (경로를 env로 전달)
3. `cygpath -w` + bash substring fallback (POSIX → Windows 변환)

170행 `printf "${ERRORS[@]}" | python3 -c "..."`는 stdin 파이프라 경로 문제 없음 — 수정 불필요. 단 Python `-c` 코드 내부에 쉘 변수 없음을 확인.

## 4. 쟁점 (GPT/Gemini에 물을 것)

1. cygpath fallback 어느 선까지? 순수 bash 구현 충분한가 vs cygpath 의존 허용
2. 공통 래퍼(`hook_common.sh` 함수) 추출 시 훅 범위 — 당장 debate_verify만 수정 vs 다른 훅 전수 점검?
3. Phase 2-C 승격 타이밍 — 이 fix 적용 후 incident 재집계 기간(7일 → 3일?)
4. `PYTHONUTF8=1`이 이미 있는데 한글 깨짐 원인 — 내 분석(소스 인라인 전개 시점 CP949 해석)이 맞는가? 다른 가설 있는가?

## 5. 반드시 지킬 것

- GPT가 "surrogate escape" 용어를 쓰면 그대로 수용 금지 → 내 실증(`os.path.exists` False, 한글 깨짐 뷰)과 대조
- Gemini가 "전면 재설계" 제안 시 과잉설계 라벨 검토
- 양측 모두 1줄 검증 payload에 GPT/Gemini 원문 전체 포함 필수
