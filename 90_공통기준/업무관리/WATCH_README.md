# watch_changes.py 실행 가이드

## 사전 준비

```bash
pip install watchdog pyyaml psutil
```

---

## 실행 방법

### 일반 실행
```bash
cd "C:/Users/User/Desktop/업무리스트/90_공통기준/업무관리"
python watch_changes.py
```

### dry-run (로그 파일 미생성, 콘솔 출력만)
```bash
python watch_changes.py --dry-run
```

### 설정 파일 지정
```bash
python watch_changes.py --config "경로/auto_watch_config.yaml"
```

---

## 동작 방식

1. 업무리스트 루트 전체를 재귀 감시
2. 파일 이벤트 발생 시 debounce 큐에 등록
3. 마지막 이벤트 시각 기준 **30분 idle** 후 1건으로 확정
4. `90_공통기준/업무관리/작업로그_YYYYMMDD.jsonl` 에 append

---

## 로그 파일 위치

| 파일 | 설명 |
|------|------|
| `90_공통기준/업무관리/작업로그_YYYYMMDD.jsonl` | 확정된 이벤트 로그 |
| `90_공통기준/업무관리/watch_errors_YYYYMMDD.log` | 예외/오류 로그 |
| `.watch.lock` | 중복 실행 방지 lock (실행 중에만 존재) |

---

## 감시 대상 확장자

`.md` `.txt` `.json` `.yaml` `.yml` `.py` `.ps1` `.bat` `.xlsx` `.xls` `.docx` `.pdf`

## 제외 경로

`98_아카이브/` `99_임시수집/` `__pycache__/` `.git/` `.claude/`

## 제외 파일 패턴

`~$*` `*.tmp` `*.temp` `*.bak` `*.swp` `*.crdownload` `*.driveupload` `Thumbs.db` `desktop.ini`

---

## 주의사항

- 종료 후 재실행 시 기존 로그는 보존됨 (append 방식)
- 재실행 시 종료 직전 debounce 대기 중이던 이벤트는 소실됨 (다음 변경 시 재감지)
- lock 파일이 남아있고 프로세스가 죽은 경우 `.watch.lock` 수동 삭제 후 재실행
- `psutil` 미설치 시 lock 파일 좀비 감지 불가 (수동 삭제 필요)

---

## 설정 변경

`auto_watch_config.yaml` 수정 후 재실행. 실행 중 설정 변경은 반영되지 않음.

| 항목 | 기본값 | 설명 |
|------|--------|------|
| `debounce_minutes` | 30 | idle 대기 시간 (분) |
| `exclude_dirs` | 5개 | 제외 폴더 목록 |
| `watch_extensions` | 12종 | 감시 확장자 목록 |
