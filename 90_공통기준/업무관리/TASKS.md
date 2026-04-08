# 업무리스트 작업 목록

> **이 파일은 AI 작업 상태의 유일한 원본이다.**
> 완료/미완료/진행중/차단 상태는 이 파일에만 기록한다.
> STATUS.md·HANDOFF.md·Notion은 이 파일을 참조하며, 독립적으로 상태를 선언하지 않는다.
> 판정 우선순위: TASKS.md > STATUS.md > HANDOFF.md > Notion
>
> **주의: 이 파일은 현업 업무 전체 목록의 원본이 아니다.**
> 실제 업무 일정, 남은 과제, 반복 업무, 마감일의 기준 원본은 `90_공통기준/업무관리/업무_마스터리스트.xlsx`이다.
> 이 파일은 그중 AI가 수행해야 하는 자동화·문서화·구조 개편·검토·인수인계 작업만 관리한다.

최종 업데이트: 2026-04-08 — 세션 마무리 (다음 세션 안건 기록)

---

## 다음 세션 안건

### write_marker hook 개선
- `.claude/` 경로 내 파일 수정은 write_marker 대상에서 제외
- 현재 메모리 파일 수정 시 completion_gate가 오탐 트리거됨 (이번 세션 2회 발생)

### completion_gate를 pre-commit hook으로 전환 검토
- 현재 stop hook(대화 종료 시)이라 커밋 자체는 통과 → 사후 차단
- pre-commit에서 TASKS/HANDOFF 갱신 여부를 검사하면 커밋 단계에서 방지 가능
- 단, write_marker 오탐 수정이 선행되어야 함

### GPT 토론 보류 의제: 스킬 생성 규칙 린터/게이트화
- GPT 제안: 스킬 생성 시 frontmatter/실패계약 위반을 자동 검출하는 린터
- Claude 판단: 스킬 생성 빈도 낮아 현시점 과잉설계 → 보류
- 빈도 증가 시 재검토

---

## 완료

### [완료] skill-creator 실동기화 보강 (2026-04-08)
- skill-creator-merged.skill 내부 + 풀어놓은 Git 원본 양쪽 동기화:
  - SKILL.md: frontmatter 필수 6필드 명시, 문서 완결성에 실패계약 4섹션 추가
  - skill-standards.md: §1-1 Frontmatter 필수 필드, §1-2 실패계약 4섹션 추가, 경로 현행화
- .skill ZIP 재패키징 완료 (7916a019 → dee3d57c로 풀어놓은 원본도 반영)
- GPT 판정: PASS (dee3d57c)

### [완료] 스킬생성.md 현행 기준 개정 (2026-04-08)
- 대상: 90_공통기준/프롬프트/스킬생성.md
- GPT 토론 합의 4개 + Claude 추가 5개 = 9개 보강 반영
- 출력구조 폴더형 / frontmatter 강제 / 실패계약 4섹션 / 완료판정 게이트 등
- GPT 판정: PASS (384328e6)

### [완료] 폴더 안전 정리 (2026-04-08)
- .bak 2개 + 임시 xlsx 2개 → `98_아카이브/정리대기_20260408/`
- rebuild_v2~v4.py 3개 → `98_아카이브/정리대기_20260408/숙련도_스크립트/`
- `__pycache__/`, `.tmp.driveupload/`(2,624개), `.tmp.drivedownload/` 삭제
- 빈 폴더는 업무용이므로 유지

