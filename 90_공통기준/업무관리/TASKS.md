# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-04-03 — PPT 자동 생성 스킬 MVP 2종 PoC 완료 (f1da0084)

---

## 진행 중

### [진행] PPT 자동 생성 스킬 구축 — **MVP 2종 PoC 완료, GPT 최종 판정 대기**
- 출처: 사용자 요청 (2026-04-03) — YouTube AI PPT 생성 영상 기반 스킬화 제안
- GPT 토론 합의: C(템플릿)+D(python-pptx+AI) 혼합, Anthropic QA 차용
- 엔진: python-pptx 1.0.2 + matplotlib 3.10.8
- MVP 1 (품질 대책서): cfb88dde — 카드형 보고서 QA PASS
- MVP 2 (월간 생산실적): b22ef085 — 표+차트+KPI 카드 QA PASS
- SKILL.md: 90_공통기준/스킬/pptx-generator/SKILL.md (3층 아키텍처 + QA 3축)
- 다음: GPT 최종 판정 → 실무 투입 준비

---

## 대기 중 (우선순위 순)

### [대기] settlement 스킬 preloading 테스트 — **대기: 4월 정산 데이터**
- 출처: subagent 확장 plan 구현 (2026-04-02)
- settlement-validator.md 생성 완료, skills preloading 실테스트는 정산 데이터 입수 후



### [대기] verify_xlsm.py COM 실검증 — **대기: 다음 xlsm 작업 시 실행**
- 출처: 1단계 구조적 가드레일 GPT 공동작업
- verify_xlsm.py 구조는 완료. COM 실검증 산출물(verify.json PASS)은 xlsm 작업 재개 시 확인
- hooks 3개 + settings merge 구현 완료 (GPT 구조 PASS)

### [auto] 정산 파이프라인 실행 테스트 확인 — **차단: 4월 데이터 대기**
- 출처: `step7_대시보드.py` 변경 감지
- 자동 생성 항목 — 4월 GERP/구ERP 실적 데이터 입수 후 자동 확인 예정
- 현 시점 강제 실행 불필요 (3월 데이터 기준 파이프라인 정상 동작 확인됨)




### ~~[낮] 루트 CLAUDE.md 하네스 원칙 승격~~ → 완료됨

### ~~[낮] 도메인 STATUS.md 점검~~ → 완료됨 (2026-03-31)
- 조립비정산 STATUS.md: 정합성 OK
- 라인배치 STATUS.md: OUTER 재개 취소 반영 (커밋 833a675b)

---

## 완료됨

