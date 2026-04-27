# 업무리스트 프로젝트

@.claude/rules/cowork-rules.md
@.claude/rules/data-and-files.md

자동차 부품 제조업(삼송 G-ERP) 업무 자동화 저장소.

## 작업 모드 판정 (실행 전 필수)

> 규칙 준수는 실행 가능 조건일 뿐, 실행 타당성 증명이 아니다.
> 모든 요청은 도메인 진입 전에 작업 모드를 먼저 판정한다.
> 토론 합의 원본: `90_공통기준/토론모드/logs/debate_20260427_185903_3way/` (Round 1+2 pass_ratio 1.0, critic-reviewer WARN 3건 반영 v2)

### 모드 5종

| 모드 | 트리거 | 적용 절차 | 적용 안 함 |
|------|-------|----------|-----------|
| **A. 실무 산출물** | ERP/MES 업로드, 정산, 라인배치, 보고서, 엑셀 가공 등 사용자 산출물 생성 | 원본 보호 + 사용자 입력 1순위 + 산출물 검증 + Pre/Post Task 프로토콜 | 토론모드 자동 승격, 시스템 개선 R1~R5 |
| **B. 시스템 분석** | "왜 깨졌나", "왜 이렇게 되나", "원인 찾아라" 등 진단 요청 | 관찰 사실 → 원인 후보 3개 → 각 후보 반증 → 최종 판단 → 수정 필요 여부 명시 | 즉시 수정 (분석 결과 보고 후 사용자 결정) |
| **C. 시스템 수정** | hook/settings/gate/스킬/CLAUDE.md/규칙 문서 수정 | Plan-first + R1~R5 반증형 + R5에 ERP/MES 잔존 데이터·논리적 롤백 필수 | 분석 없는 즉시 수정, 규칙 단순 추가 |
| **D. 토론모드** | 사용자가 명시적으로 `/debate-mode` 또는 "3자 토론" 요청 | `90_공통기준/토론모드/CLAUDE.md` 절차 | 실무 모드 작업 중 자동 승격 (B 분류 감지는 켜되 자동 진입은 차단) |
| **E. 장애 복구** | 현재 실무 작업을 직접 차단하는 오류 (정량 OR 조건 6개 중 1개 이상) | 차단 원인 최소 패치 → 정상 복귀 → 사후 B/C 분리 | Plan-first 풀절차, 시스템 개선 동시 진행 |

### 우선순위 사다리 (충돌 시)

```
1. 사용자 명시 지시 (모든 자동 사다리 위)
2. E (현재 실무 차단 시 — 시스템 망가진 상태에서 A는 오염 데이터)
3. C (시스템 파일 경로 수정 포함 시)
4. D (사용자 명시 호출만 — 자동 승격 차단)
5. B (분석)
6. A (실무 산출물 — 다른 모드 트리거 없을 때 기본값)
```

### 판정 절차

1. **모드 선언 (Claude 측 비대칭)**: Claude는 응답 첫 줄에 모드를 1줄로 선언한다. 사용자는 다르면 1단어로 정정. 사용자 입력에 모드 강제 안 함.
2. **헤더 표기 조건 (선택적)**: 다음 중 하나라도 해당 시에만 헤더 1줄. 일반 A(엑셀 가공·문서 정리·보고서)는 헤더 생략.
   - B/C/D/E 모드 응답
   - ERP/MES 외부 반영을 포함하는 A 모드 (업로드·삭제·외부 등록)
   - 모드 전환이 발생한 응답
3. **헤더 형식**: `[모드: <코드> / 대상 또는 위험 / 다음 액션]` 1줄.
4. **추측 진입 금지**: 모호하면 사용자에게 1줄로 묻는다 ("A인지 C인지").
5. **모드 전환 시**: 일시중단 → 사용자 인지 라인 → 재선언. C로 전환 시 응답 첫 줄에 명시: `[모드 전환: A → C / 사유: <시스템 파일 경로 감지> / 진행하려면 plan-first]`.

### 모드별 사전 절차

#### A. 실무 산출물
- 사용자 첨부 파일/지시값이 있으면 **1순위 입력**. 자동 추론·자동 탐색은 첨부가 없을 때만.
- 원본 xlsx/docx/pdf 직접 수정 금지 (기존 "## 금지" 항목 그대로).
- ERP/MES 외부 반영(업로드·삭제·등록)은 실행 전 **대상/일자/라인/건수 사전 확인 1줄**.
- 산출물 검증: 합계/구조/원본 대조 → 보고.
- **Post Task 프로토콜**: 종료 시 "TASKS/STATUS/HANDOFF 갱신 필요 여부" 1줄 선언.
- 토론모드/시스템 R1~R5 끌어오지 않는다.

