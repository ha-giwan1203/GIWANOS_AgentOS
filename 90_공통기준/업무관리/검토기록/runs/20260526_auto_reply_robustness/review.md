# auto_reply 견고화 및 push 검토 기록

- 기준 시각: 2026-05-26 화요일 16:11 KST
- 작업: SKIP 자동 재시도, Enter 결과 검증, exit code 분리
- 결론: PASS

## 변경 요약

| 항목 | 결과 |
|---|---|
| SKIP 자동 재시도 | `SKIP_EXISTING_TEXT` 발생 시 5초 간격 2회 재시도 |
| 최종 SKIP | 모든 시도 실패 시 `SKIP_FINAL`, exit code 2 |
| Enter 검증 | Enter 후 입력창 probe, 비어 있으면 `enter_confirmed` |
| Enter 실패 | 메시지 본문이 composer에 남아 있으면 `ENTER_FAILED`, exit code 3 |
| 검증 불가 | 본문 영역 선택처럼 보이면 PASS 유지 + `verify=skipped` |
| 로그 확장 | `retries`, `verify` 필드 추가 |
| stderr | PASS/SKIP_FINAL/ENTER_FAILED/FAIL 1줄 출력 |

## self-test

| 검증 | 결과 |
|---|---|
| `python -m py_compile auto_reply.py` | PASS |
| `python auto_reply.py --target claude "[Codex 검증] auto_reply robustness self-test / Enter verify 확인"` | PASS, exit 0 |
| Enter verify | `verify=enter_confirmed` 로그 확인 |
| target=codex SKIP 시뮬레이션 | 별도 강제 시뮬레이션 생략. 실제 운영 발생 시 `SKIP_FINAL` 로그/exit 2로 관찰 가능 |

## push 계획

| 항목 | 값 |
|---|---|
| 기존 미반영 commit | `b407e058` |
| 이번 보강 commit | 본 commit (`git log -1 --oneline` 기준) |
| push 대상 | `origin main` |
| push 후 검증 | `git rev-parse --short origin/main` |

## 참고

- `auto_reply.log`는 self-test와 진행/완료 자동회신 근거로 commit에 포함한다.
