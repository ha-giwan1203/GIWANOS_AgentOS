# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-08 — skill-creator 실동기화 보강
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-08)

### 작업: skill-creator 실동기화 보강 (완료)
- skill-creator-merged.skill 내부 SKILL.md + skill-standards.md 보강
- frontmatter 6필드 필수화, 실패계약 4섹션 문서 완결성 기준 추가
- .skill ZIP 재패키징, 구버전 백업 아카이브 이동

### 작업: 스킬생성.md 현행 기준 개정 (완료)
- 384328e6 — GPT 토론 합의 4개 + Claude 추가 5개 = 9개 보강
- GPT PASS 확정 — 9개 항목 실물 확인, TASKS 비충돌
- GPT 제안 후속: skill-creator 샘플 1건 실전 검증 (선택)

### 작업: 폴더 안전 정리 (완료)
- 임시파일 4개 + 구버전 스크립트 3개 → `98_아카이브/정리대기_20260408/`
- `__pycache__/`, `.tmp.driveupload/`(2,624개), `.tmp.drivedownload/` 삭제
- 빈 폴더(99_임시수집, _구버전 등)는 업무용 유지

### 작업: 대원테크 명찰 디자인 (완료)
- 파일: `06_생산관리/기타/명찰_디자인/nametag_70x30.html`
- 70×30mm 아크릴집게명찰(HNJ-1020) 사이즈, 컬러 포인트 스타일
- 회사명/직급/이름 표시 (라인명 제거), A4 절취선 인쇄(2열×8행) 지원
- 폰트 크기/줄간격 실시간 슬라이더 추가
- 레이아웃 개편: 좌측바 → 상단바+하단 가로배치(라인·이름·직급)
- A. 상단바 모던 선택 → 편집기+A4 인쇄 완성, 37명 명단 자동 입력, 인쇄 배경색 강제 출력 추가

### 작업: 숙련도 평가서 양식 통일 — SD9M01 + SP3M3 전체 완료
- **SD9M01 수식 복원**: rebuild_v5.py에서 비율(R30)/합계(J32)/등급(T32) 값 덮어쓰기 4줄 제거 → 곽은란 원본 수식 자동 계산 보존. SD9M01 24개 재생성
- **SP3M3 13개 곽은란 양식 기반 생성**: rebuild_sp3m3.py 신규 작성
  - MES API (`/wrk/selectListWrkProcIByWrk.do`) 호출로 13명 주공정+전환공정 전수 추출
  - SD9M01 곽은란 템플릿 사용 (라인명만 SP3M3로 변경)
  - 주간 7명 + 야간 6명 = 13개 파일
  - 수식 보존 (점수만 입력, 비율/합계/등급은 수식 자동 계산)
  - XML 정리 (externalLinks/definedNames 제거) 13/13 완료
- PPT 인증서 개인별 분리 완료 (특별특성공정 인증서/)
  - SD9M01: 최종검사자 3개 + 틸트락 5개 = 8개
  - SP3M3: 검사자인증 4개

### 작업: 4/14 판정 대비 — 4지표 재집계 + 스킬 실패계약 보강
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| aggregate_hook_metrics.py | 재집계 실행 | deny 3.37% / 오탐 0 / 우회 0 → 현행 유지 |
| assembly-cost-settlement SKILL.md | 실패계약 4섹션 추가 | 린터 PASS |
| chomul-module-partno SKILL.md | 실패계약 4섹션 추가 | 린터 PASS |
| night-scan-compare SKILL.md | 실패계약 4섹션 추가 | 린터 PASS |
| line-mapping-validator SKILL.md | 실패계약 4섹션 추가 | 린터 PASS |
| line-batch-management SKILL.md | 실패계약 4섹션 추가 | 린터 PASS |
| GPT 토론방 | 74b51298 응답 확인 | 부분정합 — unknown 45건 지적 |

### GPT 시스템 전체 분석 (ee40e90c)
- GPT 판정: "조건부 운영 안정화 단계"
- 채택 3건: STATUS 드리프트 수정 / production-result-upload 실패계약 / final_check staged 검증
- 보류 3건: 스킬 3등급 분류 / selector smoke_test / critic-reviewer 증적

### 보고 정합성 수정 (GPT 재평가 감점 대응)
- aggregate_hook_metrics.py: 오탐 문구 "resolved" → "false_positive" 전환
- smoke_test.sh: 헤더 v2→v3, 11개→16개
- check_skill_contract.py: gap report PASS/FAIL 표기에 대상 구분 추가

### 해결 완료 (2026-04-08 2차)
- ~~smoke_test evidence 5종 실체 커버리지 보강~~ → **완료**: v4 68/68 ALL PASS
- ~~unknown 버킷 47건 해소~~ → **완료**: MSG_PATTERN_MAP 추가, unknown 0건
- ~~스킬 3등급 분류~~ → **완료**: A=7/B=8/C=12, SKILL_TEMPLATE.md+린터 반영
- ~~critic-reviewer 증적~~ → **완료**: debate_20260407 대상 종합 WARN
- ~~selector smoke_test~~ → **완료**: 토론모드 CLAUDE.md 셀렉터 4개 정합성 테스트