### [완료] 대원테크 명찰 디자인 (2026-04-08)
- 대상: 06_생산관리/기타/명찰_디자인/nametag_70x30.html
- HNJ-1020 아크릴집게명찰 70×30mm 사이즈
- 포함 항목: 회사명(대원테크) / 직급 / 이름 (라인명 제거)
- 컬러 포인트 스타일 (좌측 네이비 바)
- A4 절취선 인쇄 지원 (2열×8행, 16장/페이지)
- 단일·일괄 생성 + 인쇄 기능 포함
- 폰트 크기/줄간격 실시간 슬라이더 편집기 추가
- 레이아웃 개편: 좌측바 → 상단바+하단 가로배치(라인·이름·직급)
- 디자인 샘플 8종 중 **A. 상단바 모던** 선택
- A 스타일 기반 편집기+슬라이더+일괄생성+A4 인쇄 완성
- 37명 작업자 명단 자동 입력 (박태순=반장, 나머지 36명=사원)
- 페이지 로드 시 자동 일괄 생성 (3페이지, 16+16+5장)
- 인쇄 시 배경색 강제 출력 CSS 추가 (print-color-adjust:exact)
- 사이즈 67×27mm로 조정 (실제 삽입부 맞춤)

### [완료] 작업자 숙련도 평가서 양식 통일 + 수식 복원 (2026-04-08)
- 대상: 06_생산관리/기타/작업자 숙련도 평가서/ 내 .xls 4개
- 시트별 개별 .xlsx 분리 → 라인·주야 폴더 저장: 35개 완료
  - SD9M01 야간 (11), SD9M01 주간 (11), SP3M3 야간 (6), SP3M3 주간 (7)
- 파일명: {이름} 숙련도 평가서 (26.04.01).xlsx
- 공정번호·공정명: MES 데이터 기준 반영 완료 (SD9M01 22개, SP3M3 13개)
- externalLinks + definedNames XML 제거 (파일 손상 경고 해소)
- **양식 통일 (rebuild_v5)**: 곽은란 시트 ws.Copy()로 서식·병합 100% 보존
  - SD9M01 24개 파일 생성 완료 (주간 11 + 야간 11 + 구정옥 + 정은정)
  - MES "작업자 정보 상세" 탭에서 주공정+전환공정 전수 추출 (23명)
  - 추가 작업자: 구정옥(A20241203004), 정은정(A20260323001) — 조현미 데이터 활용
  - 전환공정 N개 지원: 박태순 9개(최대) ~ 리/정은정 0개(최소)
  - 전환공정 담당 셀 배경색(연노란), 평가일 셀 테두리, 섹션 구분 열 너비 3 적용
  - definedNames/externalLinks XML 정리 완료
- **PPT 인증서 개인별 분리 완료** (특별특성공정 인증서/)
  - SD9M01라인 검사자.ppt → 최종검사자 인증자격증_조현미/김두이/구정옥.pptx (3개)
  - SD9M01틸트락.ppt → 틸트락 인증자격증_노승자/최경림/곽명옥/김순애/곽은란.pptx (5개)
  - SP3M3 검사자인증.ppt → SP3M3 검사자인증_김아름/정미량/김미령/제인옥.pptx (4개)
  - 기존 김미령/제인옥 개별 ppt도 폴더에 존재
- **완료**: 평가서 수식 복원 — rebuild_v5.py에서 비율(R30)/합계(J32)/등급(T32) 값 덮어쓰기 코드 제거, 곽은란 원본 수식 자동 계산 보존. SD9M01 24개 재생성
- **완료**: SP3M3 13개 곽은란 양식 통일 — rebuild_sp3m3.py 신규 작성, MES API로 13명 주공정+전환공정 추출, SD9M01 곽은란 템플릿 기반 생성 (주간 7 + 야간 6)

### ~~[진행] GPT 토론 합의 — sed 파싱 교체 + Python 우회 차단~~ → 완료됨 (2026-04-07)
- P1-a: hook_common.sh에 safe_json_get() 공용 파서 추가, 4개 스크립트 sed→safe_json_get 교체
- P1-b: block_dangerous.sh에 Python heredoc 경유 보호파일 조작 차단 + fail-closed
- P2: smoke_test.sh 엣지케이스 8건 추가 (escaped quotes/multiline/nested/빈키/Python/객체추출/}포함/\\n복원)
- 커밋 3건: e6d360f1, a63fe826, 7c6798cc
- smoke_test 43/43 ALL PASS
- GPT PASS: 7c6798cc
- 재검증: pathlib 패턴 미차단 발견 → 106d3d45에서 수정, 43/43 + 실동작 13건 PASS

