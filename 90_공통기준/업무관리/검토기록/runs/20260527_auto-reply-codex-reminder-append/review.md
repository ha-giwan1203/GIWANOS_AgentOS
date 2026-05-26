# auto_reply.py target=codex 회신 의무 append 검토

- 작업일: 2026-05-27
- 대상: `90_공통기준/업무관리/codex_claude_channel/auto_reply.py`
- 목적: Claude가 Codex로 위임하는 메시지 끝에 Codex 완료 회신 의무를 자동 부착해 회귀 방지.

## 변경

- `CODEX_REPLY_REMINDER` 상수 추가.
- `send(message, target)`에서 빈 메시지 거부와 target 검증을 먼저 수행한 뒤 `target=="codex"`에만 리마인더 append.
- 동일 리마인더 블록이 이미 들어 있으면 append하지 않도록 idempotent 처리.
- `target=="claude"` 경로는 메시지 변조 없음.

## append 블록

```text
---
[필수 회신] 작업 완료 시 즉시:
python 90_공통기준/업무관리/codex_claude_channel/auto_reply.py --target claude "[Codex 완료] <한 줄 요약>"
- 실패 시 require_escalated 1회 재시도
- 그래도 실패면 90_공통기준/업무관리/검토기록/runs/<YYYYMMDD_task-slug>/review.md 작성으로 fallback
```

## self-test

| 검증 | 결과 |
|---|---:|
| `target=codex` 빈 메시지 거부 | PASS (`ValueError: message is empty`) |
| `target=codex` 짧은 메시지 append | PASS (`20`자 -> `248`자) |
| 동일 리마인더 중복 방지 | PASS (`count=1`, 길이 유지 `248`) |
| `target=claude` 메시지 무변경 | PASS (`21`자 -> `21`자) |
| `python -m py_compile auto_reply.py` | PASS |
| `auto_reply.log` self-test 기록 | PASS (`SELFTEST`, codex `message_len=248`, claude `message_len=21`) |

## 실제 채널 근거

- 패치 전 현재 위임 메시지가 `target=codex`로 정상 수신됨: `auto_reply.log`의 `2026-05-27T08:46:27`, target `codex`, result `PASS`, message_len `1146`.
- 패치 후 self-test는 실제 Codex 입력창에 새 메시지를 보내지 않도록 `_attempt_send_once`만 monkeypatch하여 `send()` 전처리 결과와 로그 길이를 검증.
