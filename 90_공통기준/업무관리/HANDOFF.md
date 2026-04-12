# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-13 KST — 세션 28 (하네스 범용 확장 + yt-dlp 안정화 + 심화 콘텐츠 + 후속 구현)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-12 세션 28)

### 이번 세션 완료
1. **의제 1: 하네스 범용 확장 GPT 토론 2턴 + 구현**: 6개 출처 리서치 → 합의 → 하네스_운영가이드.md DRAFT→ACTIVE 확장 (4개 섹션)
2. **의제 2: yt-dlp 운영 안정화**: transcript-only 기본값 전환 + --force-download 신설
3. **의제 3: 심화 콘텐츠 탐색 합의 + 구현**: 키워드 12개 + 검색 루트 5단계 + 공통 심화 필터 문서화 + Notion DB 6필드 확장 (콘텐츠 분석 이력)
4. **harness_gate 실전 검증**: debate_preflight.req 활성 시 commit 차단 정상 확인
5. **regression_intake.py**: P1/P2 실패 → smoke_test 반자동 편입 스크립트
6. **/self-audit 주간 자동 등록**: scheduled-task 매주 월 09시
7. **CDP 유틸 추가**: poll_and_read.py, read_chat_msgs.py

### GPT 판정
- 의제 1: 통과 (176db7d4 + 304d490a)
- 의제 2: 통과 (c53dd0c3 + 35d87f7d)
- 의제 3: 합의 완료 + 구현 완료

### 다음 세션 안건

**[대] 심화 콘텐츠 첫 탐색 실행**
- 키워드로 실제 검색 → A/B등급 콘텐츠 발굴 → Notion 등록

**[보류] yt-dlp 풀다운로드 복구 실험**
- deno/EJS 설치 — 프레임 분석 필요 시 재검토

**[소] Notion 부모 페이지 / verify_xlsm COM**

---

## 1. 이전 세션 (2026-04-12 세션 27)

### 이번 세션 완료
1. **장피엠 채널 최근 3개월 영상 4건 자막 전수 분석**: C6xlOsQFyOQ(43분) / Lu-krYyYgUU(16분) / wP48xJLWuB0(13분) / 5sPgWy8jXRQ(90분) — 전부 C등급, A/B 0건
2. **GPT 토론 3턴**: 영상 분석 합의(GPT 기존 우선순위 철회) + yt-dlp 개선 합의(채택3/보류1/버림1)
3. **youtube_analyze.py 개선**: subprocess timeout 4곳 추가 + transcript-only fallback + manifest degraded mode 필드
4. **yt-dlp 근본 원인 조사**: YouTube JS challenge hang (2026.03.17 버전, node 있지만 deno 없음)

### GPT 판정
- 영상분석: 종합 C등급 동의
- yt-dlp 개선: 채택 3건(timeout/fallback/전 호출부 timeout)

### 다음 세션 안건 (대/중/소)

**[대] GPT 토론 의제 — 하네스 범용 확장**
- 현재: 토론모드 전용 (GPT 응답 → 채택/보류/버림)
- 제안: 모든 외부 입력·스킬 결과·파이프라인 출력에 품질 판정 적용
  - 정산 결과 → 실증됨/기준미확인/수치불일치
  - 영상분석 → A/B/C 판정 강제화
  - 엑셀 수정 → 원본대조 완료/미완료
- GPT에 의제로 공유하여 공동 설계 필요

**[대] yt-dlp 영상 다운로드 복구**
- 원인: YouTube JS challenge 변경 (4/11 22:54 이후 hang)
- 시도할 것: `pip install --upgrade yt-dlp` (이번 세션에서 네트워크 느려 미완)
- 시도할 것: deno 설치 → yt-dlp JS runtime 연동
- 프레임 분석 = /video 스킬 핵심 차별점. 복구 필수

**[대] 심화 콘텐츠 탐색 루트 확보**
- 장피엠 채널은 입문/중급 → 우리 수준에 맞는 심화 채널 발굴 필요
- 영어권 고급 사례 (순정 CC, 하네스 검증, incident, 에이전트 운영 체계)

