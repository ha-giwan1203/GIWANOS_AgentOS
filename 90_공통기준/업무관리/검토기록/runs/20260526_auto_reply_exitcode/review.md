# auto_reply exit code 충돌 해소 리뷰

- 기준 시각: 2026-05-26 화요일 16:31 KST
- 결론: PASS
- 대상: `90_공통기준/업무관리/codex_claude_channel/auto_reply.py`, `AGENTS.md`

## 요약

argparse 인자 오류의 표준 exit code `2`와 `SKIP_FINAL`의 exit code가 충돌하던 문제를 해소했다. 런타임 상태 코드는 `SKIP_FINAL=10`, `ENTER_FAILED=11`로 재매핑하고, `argparse`의 invalid argument는 기존처럼 `2`를 유지했다.

## 패치

| 항목 | 결과 |
|---|---|
| exit code 재매핑 | `0 PASS`, `1 FAIL`, `2 argparse`, `10 SKIP_FINAL`, `11 ENTER_FAILED` |
| 내부 retry sentinel | 공개 exit code와 분리된 `RETRY_SKIP=-10` 사용 |
| 호출자 가이드 | `auto_reply.py --help` epilog와 `AGENTS.md` 호출 명령 옆에 코드표 추가 |
| FAIL 경로 | 창 식별 실패도 `FAIL` 로그를 남기도록 `_select_window()`를 `try` 내부로 이동 |
| SKIP retry | 5초 대기, 2회 재시도 유지. 최종 보류 시 exit `10` |
| Enter 검증 | 텍스트 잔존 시 `ENTER_FAILED` 로그와 exit `11` 반환 |

## 자체 코드 리뷰

| 점검 항목 | 결과 |
|---|---|
| FAIL 창 식별 실패 경로 | PASS. 예외를 `main()`과 `send()`에서 exit `1`로 반환하고 로그 기록 |
| ENTER_FAILED 경로 | PASS. paste 후 Enter에도 draft가 남으면 exit `11` |
| verify 불가 경로 | PASS. 기존 설계대로 `verify=skipped`는 paste-only 성공으로 처리 |
| SKIP retry | PASS. `MAX_SKIP_RETRIES=2`, `SKIP_RETRY_DELAY_SEC=5`, 총 3회 시도 |
| argparse invalid target | PASS. `argparse`가 exit `2` 유지 |
| 추가 발견 결함 | 1건. 창 탐색 실패 시 로그가 남지 않던 경로를 함께 보강 |

## 검증

| 검증 | 결과 |
|---|---|
| `python -m py_compile auto_reply.py` | PASS |
| `python auto_reply.py --help` | PASS. exit code 표 표시 |
| `python auto_reply.py --target invalid "test"` | PASS. exit `2` |
| mock SKIP_FINAL | PASS. exit `10`, 총 3회 호출 |
| mock ENTER_FAILED | PASS. exit `11` |
| mock FAIL | PASS. exit `1` |
| target=claude 정상 호출 | PASS. exit `0`, `verify=enter_confirmed` |

## 다음 액션

commit 후 `git push origin main`으로 origin/main에 즉시 반영한다.
