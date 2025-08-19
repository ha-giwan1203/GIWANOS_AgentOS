# VELOS configs 폴더 필수 누락 파일 분석

**생성일**: 2025-08-18  
**분석자**: VELOS 시스템  
**목적**: configs 폴더의 필수 누락 파일 확인 및 생성

## 🔍 **분석 결과**

### ✅ **현재 존재하는 파일들**
```
configs/
├── 📄 settings.yaml              # ✅ 메인 설정 (환경 변수 지원)
├── 📄 feature_manifest.yaml      # ✅ 기능 매니페스트
├── 📄 .env                       # ✅ 환경 변수
├── 📄 .env.example               # ✅ 환경 변수 예제
├── 📄 __init__.py                # ✅ 설정 로더
├── 📁 security/                  # ✅ 보안 설정
└── 📁 vector_index/              # ✅ 벡터 인덱스
```

### ❌ **필수 누락 파일들**

#### 1. **`cursor_config.json`** - 🔴 **긴급 필요**
- **참조 위치**: `modules/core/cursor_integration.py` (2곳)
- **기능**: Cursor IDE 통합 설정
- **상태**: ❌ 누락됨

#### 2. **`requirements.txt`** - 🟡 **권장**
- **참조 위치**: `scripts/materialize_gpt_output.py`
- **기능**: Python 의존성 관리
- **상태**: ❌ 누락됨

#### 3. **`memory_schema.yaml`** - 🟡 **권장**
- **참조 위치**: 없음 (향후 확장용)
- **기능**: 메모리 스키마 정의
- **상태**: ❌ 누락됨

#### 4. **`search_keywords.yaml`** - 🟡 **권장**
- **참조 위치**: 없음 (향후 확장용)
- **기능**: 검색 키워드 정의
- **상태**: ❌ 누락됨

## 🎯 **우선순위별 생성 계획**

### 🔴 **Phase 1: 긴급 필요 파일**
1. **`cursor_config.json`** - Cursor IDE 통합 필수

### 🟡 **Phase 2: 권장 파일**
1. **`requirements.txt`** - 의존성 관리
2. **`memory_schema.yaml`** - 메모리 스키마
3. **`search_keywords.yaml`** - 검색 키워드

## 📋 **생성할 파일 상세**

### 1. **cursor_config.json**
```json
{
  "cursor_path": "C:/Users/User/AppData/Local/Programs/Cursor/Cursor.exe",
  "workspace_settings": {
    "auto_save": true,
    "format_on_save": true,
    "python_interpreter": "C:/Users/User/venvs/velos/Scripts/python.exe"
  },
  "velos_integration": {
    "enabled": true,
    "session_tracking": true,
    "memory_sync": true
  }
}
```

### 2. **requirements.txt**
```
# VELOS 시스템 핵심 의존성
pyyaml>=6.0
requests>=2.28.0
psutil>=5.9.0
pandas>=1.5.0
sqlite3
pathlib
typing
```

### 3. **memory_schema.yaml**
```yaml
# VELOS 메모리 스키마 정의
memory_types:
  session:
    fields:
      - id: string
      - timestamp: datetime
      - content: text
      - tags: array
  reflection:
    fields:
      - id: string
      - timestamp: datetime
      - insight: text
      - confidence: float
```

### 4. **search_keywords.yaml**
```yaml
# VELOS 검색 키워드 정의
search_keywords:
  system:
    - "VELOS"
    - "시스템"
    - "설정"
  memory:
    - "메모리"
    - "세션"
    - "리플렉션"
  workflow:
    - "워크플로우"
    - "자동화"
    - "스케줄러"
```

## ⚠️ **주의사항**

1. **VELOS 규칙 준수**: 모든 파일에 VELOS 운영 철학 선언문 포함
2. **환경 변수 지원**: 가능한 경우 환경 변수로 경로 주입
3. **기본값 제공**: 환경 변수가 없을 때의 기본값 설정
4. **문서화**: 각 파일의 용도와 설정 방법 명시

## 🚀 **다음 단계**

1. **긴급 파일 생성**: `cursor_config.json` 우선 생성
2. **권장 파일 생성**: 나머지 파일들 순차 생성
3. **테스트**: 생성된 파일들의 참조 확인
4. **문서화**: 설정 파일 사용법 가이드 작성

---
**VELOS 운영 철학**: "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."








