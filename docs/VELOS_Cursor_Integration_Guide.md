# VELOS-Cursor 통합 가이드

## 📌 개요

VELOS 시스템과 Cursor IDE를 완전히 통합하여 자동화된 코드 편집 및 파일 관리를 제공합니다.

## 🎯 주요 기능

### 1. 자동화된 파일 관리
- **파일 생성**: 자연어 명령으로 파일 자동 생성
- **파일 수정**: 라인별 수정 및 자동 저장
- **실시간 동기화**: VELOS 메모리와 Cursor 간 실시간 동기화

### 2. 명령 처리 시스템
- **자연어 파싱**: 한국어/영어 명령 자동 인식
- **명령 히스토리**: 모든 명령 기록 및 추적
- **오류 처리**: 자동 복구 및 오류 로깅

### 3. Git 통합
- **자동 커밋**: 파일 변경 시 자동 Git 커밋
- **자동 푸시**: 설정에 따른 자동 원격 저장소 푸시
- **변경 추적**: 모든 변경사항 자동 추적

## 🚀 설치 및 설정

### 1. 필수 요구사항
```bash
# Python 3.8 이상
python --version

# Git 설치
git --version

# Cursor IDE 설치 (선택사항)
# https://cursor.sh/
```

### 2. VELOS 시스템 설정
```bash
# VELOS 루트 디렉토리 설정
export VELOS_ROOT=C:\giwanos

# Python 경로 설정
export PYTHONPATH="${PYTHONPATH}:${VELOS_ROOT}"
```

### 3. Cursor 설정 파일
```json
// configs/cursor_config.json
{
  "cursor_path": "cursor",
  "auto_commit": true,
  "auto_test": true,
  "workspace_path": "C:\\giwanos",
  "git_auto_push": true,
  "file_watch_enabled": true
}
```

## 📖 사용법

### 1. 명령줄 모드

#### 기본 사용법
```bash
# 단일 명령 실행
python scripts/velos_cursor_interface.py "명령어"

# 시스템 상태 확인
python scripts/velos_cursor_interface.py --status

# 도움말 표시
python scripts/velos_cursor_interface.py --help
```

#### 파일 생성 명령
```bash
# Python 파일 생성
python scripts/velos_cursor_interface.py "파일 생성 test.py 'print(\"Hello World\")'"

# Markdown 파일 생성
python scripts/velos_cursor_interface.py "파일 생성 README.md '# 프로젝트 제목'"

# JSON 파일 생성
python scripts/velos_cursor_interface.py "파일 생성 config.json '{\"key\": \"value\"}'"
```

#### 파일 수정 명령
```bash
# 특정 라인 수정
python scripts/velos_cursor_interface.py "파일 수정 test.py 라인 5 '새로운 내용'"

# 여러 라인 수정
python scripts/velos_cursor_interface.py "파일 수정 main.py 라인 10 'def new_function():'"
```

#### 코드 실행 명령
```bash
# Python 파일 실행
python scripts/velos_cursor_interface.py "실행 test.py"

# 테스트 실행
python scripts/velos_cursor_interface.py "테스트 test.py"

# 전체 프로젝트 테스트
python scripts/velos_cursor_interface.py "테스트"
```

#### 워크스페이스 관리
```bash
# Cursor 워크스페이스 열기
python scripts/velos_cursor_interface.py "워크스페이스 열기"

# 파일 정보 조회
python scripts/velos_cursor_interface.py "파일 정보 test.py"

# 파일 목록 조회
python scripts/velos_cursor_interface.py "파일 목록"
```

### 2. 대화형 모드

#### 대화형 모드 시작
```bash
python scripts/velos_cursor_interface.py --interactive
```

#### 대화형 모드 명령 예시
```
VELOS> 파일 생성 hello.py 'print("Hello from VELOS!")'
✅ 파일이 생성되었습니다: hello.py

VELOS> 실행 hello.py
✅ 명령이 실행되었습니다: hello.py
Hello from VELOS!

VELOS> 파일 수정 hello.py 라인 1 'print("Modified by VELOS!")'
✅ 파일이 수정되었습니다: hello.py 라인 1

VELOS> 워크스페이스 열기
✅ Cursor 워크스페이스가 열렸습니다.

VELOS> quit
VELOS-Cursor 인터페이스를 종료합니다.
```

## 🔧 고급 기능

### 1. 메모리 통합
```python
# 메모리 어댑터를 통한 자동 동기화
from modules.core.memory_adapter import create_memory_adapter

adapter = create_memory_adapter()
adapter.flush_jsonl_to_json()  # JSONL → JSON 동기화
adapter.flush_jsonl_to_db()    # JSONL → SQLite 동기화
```

### 2. 명령 처리기 직접 사용
```python
# 명령 처리기 직접 사용
from modules.core.velos_command_processor import create_command_processor

processor = create_command_processor()
result = processor.process_command("파일 생성 test.py 'print(\"test\")'")
print(result)
```

### 3. Cursor 연동 직접 사용
```python
# Cursor 연동 직접 사용
from modules.core.cursor_integration import create_cursor_integration

cursor = create_cursor_integration()
cursor.create_file("test.py", "print('Hello')")
cursor.modify_file("test.py", [{"type": "replace", "line": 1, "content": "print('Modified')"}])
```

