# 업무관리 폴더 인덱스

## 상태 원본 (세션 진입점)
| 파일 | 역할 |
|------|------|
| TASKS.md | AI 작업 상태 유일 원본 |
| STATUS.md | 운영 요약, 재개 위치, 주의사항 |
| HANDOFF.md | 세션 변경사항, 다음 AI 액션 메모 |

## 운영 기준 문서
| 파일 | 역할 |
|------|------|
| CLAUDE.md | 업무관리 도메인 규칙 |
| AGENTS_GUIDE.md | 에이전트 운영 가이드 |
| skill_guide.md | 스킬 사용 기준표 |
| 운영지침_커넥터관리_v1.0.md | 커넥터·알림·권한 경계 표준 |

## 현업 업무 원본
| 파일 | 역할 |
|------|------|
| 업무_마스터리스트.xlsx | 현업 업무 일정·과제·우선순위 기준 원본 |
| 업무_자동화_통합관리.xlsx | 자동화 대상 업무 관리 |

## 실행 파일 (자동화 파이프라인)
| 파일 | 역할 |
|------|------|
| watch_changes.py | 파일 변경 감시 (Phase 1) |
| commit_docs.py | 자동 커밋 (Phase 2) |
| update_status_tasks.py | 상태문서 갱신 (Phase 3) |
| slack_notify.py | Slack 알림 (Phase 4) |
| notion_sync.py | Notion 동기화 (Phase 5) |
| skill_install.py | 스킬 설치 유틸 |

## Config
| 파일 | 역할 |
|------|------|
| auto_watch_config.yaml | 감시 설정 |
| auto_commit_config.yaml | 커밋 설정 |
| notion_config.yaml | Notion 연결 설정 |
| slack_config.yaml | Slack 연결 설정 |
| status_rules.yaml | 상태 갱신 규칙 |

## 런처 / 스케줄러
| 파일 | 역할 |
|------|------|
| watch_changes_launcher.vbs | 감시 프로세스 런처 |
| check_watch_alive.bat | 감시 프로세스 상태 확인 |
| check_watch_alive.vbs | 감시 프로세스 상태 확인 (VBS) |
| register_watch_task.bat | 작업 스케줄러 등록 |
| watch_task.xml | 작업 스케줄러 설정 |

## 하위 폴더
| 폴더 | 내용 |
|------|------|
| _로그/ | 작업로그, git 커밋로그, 에러로그 |
| _플랜/ | plan_*.md, research_*.md (완료된 작업 산출물) |
| _운영문서/ | 참고용 운영문서 (하네스 가이드, 보호목록 등) |