| 항목 | 완료일 |
|------|--------|
| 병렬 실행 규칙 신규 — 읽기/검증 병렬, 쓰기/반영 직렬, GPT 대기 병행 (GenSpark 토론 합의, GPT PASS 463dc674) | 2026-04-03 |
| 전체 기능 실동작 점검 — smoke 36/36, hooks 14종 실발화, 파이프라인 6/6 py_compile, 스킬 24pkg, 토론모드 9/9 셀렉터 (GPT 최종 PASS a68c16d3) | 2026-04-03 |
| 전체 기능 전검 — jq 완전 제거 3파일 + STATUS.md 정합 수정 (GPT PASS c0549cfb), 보류 3건 현행 유지 합의 | 2026-04-03 |
| hooks Git 추적 + A그룹 6개 통합 로깅 — 16개 hook git add -f, A그룹 6/6 실발화 실증 (GPT 최종 PASS c30c791b) | 2026-04-03 |
| hooks 수리 3건 — jq→python3, domain_guard Bash matcher, 통합 로깅 hook_common.sh (GPT 조건부 PASS 0d4288be) | 2026-04-03 |
| ZDM 일상점검 — SP3M3 19개 점검표 75건 OK 입력 (2026-04-03, day=3), 검증 75/75 PASS | 2026-04-03 |
| MES 생산실적 업로드 — 4/2 15건, 46,459ea, 건수·생산량 합계 일치 PASS | 2026-04-03 |
| ZDM 일상점검 — SP3M3 19개 점검표 75건 OK 입력 (2026-04-02, day=2) | 2026-04-02 |
| MES 생산실적 업로드 — 4/1 15건 업로드 완료, 43,249ea 검증 PASS (3/25~3/31 기존 등록 확인) | 2026-04-02 |
| MES SKILL.md 자동 로그인·iframe 동적 탐지 반영 — pyautogui 절차 + iframe-0 실증 + 재패키징 (5f990f5f) | 2026-04-02 |
| MES 전체 흐름 테스트 PASS — CDP재시작→자동로그인→MES진입→iframe탐지→데이터조회 6단계 완전 검증 | 2026-04-02 |
| completion_gate 반복 차단 수정 — openpyxl 읽기 전용 오탐 제거 (save 포함 시만 dirty 판정, 8b7ef521) | 2026-04-02 |
| post_write_dirty.sh 리다이렉트 패턴 경로인식형 전환 + matched_pattern 로깅 — 허용목록 제외형, dirty.flag 6줄, 따옴표/중괄호 변수 허용, GPT PASS (41ddb99e) | 2026-04-02 |
| hooks 층 표준화 — 24개 훅 8분류(감지/차단/정리/알림/감사/세션/미연결/유틸), README.md 문서화 (GPT 합의) | 2026-04-02 |
| smoke_test 신규 3훅 커버리지 — completion_gate+cleanup_audit+domain_guard 17건 추가, 36/36 PASS (f6d1ff92, GPT PASS) | 2026-04-02 |
| youtube-analysis 도메인 가드 등록 — config.yaml+prompt_inject+CLAUDE.md (d1250a99) | 2026-04-02 |
| 하네스 영상 분석 — 실베개발자 4축 프레임워크, 갭 분석(가비지 컬렉션 부분갭), Claude+GPT 취합 | 2026-04-02 |
| cleanup_audit.sh Stop hook — untracked 파일 감지·정리 강제, 예외(TASKS/HANDOFF 언급+도메인 산출물) (49e69f19→8d933918, GPT PASS) | 2026-04-02 |
| completion_gate v2 — 작업 완료 시 TASKS/HANDOFF 갱신 자동 강제, STATUS 경고 (08c44050→e995d0b8, GPT PASS) | 2026-04-02 |
| domain_guard 화이트리스트 전환 — 도메인 문서 미로드 시 전체 도구 차단 (d2b7d6ea, GPT PASS) + 토론모드 공유 규칙 추가 | 2026-04-02 |
| 기능 활용 갭 분석 — 커스텀 명령 우선순위·커넥터 내장·Context7 제한·병렬 반자동·IDE 보류 합의 + .claude/rules/feature-utilization.md 생성 (GPT PASS) | 2026-04-02 |
| 영상분석(Context Rot+GSD) → Fast/Full Lane 판정 규칙 신규 — GPT 토론 합의 + .claude/rules/fast-full-lane.md 생성 (커밋 15b06459, GPT 실물 검증 PASS) | 2026-04-02 |
| subagent 확장 구현 — settlement-validator 생성 + code-reviewer memory 테스트(Case A: 미활성화 확인) → 현행 유지 결정 (GPT 검증 진행 중) | 2026-04-02 |
| 영상분석 자동 모드 1차 실행 — 3영상 분석 + 교차검증 + GPT 토론 합의 → A2 SubagentStart/SubagentStop hooks 구현 + B1 subagent 확장 plan 작성 | 2026-04-01 |
| youtube-analysis 스킬 자동 모드 설계 — 8단계 워크플로우 + A/B/C 3단 게이트 + 교차검증 의무화 + 분석관점 9개 (GPT 공동작업 합의) | 2026-04-01 |
| 운영 안정화 업그레이드 — 훅 6개 + rules 5개 + agent 1개 + command 1개 + CLAUDE.md 경량화 + 토론모드 셀렉터 수정 (GPT 검증 PASS: 4e4a6264) | 2026-04-01 |
| 1단계 구조적 가드레일 구현 — hooks 3개(pre_write_guard/post_write_dirty/pre_finish_guard) + settings merge + verify_xlsm.py 2단계 구조 (GPT 구조 PASS) | 2026-04-01 |
| GPT 후속작업 강제 가드 — gpt_followup_guard.sh (PostToolUse+Stop 겸용, pending.flag 상태기계) GPT 합의 | 2026-04-01 |
| 폴더 마이그레이션 Phase 0~7 | 2026-03-28 |
| 파일 정리 1차 (94건 아카이브) | 2026-03-28 |
| 커넥터 운영 지침 v1.0 확정 | 2026-03-28 |
| 보호 파일 10건 목록 고정 | 2026-03-28 |
| 보류 파일 5건 최종 판정 | 2026-03-28 |
| CLAUDE.md 전면 개정 (1차) | 2026-03-28 |
| __pycache__ 삭제 | 2026-03-28 |
| Notion 업무 현황 페이지 생성 | 2026-03-28 |
| Slack 완료 보고 발송 | 2026-03-28 |
| Google Calendar 후속 작업 4건 등록 | 2026-03-28 |
| GitHub 운영 문서 push (PR #8) | 2026-03-28 |
| GitHub PR #8 머지 (main 반영) | 2026-03-28 |
| 자동화 동기화 Phase 1 (watch_changes.py) | 2026-03-28 |
| 자동화 동기화 Phase 2 (commit_docs.py) | 2026-03-28 |
| 자동화 동기화 Phase 3 (update_status_tasks.py) | 2026-03-28 |
| 자동화 동기화 Phase 4 (slack_notify.py) | 2026-03-28 |
| Slack 채널 연결 테스트 (MCP 경유) | 2026-03-28 |
| watch_changes.py Startup 폴더 상시 실행 등록 | 2026-03-28 |
| 작업 스케줄러 등록 파일 작성 (bat/xml) | 2026-03-28 |
| 폴더 생성 규칙 메모리 저장 | 2026-03-28 |
| 커넥터 운영구조 재정의 (Drive/GitHub/Notion 역할 확정) | 2026-03-28 |
| CLAUDE.md 2차 개정 (파일명규칙·환경설정 삭제, AI 인수인계 추가) | 2026-03-28 |
| 운영지침_커넥터관리_v1.0.md v1.1 갱신 | 2026-03-28 |
| README.md 신규 생성 (루트 AI 세션 진입점) | 2026-03-28 |
| HANDOFF.md 신규 생성 (AI 인수인계 문서 체계) | 2026-03-28 |
| GitHub PR #9 생성 및 main 머지 | 2026-03-28 |
| 조립비정산 데이터사전 동기화 (데이터사전 v1.0 + pipeline_contract.md + CLAUDE.md) | 2026-03-28 |
| line-batch-management.skill 패키지화 (v7→v9 기준 전환, SNAP-ON/LASER MARKING 갱신) | 2026-03-28 |
| ENDPART라인배정 파일 용도 확인 — 임시 참고자료 확정 (갱신 기준 불필요) | 2026-03-28 |
| MCP context7 설치 (`@upstash/context7-mcp`) | 2026-03-30 |
| MCP sequential-thinking 설치 (`@modelcontextprotocol/server-sequential-thinking`) | 2026-03-30 |
| mcp_설치현황.md 신규 생성 (전체 MCP 목록·프롬프트 문서화) | 2026-03-30 |
| youtube-analysis 스킬 제작 (URL → 자막 자동 추출 + 분석) | 2026-03-30 |
| YouTube_영상분석.md 프롬프트 신규 생성 | 2026-03-30 |
| 하네스 엔지니어링 파일럿 도입 (조립비정산 Evaluator + 운영가이드 + 스킬평가기준표) | 2026-03-30 |
| Slack Bot Token 갱신 완료 — slack_notify.py 발송 성공, slack_config.yaml 경로 수정 | 2026-03-28 |
| Slack 멘션 추가 — build_message + --message 경로 두 곳 mention_user_id 적용, 폰 알림 정상화 | 2026-03-28 |
| 파일 정리 2차 확인 — 99_임시수집 비어있음, 추가 작업 없음 | 2026-03-28 |
| 작업 스케줄러 등록 (업무리스트_WatchChanges 로그온 트리거) | 2026-03-30 |
| Step 6 FAIL 2레벨 분리 (KNOWN_EXCEPTIONS/severity/overall 3단계) | 2026-03-30 |
| skill-creator 3단계 절차 연결 (harness 모드, Planner/Generator/Evaluator) | 2026-03-30 |
| 하네스 파일럿 1회차 검증 (Generator FAIL / Evaluator PASS 94점) | 2026-03-30 |
| 상태 원본 단일화 설계 — TASKS 단일 원본, STATUS/HANDOFF 역할 재정의 | 2026-03-30 |
| 조립비 정산 step7 시각화 PoC — HTML 대시보드 + PNG 생성 (GPT PASS) | 2026-03-30 |
| watch_changes.py Phase 6 훅 — .skill 자동 설치 (skill_install.py) | 2026-03-30 |
| step7 Slack PNG 발송 — files:write 스코프 추가, Slack files v2 API 3단계 완성 | 2026-03-30 |
| Plan-First 워크플로우 도입 — CLAUDE.md 3개 규칙 + debate-mode.skill v2.4 + research/plan 템플릿 2종 | 2026-03-30 |
| 전체 폴더 정리 — 토론모드 중복 폴더 제거, debate-mode 언패킹 v2.4 동기화, _cache gitignore 추가 | 2026-03-31 |
| 하네스 파일럿 2회차 — skill-creator harness 모드 3가지 한계 해결 (평가기준참조/KnownException/피드백루프), Evaluator PASS 95점 | 2026-03-31 |
| 루트 CLAUDE.md 하네스 검증 원칙 승격 — 공통 4원칙(사용시점/3인체제/KnownException/피드백루프) GPT 공동작업 | 2026-03-31 |
| 루트 CLAUDE.md 공동작업 운영 원칙 5항목 추가 + 공동작업 표 금지 반영 | 2026-03-31 |
| Phase 1-1 Hooks 하이브리드 도입 — SessionStart/PreToolUse/Notification/ConfigChange/InstructionsLoaded/SessionEnd 6건, GPT 조건부 승인 | 2026-03-31 |
| 도메인 STATUS.md 점검 완료 — 조립비정산 정합성 OK, 라인배치 OUTER 재개 취소 반영 | 2026-03-31 |
| 프로젝트 커맨드 3종 작성 — doc-check/task-status-sync/review-claude-md (.claude/commands/ + Git 미러링) | 2026-03-31 |
| auto_commit_config.yaml 오기입 수정 — branch: "업무리스트"→"main", push_on_commit: false→true (자동화 체인 복구) | 2026-03-31 |
| Hooks 실전 패턴 적용 — PreToolUse 보호 2계층, PostToolUse 로그, Notification 스팸방지 (GPT 승인) | 2026-03-31 |
| A2 멀티에이전트 research — subagents 적합/agent teams 보류 판정 (GPT 승인) | 2026-03-31 |
| A2 subagent 파일럿 — doc-check FAIL 3건 + task-status-sync FAIL 4건 즉시 수정 (정합성 복구) | 2026-03-31 |
| B1 아키텍처 정리 — AGENTS_GUIDE.md 신설 (6계층 맵 + 구성요소 목록 + 세션 체크리스트) | 2026-03-31 |
| B2 스킬 생태계 research — 커뮤니티 벤치마킹, 도입 불필요 판정 (GPT PASS) | 2026-03-31 |
| B3 제조업 AI research — 확대 후보 3건 + Gap 분석, research 종료 (GPT PASS) | 2026-03-31 |
| CLAUDE.md 공동작업 원칙 강화 — Claude 독립 판단 의무 + 5단계 검증 절차 추가 | 2026-03-31 |
| watch_changes 헬스체크 — check_watch_alive.bat + 5분 주기 스케줄러 등록 (GPT PASS) | 2026-03-31 |
| auto_watch_config xlsx/docx/pdf 감시 소음 제거 (GPT PASS) | 2026-03-31 |
| auto-commit dry-run 검증 성공 — branch 수정 후 7배치 정상 (최종 PASS: 실제 커밋 1회 대기) | 2026-03-31 |
| debate-mode v2.5~v2.9 — 입력(execCommand)/완료감지(stop-button)/응답읽기 전면 개편 + 하네스 비판적 분석 + 사용자 중간 확인 금지 + GPT 재공유 루프 + 적응형 polling 5/10/15초 | 2026-04-01 |
| hooks 신규 3개 — Stop(stop_guard.sh v2 금지문구+채택/버림), SessionStart(등록), UserPromptSubmit(prompt_inject.sh 체크리스트 주입) | 2026-04-01 |
| hooks 강화 — post_validate.sh v2 CLAUDE.md 내부 모순 자동 감지 + stop_guard BLOCK 로깅 | 2026-04-01 |
| CLAUDE.md 슬림화 — 루트 322→230줄, 토론모드 223→167줄. skill_guide.md 분리 | 2026-04-01 |
| Context Engineering — 세션 토큰 운영 규칙 + subagent 3개(evidence-reader/debate-analyzer/artifact-validator) | 2026-04-01 |
| 운영 검증 체계 — analyze_hook_log.sh KPI + smoke_test.sh 10/10 PASS + 경고 임계치 | 2026-04-01 |
| bi_copy.bat 스케줄러 삭제 → SKILL.md 0단계 통합 (업로드 시 자동 갱신) | 2026-04-01 |
| bi_copy 잔존 참조 전면 정리 — status_rules/SKILL/STATUS/보호목록 갱신 + bat 3파일 아카이브 | 2026-04-01 |
| BI 경로 원본 단일화 — production-result-upload 0단계를 단일 원본으로 지정 | 2026-04-01 |
| 상태 메타데이터 갱신 — TASKS.md 최종 업데이트 현행화 | 2026-04-01 |
| Notion 동기화 강화 — notion_sync.py 요약 블록 상세화 + 검증 스냅샷 + 자동반영 규칙 | 2026-04-01 |
| Notion 부모 페이지 링크 허브 단순화 — 요약/이력 제거, STATUS 단일 원본화 (GPT 합의) | 2026-04-01 |
| 검증 결과 자동반영 규칙 문서화 — PASS/조건부/FAIL 표준 문장 세트 (GPT 합의) | 2026-04-01 |
| Notion 이력 보존 정책 — _trim_history_blocks(20건) + update_summary 실패 승격 ok3 | 2026-04-01 |
| settings allow 정리 172→46개 + OAuth 토큰 제거 + 요약본 문서화 | 2026-04-01 |
| 커넥터 운영지침 v1.3 — 자동화 연결 권한 경계 표준화 (읽기/쓰기/전송 3단계 + 주체별 정리) | 2026-04-01 |
| daily-doc-check scheduled task 생성 (평일 09시 TASKS/STATUS/HANDOFF 정합성 체크) | 2026-04-01 |
| PLAN_OUTPUT 동적 조회 시트 추가 — Table 기반 37컬럼, MATCH+INDEX 수식, GPT 실물 검증 PASS (v2.xlsm) | 2026-04-02 |
| GetModelGroup 동적 조회 개선 — 하드코딩 40개 차종 제거, B열 동적 수집 + StrComp 정확비교, GPT 코드 PASS + COM 자동 주입 (v2.xlsm) | 2026-04-01 |
| 영상/리소스 발굴 안건 10건 처리 완료 — hooks/subagent/문서 구현 7건 + 확인 2건 + 안내 1건 | 2026-03-31 |
| 업무리스트 전체 커버리지 맵 작성 — 27건 전수 맵핑, 우선순위 확정 | 2026-03-31 |
| sp3-production-plan.skill 패키징 — 생산계획 v3.0 문서 3건 통합 (#11) | 2026-03-31 |
| production-report.skill 패키징 — BI 실적+임률단가+API 기반 집계 (#12~14) | 2026-03-31 |
| cost-rate-management.skill 패키징 — 임률단가 3계층 관리 (#7) | 2026-03-31 |
