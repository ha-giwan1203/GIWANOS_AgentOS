# Round 1 — Claude 종합 설계안

**일시**: 2026-04-20 11:25 KST
**기준**: GPT Round 1(조건부통과×3 + 통과×1 + 실패×1) + Gemini Round 1(GPT 전면 동의) + Claude 독립 분석

## 채택 결정

양측 합의된 사항을 모두 반영하고, GPT의 "실패 1건"(cygpath fallback 범용성)과 "조건부 1건"(heredoc 전수 점검)을 종합안에 통합.

### 채택 리스트

1. **POSIX 경로 → Windows Python 미스매치가 주원인** (surrogate escape 가설 폐기)
2. **<<'PY' + os.environ[] + cygpath** 3점 변경 반영
3. **fallback 일반화** — C드라이브 전용 `${RESULT/#\/c\//C:/}` 버림, 범용 `sed` 정규식 패턴 적용
4. **Python 측 2차 안전망** — `os.path.normpath()` + POSIX prefix regex 정규화
5. **170행 stdin 파이프는 수정 제외** (통과 확정)
6. **statusline.sh 동일 커밋 수정** — heredoc 인라인 패턴 전수 점검 범위
7. **Phase 2-C 승격 7일 유지** + 3way 커밋 성공 샘플 수 확인 병행 (이번 fix로 incident 재집계 시작점만 리셋, 승격 타이밍 변경 없음)
8. **표현 완화** — 코멘트/문서에서 "CP949가 원인" → "쉘 인라인 전개 중 locale/code page 경유 한글 경로 깨짐"

### 범위 확인 결과

`grep "python3 <<PY"` (quoted 없이) = **2개 파일만 감염**:
- `.claude/hooks/debate_verify.sh` (이번 의제)
- `.claude/hooks/statusline.sh` 13행: `d = json.loads('''$input''')`

> statusline.sh는 경로 문제가 아니라 **JSON 입력값 escape 문제**(작은따옴표 3개 포함 시 파싱 실패). 같은 "heredoc 변수 인라인 삽입" 취약 패턴이지만 트리거 조건은 다름. 동일 커밋에 수정하되 해결책은 **stdin 파이프로 전달**이 더 자연스러움.

## 최종 수정안

### Fix 1: `.claude/hooks/debate_verify.sh` (80-85행)

```bash
# 경로를 Windows 형식으로 사전 변환 (cygpath 우선 + 범용 sed fallback)
RESULT_WIN=$(cygpath -w "$RESULT" 2>/dev/null || \
             echo "$RESULT" | sed -E 's|^/([a-zA-Z])/|\1:/|')

# heredoc body는 quoted ('PY')로 쉘 전개 차단, 경로는 환경변수로 전달
VALIDATE=$(RESULT_ENV="$RESULT_WIN" PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 <<'PY' 2>&1
import json, sys, os, re
path = os.environ['RESULT_ENV']
# Python 측 2차 안전망: POSIX `/<letter>/` prefix 정규화 + normpath
path = re.sub(r'^/([a-zA-Z])/', r'\1:/', path)
path = os.path.normpath(path)
try:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
except Exception as e:
    print(f"JSON_ERROR:{e}"); sys.exit(1)

issues = []
turns = d.get("turns", [])
# (이하 기존 검증 로직 동일)
PY
)
```

**핵심 변경 4점**:
1. `<<PY` → `<<'PY'` (쉘 변수 전개 완전 차단)
2. `open(r"$RESULT", ...)` → `open(os.environ['RESULT_ENV'], ...)` (인라인 삽입 제거)
3. `cygpath -w` + **범용 sed 변환** (`/d/`, `/e/` 등 모든 드라이브 문자 처리, `/cygdrive/c/` prefix도 별도 처리 필요 시 확장 가능)
4. Python 내부 `re.sub` + `os.path.normpath()` 2차 안전망 (bash 실패해도 Python이 방어)

### Fix 2: `.claude/hooks/statusline.sh` (7-22행) — 동일 커밋

```bash
# 기존 7행: input=$(cat)
# 변경: 변수 저장하지 않고 바로 stdin 파이프로 Python 전달

parsed=$(cat | PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python3 <<'PY' 2>/dev/null
import json, sys, os
try:
    d = json.load(sys.stdin)
    model = d.get('model', {}).get('display_name', 'claude')
    cwd = d.get('workspace', {}).get('current_dir', os.getcwd())
    cwd_short = os.path.basename(cwd.rstrip('/').rstrip('\\'))
    cost = d.get('cost', {}).get('total_cost_usd', 0)
    print(f"{model}|{cwd_short}|{cost:.2f}")
except Exception:
    print("claude|?|0.00")
PY
)
```

**변경 이유**: stdin 파이프로 전달하면 `$input`을 Python 소스에 인라인 삽입할 필요 없음. JSON 입력값 내 따옴표/개행 등 escape 문제 근본 해소.

### Fix 3: 주석/문서 표현 완화

`debate_verify.sh` 변경 주석에 포함할 문구:

```
# Windows Git Bash에서 POSIX 경로(/c/Users/...)를 네이티브 Python3에 전달 시
# os.path.exists 오탐지 + 쉘 인라인 전개 중 locale/code page 경유 한글 경로 깨짐 이슈 해결.
# cygpath + os.environ + <<'PY' quoted heredoc 조합으로 3중 방어.
```

("CP949" 단어 명시 제거 — 환경 종속성 반영)

## 검증 체크리스트

- [ ] Fix 1 + Fix 2 적용 후 `debate_verify.sh` 재실행 → 오탐지 해소
- [ ] `cygpath` 없는 환경 시뮬레이션(PATH 제거 테스트) → sed fallback 작동 확인
- [ ] Python `re.sub` 단독 테스트(`/d/`, `/e/` 드라이브도 정규화되는지)
- [ ] `.claude/hooks/smoke_test.sh` 섹션 47 (debate_verify) PASS
- [ ] statusline.sh 호출 — `{"model":{"display_name":"test"}}` stdin 입력 → 정상 출력
- [ ] incident_ledger 신규 `debate_verify` 레코드 중단 관찰 (7일 체크)

## Claude 하네스 요약

- **채택**: 8건 (양측 합의사항 전부 + 범위 확인된 statusline + 표현 완화)
- **보류**: 0건
- **버림**: 1건 (Claude 초안의 C드라이브 전용 bash fallback — GPT 실패 판정 수용)