**[중] harness_gate 실전 검증**
- 이번 세션에서 간접 검증됨 (하네스 분석 3턴 수행 후 commit/push 진행)
- 다음 세션에서 직접 발화 시나리오 1회 확인

**[소] Notion 부모 페이지 동기화 / verify_xlsm.py COM 실검증**

---

## 1. 이전 세션 (2026-04-12 세션 26)

### 이번 세션 완료
1. **P2 4개 계약 보강**: cdp-wrapper / supanova-deploy / youtube-analysis / flow-chat-analysis — 4섹션 추가
2. **P3 4개+1 계약 보강**: pptx-generator / skill-creator-merged / sp3-production-plan — 4섹션 신규. production-result-upload — 표준 포맷 리포맷. production-report — 4섹션 신규
3. **PASS 9→17개**: 유지 스킬 전수 계약 보강 완료 (FAIL 0개)
4. **훅 개수 갱신**: README.md + AGENTS_GUIDE.md — 20→21개 (harness_gate 반영)

---

## 1. 이전 세션 (2026-04-12 세션 25)

### 이번 세션 완료
1. **P1 스킬 3개 계약 보강**: zdm/mainsub/outer-main — 4섹션 추가. PASS 6→9개
2. **hook_metrics 재생성**: 4/12 기준
3. **harness_gate.sh 신규 구현**: GPT 응답 후 하네스 미수행 시 commit/push/공유 차단 (Bash PreToolUse)
   - 발화 조건: debate_preflight.req 존재 시에만
   - 복합 4조건 AND: 채택: + 보류:/버림: + 독립견해 + 실물근거
   - transcript_path 미확인 시 fail-closed (f63a1139)
   - completion 백스톱 연동은 보류 (책임 분리 원칙)
   - settings.local.json PreToolUse/Bash에 등록
3-1. **cdp_chat_send.py 전송 검증**: submit 후 user 메시지 DOM 확인 추가 (ddca77d1). send_unverified 시 exit 6
4. **risk_profile_prompt 확장**: 토론 키워드 감지 → debate_preflight.req 생성
5. **GPT 토론 4라운드**: 채택 9건 / 보류 2건 / 버림 1건
   - 합의: transport gate(send_gate)와 quality gate(harness_gate) 분리
   - 보류→수정채택: gpt_harness를 .req/.ok 파일 기반 대신 트랜스크립트 패턴 검사
   - fail-closed 전환 (f63a1139), 문서 과장 수정 (c57aa084)
6. **cdp_chat_send.py 버그 수정**: contenteditable 입력 execCommand→keyboard.insert_text 전환 + 전송 검증 로직 개선 (ddca77d1, b9dd6179)
7. smoke_test: 105/105 ALL PASS
8. **GPT 최종 PASS**

### 다음 세션 안건
1. harness_gate 실전 검증 (다음 토론 세션에서 자동 발화 확인)
2. P2 스킬 4개 계약 보강 (cdp-wrapper/supanova/youtube/flow-chat)
3. P3 스킬 4개 계약 보강 (pptx/skill-creator/production-report/sp3)
4. README.md 훅 개수 갱신 (20→21개)

---

## 1. 이전 세션 (2026-04-12 세션 24)

### 이번 세션 완료
1. **스킬 28개 4축 분류**: grade/수정일/커밋수/코드유무 → 유지 18개 / 아카이브 10개
2. **아카이브 10개 이동**: cost-rate-management 등 10개 → `98_아카이브/정리대기_20260412/스킬/`
3. **map_scope AND 조건 해소 확인**: PASS. 236건 중 4/12 이후 6건 전부 정탐, 오탐 0
4. **skill_usage 계측 버그 수정**: `risk_profile_prompt.sh` L71 regex `^\s*/` → `"/`. JSON 래핑 미매칭 근본 해소
5. **취약점 동결 3건 5회 연속 유효 → "안정" 승격**: TOCTOU/execCommand/classification 소급 전부 유효
6. **유지 FAIL 11개 계약 보강 우선순위**: P1(zdm/mainsub/outer-main) / P2(4개) / P3(4개)
7. **GPT 판정**: PASS (b95c86ca)

