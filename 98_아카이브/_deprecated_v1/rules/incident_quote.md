# 미해결 incident 자동 인용 규칙

> 합의 원본: 본 세션 3자 토론 (Claude·GPT·Gemini, 2026-04-30). 채택: 안1+안3. 보류: 안2.
> 배경: incident 데이터(`.claude/incident_ledger.jsonl`)는 정상 적재되지만, Claude가 응답 진입 시 자동 인용 경로가 없어 사용자가 매번 수동 요청하던 문제 해소.

## 트리거 조건

session_start hook 출력에 `--- 미해결 incident: N건` 라인이 보이고 N ≥ 1.

## 적용 절차

1. **첫 응답 본문 진입 전** 1회 실행:
   ```bash
   python .claude/hooks/incident_repair.py --json --limit 3
   ```
2. 출력에서 다음 3개 항목을 응답 도입부 1블록(3줄 이내)으로 인용:
   - 가장 최근/반복 fingerprint 기준 1건의 **classification_reason**
   - **inferred_next_action** (incident_repair.py가 제시하는 다음 행동)
   - **재시도 가능성** 한 줄 (advisory — 사용자 결정 사항)
3. 인용 후 사용자 요청 본문 진행.

## 적용 예시

### D0 실패 시
```
D0 실패 관련 최근 incident 3건 확인됨.
1) OAuth 콜백 정체 2회 반복 — RETRY_OK 가능
2) recover 로그 cp949 출력 오류는 1812603c에서 패치됨
3) 오늘 morning 로그 미확인 — 자동 재실행 전 중복 반영 여부 확인 필요

판단: 바로 재업로드 금지. 먼저 morning 로그와 SmartMES 반영 여부 확인.
```

### commit 실패 시
```
commit 관련 최근 incident 확인됨.
1) auto_commit_state가 수동 커밋 메시지를 선점한 이력 있음
2) commit_gate 차단 후 staged 풀림 신규 이슈 있음
3) final_check 실패 시 TASKS/HANDOFF/STATUS 동기화 필요

판단: 바로 commit 재시도 금지. staged 상태와 final_check 결과부터 확인.
```

## 적용 범위

- **적용**: 모드 A(실무 산출물)·모드 C(시스템 수정)·모드 E(장애 복구) 첫 응답.
- **건너뜀**: 모드 B(분석)·모드 D(토론모드) 첫 응답 — 메타 응답이라 incident 인용이 본문 흐름과 무관.
- **세션 중 후속 응답**: 미적용 (첫 응답 1회만).

## 금지

- incident 자동 resolve 호출 금지 (`--auto-resolve` 플래그 사용 금지).
- TASKS/HANDOFF 자동 등록 금지.
- 자동 수정·자동 hook 추가 금지.
- 사용자 결정 없이 incident 관련 파일 수정 금지.

## 비용

- 토큰 ~30~80 (3줄 인용).
- 실행 시간 ~수백 ms (incident_repair.py CLI).
- 외부 호출 0.