## 📊 시스템 모니터링

### 1. 상태 확인
```bash
# 시스템 상태 확인
python scripts/velos_cursor_interface.py --status
```

출력 예시:
```
📊 VELOS-Cursor 시스템 상태
==================================================
메모리 버퍼: 0개 항목
JSON 레코드: 21개
DB 레코드: 0개
명령 히스토리: 5개

최근 명령:
  1. ✅ 파일 생성 test.py 'print("Hello")'...
  2. ✅ 실행 test.py...
  3. ✅ 파일 수정 test.py 라인 1 'print("Modified")'...
==================================================
```

### 2. 로그 확인
```bash
# 메모리 로그 확인
cat data/memory/memory_buffer.jsonl

# 명령 히스토리 확인
python -c "from modules.core.velos_command_processor import create_command_processor; p = create_command_processor(); print(p.get_command_history())"
```

## 🛠️ 문제 해결

### 1. 일반적인 오류

#### Cursor 설치 오류
```
❌ 오류: 워크스페이스 열기 실패: Cursor가 설치되지 않았거나 PATH에 없습니다.
```
**해결방법:**
1. Cursor IDE 설치: https://cursor.sh/
2. PATH에 Cursor 추가
3. `configs/cursor_config.json`에서 `cursor_path` 확인

#### 파일 권한 오류
```
❌ 오류: 파일 생성 실패: Permission denied
```
**해결방법:**
1. 파일 권한 확인
2. 관리자 권한으로 실행
3. 안티바이러스 예외 설정

#### Git 오류
```
❌ 오류: 자동 커밋 실패: not a git repository
```
**해결방법:**
1. Git 저장소 초기화: `git init`
2. Git 설정 확인: `git config --list`
3. 원격 저장소 설정: `git remote add origin <url>`

### 2. 성능 최적화

#### 메모리 사용량 최적화
```python
# 주기적 메모리 정리
adapter.cleanup_old_records(days=30)

# 버퍼 크기 제한
if adapter.get_stats()['buffer_size'] > 1000:
    adapter.flush_jsonl_to_json()
```

#### 파일 처리 최적화
```python
# 대용량 파일 처리
cursor_config = {
    "max_file_size": 10485760,  # 10MB
    "allowed_extensions": [".py", ".md", ".json"]
}
```

## 🔄 자동화 스크립트

### 1. 스케줄링 설정

#### Windows (작업 스케줄러)
```powershell
# 매일 자동 동기화
schtasks /create /tn "VELOS_Cursor_Sync" /tr "python C:\giwanos\scripts\velos_cursor_interface.py --status" /sc daily /st 09:00

# 매시간 메모리 정리
schtasks /create /tn "VELOS_Memory_Cleanup" /tr "python -c \"from modules.core.memory_adapter import create_memory_adapter; create_memory_adapter().cleanup_old_records(30)\"" /sc hourly
```

#### Linux/macOS (cron)
```bash
# crontab 편집
crontab -e

# 매일 자동 동기화
0 9 * * * cd /path/to/giwanos && python scripts/velos_cursor_interface.py --status

# 매시간 메모리 정리
0 * * * * cd /path/to/giwanos && python -c "from modules.core.memory_adapter import create_memory_adapter; create_memory_adapter().cleanup_old_records(30)"
```

### 2. CI/CD 통합

#### GitHub Actions 예시
```yaml
name: VELOS-Cursor Integration

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    - name: Install dependencies
      run: |
        pip install -r configs/requirements.txt
    - name: Run VELOS tests
      run: |
        python scripts/velos_cursor_interface.py "테스트"
```

## 📈 확장 가능성

### 1. 새로운 명령 추가
```python
# velos_command_processor.py에 새 명령 추가
def _parse_new_command(self, command: str) -> Dict:
    # 새 명령 파싱 로직
    return {"type": "new_command", "params": {...}}

def _execute_new_command(self, parsed: Dict) -> Dict:
    # 새 명령 실행 로직
    return {"success": True, "message": "새 명령 실행 완료"}
```

### 2. 플러그인 시스템
```python
# 플러그인 인터페이스
class VELOSPlugin:
    def process_command(self, command: str) -> Dict:
        pass
    
    def get_help(self) -> str:
        pass
```

### 3. API 서버
```python
# Flask API 서버 예시
from flask import Flask, request, jsonify
from modules.core.velos_command_processor import create_command_processor

app = Flask(__name__)
processor = create_command_processor()

@app.route('/api/command', methods=['POST'])
def execute_command():
    command = request.json.get('command')
    result = processor.process_command(command)
    return jsonify(result)
```

## 📝 변경 로그

### v1.0.0 (2025-08-14)
- ✅ 기본 파일 생성/수정 기능
- ✅ 자연어 명령 파싱
- ✅ 메모리 통합
- ✅ Git 자동 커밋
- ✅ 대화형 모드
- ✅ 시스템 상태 모니터링

### 향후 계획
- 🔄 실시간 파일 감시
- 🔄 다중 워크스페이스 지원
- 🔄 클라우드 동기화
- 🔄 AI 기반 코드 생성
- 🔄 협업 기능

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
