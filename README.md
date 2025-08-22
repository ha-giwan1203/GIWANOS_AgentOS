# VELOS

[![VELOS Bench](https://github.com/ha-giwan1203/GIWANOS_AgentOS/actions/workflows/velos-bench.yml/badge.svg?branch=main)](https://github.com/ha-giwan1203/GIWANOS_AgentOS/actions/workflows/velos-bench.yml)

VELOS는 "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다" 철학을 따르는 AI 메모리 시스템입니다.

## 빠른 시작
```powershell
$env:VELOS_DB_PATH="C:\giwanos\data\velos.db"
python .\scripts\memory_tick.py
```

## 🚀 VELOS 운영 철학

> "판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

VELOS는 지능형 에이전트 운영 시스템으로, 다음과 같은 핵심 원칙을 따릅니다:

### 📋 핵심 원칙
1. **파일명 고정**: 시스템 파일명·경로·구조는 고정, 임의 변경 금지
2. **자가 검증 필수**: 수정/배포 전 자동·수동 테스트를 통과해야 함
3. **실행 결과 직접 테스트**: 코드 제공 시 실행 결과를 동봉/기록
4. **저장 경로 고정**: ROOT=/home/user/webapp 기준, 우회/추측 경로 금지
5. **실패 기록·회고**: 실패 로그를 남기고 후속 커밋/문서에 반영
6. **기억 반영**: 작업/대화 맥락을 메모리에 저장하고 로딩에 사용
7. **구조 기반 판단**: 프로젝트 구조 기준으로만 판단 (추측 금지)
8. **중복/오류 제거**: 불필요/중복 로직 제거, 단일 진실원칙 유지
9. **지능형 처리**: 자동 복구·경고 등 방어적 설계 우선
10. **거짓 코드 절대 불가**: 실행 불가·미검증·허위 출력 일체 금지

## 🏗️ 시스템 구조

```
C:\giwanos\
├── modules/          # 핵심 모듈
├── scripts/          # 실행 스크립트
├── interface/        # 사용자 인터페이스
├── tests/           # 테스트 및 벤치마크
├── data/            # 데이터 저장소
├── configs/         # 설정 파일
└── tools/           # 유틸리티 도구
```

## 🔧 주요 기능

### 📊 성능 모니터링
- **자동 벤치마크**: GitHub Actions를 통한 일일 성능 테스트
- **FTS5 검색**: SQLite Full-Text Search 기반 고성능 검색
- **메모리 관리**: 자동 메모리 정리 및 최적화

### 🤖 자동화 시스템
- **마스터 스케줄러**: 중앙 집중식 작업 관리
- **디스패치 시스템**: Slack, Notion, Email 자동 전송
- **상태 모니터링**: 실시간 시스템 상태 추적

### 🔍 검색 및 분석
- **REPORT_KEY 검색**: 통합 검색 인터페이스
- **로그 분석**: 구조화된 로그 처리 및 분석
- **메모리 인사이트**: 학습 데이터 기반 인사이트 생성

## 🚀 빠른 시작

### 환경 설정
```powershell
# 환경변수 설정
$env:VELOS_DB_PATH = "C:\giwanos\data\velos.db"

# VELOS 실행
powershell -ExecutionPolicy Bypass -File scripts\run_velos_search.ps1
```

### 대시보드 실행
```powershell
# Streamlit 대시보드
streamlit run apps\search_app.py
```

## 📈 성능 벤치마크

VELOS는 지속적인 성능 모니터링을 통해 시스템 안정성을 보장합니다:

- **Insert 성능**: 2000행 삽입 최소 500 QPS
- **Search 성능**: 40회 검색 최대 0.5초
- **자동 테스트**: 매일 UTC 18:00 (KST 03:00) 자동 실행

## 🧯 문제 발생 시

### 배지 상태 진단
- **배지 회색, "No runs" 표시** → 워크플로우 한 번 수동 실행
- **배지 404** → 파일명/경로 오타, 리포 이름 불일치
- **초록불인데 실제 느리다** → Actions 로그의 `bench_*.log`에서 `[sanity] mode/sync` 먼저 확인. `mode=wal`, `sync=2` 아니면 PRAGMA 미적용이다. 코드를 `db_open()` 하나로 통일했는지 다시 봐

### 시스템 건강도 체크
> **깃허브 첫 화면만 봐도 오늘 시스템이 건강한지 알 수 있다. 숫자가 초록이면 일단 커피 마셔도 된다. 빨갛게 되면… 커피는 내려놓고 로그부터 봐라.**

## 📝 라이선스

이 프로젝트는 VELOS 운영 철학에 따라 개발되었습니다.

## 🤝 기여

VELOS 운영 철학을 준수하며 기여해 주세요. 모든 변경사항은 자가 검증을 거쳐야 합니다.
