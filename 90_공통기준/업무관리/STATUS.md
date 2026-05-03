# 업무리스트 전체 운영 현황

> **이 파일은 운영 요약·재개 위치·주의사항 전용이다.**
> 작업 완료/미완료 상태의 원본은 TASKS.md이다. 이 파일에 상태를 독립 선언하지 않는다.
> 도메인 하위 `STATUS.md`와 `TASKS.md`는 도메인 내부 메모로만 사용한다. 전역 상태 우선순위는 `업무관리/TASKS.md` 기준이다.

최종 업데이트: 2026-05-03 KST — 세션137 ([D+3way] **Claude Code 환경 리모델링 Round 1 합의 — pass_ratio 1.0** — 토론 (Claude × GPT × Gemini). 결론: Option 3 Hybrid 2-Layer 채택 (메타 .claude/는 결정론 도구·코드로 치환, 도메인 자산 보존·격리). 진입: R5 dry-run 선행 → 단일 PR(동작 무변경: 태그+백업+격리 폴더+측정 베이스라인) → Phase 점진 8단계(rules/* 5→1 → hook 45→5 → Slash 33→5 → Skill 평균 305→80 → Subagent 9→5 → Permissions 130→15 → Worktree 17→3 → 7일 측정). 실패 정의: 관리비용 역전 + 인지적 부채(GPT+Gemini). 메타 한계: spec drift·자기교정·결정 회피는 셋팅 보완 불가, 행동 교정 문구 추가는 누적 부패 시작점. 산출물: 90_공통기준/토론모드/logs/debate_20260503_101125_3way/ (consensus.md + round1_*.md + session.json). critic-reviewer 통과 (필수 2축 PASS, 일방성 WARN — Claude 독자 기여 가시화 미흡). 미합의 Round 2 의제 4건: (1) 사용자 답변 필요 — 17 worktree+45 hook 중 생존 필수 3가지 (2) 헤비유저 4지표 목표선 구체 수치 (3) 행동 교정 메타 0 경계 (4) GLOSSARY.json+RAG 도입. 다음: R5 dry-run 실측 또는 Round 2 진입) / 세션136 ([C] 자동모드 layer 폐기 3way 양측 부분PASS) / 세션135 ([A] **D0+잡셋업 chain GPT 최종 PASS** — verdict PASS, 4 items 전부 동의 (item 1·2·4 실증됨 / item 3 구현경로미정 동의). 하네스 채택 4 / 보류 0 / 버림 0. 추가제안 없음. 다음 의제: 5/4 월요일 morning 자동 chain 첫 실가동 로그 확인) ([A] **D0+잡셋업 chain end-to-end 실측 PASS** — 휴일 5/2 테스트. 5/4 xlsm에서 RSP3SC0584 150EA 1건 추출 → ERP D0 등록 (REG_NO=320623, MES rsltCnt=50) → SmartMES 검증 ✅ → schedule API 자동 회수 → list.api 17 items already_done dedupe ✅. --xlsx 분기 chain 호출 누락 발견 + 정정 1줄 추가) ([A] **잡셋업 v3.x GPT 부분PASS** — verdict 부분PASS / item 1·2·4 동의 (구조정합·실증완료·정책정합) / item 3 chain 보류 (조건부활성, 5/4 실가동 미검증). 하네스: 채택 3 / 보류 1 / 버림 0. 추가제안 A분류 "5/4 첫 실행 list-only 1회 후 commit-all 복귀" 사용자 결정 대기) ([A] **잡셋업 chain 활성** — d0-production-plan/run.py morning SP3M3 등록 성공 직후 잡셋업 v3.x 자동 호출 (subprocess + 180s timeout + advisory). --no-jobsetup / --jobsetup-mode flag 추가 (default commit-all). dry-run/parse-only/--no-jobsetup 시 스킵. 5/4 월요일 첫 자동 실행 사용자 입회 monitoring 권장) ([A] **잡셋업 v3.3 완료 — 첫 서열 자동 회수 (schedule API)** — dnSpy 비대화 디컴파일로 GetProductionSchedule 추출 (POST /v2/prdt/schdl/list.api, body {prdtDa, lineCd}). 라이브 검증 4/29·4/30·5/1 morning xlsm 기록과 rank=1 100% 일치. call_schedule/resolve_first_sequence 함수 + --auto-resolve-pno flag + 사용자 --pno cross-check abort. 토요일(5/2) items=0 abort 정상. spec: state/schedule_api_spec_20260502.md. 다음 chain 적용 가능: `--mode commit-all --auto-resolve-pno` (xlsm 의존성 제거 가능, 활성은 입회 monitoring 후)) ([A] **잡셋업 v3.2 부분 — config 외부화 + --env dev|prod flag** — run_jobsetup.py에 load_env_config() 신설 (환경변수 → config.json[env] → dev_default 3순위 fallback) + setup_runtime() + --env CLI flag (default dev). config.example.json 신규 + .gitignore에 config.json 추가 (token 차단). SKILL.md 선결조건 v3.x/legacy 2섹션 분리. PLAN_REST_API.md 후속 v3.2 부분 완료 표기. 검증 PASS: dev list-only 17 items + prod 미설정 abort + 환경변수 override 적용. prod 실값(server/token)은 사용자 prod MESClient.exe.config 제공 시 즉시 적용 가능. plan: tingly-gathering-shannon.md / Phase B(v3.3 dnSpy)·Phase C2(B형 strict) 사용자 결정 대기) / 세션134 ([A] **잡셋업 v3.0 REST API 직호출 마이그레이션 완료** — UI 자동화 완전 폐지. MESClient.exe.config + dnSpy 디컴파일로 endpoint·token·헤더 spec 추출 → POST /v2/checksheet/check-result/jobsetup/{list,save}.api + 헤더 7개(tid/chnl/from/to/lang/usrid/token) + JobSetupItem JSON. 5/2 첫 서열 RSP3SC0646_A 17/17 검사항목 commit-all PASS ~30초. 4모드 list-only/dry-run/commit-one/commit-all. 시나리오 3 → 시나리오 1 정정. v3.0 본체 promote, v2.x/v1 legacy 보존. PLAN_REST_API.md / 다음 morning 2026-05-03 chain 자동 실행 시 사용자 입회 모니터링 / v3.x: 다른 라인 지원·prod endpoint·B형 fallback 운영 정책 검증) ([A+C] **잡셋업 v2.0 pywinauto UIA 마이그레이션 완료** — mesclient.exe TCP 폴링으로 시나리오 3 확정(210.216.217.95 + 6379/18100/19220 비표준 포트, 표준 HTTP 0건) → pywinauto UIA inspect 12/12 컨트롤 식별 → run_jobsetup.py v2 promote (좌표·해상도·numpad 의존성 0%) + run_jobsetup_legacy.py 보존 + 4모드 probe(fast_fail)/select-only/enter-only/commit + ComboBox HOME+ENTER + LegacyIAccessible Value read-back. Phase 1 검증 4/4 PASS — 실측 SmartMES `[ OK ] 점검결과 저장 성공` lblMsg 회수. SKILL.md status v2.0. plan: wiggly-gliding-sundae.md / 다음 morning 2026-05-02 chain 자동 실행 시 사람 입회 모니터링 / v2.x 미해결: 다중 검사항목·다중 공정·OCR·chain 활성 후 안정성) ([C] /self-audit 기준 보강 — settings.local.json 1순위 표현 폐기 → `list_active_hooks.sh --full` SSoT 정렬, 세션93 합의 적용 / commands/self-audit.md + agents/self-audit-agent.md 보강 / C 모드 전환 7경로 명시 + Git 상태 진단 헤더 + GPT 정밀평가 분리 + selfcheck 분리 / 검증 6단계 dry-run PASS — N1=N2=36, 이름 set 대칭차 빈 집합 / 후속 안건: 하네스_운영가이드.md self-audit 현재 상태 정합화 완료, hook_registry.sh는 헤더 LEGACY 명시 충실로 추가 조치 없음 / plan: c-resilient-frost.md / **/self-audit 첫 실행 완료** — anomaly 1건 P1 (share_after_push Failure Contract 누락) 즉시 정합화, P0=completion_before_state_sync 55건/7일은 GPT 정밀평가 대상 보류, P2 일부 정정(gate_boundary_check는 smoke_fast 호출 경로 존재) / **P0 Phase 1 완료** — auto_commit_state.sh 단독 수정 (A+B-lite 채택). final_check stdout/stderr 캡처 → 처방 분류 7종+fallback + session_key/source_file/failure_signature 60분 dedupe. 검증 10항목 전수 PASS. final_check.sh / completion_gate.sh / write_marker.sh 무수정. 7일 모니터링 후 Phase 2/B안 임계 강화/D안(/finish) 별건 검토. plan: p0-completion-loop-plan.md v2 / **정정** auto_commit_state.sh 주석 명확화 — dedupe 판정(60분 윈도우)과 stale 정리(개수 50개 보존)는 분리된 두 메커니즘. 코드 동작은 의도대로, 주석만 혼동 유발해 통일) / 세션133 ([A+C] SP3M3 5/1 morning D0 20건 PASS / 잡셋업 commit / 8개 이슈 근본 수정 / 옵션 A 하이브리드 P3 PASS / 중복 가드 dedupe_existing_registrations 추가 / **--no-mes-send 플래그 + P4 단계 1·2·3 PASS — Content-Type=application/json 발견 + api_rank_batch 함수 본체 + DELETE 정리 / P5 --api-mode dual-mode PASS — 화면 모드 회귀 안전 / **하이브리드 기본화 + 1건 PoC PASS + 문서 정합화** — run.py --api-mode default=True + --legacy-mode fallback. 5/1 14:50 RSP3PC0054 950EA 1건 PoC PASS (REG_NO=320599 + MES 전송). SKILL.md v4.0 + d0-plan.md + erp-mes-recovery-protocol.md 갱신**) / 세션132 ([A+D+C] D0 evening 24건 PASS + 결정 회피 사고 패턴 3자 토론 + 외부 자료 검색 + 환경 슬림화 1라운드 + Round 2 routine 즉시 실행 원칙 + Round 3 근본 해결 1단계 (block_dangerous + protect_files PY_CMD fallback 적용 → incident python3_dependency WARN 12건 차단)) ([E+C] 잡셋업 v0.3 결함 5종 정정 + v1.0 baseline / run_jobsetup.py 230줄 신설 + numpad/minus/C 입력 메커니즘 실측 검증 + 좌표 1456→1920 스케일 1.319 변환 + 매일 1번 품번 변경 발견 + chain 미활성 명시 / v1.x 미해결: 좌표 정확도·B형 분기·OCR·chain 활성) / 세션131 ([B+C] 실패 대응 자동 진단 인용 개선 — 3자 토론 안1+안3 채택, 안2 보류 / incident_quote.md 신설 + finish/daily/d0-plan 사전 점검 / 새 hook 0개 / SP3M3 morning 자동화 모드 E 패치 / 검증은 2026-05-01 07:10 auto-run / **옵션 A 하이브리드 P1+P2 PASS 실증 완료** — P1 GET 200 / P2 사용자 명시 진입 RSP3SC0665 1건 selectList → multiList(REG_NO 319941) → DELETE → 16건 복원 + SmartMES 0 영향. 발견: ajax:true custom header + XSRF 매 요청 갱신 + DELETE method / P3 rank+MES는 시스템팀 답변 후) / 세션130 (hook 부하 B-mode 진단 + settings.local allow 41→23 1회용 정리 + README PreToolUse 표 번호 정합화 / settings.json·hook 스크립트 무수정 / list_active_hooks --count 36 변동 없음) / 세션129 (정량 신호 3개 측정 시작, 옵션C 1주/7세션 / quant_signal_log.md 신설) / 세션128 (block_dangerous false positive + config awk 파싱 버그 패치 14/14 PASS, 양측 PASS [GPT+Gemini 실증됨·동의] / 옵션A 위생 정리 TASKS 598→157·incident 122→0 / ZDM DB 다운 + MES 단독 4/28 15건 OK)

---

## 현재 운영 상태

| 항목 | 내용 |
|------|------|
| 현재 브랜치 | `main` |
| 활성 작업 원본 | `90_공통기준/업무관리/TASKS.md` |
| 미완료 작업 수 | TASKS.md 참조 |
| 자동화 체계 | **Claude hooks 일원화** (2026-04-11). 백그라운드 프로세스 체인(watch_changes→auto_commit→slack→notion) 폐기, Windows 스케줄러 제거 |
| hooks 체계 | **활성 수 기준축: `bash .claude/hooks/list_active_hooks.sh --count` (Single Source, 세션93 2자 토론 합의 / 세션107 수동 카운트 표기 제거)**. 스킬 19개. 세션101 auto_commit_state.sh 신설 (Stop 5번째, 하이브리드 자동 커밋: 상태문서 AUTO, 나머지 MANUAL 리마인더). 세션93 hook_registry.sh legacy 격하. 세션91 final_check statusLine 버그 수정. 세션76 commit_gate push 단독 final_check 스킵 근본 해결. 세션74 쟁점 G 실물 분리. 세션72 Phase 2-B: 핵심 훅 6종 exit 2 전환 + completion_gate 소프트 블록 + timing 배선. |

---

## 현재 재개 위치

| 도메인 | 재개 위치 | 참조 |
|--------|---------|------|
| ~~라인배치 OUTER~~ | ~~runOuterLine(295)~~ — **사용자 취소** (2026-03-31) | `10_라인배치/STATUS.md` 참조 |
| 조립비정산 | 파이프라인 정상 운영 중 | `05_생산실적/조립비정산/CLAUDE.md` |
| subagent 확장 | 구현 완료 (GPT PASS 7bae2a78) | `_플랜/plan_subagent_expansion.md` |
| Fast/Full Lane | 규칙 확정 (GPT PASS 15b06459). 규칙은 `data-and-files.md`로 통합됨 | `.claude/rules/data-and-files.md` |
| 기능 활용 | 합의 완료 (GPT PASS). 별도 규칙 파일 폐기, CLAUDE.md 본문으로 흡수 | `CLAUDE.md` |
| domain_guard | v3 구현 후 폐기 → _archive 이동. risk_profile_prompt로 대체 | `.claude/hooks/_archive/domain_guard.sh` |
| evidence hook | 증거기반 위험실행 차단기 5개 구현 (GPT 부분반영) | `.claude/hooks/evidence_*.sh` |
| 토론모드/게이트 보정 | **현재 정책: chrome-devtools-mcp(CDP) 단독** (세션105 전환, 세션107 L-3 정합). 세션32 Chrome MCP 단일화 → 세션105 CDP 전환으로 갱신됨. send_gate→mcp_send_gate 교체, harness_gate 유지. idle composer 오탐 제거, completion gate 축소, 한국어-only, final_check settings 기준 재정렬 | `90_공통기준/토론모드/`, `.claude/hooks/` |
| 토론모드 보류 안건 | → TASKS.md "진행중 / 보류" 참조 | `90_공통기준/업무관리/TASKS.md` |
| GPT 전송 스킬 | /gpt-send, /gpt-read 실사용 PASS (세션36) | `.claude/commands/gpt-send.md` |
| verify_xlsm | 1차 구조 검증 10/10 PASS, 2차 COM 불필요(결과 시트) | `90_공통기준/agent-control/verifiers/verify_xlsm.py` |
| Notion 부모 페이지 | Integration 연결 + sync_parent_page() 정상 동작 (세션36) | `90_공통기준/업무관리/notion_sync.py` |
| PPT 자동 생성 | 실무 투입 최종 PASS — 실데이터+육안검수 5/5 완료 | `90_공통기준/스킬/pptx-generator/SKILL.md` |
| GPT 지침 Git 관리 | 구현 완료 (GPT PASS 4bcd7877) | `90_공통기준/업무관리/gpt-instructions.md` |

---

## 자동화 체계 (2026-04-11 훅 일원화 전환)

| 기능 | 이전 (폐기) | 현재 |
|------|------------|------|
| 파일 감시 | `watch_changes.py` + Windows 스케줄러 | 폐기 (SPOF — 크래시 시 자동복구 불가) |
| 자동 커밋 | `commit_docs.py` (watch_changes 호출) | 폐기 (hooks 내 completion_gate로 대체) |
| 상태 갱신 | `update_status_tasks.py` | 폐기 (Edit 도구로 직접 갱신) |
| Slack 알림 | `slack_notify.py` (watch_changes 호출) | `notify_slack.sh` Notification hook → `slack_notify.py` |
| Notion 동기화 | `notion_sync.py` (watch_changes 호출) | `/finish` 3.5단계 → MCP `notion-update-page` |
| 스킬 설치 | `skill_install.py` | 유지 (.skill 변경 시 자동 압축 해제) |

---

## 주요 경로 기준

| 역할 | 경로 |
|------|------|
| 조립비 정산 파이프라인 실행 | `05_생산실적\조립비정산\03_정산자동화\run_settlement_pipeline.py` |
| BI 자동갱신 (스킬 내장) | `90_공통기준\스킬\production-result-upload\SKILL.md` 0단계 |
| 조립비 기준정보 | `05_생산실적\조립비정산\01_기준정보\기준정보_라인별정리_최종_V1_20260316.xlsx` |
| 스킬 패키지 위치 | `90_공통기준\스킬\` |
| 운영 지침 문서 | `90_공통기준\업무관리\` |
| ~~파일 감시 런처~~ | ~~`90_공통기준\업무관리\watch_changes_launcher.vbs`~~ (폐기 — 훅 일원화) |
| ~~스케줄러 등록 배치~~ | ~~`90_공통기준\업무관리\register_watch_task.bat`~~ (폐기 — 훅 일원화) |
| 마이그레이션 증적 | `98_아카이브\마이그레이션_20260328\` |

---

## 운영 주의사항

- 동기화 금지 구간: 매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53
- GitHub에 대용량 원본 엑셀 적재 금지
- 업무리스트 폴더 루트 임의 폴더 생성 금지
- Notion을 AI 작업 기준 저장소로 사용 금지
- 상태 판정은 TASKS.md 기준. STATUS/HANDOFF/Notion이 충돌하면 TASKS.md가 우선
- settings.local.json 토큰 하드코딩 금지 (2026-04-01 OAuth 토큰 제거)
- hooks 수정 후 반드시 smoke_test.sh 실행 (102케이스, 세션14 기준)
- 토론모드 금지 문구는 stop_guard.sh가 deterministic 차단
- Windows PowerShell 세션에서 Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'` 또는 `C:\Program Files\Git\bin\bash.exe -lc '<command>'`를 사용한다

---

## GPT 검증 결과 자동반영 규칙

GPT 검증 결과를 기록할 때 아래 표준 문장만 사용한다.

### TASKS.md 완료 이력용
- `검증 PASS — {대상} 반영 실물 확인`
- `검증 조건부 PASS — {대상} 핵심 반영 확인, 부수 정합성 {N}건 후속 수정`
- `검증 FAIL — {대상} 설명과 실물 불일치, 재검토 필요`

### HANDOFF.md 공동작업 상태용
- `GPT 검증: {sha} PASS`
- `GPT 검증: {sha} 조건부 PASS ({사유})`
- `GPT 검증: {sha} FAIL ({사유})`

### 위치 규칙
- PASS/조건부 PASS/FAIL은 **HANDOFF에만 현재형**으로 남긴다
- 완료 이력은 **TASKS에만 누적**한다
- STATUS.md에는 검증 상태를 새로 선언하지 않는다 — "TASKS/HANDOFF 참조" 유지

---

## 완료 이력 참조

완료된 작업 전체 목록은 `TASKS.md`의 "## 완료됨" 섹션 참조.
Git 이력: `git log --oneline` 또는 GitHub `ha-giwan1203/GIWANOS_AgentOS`

## 자동 감지 변경 이력
| 시각 | 이벤트 | 파일 | 변경 내용 |
|------|--------|------|----------|
| 2026-04-06 18:42 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 18:41 | modified | verify_master_from_gerp.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 18:41 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 18:21 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:56 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:46 | modified | step4_기준정보매칭.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:25 | moved    | verify_master_from_gerp.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:22 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 17:22 | modified | _pipeline_config.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 17:22 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:23 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:16 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:14 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:14 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 16:12 | modified | build_formula_version.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:54 | modified | SKILL.md | 스킬 문서 갱신 |
| 2026-04-06 15:27 | modified | step8_오류리스트.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | step7_보고서.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | step5_정산계산.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | run_settlement_pipeline.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:27 | modified | README.md | README.md 수정 |
| 2026-04-06 15:19 | modified | CLAUDE.md | CLAUDE.md 운영 기준 수정 |
| 2026-04-06 15:14 | modified | _test_helpers.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_unmatched_parts.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_normal.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | test_missing_column.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_시각화입력생성.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_대시보드.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step7_slack_보고.py | 정산 파이프라인 스크립트 수정 |
| 2026-04-06 15:14 | modified | step6_검증.py | 정산 파이프라인 스크립트 수정 |
