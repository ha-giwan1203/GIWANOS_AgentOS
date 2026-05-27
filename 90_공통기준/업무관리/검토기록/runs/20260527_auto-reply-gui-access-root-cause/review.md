# auto_reply GUI 접근 실패 근본원인 보강

- 작업일: 2026-05-27
- 원인: Codex 앱의 일반 샌드박스 셸에서는 Windows GUI 창 열거가 0개로 보일 수 있음.
- 증상: Claude 프로세스는 실행 중인데 `auto_reply.py --target claude`가 `Claude window not found`로 실패.
- 실제 확인: 동일 메시지를 `require_escalated` GUI 권한으로 재실행하자 `PASS: target=claude paste+enter submitted`.

## 변경

- `auto_reply.py`: 대상 프로세스 존재 여부와 visible top-level window 수를 확인해 `GUI_ACCESS_UNAVAILABLE` 원인을 명확히 표시.
- `AGENTS.md`: 일반 실행에서 `GUI_ACCESS_UNAVAILABLE` 또는 `window not found` 발생 시 `require_escalated`로 1회 재시도하도록 명시.
- `codex_claude_channel/README.md`: auto_reply GUI 실행 권한과 fallback 판정 기준 추가.

## 검증

- `python -m py_compile auto_reply.py`: PASS.
- 일반 샌드박스 창 선택 진단: `GUI_ACCESS_UNAVAILABLE` 메시지 확인.
- `auto_reply.py --help`: exit-code 안내 출력 확인.
- 권한 실행 자동회신: `PASS`, `verify=enter_confirmed` 로그 확인.
- 최종 Claude 완료 회신: `PASS: target=claude paste+enter submitted`.