### [진행] 옵션C — bypassPermissions 제거 + 부분 우회 (2026-04-07)
- defaultMode: "bypassPermissions" 제거
- 위험 Bash(python, cp, mv, chmod, taskkill) allow에서 제거 → 승인 필요
- Write/Edit는 allow 유지 (protect_files.sh hook이 보호)
- 1주 로깅: 승인 요청 수 / hook deny 수 / 오탐 수 / 우회 감지 수
- 판정: 1주(~2026-04-14) 후 수치 기반 결정
- 커밋: 9babb720 (bypassPermissions 제거), 69dbe860 (permissions.ask 추가)
- ~~GPT 판정: 부분반영~~ → **GPT 정합 확인 완료 (2026-04-07)** — 점수 철회, 2건 합의 구현, 보완 3건 반영
- 글로벌 ~/.claude/settings.local.json 정리: 146건→3건 (python 92건 등 1회성 allow 제거)
- ask 팝업 미동작 원인: 글로벌 allow가 프로젝트 ask를 override — 정리 완료
- **ask 팝업 재검증 완료 (2026-04-07)**: python/python3/cp/mv 4개 명령 모두 승인 팝업 정상 동작 확인 (4/4 PASS)
- **4지표 집계 스크립트 구현 완료 (2026-04-07)**: aggregate_hook_metrics.py
  - hook_log.jsonl + incident_ledger.jsonl 파싱 → JSON+MD 리포트 자동 생성
  - 첫 집계: 승인요청 1396 / deny 46 (3.30%) / 오탐 0 / 우회 0
  - GPT 보완 3건 반영: 오탐 분리, hook명 정규화(비정규 버킷 제거), 플레이스홀더 탐지
  - 커밋: 3adf5d5a (초판), 74b51298 (보완)
- **SKILL 실패계약 표준화 (2026-04-07)**: SKILL_TEMPLATE.md + check_skill_contract.py
  - 필수 4섹션: 실패 조건 / 중단 기준 / 검증 항목 / 되돌리기 방법
  - 갭 리포트: 27개 중 27개 FAIL (기존 스킬에 표준 헤딩 없음, 점진 보강 예정)
- **4/8 재집계**: 승인 1485 / deny 50 (3.37%) / 오탐 0 / 우회 0 → 현행 유지
- **SKILL 실패계약 5개 보강 완료 (2026-04-08)**: 린터 5/5 PASS
  - assembly-cost-settlement, chomul-module-partno, night-scan-compare, line-mapping-validator, line-batch-management
  - 갭 리포트: 27개 중 5개 PASS / 22개 FAIL (미자동화 스킬은 보강 대상 아님)
- GPT 74b51298 응답 확인: 부분정합 — unknown 45건 미분류 잔존 지적
- **GPT 시스템 전체 분석 요청 (2026-04-08)**: ee40e90c 공유 + 5영역 분석 요청
  - GPT 응답: "조건부 운영 안정화 단계" — 핵심 지적 3건 채택
  - ① STATUS.md 드리프트 수정 (04-07→04-08)
  - ② production-result-upload 실패계약 보강 (린터 6/6 PASS)
  - ③ final_check #6 staged snapshot 우선 검증으로 개선
  - 보류: 스킬 3등급 분류, selector smoke_test, critic-reviewer 증적
- **GPT 재평가 (2026-04-08)**: 7.5/10점, "4/14 PASS 가능 권역"
  - 감점: 검증 커버리지 불완전(-1.0), 보고 문구 정합성(-1.0), 토론모드 UI 의존(-0.5)
  - 보고 정합성 3건 즉시 수정: 오탐 문구 false_positive 전환, smoke_test 헤더 v3(16개), gap report 표기 개선
- GPT 3b7d4976 판정: 부분정합 — 보고 문구 OK, smoke_test 실체 커버리지(evidence 5종) 미추가 지적
- **smoke_test evidence 커버리지 보강 완료 (2026-04-08)**: v3→v4, 63→68개 테스트
  - evidence_gate/evidence_stop_guard/evidence_mark_read/risk_profile_prompt/date_scope_guard 5종 추가
  - 토론모드 selector 문서 정합성 테스트 추가 (4개 셀렉터)
  - 68/68 ALL PASS
