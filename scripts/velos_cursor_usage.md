# VELOS Cursor 사용법 요약

## 🚀 빠른 시작

### 1. 필수 파일 저장
다음 4개 파일을 그대로 저장:
- `.cursorrules`
- `.vscode/tasks.json`
- `scripts/velos_health_check.ps1`
- `scripts/velos_cursor_checklist.md`

### 2. 헬스체크 실행
```
Cursor에서 Command Palette (Ctrl+Shift+P)
→ Run Task
→ "VELOS: 풀 헬스체크(원클릭)"
```

### 3. 실패 시 수정
헬스체크가 실패하면 다음 Cursor 프롬프트 템플릿을 붙여서 고치게 시킴:

```
You are the workspace auditor. Follow .cursorrules strictly. Task: 1) Run the VSCode task "VELOS: 풀 헬스체크(원클릭)". 2) If any step fails, open the failing file, fix it to satisfy rules (no renaming, no hardcoded paths), and re-run the task until all steps pass. 3) Summarize: what you changed, which tests you ran, and paste the exact terminal outputs.
```

### 4. 스케줄러 창 숨김 강제
마지막으로 -FixHidden 옵션으로 스케줄러 창 숨김을 강제:
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos_health_check.ps1" -FixHidden
```

## 📋 체크리스트 항목

### ✅ 필수 (7개)
- [ ] .cursorrules 존재, 규칙 반영됨
- [ ] tasks.json 배치, "풀 헬스체크" 수행 OK
- [ ] session_store --selftest OK
- [ ] 학습 메모리 JSONL/JSON 갱신 OK
- [ ] snapshots 생성 OK
- [ ] 대시보드 import OK
- [ ] 스케줄러 창 숨김 OK

### ✅ 로그 확인 (2개)
- [ ] data/logs/* 최근 오류 없음
- [ ] 보고서 생성 시 폰트 경고 제거

### ✅ 금지 (2개)
- [ ] 파일명 변경 없음
- [ ] 절대 경로 하드코딩 없음

## 🔧 주요 명령어

### 헬스체크
```powershell
# 기본 헬스체크
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos_health_check.ps1"

# 창 숨김 강제 수정
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\giwanos\scripts\velos_health_check.ps1" -FixHidden
```

### 세션/메모리 테스트
```bash
# 세션 스토어 selftest
python -m modules.core.session_store --selftest

# 세션 병합
python -m modules.core.session_store --merge
```

### 대시보드 임포트 테스트
```bash
python -c "import os,sys; sys.path.append(os.environ.get('VELOS_ROOT', 'C:/giwanos')); import interface.velos_dashboard; print('[OK] import 성공')"
```

## 🎯 목표 상태

- **모든 VELOS 스케줄러 태스크가 창 숨김 모드**
- **interface/* 임포트가 절대 실패하지 않음**
- **세션/메모리 시스템이 정상 작동**
- **절대 경로 하드코딩 없음**

## 📝 문제 해결

### 스케줄러 창 숨김 문제
- XML에서 `-WindowStyle Hidden` 감지 실패 시 정규식 패턴 수정
- `-FixHidden` 옵션으로 자동 재생성

### 임포트 실패
- sys.path에 VELOS_ROOT 추가
- 환경변수 기반 경로 설정

### 세션/메모리 문제
- JSONL append-only 정책 확인
- merge+snapshot 로직 검증

## 🏁 완료 기준

체크리스트의 모든 항목이 ✅로 표시되면 VELOS 시스템이 정상 작동 중입니다.