#### B. 시스템 분석
- 출력 고정 포맷:
  1. **관찰 사실** (실물 로그·파일·git 결과 인용)
  2. **원인 후보 3개** (각각 1줄)
  3. **각 후보 반증** (어떤 관찰이 그 후보를 부정/지지하는가)
  4. **최종 판단** (3개 중 어느 것, 또는 추가 관찰 필요)
  5. **수정 필요 여부** (필요/불필요/보류) — 필요면 모드 C로 전환 제안
- 분석 단계에서 코드/설정 수정하지 않는다.
- B 분류 감지 라벨(hook/settings/SKILL Step 변경 등)은 결과 보고 시 1줄 표기 — `[B 감지: 구조 변경 후보 — 사용자가 명시 호출하면 D 또는 C 진입]`. **자동 D 진입은 안 함**.

#### C. 시스템 수정
- Plan-first: 수정 전에 plan 파일(`.claude/plans/`) 작성.
- **R1~R5 반증 질문형** (체크리스트 채우기 금지, 항목별 "해당 없음" 명시 허용 + 사유 1줄 필수):
  - **R1 (진짜 원인)**: 이 파일이 진짜 원인인가? 수정 없이 해결 가능한가?
  - **R2 (직접 영향)**: 어떤 hook/skill/command가 즉시 동작이 바뀌는가? 외부 ERP/MES 영향 있는가?
  - **R3 (간접 영향·grep)**: 같은 패턴이 어디서 호출되는가? 같은 포트/프로필/경로를 공유하는 다른 자동화가 있는가?
  - **R4 (선례 검색)**: incident_ledger·최근 커밋에 같은 패턴? 세션107/110/115 D0 계열과 같은가?
  - **R5 (롤백·잔존 데이터)**: 실패 시 ERP/MES/SmartMES/파일서버/Z드라이브에 잔존 데이터? dry-run/parse-only/건수 확인/논리적 롤백 스크립트 경로? 비가역 행동(삭제/업로드/등록)인가?
- **C 강제 승격 트리거** (A로 시작했어도 자동 C 전환되는 경로 7개):
  - `.claude/hooks/`, `.claude/settings*.json`, `.claude/commands/`, `.claude/agents/`
  - `90_공통기준/스킬/*/SKILL.md` (Step 절차 분기 신설·삭제)
  - 루트/도메인 `CLAUDE.md`
  - gate 판정 분기 변경

#### D. 토론모드
- `/debate-mode` 슬래시 호출 또는 사용자 명시 요청만 진입 (자동 승격 차단).
- B 분류 감지는 켜되 D 자동 진입은 끈다 (비대칭 설계).
- B 결과 보고에 "토론 권장" 라벨이 붙으면 사용자가 호출 결정.
- 절차는 `90_공통기준/토론모드/CLAUDE.md` 그대로.

#### E. 장애 복구
- **정량 판정**: "이미 시작된 실무 실행" AND 다음 OR 조건 1개 이상:
  1. **시간 임계 초과 (작업별 차등)**: UI 30초·ERP/selectList 60초·OAuth 60초/재진입 1회 이상·업로드 응답 60초·스케줄러 예정 시각 +10분 무로그
  2. **외부 응답 부재**: timeout·5xx·미응답
  3. **잔존 데이터 위험**: 응답 200인데 중복 등록, selectList 성공인데 잘못된 파일, 삭제 성공인데 SmartMES 캐시 잔존
  4. **입력 소스 충돌**: 첨부 파일 vs 자동 탐색 파일, OAuth 통과인데 다른 Chrome 프로필
  5. **프로세스 고착**: 스케줄러 lock 잔존, OAuth redirect 무한 루프, hook 무한 루프
  6. **마스터 정보 불일치**: 품번·공정코드·라인 매핑 충돌 — 즉시 E + B 강제 이관
- **단순 건수 불일치 2단 판정**:
  - 1차: E 후보 + 1줄 경고("[E 후보: 건수 불일치 — 입력 오류·필터링 가능성 1차 점검]"). 점검 단계는 **30초 이내 + 외부 시스템 추가 호출 없음 + 오류 로그 1건 이상 인용**.
  - 2차: 입력 오류·필터링이 명백히 부정되거나 외부 잔존 데이터 흔적 확인 시 E 진입. 단순 입력 오류 명백하면 A 복귀.