- **unknown 버킷 50건 완전 해소 (2026-04-08)**: aggregate_hook_metrics.py MSG_PATTERN_MAP 추가
  - task_status_sync 41건, debate_quality, 보호경로 등 매핑 → unknown 0건
  - 재집계: 승인 1686 / deny 53 (3.14%) / 오탐 0 / 우회 0
- **스킬 3등급 분류 설계 완료 (2026-04-08)**: A(실행7) / B(파일수정8) / C(분석12)
  - SKILL_TEMPLATE.md에 grade 필드 추가
  - check_skill_contract.py에 SKILL_GRADE_MAP + grade 검증 추가
  - 각 스킬 SKILL.md에 grade frontmatter 추가는 점진 보강 예정
- **critic-reviewer 증적 생성 완료 (2026-04-08)**: debate_20260407 대상 → 종합 WARN
  - 독립성 WARN (GPT 프레임 부분 수용), 하네스 WARN (A 보류 라벨 실증 부재)
  - 증적: 90_공통기준/토론모드/logs/critic_review_20260407.md
- **GPT 1e480a13+64576762 PASS (2026-04-08)**: 헤더 문구 수정 후 전체 묶음 정합 확인
- 남은 작업: 4/14 최종 판정 (최종 재집계만 남음)

### ~~[진행] Claude Code 자체 진단 + 정리~~ → 완료됨 (2026-04-07)
- final_check --fast ALL CLEAR, smoke_test 35/35 PASS
- 이전 수정 5건 실물 반영 확인 (gpt_followup_guard 제거, DRY, 리네이밍, python3 제거, README 완화)
- 정리: hook_log.txt 삭제(221KB 구 로그), 토론모드 STATUS.md 갱신(03-29→04-07), _tmp/ 아카이브 이동

### ~~[진행] Claude Code 구조 분석 + P0/P1 개선~~ → 완료됨 (2026-04-07)
- P0: git rm gpt_followup_guard.sh, hooks README 실행순서 문서화
- P1: hook_common.sh에 session_key()/경로 집중 (DRY, 9개 파일 중복 제거)
- P1: rules/_archive/ → rules_retired/ 이동 (자동로드 방지), fast-full-lane 판정 기준 data-and-files.md 통합
- P2: send_gate.sh Windows 절대경로 → ${TEMP} 변수화
- GPT 피드백: STATE_AGENT→STATE_AGENT_CONTROL 리네이밍, README 순서 가정 완화
- GPT PASS: a2c94bdc (본체) + 92d684dc (피드백 반영)

### ~~[진행] Claude Code 문제점 6건 개선~~ → 완료됨 (2026-04-06)
- 1~5순위 구현 완료, GPT 전항목 PASS (78c46b72, b0888223)
- 6순위 bypassPermissions 전환: 1주 로깅 후 결정 (보류)

### ~~[진행] 토론 품질 게이트 1단계 + 드리프트 방지 강화~~ → 완료됨 (2026-04-07)
- GPT 리서치 취합: 작성자-리뷰어 분리 패턴 합의
- send_gate.sh 토론 품질 경량 검사 추가 (주력: 반론/대안/독립견해 마커 0건 차단)
- stop_guard.sh 독립 견해 백스톱 추가 (보조)
- final_check.sh: settings.local hook 수 대조(5번) + 상태문서 날짜 동기화(6번) 추가
- STATUS.md 드리프트, settings-README 불일치 → 커밋 자동 차단
- smoke_test 35/35 ALL PASS

### ~~[진행] 토론 품질 게이트 2단계~~ → 완료됨 (2026-04-07)
- critic-reviewer.md subagent 신규 생성 (sonnet, 읽기전용)
- 4축 평가: 독립성/하네스 엄밀성(필수) + 0건감사/결론 일방성(보조)
- SKILL.md Step 4 → 4a(종료판정)/4b(critic-reviewer 1회 호출) 분리 (v2.5)
- 스모크 테스트: 기존 로그(debate_20260402_토론1.md)로 정상 동작 확인
- GPT 합의: 2필수+2보조 구조, sonnet 모델, 세션 종료 1회 호출

