# /debate-mode `--quick` 옵션화 PLAN (세션156 발의 → 다음 세션 진행)

> **다음 세션 Claude 진입점**: 이 파일만 읽고 self-contained 진행 가능.
> 사용자 발화 "토론모드는 --http-only 유사방식으로 안되는건가?? → 다음 세션에서 이어서 하게 플랜을 만들어바" (2026-05-13 세션156).

## 1. 배경

### 1-1. 직전 사고 (세션156)
- `/debate-mode` 명시 호출 → 의제가 단순 A 분류(문구·BOM·오타·메모리)였는데도 3자 토론 thinking 라운드 진행 → 토론 비용(thinking 라운드당 2~3분 × N라운드 + GPT/Gemini 웹 UI 응답 대기) > 변경 비용. 사용자 10분 소비 후 "A 직행 했어야 한다" 합의.
- 결과: 메모리 `feedback_debate_mode_cost_check.md` 신설. 다만 메모리 룰은 **Claude 행위 의존** — `--http-only` 같은 명시 옵션이 없어 새 세션 Claude가 또 놓칠 위험.

### 1-2. `--http-only` 패턴 유사 적용
- 세션153 A안 3단계에서 `d0-production-plan/run.py`에 `--http-only` 옵션 도입 — default off + 명시 활성. 회귀 보험 1~2주.
- 같은 패턴: `/debate-mode`에 `--quick` / `--auto` / `--full` flag 도입 + 의제 자동 분류 게이트.

## 2. 목표

`/debate-mode` 호출 시 의제 분류에 따라 **토론 라운드 자동 우회**:
- A 분류(문구·BOM·오타·단순 값 조정) → 토론 생략, Claude 단독 판단 즉시 진행
- B 분류(실행 흐름·hook gate·정책 변경) → 정식 3자 토론 (현재 동작)
- C 분류(고위험·외부 인터페이스) → 정식 3자 토론 + R1·R5 강제

사용자 의지 표현 명시 flag 우선:
- `--quick`: 분류 무시 + 토론 단축 (Claude 단독 + GPT 1줄 검증만)
- `--full`: 분류 무시 + 정식 3자 토론 강제
- `--auto` (default): 의제 분류 → A 직행 / B·C 정식 토론

## 3. 범위

### 3-1. 수정 대상
| 파일 | 변경 |
|------|------|
| `.claude/commands/debate-mode.md` | trigger 섹션에 `--quick`/`--full`/`--auto` flag 명시 + 자동 분류 안내 |
| `90_공통기준/토론모드/debate-mode/SKILL.md` | Step 0(의제 분류 게이트) 신설 + flag 분기 |
| `90_공통기준/토론모드/CLAUDE.md` | "## 의제 분류 게이트" 섹션 신설 (B 분류 감지 섹션 옆) |
| 신설: `90_공통기준/토론모드/_classify_agenda.py` | 의제 → A/B/C 분류 헬퍼 (CLI 또는 import) |
| `feedback_debate_mode_cost_check.md` 메모리 | 옵션 도입 완료 후 갱신 (행위 의존 → 옵션 기반) |

### 3-2. 비범위
- 토론 라운드 내부 로직(Step 6-1~6-5)은 무수정 — 분류 게이트만 추가
- B 분류 자동 감지(세션116-117 비대칭 설계)는 그대로 유지 — `--full` flag와 조합
- chrome-devtools-mcp / CDP Chrome 단독 사용 정책 무수정

## 4. 작업 단계

### Step 1. 의제 분류 헬퍼 작성
```python
# 90_공통기준/토론모드/_classify_agenda.py
import re, sys

A_PATTERNS = [
    r'(문구|오타|드리프트|단순\s*수정)',
    r'(BOM|품번\s*변경)',
    r'(메모리\s*추가|메모리\s*신설|.md\s*추가)',
    r'(주석|문서\s*정리|TASKS|HANDOFF)',
    r'(단가|수치|상수\s*조정)',
]
B_PATTERNS = [
    r'(hook|gate|policy|정책)',
    r'(\.claude/settings|permissions)',
    r'(실행\s*흐름|판정\s*분기)',
    r'(SKILL\.md\s*Step|skill\s*절차)',
    r'(파이프라인\s*단계)',
]
C_PATTERNS = [
    r'(ERP|MES|SmartMES|G-ERP)\s*(반영|비가역|업로드)',
    r'(파괴|delete|drop|truncate)',
    r'(외부\s*인터페이스|스프레드시트\s*양식)',
]

def classify(agenda: str) -> str:
    for p in C_PATTERNS:
        if re.search(p, agenda, re.I): return 'C'
    for p in B_PATTERNS:
        if re.search(p, agenda, re.I): return 'B'
    for p in A_PATTERNS:
        if re.search(p, agenda, re.I): return 'A'
    return 'B'  # 모호 시 안전측 — 기본 B

if __name__ == "__main__":
    print(classify(sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()))
```

**검증 단위 케이스**:
- "오타 정정해라" → A
- "BOM 89870AT500CCV 단가 변경" → A
- "commit_gate.sh 차단 정책 추가" → B
- "ERP 비가역 반영 흐름 변경" → C
- 빈 문자열 / 모호 → B (안전측)

