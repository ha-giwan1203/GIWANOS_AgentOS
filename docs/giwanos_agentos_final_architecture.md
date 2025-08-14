# VELOS AgentOS 최종 아키텍처 문서

## 1. 시스템 개요

VELOS (VELocity OS)는 지능형 자동화 및 메모리 관리 시스템으로, 외부 메모리 기반의 안정적인 운영을 목표로 설계되었습니다.

### 1.1 핵심 철학
- **파일명 절대 변경 금지**: 시스템 안정성 확보
- **모든 수정 후 자가 검증 필수**: 품질 보증
- **결정·기억·보고의 구조적 사고**: 체계적 운영
- **실시간 외부 메모리 반영**: 지속적 학습

## 2. 폴더 구조 및 역할

```
giwanos/
├── configs/                 # 설정 및 보안
│   ├── settings.yaml       # 시스템 경로 및 기능 설정
│   ├── system_config.json  # 시스템 동작 규칙
│   ├── judgment_rules.json # 판정 기준
│   ├── decision_rules.json # 의사결정 규칙
│   └── security/          # 암호화 및 보안
├── data/                   # 데이터 저장소
│   ├── memory/            # 메모리 시스템
│   │   ├── learning_memory.json      # 학습 메모리
│   │   ├── learning_summary.json     # 메모리 요약
│   │   ├── velos_memory.db          # SQLite 메모리 DB
│   │   └── memory_buffer.jsonl      # 실시간 버퍼
│   ├── reports/           # 보고서 시스템
│   │   ├── auto/         # 자동 생성 보고서
│   │   └── _dispatch/    # 전송 대기열
│   ├── reflections/      # 자기 성찰 데이터
│   ├── logs/            # 시스템 로그
│   ├── backups/         # 백업 파일
│   └── snapshots/       # 시스템 스냅샷
├── modules/              # 핵심 모듈
│   ├── core/            # 핵심 기능
│   ├── automation/      # 자동화
│   ├── evaluation/      # 평가 및 검증
│   └── advanced/        # 고급 기능
├── scripts/             # 실행 스크립트
│   ├── run_giwanos_master_loop.py    # 메인 루프
│   ├── velos_bridge.py               # 브릿지 시스템
│   ├── velos_ai_insights_report.py   # AI 인사이트
│   └── velos_report.py               # 기본 보고서
├── tools/               # 유틸리티
│   ├── notifications/   # 알림 시스템
│   ├── notion_integration/ # Notion 연동
│   └── email_management/   # 이메일 관리
├── interface/           # 사용자 인터페이스
├── fonts/              # 폰트 파일
└── vector_cache/       # 벡터 캐시 (선택적)
```

## 3. 메모리 설계

### 3.1 메모리 계층 구조
```
1. 실시간 버퍼 (memory_buffer.jsonl)
   ↓ (flush)
2. 학습 메모리 (learning_memory.json)
   ↓ (동기화)
3. SQLite DB (velos_memory.db)
   ↓ (백업)
4. 스냅샷 (backups/)
```

### 3.2 메모리 동작 원리
- **JSONL 버퍼**: 실시간 데이터 수집
- **주기적 Flush**: JSONL → JSON 변환
- **DB 동기화**: JSON → SQLite 저장
- **자동 백업**: 주기적 스냅샷 생성

## 4. 백업 전략

### 4.1 백업 유형
- **일일 백업**: 매일 새벽 1시 자동 실행
- **스냅샷**: 시스템 상태 보존
- **클라우드 백업**: GitHub Private Repo 연동

### 4.2 백업 대상
- `velos.db` (메인 데이터베이스)
- `learning_memory.json` (학습 메모리)
- `learning_summary.json` (메모리 요약)
- 시스템 설정 파일들

## 5. 자동화 스크립트 구조

### 5.1 스케줄링 시스템
```
modules/automation/scheduling/
├── backup_scheduler.py      # 백업 스케줄러
├── integrity_checker.py     # 무결성 검사
├── report_generator.py      # 보고서 생성
└── notification_sender.py   # 알림 전송
```

### 5.2 실행 순서
1. **시스템 상태 확인** → `system_health.json` 업데이트
2. **메모리 동기화** → JSONL → DB 변환
3. **보고서 생성** → 자동 보고서 작성
4. **외부 전송** → Slack/Notion/이메일
5. **백업 실행** → 스냅샷 생성

## 6. 외부 연동 아키텍처

### 6.1 Slack 연동
- **API 토큰**: `SLACK_BOT_TOKEN`
- **채널 ID**: `SLACK_CHANNEL_ID`
- **전송 방식**: 파일 업로드 + 텍스트 메시지
- **재시도 로직**: 3회 시도 후 실패 처리

### 6.2 Notion 연동
- **API 토큰**: `NOTION_TOKEN`
- **페이지 ID**: `NOTION_PARENT_PAGE_ID`
- **전송 내용**: 보고서 및 백업 요약
- **형식**: Markdown → Notion 페이지

### 6.3 이메일 연동
- **SMTP 설정**: Gmail/Outlook 지원
- **수신자**: 관리자 이메일
- **내용**: 시스템 상태 보고서
- **주기**: 주간 자동 발송

## 7. 오류 처리 및 복구

### 7.1 오류 분류
- **경고 (Warning)**: 일시적 문제, 자동 복구
- **오류 (Error)**: 수동 개입 필요
- **치명적 (Critical)**: 시스템 중단, 즉시 알림

### 7.2 복구 전략
- **자동 복구**: 간단한 오류는 자동 처리
- **스냅샷 복구**: 백업에서 시스템 복원
- **수동 복구**: 복잡한 오류는 관리자 개입

## 8. 성능 최적화

### 8.1 메모리 최적화
- **JSONL 버퍼 크기**: 최대 1000개 항목
- **DB 인덱싱**: 자주 검색되는 필드 인덱스
- **정기 정리**: 오래된 로그 및 임시 파일 삭제

### 8.2 CPU 최적화
- **비동기 처리**: I/O 작업 비동기화
- **배치 처리**: 대량 데이터 일괄 처리
- **캐싱**: 자주 사용되는 데이터 캐시

## 9. 보안 고려사항

### 9.1 데이터 보호
- **암호화**: 민감 정보 AES-256 암호화
- **접근 제어**: 파일 권한 설정
- **백업 암호화**: 클라우드 백업 암호화

### 9.2 API 보안
- **토큰 관리**: 환경변수로 API 토큰 관리
- **요청 제한**: API 호출 빈도 제한
- **로깅**: 모든 API 호출 로그 기록

## 10. 확장성 계획

### 10.1 단기 확장 (3개월)
- 벡터 검색 기능 추가
- 멀티 유저 지원 준비
- 고급 분석 기능 구현

### 10.2 중기 확장 (6개월)
- 클라우드 네이티브 아키텍처
- 마이크로서비스 분리
- 실시간 대시보드

### 10.3 장기 확장 (1년)
- AI 모델 통합
- 분산 처리 시스템
- 엔터프라이즈급 기능

---

**문서 버전**: 1.0  
**최종 업데이트**: 2025-08-14  
**작성자**: VELOS Development Team