### ~~[진행] 문서-구현 정합성 복구 + python3 전면 제거~~ → 완료됨 (2026-04-07)
- GPT "클로드 코드 문제 분석" 방 지적 → Claude 실물 검증 → 합의
- ① block_dangerous.sh DANGER_CMDS cp 추가 + python3→bash
- ② gpt_followup_post/stop.sh python3→bash (주석-코드 불일치 해소)
- ③ README.md(8→10개) + STATUS.md(9→10개) hook 개수 동기화
- ④ send_gate/stop_guard/write_marker/notify_slack python3→bash 전환
- ⑤ protect_files.sh python3→bash 전환
- ⑥ final_check.sh 자체검증 4건 추가 (python3잔존/hook개수/HANDOFF교차/cp확인)
- ⑦ commit_gate.sh 신규 (git commit/push 전 final_check 강제)
- ⑧ final_check.sh --fast/--full 2단 분리
- 결과: 운영 훅 python3 의존 0건, 커밋 전 자체검증 자동 강제
- smoke_test 35/35 + final_check ALL PASS

### ~~[진행] GPT 피드백 실물 검증 강제~~ → 완료됨 (2026-04-07)
- 문제: GPT 조건부 PASS/FAIL 지적 시 실물 확인 없이 바로 수정하는 패턴
- GPT 토론 합의: C(Step 5-4→5-0 재진입) 단독, B(실물확인 마커) 보류
- SKILL.md Step 5-0 범위 확장 (제안→제안·지적), Step 5-4 분기 3행에 Step 5-0 재수행 강제
- 재발 시 A-lite(Read 이력 추적) 승격 경로 유지

### ~~[진행] 증거기반 위험실행 차단기(evidence hook)~~ → 완료됨 (2026-04-07)
- 문제: 5건 연속 실수 근본 원인 = "생각 없이 실행", 의지력 의존 규칙으로 해결 불가
- GPT 토론 4턴 → "증거 없는 위험 실행 차단기" 설계 합의
- 신규 hook 5개: risk_profile_prompt / date_scope_guard / evidence_mark_read / evidence_gate / evidence_stop_guard
- 핵심: req 없으면 no-op, 세션 격리 (sha1+mtime)
- settings.local.json 11→16 hook merge, 기능 테스트 6건 ALL PASS
- 커밋 c0ffc54c, GPT 부분반영 (STATUS.md 드리프트 지적 → 해소)

### ~~[진행] 토론모드 코어/참조 분리~~ → 완료됨 (2026-04-07)
- SKILL.md 326→133줄 슬림화, REFERENCE.md 신설 (JS코드/완료감지/오류대응/변경이력 분리)
- 토론모드 CLAUDE.md ENTRY.md 참조 제거, SKILL.md/REFERENCE.md 구조로 정리
- completion_gate 역할 문서화: CLAUDE.md 29줄에 이미 명시 확인 (실물 검증)

### ~~[진행] GPT Project Instructions Git 관리 방향 토론~~ → 완료됨
### ~~[진행] 8단계 자동 루틴 강제 — /finish + completion_gate 연동~~ → 완료됨
### ~~[대기] PPT 자동 생성 스킬 — 실무 투입 준비~~ → 완료됨
### ~~[중] 도메인 지시문 미읽기 근본 해결~~ → 완료됨
### ~~[진행] Claude Code 환경 근본 경량화 GPT 토론~~ → 완료됨 (2026-04-06)
### ~~[진행] Claude Code 자체진단 + 잔여 정리~~ → 완료됨 (2026-04-06)

---

## 대기 중 (우선순위 순)

### ~~[대기] settlement 스킬 preloading 테스트~~ → 완료됨 (3월 정산 04월 폴더 실행)

