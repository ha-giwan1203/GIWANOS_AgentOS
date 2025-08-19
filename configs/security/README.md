# VELOS Security Configuration

## 📁 C:\giwanos\configs\security

VELOS 시스템의 보안 및 환경변수 관리 센터

## 🔐 보안 기능

### 1. 환경변수 암호화
- **`encrypt_config.py`**: 환경변수 암호화/복호화 로직
- 민감한 환경변수 보안 저장
- 키 관리 및 접근 제어

### 2. 파일 무결성 검증
- **`guard_hashes.json`**: 핵심 파일들의 SHA256 해시 저장
- 파일 변조 감지 및 보안 검증
- 자동 무결성 체크

### 3. 환경변수 통합 관리
- **`env_manager.py`**: 통합 환경변수 관리 시스템
- 보안 환경변수 로딩
- 환경별 설정 분리

## 🛡️ 보안 정책

### 환경변수 보안
- 민감한 정보는 암호화 저장
- 접근 권한 기반 환경변수 로딩
- 환경별 설정 분리 (dev/prod)

### 파일 무결성
- 핵심 스크립트 해시 검증
- 자동 무결성 체크
- 변조 감지 시 알림

### 접근 제어
- 권한 기반 환경변수 접근
- 로그 기반 접근 추적
- 보안 이벤트 모니터링

## 🔧 사용법

### 환경변수 설정
```powershell
# 보안 환경변수 설정
python configs/security/env_manager.py --set-secure

# 환경변수 로딩
python configs/security/env_manager.py --load
```

### 무결성 검증
```powershell
# 파일 무결성 체크
python configs/security/encrypt_config.py --verify

# 해시 업데이트
python configs/security/encrypt_config.py --update-hashes
```

## 📋 파일 구조

```
configs/security/
├── README.md              # 이 파일
├── encrypt_config.py      # 암호화/무결성 검증
├── guard_hashes.json      # 파일 해시 저장소
└── env_manager.py         # 환경변수 관리 (생성 예정)
```

## 🔄 통합 계획

### 1단계: 환경변수 통합
- scripts/의 env 관련 파일들을 security/로 이동
- 통합 환경변수 관리 시스템 구축

### 2단계: 보안 강화
- 환경변수 암호화 구현
- 접근 제어 시스템 구축

### 3단계: 모니터링
- 보안 이벤트 로깅
- 자동 무결성 검증

---

**VELOS 운영 철학**: "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."