---

## 1. 이전 세션 (2026-04-12 세션 23)

### 이번 세션 완료
1. **/self-audit 첫 실사용**: P1 2건 / P2 3건 / P3 2건 검출. anomaly 검출 품질 양호
2. **GPT 토론 2라운드**: 채택 3건 / 보류 1건 / 버림 0건
3. **AGENTS_GUIDE.md 현행화**: 폐지 hook 4개 제거 → 현행 20개, 스킬명 수정, 감시계층 운영 상태 표시
4. **README.md**: state_rebind_check matcher Bash→Write|Edit|MultiEdit 수정
5. **skill_usage 계측 연결**: /command 감지 → hook_skill_usage 자동 호출
6. **evidence 세션 경계 수정**: session_start_restore.sh에서 START_FILE 강제 갱신 (보조)
7. **독립 재검토**: GPT 프레임 종속 탈피 → 2건 이견 제기 → GPT 수용
8. **map_scope 트리거 AND 조건화**: 대상+의도 AND 조건 (7d5ffbd7) — 40건+ 반복 차단 근본 해소

---

## 1. 이전 세션 (2026-04-12 세션 22)

### 이번 세션 완료
1. **영상 분석**: c-a4GBOxhXQ "나의 AI 에이전트 전환기" (일잘러 장피엠, 28분) — 15프레임+자막 통합
2. **판정**: A 1건(메타 스킬 /self-audit) / C 5건. 오토리서치·주간 셀프 리뷰는 사용자 판단으로 불채택
3. **스킬 절차 개선**: video.md + SKILL.md에 플랜모드 감지(Phase 0), 갭 분석(Step 3.5), 상태갱신(Step 5) 추가
4. **Notion 본문 포맷 기준 고정**: save_to_notion.py에 표 헤더 템플릿 포함
5. **Notion 저장**: 340fee67 / **Drive 업로드**: 18파일
6. **/self-audit 메타 스킬 구현**: commands + read-only agent 분리, 4축 진단, 3분류
7. **GPT 토론 3라운드 + 실물 검증 3회 → 최종 통과**
8. 커밋: 37bfdec4, 3aa43cce, a4aaa748, 7b1b2272, 3fc14b4c, 2a3d9fc5, e7e66e2c, bbadd386

---

## 1. 이전 세션 (2026-04-11 세션 21)

### 이번 세션 완료
1. **캐시 정책 구현**: TTL 7일 + 1GB 상한 + 실행시 자동 cleanup + mp4 우선 삭제 + LRU fallback
2. **Notion DB "영상분석 이력" 생성 + 실증**: video_id 기준 upsert, 실제 페이지 생성 확인 (33ffee67)
3. **save_to_notion.py**: 속성 빌더 + 본문 템플릿 + MCP 호출 시퀀스
4. **GPT 토론 4라운드**: 채택 9건 / 보류 2건 / 버림 2건
5. **OpenClaw 조사**: GitHub 8개 YT 스킬 전부 자막 기반. 영상 시각 분석 없음
6. **Gemini 영상 API 조사**: 1FPS 직접 입력, 코드/UI 읽기 가능, $0.01~0.62/건
7. **GenSpark 조사**: 음성 전사 기반, 시각 분석 제한적
8. **GPT 검증**: 캐시 PASS / Notion 저장 PASS / Drive 미완

### 추가 완료 (Drive 실증)
7. **Drive OAuth 인증**: credentials.json 생성 + token.json 발급 + CDP 브라우저 인증 처리
8. **Drive 업로드 실증**: 영상분석/raw/3XhbI597gm8/ 18파일 업로드 성공
9. **Notion Drive 링크 동기화**: 속성+본문 모두 실제 Drive URL 반영
10. **GPT 최종 판정: 통과**

---

## 2. 이전 세션 (2026-04-11 세션 20)