### ~~[진행] 기준정보 다중단가 파괴 복구~~ → 완료됨 (2026-04-06)
- 관리DB 기반 재생성 + GERP 신규품번 추가 + X9000/X9500 삭제
- 다중단가 269건 보존 확인, Step6 PASS, GERP 261,038,171원

### ~~[진행] step5 파이프라인 신뢰성 검증~~ → 완료됨 (2026-04-06)
- 버그 4건 수정: ①미매핑 구ERP조회 누락 ②다중단가 2번째행 오분류 ③SP3M3 야간 미가산 ④비SD9A01 야간변수 미초기화
- 에러 388→190건, 차이 +25.6M→+7.2M (SD9A01 -2,613원 거의 완벽)
- 남은 +7.2M: 원천 데이터 불일치 (파이프라인 버그 아님, 사용자 확인)
- GPT 3라운드 공동작업 완료, 커밋 fb81d7a5

### ~~[진행] 에이전트 운영 체계 개선~~ → 완료됨 (2026-04-07)
- GPT 토론 합의 → Claude 하네스 판정 → 구현 + 자체검증 + 개선안건 마무리
- ① hook_common.sh JSON 로그 전환 (hook_log.jsonl)
- ② incident_ledger.jsonl 도입 (auto_compile, completion_gate, stop_guard 연동)
- ③ candidate 브랜치 규칙 문서화 (data-and-files.md)
- ④ smoke_test 퇴행 방지 검사 추가 (hook_log.txt 직접 참조 0건)
- ⑤ 토론모드 공유 규칙 강화 (SHA + git show --stat)
- ⑥ CLAUDE.md 운영 규칙 2건 추가 (grep 전수확인, 상태문서 동시갱신)

### [대기] 4월 실적 정산 — **대기: 4월 GERP/구ERP 데이터**
- 4월 정산 데이터 입수 후 `/settlement 04` 실행



### [대기] verify_xlsm.py COM 실검증 — **대기: 다음 xlsm 작업 시 실행**
- 출처: 1단계 구조적 가드레일 GPT 공동작업
- verify_xlsm.py 구조는 완료. COM 실검증 산출물(verify.json PASS)은 xlsm 작업 재개 시 확인
- hooks 3개 + settings merge 구현 완료 (GPT 구조 PASS)

### ~~[auto] 정산 파이프라인 실행 테스트 확인~~ → 완료됨 (04월 폴더 step1~8 정상 실행)




### ~~[낮] 루트 CLAUDE.md 하네스 원칙 승격~~ → 완료됨

### ~~[낮] 도메인 STATUS.md 점검~~ → 완료됨 (2026-03-31)
- 조립비정산 STATUS.md: 정합성 OK
- 라인배치 STATUS.md: OUTER 재개 취소 반영 (커밋 833a675b)

---

## 완료됨

