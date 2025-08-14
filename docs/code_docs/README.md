# VELOS 코드 문서화

이 디렉토리는 VELOS 시스템의 주요 모듈과 함수에 대한 상세한 문서를 포함합니다.

## 문서 구조

```
docs/code_docs/
├── README.md                    # 이 파일
├── modules/                     # 모듈별 문서
│   ├── core/                   # 핵심 모듈 문서
│   ├── automation/             # 자동화 모듈 문서
│   └── evaluation/             # 평가 모듈 문서
├── scripts/                    # 스크립트별 문서
│   ├── run_giwanos_master_loop.md
│   ├── velos_bridge.md
│   └── velos_ai_insights_report.md
└── tools/                      # 도구별 문서
    ├── notifications.md
    └── notion_integration.md
```

## 문서 작성 가이드라인

### 1. 함수 문서화 형식
```markdown
## 함수명

**위치**: `모듈경로/파일명.py`

**설명**: 함수의 목적과 동작 방식

**매개변수**:
- `param1` (type): 설명
- `param2` (type): 설명

**반환값**:
- `return_type`: 설명

**예제**:
```python
# 사용 예제 코드
result = function_name(param1, param2)
```

**주의사항**: 
- 중요한 주의사항이나 제한사항
```

### 2. 클래스 문서화 형식
```markdown
## 클래스명

**위치**: `모듈경로/파일명.py`

**설명**: 클래스의 목적과 역할

**주요 메서드**:
- `method1()`: 설명
- `method2()`: 설명

**속성**:
- `attr1`: 설명
- `attr2`: 설명

**사용 예제**:
```python
# 클래스 사용 예제
instance = ClassName()
result = instance.method1()
```
```

### 3. 모듈 문서화 형식
```markdown
# 모듈명

## 개요
모듈의 전반적인 목적과 기능

## 주요 구성요소
- **클래스1**: 설명
- **함수1**: 설명
- **상수1**: 설명

## 사용법
모듈 사용 방법과 예제

## 의존성
이 모듈이 의존하는 다른 모듈이나 패키지
```

## 문서 업데이트 규칙

1. **코드 변경 시**: 관련 문서도 함께 업데이트
2. **새 기능 추가 시**: 즉시 문서화
3. **API 변경 시**: 문서 버전 관리
4. **정기 검토**: 월 1회 문서 정확성 검토

## 문서 생성 도구

### 자동 문서 생성
```bash
# Python docstring에서 문서 생성
python -m pydoc -w 모듈명

# Sphinx 문서 생성 (선택사항)
sphinx-apidoc -o docs/source/ modules/
```

### 문서 검증
```bash
# 링크 검증
python -c "import markdown; print('Markdown 문법 검증 완료')"

# 코드 예제 실행 검증
python -c "exec(open('example_code.py').read())"
```

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