- **최소 패치 정량 기준**: 패치 라인 ≤ 20줄 + 신규 함수·hook·gate·settings 추가 금지(기존 값 변경·timeout 상향만) + 변경 파일 ≤ 2개. 초과 시 자동 모드 C 전환.
- **종료 후 사후 분석 강제**: E 종료 시 "B 분석 필요 여부" 1줄 선언, 필요하면 TASKS.md 등록.
- 복구 중 시스템 개선 동시 진행 금지.

### 시스템 개선 중단 이후 예외 (세션91 안전안 채택 이후)

- `glimmering-churning-reef` 안전안 이후 시스템 개선은 원칙적으로 중단 상태.
- 예외 수정은 **모드 E (장애 복구)** 또는 **사용자 명시 모드 C 요청**에 한정.
- "더 좋아 보여서" 또는 "다른 곳도 같이"는 사유가 안 됨.

## 도메인 진입

| 키워드 | 도메인 문서 |
|--------|-----------|
| 토론 / 토론모드 / 3자 토론 / 3-way / Claude×GPT×Gemini / 공동작업 / 공유 | `90_공통기준/토론모드/CLAUDE.md` → `/debate-mode` 스킬 |
| NotebookLM / 노트북 / 노트북lm / 사이드패널 노트북 | `90_공통기준/notebooklm/CLAUDE.md` → `/notebooklm` 스킬 |
| 정산 / 조립비 / settlement | `05_생산실적/조립비정산/CLAUDE.md` |
| 라인배치 / OUTER / ERP 라인배정 | `10_라인배치/CLAUDE.md` |
| MES 업로드 / 실적 올려 | `90_공통기준/스킬/production-result-upload/SKILL.md` |
| 일상점검 / ZDM | `90_공통기준/스킬/zdm-daily-inspection/SKILL.md` |
| 급여 / 단가 | `02_급여단가/CLAUDE.md` |
| 생산계획 / 계획 | `04_생산계획/CLAUDE.md` |
| 생산관리 / 관리 | `06_생산관리/CLAUDE.md` |

도메인 키워드 감지 시 해당 문서를 먼저 읽는다.

## 상태 원본

작업 상태는 **TASKS.md에만 기록**한다.
- TASKS: `90_공통기준/업무관리/TASKS.md`
- HANDOFF: `90_공통기준/업무관리/HANDOFF.md`
- STATUS: 각 도메인 하위 `STATUS.md`
- 우선순위: TASKS.md → STATUS.md → HANDOFF.md → Notion
- 현업 업무: `90_공통기준/업무관리/업무_마스터리스트.xlsx` 우선. AI 작업: TASKS.md 우선
- Git이 기준 원본. Notion은 보조. 중복 유지 금지

## 완료 판정 (사람/GPT 판정 기준 — 자동 게이트 아님)

기준 문서 확인 + 반영 위치 확인 + Git 실물 존재 + TASKS.md 비충돌 → PASS
미충족 시: 정합 / 부분반영 / 미반영 / 보류 / 기준 미확인 / 임시검토

> completion_gate는 TASKS/HANDOFF 갱신 여부만 검사하는 최소 게이트다. 위 4개 기준 전체를 자동 검증하지 않는다.

## 종료 시 갱신
1. TASKS.md → 2. 도메인 STATUS.md → 3. HANDOFF.md → 4. Notion (필요 시)

## 외부 모델 호출 (3-tool 합의안, 2026-04-18)

워크플로우 설계 주체는 항상 Claude. GPT/Gemini는 입력 제공자로만 호출.

| 도구 | 호출 경로 | 사용 시점 |
|------|----------|----------|
| GPT (웹) | `/gpt-send`, `/gpt-read` | 토론, 추론·창의·아이디어 다변화, 반대논리 검증 |
| Gemini (웹) | `/gemini-send`, `/gemini-read` | 토론, 멀티턴 대화 |
| Gemini (CLI minion) | `/ask-gemini` | 빠른 단발 질의, WebFetch fallback, 대용량/멀티모달 |