| 항목 | 완료일 |
|------|--------|
| 증거기반 위험실행 차단기 — evidence hook 5개 구현 (c0ffc54c), hooks 11→16, 기능테스트 6건 PASS, GPT 부분반영→STATUS 해소 | 2026-04-07 |
| 에이전트 운영 체계 개선 9건 — JSON로그+incident_ledger+candidate규칙+smoke동기화+구참조제거+퇴행검사+공유규칙+운영규칙+final_check (ba301b41~38c935a1) GPT 전항목 PASS | 2026-04-07 |
| Claude Code 문제점 6건 개선 — 보안봉합+README동기화+guard분리+토론모드분리+판정문서화 (78c46b72, b0888223) GPT 전항목 PASS | 2026-04-06 |
| Claude Code 근본 경량화 GPT 토론 — hooks 23→9, rules 6→2, CLAUDE.md 71→38줄, permissions 78→37, completion_gate v4 단순화. 20개 hook + 4개 rules 아카이브 | 2026-04-06 |
| CLAUDE.md+rules/ 경량화 — 143→71줄(CLAUDE.md), rules/ 145→64줄, 전체 135줄. GPT PASS (de416123+8a4fbd11) | 2026-04-06 |
| step5 매핑 버그 4건 수정 — 에러 388→190건, 차이 +25.6M→+7.2M. GPT 공동작업 완료 (fb81d7a5) | 2026-04-06 |
| SEND GATE 구현 — send_gate.sh PreToolUse hook + 토론모드 ENTRY/CLAUDE.md 반영 (54908fab) | 2026-04-06 |
| MES 생산실적 업로드 — 4/3(12건,39,587ea), 4/4(10건,19,159ea), 4/6(15건,46,317ea) 건수+생산량 ALL PASS | 2026-04-07 |
| ZDM 일상점검 — SP3M3 75건 OK ×2일(4/6~4/7), 검증 75/75 ALL PASS. 4/5(일) 오입력→삭제 완료 | 2026-04-07 |
| THINK GATE 구현 — 전역 4칸 사고 흔적 강제 규칙 (fc438e3d) | 2026-04-06 |
| 야간스캔비교 스킬+커맨드 Phase 통일 — SKILL.md v1.1 + night-scan.md Phase 0~7 (15783b06, GPT PASS) | 2026-04-06 |
| 기준정보 다중단가 파괴 복구 — 관리DB 재생성(16,524행), 다중단가 269건 보존, X9000/X9500 삭제, Step6 PASS | 2026-04-06 |
| 3월 정산 04월 폴더 재실행 + 스킬화 — setup_month.py + step8 오류리스트 + `/settlement` 슬래시 명령 + SKILL.md, 데이터 검증 PASS (10라인 0원 차이) | 2026-04-05 |
| 8단계 자동 루틴 강제 — /finish 커맨드 + finish_state.json + completion_gate 연동, GPT 토론 3턴 합의 + 부분반영→PASS (19400bed) | 2026-04-04 |
| post_write_dirty.sh EXEMPT_COMMANDS — git HEREDOC 오탐 제거 (GPT PASS 880cb437) | 2026-04-04 |
| GPT 지침 Git 관리 구현 — gpt-instructions.md 기준 원본 + fallback + cowork-rules 합의 반영, GPT 토론 7턴 (ff16142a) | 2026-04-04 |
| PPT Graphviz 확장 — diagram_renderer.py 신규 (순서도/프로세스/조직도 3종 + 시각타입 자동선택 + PPTX 삽입), QA 3축 PASS | 2026-04-04 |
| hooks 안정화 — domain_guard Python 분리 + /tmp 경로 수정 + I/O 테스트 4건 추가, 40/40 PASS (e563f3c1) | 2026-04-04 |
| 양방향 하네스 합의 — GPT도 설계·토론형 판정에 하네스(채택/보류/버림) 적용, 실물 검증은 PASS/FAIL 유지 (cowork-rules.md 반영) | 2026-04-04 |
| hooks cp949 인코딩 버그 수정 — prompt_inject/domain_guard/domain_read_tracker 3개 hook sys.argv→stdin 파이프 전환, 한글 키워드 감지 복구 (211ab177) | 2026-04-04 |
| 규칙 완화+등급제 — ENTRY.md=Primary(NEVER만), CLAUDE.md=Reference(등급태그), additionalContext 7줄→5줄 축소 (GPT 합의 2턴) | 2026-04-04 |
| domain_guard phase guard — 토론모드 3단 시퀀스(entry_read→doc_read→full) + 키워드 2단 조합 11패턴 + ENTRY.md 신규 (GPT 합의 2턴, PASS 65c34115) | 2026-04-04 |
| PPT 실무 투입 최종 PASS — 실데이터 2종 생성(NCR 사진포함+월간 13라인) + PowerPoint 육안 검수 5/5 + 엣지 7/7 + 재현성 2/2 + 입력계약 검증 (308a588d) | 2026-04-04 |
| PPT 자동 생성 스킬 MVP 2종 PoC — ncr_generator.py + monthly_production_generator.py, 검증 PASS — MVP 2종 엔진 적합성 실물 확인 (GPT PASS, cfb88dde/b22ef085/f1da0084) | 2026-04-04 |
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
