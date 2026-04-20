# Round 1 — GPT 본론·판정 (수동 중재 경유)

## 맥락
- gpt-5-4-thinking 모델 사용 중 자동 전송 후 stream halt 2회 발생 (blockCount 15 → lastLen 183 고정 → 새 대화방 이동 후 blockCount 3 → lastLen 99 고정)
- 사용자가 수동 중재 경유로 최종 본론·판정 텍스트 전달
- Claude 탐지 실패 원인: `data-message-model-slug="gpt-5-4-thinking"` 속성 + 짧은 progress 메시지 누적 패턴을 stream halt로 오판 → stop 클릭 (세션83+ gpt-send/gpt-read 스킬 개선 대상)

## 의제 1 — evidence_gate 과다 발화 원인 분석

### 본론
(1) 333건을 현재 코드의 단일 워크플로우 폭주로 보기 어려움. 현재 main 실물 기준으로 `tasks_handoff.req` 조기 발행은 이미 제거됐고, `evidence_gate`는 `git commit` 시점에 `tasks_updated`/`handoff_updated` 흔적을 독립 검증. 반면 `map_scope`는 여전히 req/ok 구조를 타고, incident suppress도 30초·tail 30줄 기준이라 같은 세션 재시도 누적이 충분히 생길 수 있음. 즉 구버전 tasks_handoff 패턴 + 현재 map_scope 반복 + commit 시점 차단이 섞였을 가능성이 큼.

(2) `map_scope`와 `tasks_handoff`를 여기서 더 완화하는 건 우선순위가 아님. `map_scope`는 이미 "hook/settings/migration + 수정 의도"로 좁혀졌고, 실제 차단도 `.claude/hooks/*.sh`와 `.claude/settings*.json` 편집에만 걸리게 재정의됨. `tasks_handoff`도 이미 push-only가 아니라 commit-only 검증으로 줄어든 상태라, 지금 더 풀면 통제력만 잃고 원인 해결은 안 됨.

(3) 조치 우선순위: **워크플로우 자동 충족 > gate 조건 완화 > 커밋 타입별 면제**. `evidence_mark_read.sh`는 이미 `TASKS.md`/`HANDOFF.md` 수정 흔적과 `SKILL.md` 읽기 흔적을 ok 마커로 적립하므로, 사용자 별도 수동 절차 없이 증거가 자동으로 닫히게 만드는 쪽이 가장 효과적. 커밋 타입별 면제는 이미 push-only 면제가 들어가 있어 추가 여지가 작음.

### 판정
**검증 필요** — 333건 전수 재집계는 아직 못 했지만, 현재 main 실물상 단일 current workflow 폭주라기보다 구버전 로그와 현재 재시도 누적이 섞인 구조로 보는 게 맞음.

## 의제 2 — 생산계획자동화 고아 폴더 처리

### 본론
판단은 **A, 98_아카이브 이동**. 현재 활성 스킬은 이미 `90_공통기준/스킬/sp3-production-plan/SKILL.md`로 살아 있고, 여기엔 이름·설명·트리거·대상 파일·검증/중단 기준까지 완결된 규범 문서가 있음. 반면 `생산계획자동화` 쪽은 변경이력 문서이고, 이 문서 스스로도 "기존 단일 문서를 스킬/운영절차/변경이력으로 분리했다"고 적고 있어 규범 엔트리라기보다 레거시 분리 산출물에 가까움.

B처럼 `SKILL.md` 신설하면 활성 스킬 이중화. C처럼 `04_생산계획` 도메인 이동하려면 "이 문서가 아직 규범 원본인지" 증명 필요하나 실물 근거 약함. repo 검색에서도 추가 참조 없음. 행동 변경 없는 문서 정리로 보고 3자 토론 간소 판정에 동의.

### 판정
**동의** — 활성 스킬 별도 완성 + `생산계획자동화` 레거시 변경이력 성격 → A 분류 단순 문서 정리가 가장 정합.

## 의제 3 — debate_verify.sh Phase 2-C 승격 판정

### 본론
(1) 7일 재집계 시작점: **세션81 수정 커밋 시점**. `debate_verify.sh` 헤더도 "incident 18건 잔존으로 Phase 2 전환 보류" 기록. 이번 파일 실물에 한글 경로/Python 오탐지 수정 주석과 방어 코드 반영됨. 세션80 resolved 처리는 과거 incident 정리이지 훅 정상 동작 기준점 아님.

(2) 승격: **즉시 전환 말고 7일 대기 유지**. 훅 헤더에 승격 조건 이미 "incident 7일 연속 0건" 박혀 있고, 이번 수정은 원인 제거일 뿐 아직 post-fix 운영 안정성 관찰 안 됨. 최근 7일 debate_verify 0건 수치는 ledger 재집계로 재검증 안 함. post-fix 기준 재집계 안전.

(3) 승격 방식: **기존 Phase 2-B 6종 준용**(hook gate 래퍼 + deny JSON + 차단 경로). 현재 `debate_verify.sh` 검출 코어는 이미 완성. Phase 1에서는 advisory만 내고 ledger 적는 상태. 승격은 탐지 로직 갈아엎는 것 아니라 현재 advisory 출력을 다른 gate들과 같은 deny 경로로 감싸는 수준.

### 판정
**동의** — 재집계 시작 = 세션81 수정 커밋 시각. 7일 관찰 후 기존 gate 패턴으로 승격하는 보수적 경로가 가장 정합.
