# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-11 KST — 세션 19 (취약점 모니터링 + evidence_stop_guard 리팩토링)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 0. 최신 세션 (2026-04-11 세션 19)

### 이번 세션 완료
1. **동결 취약점 3건 3회 연속 확인**: TOCTOU(단일스레드) / execCommand(fallback 전용) / classification 소급(.req+.ok) — 전부 가정 유효
2. **evidence_stop_guard.sh 리팩토링**: 직접 sed 파싱(L24-29, 6줄) → `last_assistant_text()` 공용 함수 호출(1줄). completion_gate/stop_guard와 패턴 통일 완료
3. **smoke_test**: 105/105 ALL PASS

### 다음 세션 안건
1. 취약점 동결 3건 계속 모니터링
2. GPT 토론 — 세션19 변경 공유 및 추가 개선 의제 발굴

---

## 1. 이전 세션 (2026-04-11 세션 18)

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
