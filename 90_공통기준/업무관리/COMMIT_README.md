# commit_docs.py 실행 가이드

## 동작 방식

Phase 1(`watch_changes.py`)의 30분 debounce flush 이후 자동 호출되거나,
단독 CLI로 오늘 날짜 작업로그를 읽어 커밋할 수 있습니다.

```
로컬 파일 변경
    → watch_changes.py 감지
    → 30분 idle
    → 작업로그_YYYYMMDD.jsonl 기록  ← Phase 1
    → commit_docs.process_events()  ← Phase 2
        → allowlist 필터링
        → git add / commit / push
        → git_commit_log_YYYYMMDD.jsonl 기록
```

---

## 실행 방법

### 자동 실행 (watch_changes.py 기동 시 Phase 2 자동 연결)
```bash
python watch_changes.py
```

### 단독 실행 (오늘 날짜 로그 처리)
```bash
python commit_docs.py
```

### dry-run (커밋하지 않고 대상 파일 확인만)
```bash
python commit_docs.py --dry-run
```

### 특정 로그 파일 지정
```bash
python commit_docs.py --log-file "90_공통기준/업무관리/작업로그_20260328.jsonl"
```

---

## allowlist (자동 커밋 포함)

| 패턴 | 설명 |
|------|------|
| `CLAUDE.md` `README.md` `STATUS.md` `TASKS.md` | 루트 운영 문서 |
| `90_공통기준/**/*.md` `*.py` `*.yaml` `*.skill` | 공통기준 전체 |
| `05_생산실적/조립비정산/03_정산자동화/*.py` | 정산 파이프라인 스크립트 |
| `05_생산실적/_자동화/*.bat` `*.py` | BI 자동화 |
| `10_라인배치/CLAUDE.md` `STATUS.md` | 라인배치 운영 문서 |
| `03_품번관리/초물관리/_scripts/*.py` | 초물관리 스크립트 |

## blocklist (자동 커밋 제외)

`*.xlsx` `*.xls` `*.docx` `*.pdf` `*.csv` `작업로그_*.jsonl` `*.log`
`98_아카이브/**` `99_임시수집/**` `~$*` `*.tmp` `*.bak` `*.driveupload`

---

## 커밋 메시지 규칙

| 파일 유형 | 커밋 prefix |
|----------|------------|
| STATUS.md, TASKS.md | `docs(status)` |
| *.py, *.bat (수정) | `fix(script)` |
| *.py, *.bat (신규) | `feat(script)` |
| *.skill | `feat(skill)` |
| *.yaml, *.yml, *.json | `chore(config)` |
| *.md | `docs(ops)` |
| 기타 | `chore(ops)` |

---

## 로그 파일 위치

| 파일 | 설명 |
|------|------|
| `git_commit_log_YYYYMMDD.jsonl` | 커밋 성공/실패 기록 |
| `git_commit_errors_YYYYMMDD.log` | 예외/오류 로그 |
| `.commit_state.json` | 처리된 batch_id 상태 (중복 커밋 방지) |

---

## 주의사항

- `delete` 이벤트는 커밋하지 않음 (원본 보호 원칙)
- 커밋 후 자동 push (설정: `push_on_commit: true`)
- push 실패 시 커밋은 로컬에 남고 오류만 로그에 기록
- `auto_commit_config.yaml`의 `branch`가 현재 체크아웃 브랜치와 일치해야 함