**원칙**:
- Claude가 호출 시점·입력·검증 절차를 설계
- GPT/Gemini 응답은 무결성 검증 후 채택 (실물 파일/Git/실증 데이터 대조)
- 도메인 한정 발상 금지 — 강점 기반 분담
- **상호 감시**: 3자 토론 시 단일 모델 단독 통과 금지 — GPT 답은 Gemini 검증, Gemini 답은 GPT 검증, Claude 설계는 양측 검증 (`90_공통기준/토론모드/CLAUDE.md` "상호 감시 프로토콜")
- 자세한 합의안: 메모리 `project_three_tool_workflow.md`

## 설계 원칙 (Plan glimmering-churning-reef, 2026-04-22 세션91 반영)

자기유지형 시스템의 7원칙은 `.claude/self/DESIGN_PRINCIPLES.md` 단일 원본을 따른다.
이전 Self-X Layer 1/2/4 + B5 Subtraction Quota 정책은 전면 폐기 (안전안 채택).
자세한 맥락: `C:/Users/User/.claude/plans/glimmering-churning-reef.md` Part 2.

- 활성 hook 자동 집계: `bash .claude/hooks/list_active_hooks.sh`
- 주 1회 수동 점검: `bash .claude/self/selfcheck.sh`
- 보호 자산: `90_공통기준/protected_assets.yaml` (Self-X/quota 블록 제거됨, 세션91 V-4/V-5)

## 운영 안정성
- settings/hook 파일 변경 후 반드시 세션 재시작 (변경사항은 세션 시작 시 캐싱됨)
- 장시간 세션 방치 금지 — 도메인/의제 전환 시 세션 재시작 권장
- 공통 모듈(hook_common 등) 수정 시 `grep -r` 호출부 전수 확인 선행
- 파일 변경 후 TASKS/HANDOFF 갱신을 커밋 직전에 함께 수행 (completion_gate 반복 방지)
- Windows PowerShell 세션에서는 `bash`가 PATH에 없을 수 있다. Bash가 필요하면 `.claude/scripts/run_git_bash.ps1 '<command>'` 또는 `C:\Program Files\Git\bin\bash.exe -lc '<command>'`를 사용한다.

## /rewind 한계 (2026-04-18 3자 토론 합의)
- `/rewind`(Esc×2)는 **Claude가 만든 코드 변경만** 되돌린다. Git 대체재가 아니다.
- bash 명령으로 수행한 변경(`rm`, `mv`, `cp`, 외부 스크립트 실행, ERP/MES 업로드)은 **추적·복구 불가**.
- 저장소는 Bash 훅·외부 스크립트·G-ERP 연동이 많으므로, 중요한 변경은 반드시 `git commit` 후 작업한다.

## 문서 조회 우선순위 (2026-04-18 3자 토론 합의)
- **라이브러리/SDK/API 문서 조회**: `context7` MCP 우선 사용 (`mcp__context7__query-docs`, `resolve-library-id`). WebSearch는 fallback.
- **일반 리서치·최신 뉴스·사례 조사**: WebSearch 우선.
- 이유: context7은 공식 저장소에서 최신 버전별 문서를 가져와 학습 데이터 오래됨 문제를 해소한다.

## hook vs permissions 역할 경계 (2026-04-19 의제5 3자 토론 합의)

> 배경: `.claude/settings.local.json` permissions.allow가 110개까지 누적되며 1회용 16건 + 완전 중복 2건이 섞여 들어온 문제를 근본 해결. 상세 로그: `90_공통기준/토론모드/logs/debate_20260418_190429_3way/`.

### 경계 원칙
- **permissions = 도구 호출 허용 on/off 게이트** — "이 Bash/Write/MCP 호출 자체를 허용할지"
- **hook = 호출 시점 맥락 검증 (조건부 게이트)** — "호출 시점의 지시문/상태/커밋 기준 등 맥락이 맞는지"
- **기능 직교**: 동일 보안 목적이라도 permissions와 hook 중 하나만 씀. 중복 금지
- **포괄 Bash 허용 vs dedicated tool**: 포괄 `Bash(cat:*)`·`Bash(grep:*)` 등은 fallback. **우선순위는 Read/Grep/Glob** 전용 도구

### 신규 추가 5단계 의사결정 트리
permissions나 hook을 추가할 때 위에서 아래로 순서대로 묻는다.

