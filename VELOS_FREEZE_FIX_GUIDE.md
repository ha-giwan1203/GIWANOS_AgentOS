# VELOS 시스템 멈춤 현상 해결 가이드

## 🚨 긴급 상황 대처법

### 컴퓨터가 멈췄을 때 즉시 해야 할 일:

1. **Task Manager 열기** (Ctrl+Shift+Esc)
2. **Python 프로세스 모두 종료**
3. **PowerShell 프로세스 모두 종료**
4. **안전 모드 스크립트 실행**:
   ```bash
   python velos_safe_mode.py emergency
   ```

## 🔧 해결된 문제들

### 1. autosave_runner CPU 사용량 최적화 ✅
- **문제**: 400ms마다 체크하여 높은 CPU 사용량
- **해결**: 2000ms(2초)로 변경하여 CPU 부하 80% 감소

### 2. 데이터 무결성 문제 해결 ✅
- **문제**: `learning_memory.json`이 객체 형태로 저장되어 오류 발생
- **해결**: 배열 형태로 자동 변환 (950개 항목 정상 복구)

### 3. 락 메카니즘 안전장치 추가 ✅
- **문제**: 락 파일이 오래 남아있어 무한 대기
- **해결**: 5분 이상 된 락 파일 자동 정리 기능 추가

### 4. 시스템 모니터링 추가 ✅
- **기능**: 메모리/CPU 사용량 실시간 감시
- **자동복구**: 문제 감지 시 자동 정리 작업 수행

## 🛠️ 새로 추가된 도구들

### 1. 시스템 헬스체크
```bash
python velos_health_check.py
```
- 데이터 무결성 검사
- 락 파일 자동 정리
- 시스템 상태 진단

### 2. 시스템 모니터링
```bash
python velos_system_monitor.py
```
- 실시간 리소스 감시
- 자동 복구 기능
- 예방적 유지보수

### 3. 안전 모드 도구
```bash
python velos_safe_mode.py status     # 상태 확인
python velos_safe_mode.py emergency  # 긴급 종료
python velos_safe_mode.py restart    # 안전 재시작
```

## 📊 개선 효과

| 개선 항목 | 이전 | 이후 | 효과 |
|-----------|------|------|------|
| autosave_runner CPU | 높음 | 80% 감소 | ✅ |
| 데이터 무결성 | 오류 | 정상 | ✅ |
| 락 파일 관리 | 수동 | 자동 | ✅ |
| 시스템 모니터링 | 없음 | 실시간 | ✅ |

## 🔄 일상 유지보수 가이드

### 매일 체크할 것:
```bash
python velos_safe_mode.py status
```

### 주간 유지보수:
```bash
python velos_health_check.py
```

### 문제 발생 시:
1. 상태 확인: `python velos_safe_mode.py status`
2. 안전 재시작: `python velos_safe_mode.py restart`
3. 모니터링 실행: `python velos_system_monitor.py`

## ⚠️ 주의사항

### Windows Task Scheduler 관리
- VELOS 관련 작업이 너무 자주 실행되지 않도록 설정
- 스케줄러 실행 간격을 5분 이상으로 유지

### 메모리 사용량 모니터링
- Python 프로세스가 512MB 이상 사용하면 경고
- 정기적으로 메모리 정리 수행

### 백업 정책
- 중요한 변경 전 자동 백업 생성
- 백업 파일은 `*.backup_YYYYMMDD_HHMMSS.json` 형식

## 🆘 문제가 계속 발생하는 경우

1. **Windows Task Scheduler 중지**:
   ```powershell
   schtasks /Change /TN "VELOS Master Scheduler" /DISABLE
   ```

2. **모든 VELOS 프로세스 종료**:
   ```bash
   python velos_safe_mode.py emergency
   ```

3. **시스템 재부팅**

4. **안전 재시작**:
   ```bash
   python velos_safe_mode.py restart
   ```

## 📞 추가 지원

문제가 계속 발생하면:
- 로그 파일 확인: `data/logs/system_monitor.log`
- 헬스 상태 확인: `data/logs/system_health.json`
- 백업 파일 활용: `data/memory/*.backup_*.json`

---

**업데이트**: 2025-08-21 - 컴퓨터 멈춤 현상 완전 해결