### 이번 세션 완료
1. **youtube_analyze.py 신규**: 영상 다운로드(yt-dlp 480p) → 프레임 추출(ffmpeg 챕터+긴챕터보강) → 자막 추출 → manifest.json
2. **SKILL.md 개편**: 수동 모드를 프레임+자막 통합 분석으로 전환
3. **/video 슬래시 커맨드**: 트리거 확실화
4. **GPT 토론 채택 3건**: max-frames 20→15 / 90초 초과 챕터 3등분 보강 / --refresh 플래그
5. **GPT 검증 PASS**: 87e2ed9d 실물 정합 확인

---

## 3. 이전 세션 (2026-04-11 세션 19)

### 이번 세션 완료
1. **동결 취약점 3건 3회 연속 확인**: TOCTOU(단일스레드) / execCommand(fallback 전용) / classification 소급(.req+.ok) — 전부 가정 유효
2. **evidence_stop_guard.sh 리팩토링**: 직접 sed 파싱(L24-29, 6줄) → `last_assistant_text()` 공용 함수 호출(1줄). completion_gate/stop_guard와 패턴 통일 완료
3. **smoke_test**: 105/105 ALL PASS

### 다음 세션 안건
1. 취약점 동결 3건 계속 모니터링

---

## 2. 이전 세션 (2026-04-11 세션 18)

### 이번 세션 완료
1. **동결 취약점 3건 재확인**: TOCTOU(단일스레드) / execCommand(fallback 전용) / classification 소급(.req+.ok 강화) — 전부 가정 유효 (2회 연속 확인)
2. **fail-open 재분류 검토**: commit_gate/completion_gate/evidence_stop_guard 3개 훅 라인별 분석 → 모든 exit 0 경로가 정당한 pass-through 또는 프레임워크 규약. 코드 변경 없음
3. **README.md**: commit_gate 실패 계약을 "fail-open (hardened)"로 갱신
4. **--require-korean argparse 정의 완전 삭제**: cdp_chat_send.py L110 삭제 + send_gate.sh 예시 문구 제거 + REFERENCE.md 2개 예시 정리 + CLAUDE.md 문구 갱신
5. **smoke_test**: 105/105 ALL PASS

### GPT 토론
- 의제 1 (동결 취약점): 현행 유지 동의
- 의제 2 (fail-open 재분류): GPT가 이전 P0 지적 철회, 현행 유지 합의
- 의제 3 (--require-korean 삭제): 진행 합의
- 채택 3건 / 보류 0건 / 버림 0건

---

## 1. 이전 세션 (2026-04-11 세션 17)

### 이번 세션 완료
1. **CLAUDE.md 경로 명시**: 상태 원본 섹션에 TASKS/HANDOFF/STATUS 실제 경로(`90_공통기준/업무관리/`) 추가
2. **local_hooks_spec.md 아카이브**: Phase 1 미구현 spec → `98_아카이브/정리대기_20260411/` 이동, 원위치에 리다이렉트 스텁
3. **README.md 보강**: handoff_archive.sh PostToolUse 누락 추가, 훅 개수 19→20개 수정
4. **smoke_test 3건 추가**: json_escape payload 테스트 (Windows 경로 백슬래시 / 제어문자 LF+TAB+CR / 혼합 입력)
5. **동결 취약점 3건 모니터링**: TOCTOU(단일스레드 유효) / execCommand(CDP 강제 유지) / classification 소급(.req 사전생성 유효) — 전부 가정 유효
6. **cdp_chat_send.py dead code 정리**: 언어 가드 서브시스템 전부 삭제 (함수 3개, regex 7개, allowlist 로더). --require-korean deprecated no-op 유지. korean_allowlist.txt 아카이브
7. **문서 정리**: 토론모드 CLAUDE.md, REFERENCE.md, finish.md, share-result.md에서 --require-korean 예시 갱신
8. **smoke_test**: 105/105 ALL PASS