### GPT 최종 판정 (1e480a13 + 64576762)
- GPT PASS: smoke_test 헤더 수정 후 전체 묶음 정합 확인
- "남은 건 4/13~14 최종 재집계 후 4/14 운영 안정화 최종 판정만"

### 미해결
- 4/14 최종 판정: 최종 재집계 1회만 남음

---

## 다음 세션 할 일

### 1순위: 4/14 판정 최종 (마감 4/14)
- [ ] 4/13~14 aggregate_hook_metrics.py 최종 집계 → 판정 수치 확정
- [ ] deny <10%, 오탐 0%, 우회 0% 확인 → 현행 유지 or allow 확대

### 2순위: 실무 업무
- [ ] 4월 실적 정산 — GERP/구ERP 데이터 입수 후 `/settlement 04`
- [ ] SP3M3 미매칭 RSP 4건 갱신 (RSP3SC0291~0294)

### 3순위: 점진 보강
- [ ] 각 스킬 SKILL.md에 grade: A|B|C frontmatter 추가 (27개)

---

### 이전 작업 (2026-04-07): GPT 토론 합의 — sed 파싱 교체 + Python 우회 차단
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| hook_common.sh | safe_json_get() 공용 파서 추가 | escaped quotes/multiline/nested JSON 처리 |
| block_dangerous.sh + commit_gate.sh + gpt_followup_post.sh + gpt_followup_stop.sh | sed 단독 파싱 → safe_json_get() 교체 | 4개 스크립트 취약점 해소 |
| block_dangerous.sh | Python heredoc 경유 보호파일 조작(os.remove/shutil) 차단 | GPT 실증 시나리오 대응 |
| smoke_test.sh | 엣지케이스 8건 추가 (escaped quotes/multiline/nested/빈키/Python/객체추출/}포함/\\n복원) | 43/43 PASS |

### 미해결
- 글로벌 ~/.claude/settings.local.json 정리 완료 (146건→3건, python 92건 등 1회성 allow 제거)
- ~~ask 팝업 미동작 원인: 글로벌 allow가 프로젝트 ask를 override~~ → **재검증 완료 4/4 PASS** (글로벌 정리 후 정상)
- bypassPermissions 제거 후 1주 로깅 진행 중 (~2026-04-14)
  - 판정 기준: 승인 요청 수 / hook deny 수 / 오탐 수 / 우회 감지 수
  - 팝업이 과도하면 allow 확대, 문제 없으면 현행 유지
- ~~4지표 로깅 메커니즘 미구현~~ → **구현 완료 (2026-04-07)**
  - `90_공통기준/업무관리/운영검증/scripts/aggregate_hook_metrics.py`
  - 첫 집계: 승인요청 1396 / deny 46 (3.30%) / 오탐 0 / 우회 0
  - 보완: 오탐 분리, hook명 정규화, 플레이스홀더 탐지 (74b51298)
- SKILL 실패계약 표준화 신규 (2026-04-07)
  - `90_공통기준/스킬/SKILL_TEMPLATE.md` + `check_skill_contract.py` 린터
  - 갭 리포트: 27개 전부 FAIL → 점진 보강 예정
- hook 의존 그래프 문서화 (보류)

---

### 이전 작업: Claude Code 자체 진단 + 경미 정리
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| 자동 검증 | final_check --fast + smoke_test | ALL CLEAR / 35/35 PASS |
| hook_log.txt | 구 텍스트 로그 삭제 (221KB) | JSONL만 남음 |
| 토론모드 STATUS.md | 03-29 → 04-07 갱신 | v2.6 + critic-reviewer 반영 |
| _tmp/ | 8개 임시 스크립트 → 98_아카이브/정리대기_20260407/ | _tmp 폴더 제거 |

### 미해결
- bypassPermissions 1주 로깅 후 결정 (보류 유지)

---

### 이전 작업: Claude Code 전수 분석 + 문제점 개선
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| gpt_followup_guard.sh | git rm (삭제 미커밋 해소) | git status 정상화 |
| hooks/README.md | PreToolUse 실행순서 ①~⑥ 문서화 | 순서 의존성 명시 |
| hook_common.sh | session_key() + 경로 5종(STATE_EVIDENCE/STATE_AGENT/PATH_TASKS/PATH_HANDOFF/PROJECT_ROOT) 집중 | DRY 달성 |
| evidence_*.sh (4개) + 상태훅 (4개) | 중복 session_key/경로 제거, hook_common source | 9개 파일 정리 |
| send_gate.sh | Windows 절대경로 → ${TEMP} 변수 | 이식성 개선 |
| rules/_archive/ | rules_retired/로 이동 (4파일) | 퇴역 규칙 자동로드 방지 |
| data-and-files.md | fast-full-lane 판정 기준 통합 | 규칙 일원화 |

