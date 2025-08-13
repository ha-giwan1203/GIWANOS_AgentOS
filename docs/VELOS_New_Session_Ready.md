# VELOS 시스템 정리 현황 (새 방 작업용)

## 1. 최상위 폴더 구조 (C:\giwanos)
C:\giwanos
├── configs
│   └── security
├── data
│   ├── logs
│   ├── reports
│   ├── reflections
│   ├── memory
│   ├── snapshots
│   └── backups
├── docs
├── fonts
├── interface
├── modules
│   ├── core
│   ├── advanced
│   ├── evaluation
│   └── automation
├── scripts
├── tools
│   ├── notifications
│   ├── notion_integration
│   ├── email_management
│   └── chatbot_tools
└── vector_cache

📌 원칙: 폴더 구조 고정 / 변경 금지
📌 경로는 항상 절대경로 사용
📌 파일명 변경 금지

---

## 2. 데이터 복원
- memory: 백업본에서 파일만 추출 → C:\giwanos\data\memory 병합
- reflections: 백업본에서 파일만 추출 → C:\giwanos\data\reflections 병합

---

## 3. 자동화 스크립트
- housekeep.py: 30일 이상 된 로그/임시/백업 파일 자동 삭제
- 스케줄러: 매일 01:00 SYSTEM 권한 실행
- 로그 저장: C:\giwanos\data\logs\report_cleanup_log.json

---

## 4. 남은 작업
1. VELOS 마스터 루프 테스트
2. 백업본 보관
3. 모듈 경로 및 import 점검
4. 실행 환경 테스트

---

## 5. 주의사항
- 폴더 구조 변경 금지
- 경로 절대경로 고정
- 파일명 변경 금지
- 데이터 병합 시 폴더 단위 복사 금지 (파일만 병합)


