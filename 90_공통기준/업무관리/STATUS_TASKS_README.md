# update_status_tasks.py 가이드

## 동작 위치

Phase 1 flush → **Phase 3 (STATUS/TASKS 갱신)** → Phase 2 (Git 커밋)

STATUS.md와 TASKS.md 갱신이 완료된 후 Phase 2가 이를 포함해 한 번만 커밋합니다.

---

## 실행 방법

### 자동 실행 (watch_changes.py 기동 시 자동 연결)
```bash
python watch_changes.py
```

### 단독 실행 (오늘 날짜 로그 처리)
```bash
python update_status_tasks.py
```

### dry-run
```bash
python update_status_tasks.py --dry-run
```

### 특정 로그 파일 지정
```bash
python update_status_tasks.py --log-file "90_공통기준/업무관리/작업로그_20260328.jsonl"
```

---

## STATUS.md 갱신 규칙

- 섹션 `## 자동 감지 변경 이력` 에 최신 이력 추가 (없으면 자동 생성)
- 최대 30건 보관, 초과 시 오래된 항목 제거
- STATUS.md 자체 변경은 무한루프 방지를 위해 제외

| 컬럼 | 내용 |
|------|------|
| 시각 | 변경 감지 확정 시각 |
| 이벤트 | created / modified / moved |
| 파일 | 변경된 파일명 |
| 변경 내용 | status_rules.yaml의 label |

---

## TASKS.md 갱신 규칙

- `## 대기 중` 섹션 하단에 `[auto]` 태그와 함께 추가
- 24시간 이내 동일 내용 중복 추가 방지
- TASKS.md 자체 변경은 제외

```
### [auto] 파이프라인 실행 테스트 확인 (2026-03-28)
- 출처: `step5_정산계산.py` 변경 감지
- 자동 생성 항목 — 확인 후 처리 또는 삭제
```

---

## 운영 의미 있는 파일 (status_rules.yaml 기준)

| 파일 패턴 | label | [auto] 작업 추가 |
|----------|-------|:---:|
| `90_공통기준/스킬/**/*.skill` | 스킬 패키지 갱신 | ✗ |
| `05_생산실적/조립비정산/03_정산자동화/*.py` | 정산 파이프라인 스크립트 수정 | ✓ |
| `05_생산실적/_자동화/*.bat` | BI 자동화 배치 파일 수정 | ✓ |
| `CLAUDE.md` | CLAUDE.md 운영 기준 수정 | ✗ |
| 기타 allowlist .md/.py | 각 label 참조 | ✗ |

---

## 제외 대상

`98_아카이브/**` `99_임시수집/**` `*.log` `*.jsonl`
`STATUS.md` `TASKS.md` (자체 제외) `*.tmp` `*.bak` `*.driveupload`

---

## 오류 로그

`status_tasks_errors_YYYYMMDD.log` — 갱신 실패 시 원본 파일은 유지됨
