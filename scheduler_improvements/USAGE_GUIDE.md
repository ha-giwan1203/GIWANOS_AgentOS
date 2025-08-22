# VELOS 스케줄러 창 숨김 완전 해결 가이드

## 🎯 문제 해결 과정

### 1단계: 현재 상황 진단
```cmd
# Windows에서 관리자 권한으로 실행
powershell -ExecutionPolicy Bypass -File "C:\giwanos\scripts\windows_scheduler_diagnosis.ps1"
```

### 2단계: 자동 수정 적용
```cmd
# 관리자 권한으로 배치 파일 실행
"C:\giwanos\scheduler_improvements\fix_all_velos_schedulers.bat"
```

### 3단계: 수동 확인 (필요시)
```cmd
# 현재 등록된 VELOS 작업 확인
schtasks /query /tn "*VELOS*" /fo table

# Hidden 설정 확인
Get-ScheduledTask | Where-Object {$_.TaskName -like "*VELOS*"} | Get-ScheduledTaskInfo
```

## 🔧 개선 사항

### ✅ 완전한 창 숨김 보장
- 모든 XML에 `<Hidden>true</Hidden>` 설정
- VBScript 래퍼로 100% 창 숨김
- SYSTEM 계정으로 실행하여 권한 문제 해결

### ✅ 표준화된 실행 방식
- 범용 VBScript 래퍼 제공
- 일관된 XML 템플릿 적용
- 환경변수 및 경로 자동 설정

### ✅ 자동화된 수정 도구
- 진단 스크립트로 문제 파악
- 배치 스크립트로 일괄 수정
- 백업 및 복원 기능

## 🚨 주의사항

### 관리자 권한 필수
- 모든 스케줄러 조작은 관리자 권한 필요
- PowerShell 실행 정책 확인 필요

### 백업 권장
- 기존 스케줄러 작업 백업 필수
- XML 파일 원본 보관

## 📊 예상 결과

### Before (문제 상황)
- ❌ 스케줄러 실행 시 창이 나타남
- ❌ PowerShell/CMD 창 깜빡임  
- ❌ 사용자 인터페이스 방해

### After (해결 후)
- ✅ 완전한 백그라운드 실행
- ✅ 창 노출 없음
- ✅ 조용한 스케줄러 동작

## 🔍 트러블슈팅

### 문제: 여전히 창이 나타남
```cmd
# 1. Hidden 설정 확인
schtasks /query /tn "작업이름" /xml | findstr "Hidden"

# 2. 작업 재등록
schtasks /delete /tn "작업이름" /f
schtasks /create /xml "새로운XML파일" /tn "작업이름"
```

### 문제: 작업이 실행되지 않음
```cmd
# 1. 작업 상태 확인
schtasks /query /tn "작업이름" /fo list /v

# 2. 실행 테스트
schtasks /run /tn "작업이름"
```

## 📞 지원

문제 발생 시 다음 정보를 수집하여 보고:
1. `windows_scheduler_diagnosis.ps1` 실행 결과
2. 문제가 되는 작업의 XML 내용
3. 이벤트 로그 오류 메시지