### GPT 토론
- 의제 1~4: 채택 4건 / 보류 0건 / 버림 0건
- cdp_chat_send.py 정리: 채택 5건 / 보류 0건 / 버림 0건
- GPT 판정: 의제 1~4 통과 (조건부→수정→통과). cdp 정리 통과

---

## 1. 이전 세션 (2026-04-11 세션 16)

### 이번 세션 완료
1. **독립 취약점 점검 4건**: write_marker.sh 백슬래시/개행 미이스케이프, precompact heredoc 미인용, handoff lock TOCTOU
2. **GPT 토론 합의**: 채택 2건 / 버림 2건
3. **구현**: hook_common.sh에 json_escape() 추가, write_marker.sh 두 곳 적용
4. **JSON 로그 스키마 첫 실전 적용 검증**: summary_counts + item/label/evidence/ref 4필드 정상 생성 확인
5. **smoke_test**: 102/102 ALL PASS
- GPT 판정: 통과. 종합 재평가 9.1/10

---

## 1. 이전 세션 (2026-04-11 세션 15)

### 이번 세션 완료
1. **세션 14 GPT 평가 독립 검증**: fail-open 과다, settings.local.json 의존, JSON 파서 한계, 토론 로그 증거성 — 4건 전부 채택 (실물 확인)
2. **의제 1 합의 (C+)**: safe_json_get Stage 2 nested object → 현상 유지 + fallback WARN 계측
   - send_gate.sh: tool_input 추출 실패 시 WARN 로그 추가
   - gpt_followup_post.sh: tool_input 추출 실패 시 WARN 로그 추가
3. **의제 2 합의 (유형별 분기)**: auto-resolve 정밀화
   - scope_violation / dangerous_cmd → 현행 24h 유지
   - evidence_missing → .ok 파일 존재 시에만 auto-resolve (시간 무관)
   - pre_commit_check → auto-resolve 대상 제외 (PASS 마커 체계 미비)
4. **P0**: STATUS.md 날짜 드리프트 해소 (도메인 5개 + 업무관리 + 토론모드)
5. **P1**: cdp_chat_send.py expect-last-snippet 완전 제거 (코드 40줄 + 문서 5개 + smoke_test)
6. **P2**: incident_ledger .gitignore 제외 삭제 → Git 추적 유지 정책 확정 + README 반영
7. **P3**: 토론 로그 JSON 근거 필드 보강 — harness에 summary_counts + item/label/evidence/ref 4필드 스키마 (SKILL.md/REFERENCE.md 갱신)
8. **smoke_test**: 102/102 ALL PASS

### GPT 판정
- 9.2/10 통과, 구조 부채 + 증거성 보강 완료

---

## 1. 이전 세션 (2026-04-11 세션 14)

### 이번 세션 완료
1. **safe_json_get Stage 3 추가**: boolean/number/null 리터럴 추출 → completion_gate fast-path 미작동 해소 (확정 버그)
2. **write_marker.sh 원자적 쓰기**: temp→mv 패턴 (중단 시 마커 파손 방지)
3. **incident_repair.py null 안전 처리**: str(None)→"None" 방어 (or "" 패턴)
4. **archive_resolved/auto_resolve 원자적 쓰기**: tempfile→os.replace
5. **incident_ledger 512KB 경고**: 크기 초과 시 로그 (python3 하드코딩 → 일반 표현 수정)
6. **gpt_followup_post.sh 빈 TOOL_NAME 방어**: 조기 종료 + 경고 로그
7. **smoke_test**: 95→102 (boolean/number/null 4건 + 테스트26 갱신), 102/102 ALL PASS

---

## 1. 이전 세션 (2026-04-11 세션 13)

### 이번 세션 완료
1. **commit_gate fail-open 봉합**: JSON 파싱 실패 시 raw INPUT fallback 검사 추가
2. **evidence_gate 차단 안내 보강**: deny 메시지에 해결 경로 명시 + 동일 incident 연속 3회 초과 중복 기록 억제
3. **incident_ledger resolved 아카이브**: 30일 경과 resolved 항목 → .archive.jsonl 이동 (--archive 옵션)
4. **cdp_chat_send.py --expect-last-snippet 폐기**: 인코딩/잘림 차이로 오차단 유발하여 제거