### 핵심 발견
- `.claude/rules/_archive/`가 `.claude/rules/` 하위이므로 Claude Code가 퇴역 규칙을 활성 로드하고 있었음
- settings 권한 목록은 `defaultMode: bypassPermissions` 때문에 현재 무효 (hook만 실질 가드)
- 토론모드 TASKS.md는 STATUS.md와 일관 (거짓 아님)

### 미해결

## 1. 이번 세션 작업 목적

1. ZDM 일상점검 밀린 실적 일괄 등록
2. MES 생산실적 밀린 날짜 업로드
3. 연속 실수 근본 원인 분석 + GPT 토론 → 증거기반 위험실행 차단기 hook 구현

---

## 2. 실제 변경 사항

### 토론 품질 게이트 1단계 + 드리프트 방지 강화
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| send_gate.sh | 토론 품질 경량 검사 추가 (주력) | 반론/대안 0건 시 전송 차단 |
| stop_guard.sh | 독립 견해 백스톱 추가 (보조) | 종료 직전 2중 검사 |
| final_check.sh | settings hook 대조(5번) + 날짜 동기화(6번) | 드리프트 시 커밋 차단 |
| STATUS.md | 최종 업데이트 04-06→04-07 동기화 | 드리프트 해소 |

### 증거기반 위험실행 차단기(evidence hook) 5개 구현
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| risk_profile_prompt.sh | UserPromptSubmit → .req 파일 생성 | 위험 키워드 감지 시 증거 요구 |
| date_scope_guard.sh | PreToolUse/Bash → 일요일/일괄/MM-DD 차단 | ZDM 4/5(일) 재발 방지 |
| evidence_mark_read.sh | PostToolUse → .ok 증거 적립 | SKILL/TASKS 등 읽기 추적 |
| evidence_gate.sh | PreToolUse → req있고 ok없으면 deny | 증거 없는 실행 차단 |
| evidence_stop_guard.sh | Stop → 증거 없는 결론 차단 | 로그인실패/완료 무근거 주장 차단 |
| settings.local.json | 기존 11 + 신규 5 = 16개 | UserPromptSubmit 이벤트 추가 |

### 문서-구현 정합성 복구 + python3 전면 제거 (smoke_test 32/32 + final_check PASS)
| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| block_dangerous.sh | DANGER_CMDS cp추가 + python3→bash | HANDOFF 일치 + #34457 대응 |
| gpt_followup_post/stop.sh | python3→bash (주석 실현) | #34457 멈춤 위험 감소 |
| protect_files.sh | python3→bash | 경량화 |
| send_gate.sh | python3→bash (3곳: tool_name, insertText, gate_age) | #34457 대응 |
| stop_guard.sh | python3→bash (content배열 파싱→raw grep) | #34457 대응 |
| write_marker.sh | python3→bash (v5) | #34457 대응 |
| notify_slack.sh | python3→bash (message 추출) | #34457 대응 |
| README.md / STATUS.md | hook 개수 10개 통일 | 문서 정합 |
| final_check.sh | --fast/--full 2단 분리 + 자체검증 5건 | 매 커밋 fast, hook변경 시 full |
| commit_gate.sh | 신규: git commit/push 감지 → final_check 강제 | 자체검증 시스템 전체 적용 |

---

## 3. 미해결 / 다음 AI 액션

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| ~~완료~~ | ZDM 일상점검 4/5~4/7 일괄 등록 | 4/6, 4/7 등록 PASS. 4/5(일) 오입력→삭제 완료 |
| ~~완료~~ | MES 생산실적 4/3, 4/4, 4/6 업로드 | 37건 105,063ea, 건수+생산량 ALL PASS |
| 대기 | 4월 실적 정산 | 4월 GERP/구ERP 데이터 입수 후 `/settlement 04` |
| 대기 | SP3M3 미매칭 RSP 4건 | RSP3SC0291~0294 모듈품번 갱신 |

## 4. 이번 세션 확인된 사실

- 연속 실수 5건 근본 원인: "생각 없이 실행" — 의지력 규칙으로 해결 불가
- GPT 토론 4턴 → "증거 없는 위험 실행 차단기" 아키텍처 합의 + 구현
- evidence hook: req 없으면 no-op (일상 마찰 0), 세션 격리 (sha1+mtime)
- GPT 검증: c0ffc54c 부분반영 → d6fdc413 STATUS 동기화 후 **PASS**
- MES SKILL.md 로그인 판정: auth-dev URL 부재가 아닌 MES 직접 접속으로 수정
- completion_gate 순서 버그 발견: 상태문서 갱신 후 다른 파일 수정 시 마커 재생성 → 상태문서는 커밋 직전 마지막에 수정해야 함
- **세션 재시작 필수**: settings.local.json에 UserPromptSubmit + hook 5개 추가됨 (캐싱)