### Step 2. debate-mode.md 트리거 분기 추가
```markdown
## flag 옵션 (세션156→다음 세션 신설)

- `/debate-mode --quick` : 토론 라운드 생략. Claude 단독 판단 + GPT 1줄 검증만(`gpt-send` 1회 + `gpt-read` 1회)
- `/debate-mode --full` : 의제 분류 무시 + 정식 3자 토론 강제 (현재 동작과 동일)
- `/debate-mode` / `/debate-mode --auto` : 의제 자동 분류 → A 직행 / B·C 정식 토론 (default)

## 자동 분류 게이트 (Step 0 신설)
SKILL.md Step 1 전에 `_classify_agenda.py`로 의제 분류:
- A → 토론 생략 + Claude 단독 판단 + 결과 보고
- B / C → 기존 Step 1~6 정식 진행
- 사용자가 `--full` 명시 시 분류 무시
```

### Step 3. SKILL.md Step 0 신설
```markdown
## Step 0. 의제 분류 게이트 (세션156→다음 세션 신설)

진입 직후 다음 분류 명령 실행:
```bash
python 90_공통기준/토론모드/_classify_agenda.py "<의제 요약>"
```

분기:
- 결과 = `A` AND flag != `--full` → Step 1~6 모두 생략. Claude 단독 판단 후 사용자 보고. 종료.
- 결과 = `B` OR `C` OR flag = `--full` → Step 1 진행 (현재 흐름)
- flag = `--quick` → 분류 무시. Step 1 Claude 단독 판단 + Step 6-2 GPT 1줄 검증 1회만. Gemini·종합 라운드 생략.

분류 결과를 `logs/debate_YYYYMMDD_HHMMSS/agenda_classification.json` 기록.
```

### Step 4. 검증 PoC (1건)
- 사용자 임의 의제 1개로 `python _classify_agenda.py "<의제>"` 호출 → 분류 결과 PASS
- `/debate-mode --quick` 명시 호출 시 thinking 라운드 생략 확인
- 기존 `/debate-mode` (no flag) 의제 = A 시 자동 생략 확인
- 기존 `/debate-mode` 의제 = B 시 기존 흐름 보장 (회귀 0)

### Step 5. 메모리 갱신
`feedback_debate_mode_cost_check.md` 본문 갱신:
- 이전: "Claude 행위 의존 (호출 전 직접 확인)"
- 이후: "옵션 기반 자동 게이트 (`_classify_agenda.py` + flag)"

### Step 6. commit + push + finish
- commit 1: `feat(debate-mode): --quick/--full/--auto flag + 의제 자동 분류 게이트`
- finish: A 모드(문서·룰 변경 위주) — GPT 공유 5~8단계 생략 가능. 다만 SKILL.md Step 분기 신설은 B 분류라 GPT 공유 권고. 자체 판단으로 분류.

## 5. R1·R5

**R1 (진짜 원인)**:
- 토론 비용 > 변경 비용인 케이스가 빈번. 메모리 룰만으로는 새 세션 Claude가 행위 의존이라 놓침.
- 옵션 + 자동 분류 게이트로 SSoT 1곳 + flag 명시 보장.

**R5 (잔존 데이터 / 롤백)**:
- 회귀 보험: default `--auto` + 모호 시 B 안전측. 기존 `/debate-mode` 호출 시 분류 = B → 정식 토론 (현재 동작 그대로).
- 잔존: `logs/debate_YYYYMMDD_HHMMSS/agenda_classification.json` (작은 메타 데이터, 회귀 영향 0).
- 롤백 경로: `_classify_agenda.py` 삭제 + SKILL.md Step 0 제거 → 기존 흐름 100% 복원.

## 6. 검증 기준

- [ ] `_classify_agenda.py` 단위 테스트 5케이스 PASS (A/B/C/모호/빈문자열)
- [ ] `/debate-mode` no-flag + A 의제 → 토론 생략 + 즉시 종료 PASS
- [ ] `/debate-mode` no-flag + B 의제 → 기존 3자 토론 진입 (회귀 0)
- [ ] `/debate-mode --full` → 분류 무시 + 정식 진입 PASS
- [ ] `/debate-mode --quick` → Claude 단독 + GPT 1줄 검증 1회만 PASS
- [ ] `agenda_classification.json` 로그 기록 검증

## 7. 회귀 보험

- default = `--auto` (분류 게이트 활성)
- 모호 시 → B (안전측)
- 기존 호출 시 의제 = B 자동 분류 → 정식 토론 진입 (현재 동작과 동일)
- 1~2주 관찰 후 default 정책 재조정 검토 (별건)

## 8. 다음 세션 첫 행동

1. 이 파일(`debate_mode_quick_option_plan.md`) 1회 읽기
2. Step 1 `_classify_agenda.py` 신설 → 단위 테스트 5케이스
3. Step 2-3 debate-mode.md + SKILL.md 분기 추가
4. Step 4 PoC 1건 (사용자 임의 의제)
5. Step 5 메모리 갱신
6. Step 6 commit + push + finish (분류 = B 가능성 — GPT 공유 자체 판단)

## 9. 산출물 위치

- 본 plan: `99_임시수집/20260513/debate_mode_quick_option_plan.md`
- 다음 세션 산출물 예정 위치:
  - `90_공통기준/토론모드/_classify_agenda.py`
  - `90_공통기준/토론모드/debate-mode/SKILL.md` (Step 0 추가)
  - `.claude/commands/debate-mode.md` (flag 섹션 추가)
  - `90_공통기준/토론모드/CLAUDE.md` (분류 게이트 섹션 추가)
  - `feedback_debate_mode_cost_check.md` (행위 의존 → 옵션 기반 갱신)
