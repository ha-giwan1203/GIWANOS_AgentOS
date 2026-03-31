# research: watch_changes.py Git 커밋 실패 원인 분석

작성일: 2026-03-31
작성자: Claude (Plan-First 1단계)

---

## 1. 실패 패턴 (Slack AutoBot 알림 기준)

| 시각 | 배치 | 내용 |
|------|------|------|
| 08:10 | d304adf6 | [Git 커밋 실패] 2건 |
| 08:24 | aebc9ddf | [STATUS/TASKS 갱신 실패] |
| 08:40 | c03b28bb | [Git 커밋 실패] 4건 |
| 08:49 | af59d75d | [STATUS/TASKS 갱신 실패] |
| 09:17 | 4ef003a5 | [Git 커밋 실패] 1건 |
| 09:20 | d1ca5a63 | [Git 커밋 실패] 1건 |
| 09:25 | ba52fb1b | [STATUS/TASKS 갱신 실패] |
| 09:26 | eabb5f04 | [Git 커밋 실패] 4건 |

패턴: Phase 2(Git 커밋) 실패 + Phase 3(STATUS/TASKS 갱신) 실패가 번갈아 발생.
Phase 2 실패가 우선 원인 — Phase 3 갱신 후 생성되는 파일도 커밋 실패로 이어짐.

---

## 2. 근본 원인: 브랜치 불일치 (확정)

| 항목 | 값 |
|------|-----|
| `auto_commit_config.yaml` branch 설정 | `"업무리스트"` |
| 실제 Git 브랜치 | `main` |
| 실패 코드 위치 | `commit_docs.py:303` |

```python
# commit_docs.py 브랜치 확인 로직 (line 300~305)
current = git_current_branch(repo)
if current != branch:
    error_logger.error(f"브랜치 불일치: current={current}, expect={branch}")
    result["failed"] += len(existing)
    return result  # ← 즉시 종료
```

`commit_docs.py`는 브랜치가 다르면 **git add도 시도하지 않고** 즉시 실패 반환.
모든 Phase 2 실패의 단일 원인.

---

## 3. 부가 확인 사항

### 3-1. push_on_commit 설정
```yaml
push_on_commit: false
```
커밋 성공해도 push 없음. 의도적 설정(수동 push 전략) 또는 미검토 항목.

### 3-2. .watch.lock 상태
- 현재 PID: `8700` (프로세스 실행 중)
- watch_changes.py 정상 동작 중 — 파일 감지 자체는 문제 없음

### 3-3. 에러 로그 파일
- `git_commit_errors_*.log` 파일 없음 (로그 디렉토리에 생성 안 됨)
- 원인: commit_docs.py가 에러 로거 초기화 전 브랜치 불일치로 종료하는 경우
  또는 로그 경로 오기입 가능성 — 별도 확인 필요

### 3-4. auto_watch_config.yaml
- debounce_minutes: 30 (30분 idle 후 flush)
- 감시 확장자에 .xlsx 포함 → 엑셀 열기/닫기마다 이벤트 발생 가능

---

## 4. 수정 범위

| 파일 | 수정 내용 | 위험도 |
|------|---------|-------|
| `auto_commit_config.yaml` | `branch: "업무리스트"` → `branch: "main"` | 낮음 |
| `auto_commit_config.yaml` | `push_on_commit` 방향 확정 (true/false) | 낮음 |

---

## 5. 확인 필요 항목

- [ ] `push_on_commit: false` — 의도적 설정인지 확인 후 방향 결정
- [ ] 에러 로그가 생성 안 되는 경로 문제 여부
- [ ] 브랜치 수정 후 dry-run으로 커밋 정상 동작 검증

---

## 판정

**FAIL 원인: `auto_commit_config.yaml` branch 오기입 1건**
수정 대상: `branch: "업무리스트"` → `branch: "main"`
수정 후 즉시 자동 커밋 체인 복구 가능.