1. **전역 규칙인가 일회성 예외인가?** — 1회용(PID·URL·특정 경로 하드코딩)이면 **등록하지 않는다**. 포괄 패턴(`Bash(echo:*)` 등)이 이미 있으면 그걸 쓴다. 포괄이 없으면 포괄 등록을 고려한다.
2. **도구 호출 허용 문제인가?** — 호출 자체를 막거나 풀어주는 문제면 `permissions`.
3. **호출 시점 맥락 문제인가?** — 호출 조건(지시문 읽음·커밋 기준 갱신 등)에 따라 허가가 달라지면 `hook`.
4. **둘 다 필요한가?** — 허용은 permissions로, 조건은 hook으로 분리. 한 곳에 섞지 않는다.
5. **기록/만료 정책이 필요한가?** — 일시적 허용이면 `.claude/state/` 또는 `hook_log.jsonl`에 기록하고 만료 조건을 문서화.

### settings 계층 분리 가이드 (쟁점 G — 선제조건 검토만, 실물 이동은 세션72 이월)
- **팀 공용 정책** (전역 허용·전역 hook): `.claude/settings.json` 또는 기준 문서 (Git 커밋)
- **개인·세션성 예외**: `.claude/settings.local.json` (gitignore 또는 최소 범위)
- 재분류 인벤토리: `90_공통기준/토론모드/settings_inventory_20260419.md`

### 재발 방지 훅
- `.claude/hooks/permissions_sanity.sh` (advisory): 1회용 패턴·완전 중복 자동 탐지 → stderr 경고 + `hook_log.jsonl` 기록. 차단 없음. 60분 캐시.
- Phase 2-B(세션71 후속 또는 세션72): `completion_gate.sh` 소프트 블록 — 동일 1회용 패턴 3회 누적 탐지 시 사용자 명시적 확인 프롬프트. **하드페일 사용 안 함** (제조업 급한 세션 중단 리스크 회피)

## 훅 등급 + 에러 전파 정책 (2026-04-19 의제5 Gemini 제안·GPT 승격)

> 활성 훅이 맞물린 상태에서 특정 훅 exit 1 전파 정책이 제각각이던 문제를 표준화. hook_common.sh 공통 래퍼 + .claude/hooks/README.md 등급 분류 테이블 참조. 활성 수 집계: `bash .claude/hooks/list_active_hooks.sh --count`.

### 훅 등급 3종
- **advisory (경고성)**: 실패해도 세션 계속. `exit 0` 강제. stderr 로그만. `|| true` 허용 명시. 예: `permissions_sanity.sh`, `auto_compile.sh`, `notify_slack.sh`
- **gate (차단성)**: 실패 시 상위 도구 호출 차단. `exit 2` + JSON `decision=deny` 병행(belt-and-suspenders). `|| true` 금지. 예: `block_dangerous.sh`, `commit_gate.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh` (Phase 2-B 세션72 exit 2 전환 완료). `debate_verify.sh`는 incident 18건 잔존으로 Phase 1 advisory 유지 (Phase 2-C 재평가).
- **measurement (계측)**: 실패 영향 없음. `exit 0` 강제. timing·통계만 기록. `trap ERR` 무시. 예: timing 래퍼, `hook_log`

### 공통 래퍼 함수 (hook_common.sh 정의)
- `hook_advisory <hook_path>` — 실패 시 stderr 로그 + exit 0
- `hook_gate <hook_path>` — 실패 시 exit 2 전파
- `hook_measure <hook_path>` — trap ERR 예외 무시, timing만

### Phase 2-B 적용 현황 (2026-04-19 세션72)
- **exit 2 + timing 배선 완료 (6개 gate)**: `commit_gate.sh`, `block_dangerous.sh`, `date_scope_guard.sh`, `protect_files.sh`, `evidence_stop_guard.sh`, `stop_guard.sh`
- **timing만 배선 (Phase 2 승격 보류)**: `debate_verify.sh` — `incident_ledger` `debate_verify` 태그 18건 잔존. incident 7일 0건 달성 시 Phase 2-C에서 exit 2 전환
- **completion_gate.sh 소프트 블록 추가**: 최근 7일 permissions 1회용 패턴 동일 라벨 3회 이상 누적 시 deny 1회(60초 쿨다운) — 하드페일 없음
- **나머지 훅 등급 분류**: `.claude/hooks/README.md` 표 참조. 일괄 timing 배선은 Phase 2-C 이월
- 확장 여지: 복구(cleanup/teardown) 등급 — Gemini 제안, 세션73+ 평가

## 금지
- 원본 xlsx/docx/pdf 직접 수정
- 승인 없는 파일명/시트명/컬럼명 변경
- 검증 없이 값 덮어쓰기
- Git 미확인 추측 답변
- 미푸시 상태를 완료로 간주
- Claude 설명만 듣고 PASS
