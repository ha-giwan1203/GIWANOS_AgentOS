# 합의 완료 (세션96 M2)

- 모드: 2자 토론 (Claude × GPT)
- 의제: M2 — README regex 정교화 + list_active_hooks 헬퍼 전환
- 라운드 수: 2
- 채택: 6건 (GPT 5 + Claude 독립 1)
- 보류: 0 / 버림: 0

## 합의 항목

| # | 항목 | 출처 | 비고 |
|---|---|---|---|
| 1 | A 분류 동의 | GPT | B 트리거 미해당 — 2자 토론 진행 |
| 2 | render_hooks_readme.sh 의존자 인지 | GPT | --count/--by-event 직접 호출, awk -F': ' 파싱 |
| 3 | M2-D (final_check 셸 파서 유지) | Claude → GPT 동의 | M3 이월 |
| 4 | 5-추가 A: render_hooks_readme.sh --dry 검증 | GPT | EVENT_LINE 변경 전과 동일 확인 |
| 5 | 5-추가 B: shadow 기준 변경 — helper↔shell parser 동등성 | GPT | implementation: subprocess 대신 헬퍼 내부 shell-equivalent 함수 (GPT 권고) |
| 6 | 5-추가 C: list_active_hooks.sh stdout byte-exact 회귀 | Claude 독립 | --count/--names/--by-event/--full 4모드 diff -u 0 |

## 비차단 메모 (선택)
- "settings.local.json 부재 시에도 동일 동작" 검증 — 추가하면 더 깔끔, PASS 막지 않음.

## 8단계 검증 (구현 후 모두 PASS 시 커밋)

1. 헬퍼 단독: `--op readme_hook_names` count=31, `--op shadow_diff_readme` match=true
2. list_active_hooks 외부 계약: `--count`=31, `--names | wc -l`=31, `--by-event` 7개 라인, diff 0
3. smoke_test 217/217 ALL PASS, smoke_fast 11/11
4. final_check --fast README/STATUS/settings 모두 31, exit 0
5. drift 재현 회귀
6. render_hooks_readme.sh --dry: COUNT=31, EVENT_LINE 변경 전과 일치
7. shadow_diff_readme: helper Python regex ↔ helper 내부 shell-equivalent 결과 match=true
8. list_active_hooks stdout byte-exact 회귀 (4모드 diff -u 0)

## 다음 행동
즉시 구현 착수.