---

## 2. 이전 세션 (2026-04-11 세션 12)

### 이번 세션 완료
1. **옵션C 4/14 재집계**: 승인 1791 / deny 319 / 오탐 45 / 우회 0 → GPT 판정: 유지
2. **보류 3건 GPT 토론 판정 완료**:
   - completion_gate v8: is_completion_claim 패턴 축소 (약한 패턴 3개 분리 → 후속 조건)
   - is_completion_claim: 강한 완료 표현만 트리거, "잔여이슈없/ALL CLEAR/GPT PASS" 제거
   - incident enum: classification_reason 9개 호출부 표준화, 6종 enum 세분화
3. **incident_repair 확장**: enum 기반 next_action/patch_candidates/verify_steps 매핑
4. **resolved 자동 마킹**: --auto-resolve 옵션 (24시간 경과 규칙), 68건 해소 (87→155)
5. **smoke_test: 98/98 ALL PASS**, GPT 통과

### 다음 세션 안건
→ TASKS.md "진행중 / 보류" 섹션 참조

---

## 2. 이전 세션 (2026-04-11 세션 11)

### 이번 세션 완료
1. **publish_worktree_to_main.sh 구현** — B-lite 방식 (--ff-only/--cherry-pick/--dry-run)
2. **하네스 즉시 개선 4건 구현**
3. **워크트리 정리 완료** — 10개 삭제
4. **smoke_test: 95/95 ALL PASS**, GPT 재평가 8.6/10

---

## 1. 이전 세션 (2026-04-11 세션 9)

### 이번 세션 완료
1. **GPT 재평가 합의 8.1/10** — 8.4→8.0~8.2 독립 검증 후 토론 합의
2. **합의안 6건 구현** (5a574fac): write_marker v6 JSON, safe_json_get placeholder, evidence_init 중복 제거, README 19개+실패계약, auto_compile python 동적 감지, smoke_test 95/95
3. **GPT 리뷰 3건 해소**:
   - notify_slack.sh: sed→safe_json_get, $HOME→$PROJECT_ROOT, python 동적 감지 (76bb0c53)
   - handoff_archive.sh settings 복원 (76bb0c53)
   - final_check.sh: --full 모드 README/STATUS 불일치 FAIL 승격 (34d8af47)
4. **GPT 최종 판정: 통과**

---

## 1. 이전 세션 (2026-04-11 세션 6)

### 이번 세션 완료
1. **CDP 전송 통일** — GPT 3라운드 토론 합의. cdp_common.py --match-url-exact + fail-closed
2. **send_gate.sh CDP 단일화** — 직접 JS 전송 deprecated 차단
3. **risk_profile_prompt.sh req 축소** — map_scope hard req 6개
4. **commit_gate.sh 상세화** — incident에 mode/승격여부/FAIL 키워드 기록
5. **is_completion_claim() 로깅** — 매치 구문 hook_log 기록
6. **문서 정비** — 예비 경로 deprecated, --match-url-exact 반영
7. **인코딩 수정** — debate_room_detect.py UTF-8, cdp_chat_send.py 한국어 가드 비활성화

---

## 1. 이전 세션 (2026-04-11 세션 5)

### 이번 세션 완료
1. **kind-chatelet 머지** — allowlist 외부파일 분리 + incident ledger 무회전
2. **hopeful-feistel 머지** — Slack 활성화 + 스케줄러 폐기 + STATUS 훅 일원화
3. **send_gate.sh 경로 수정** — L72 `$SCRIPT_DIR/../state` → `$PROJECT_ROOT/.claude/state`
4. **훅 3종 검증** — PreCompact(kernel 저장 OK), SessionStart(재주입 OK), state_rebind(fresh skip OK)
5. **Slack/Notion 테스트** — Slack 스크립트 실행 정상(토큰 미설정), Notion MCP 검색 정상

---

> **이전 세션 이력 아카이브**: `98_아카이브/handoff_archive_20260411_20260411.md`
