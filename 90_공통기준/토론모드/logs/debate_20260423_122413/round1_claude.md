# Round 1 — Claude 초안 설계 (본론 질문 전)

## 의제
1. `final_check.sh` 2축 분리 — 실행 안전 vs 문서 정합
2. 파싱 공통층 Python 헬퍼화 — list_active_hooks / final_check / risk_profile_prompt 손파싱 통합

두 안건은 **연쇄**: 헬퍼 먼저면 final_check 2축 분리 시 공용 헬퍼 활용 가능.

## Claude 초안 설계 (비판 대상)

### 파싱 헬퍼 모듈 (단계 1)
- 위치: `.claude/scripts/parse_helpers.py`
- 기능:
  - `parse_hooks_from_settings(json_paths) -> list[dict]` (team+local union)
  - `count_hooks_in_readme(md_path) -> int`
  - `count_hooks_in_status(md_path) -> int`
  - `parse_domain_registry(yaml_path) -> dict`
- 호출 패턴: 각 shell 훅에서 `$PY_CMD .claude/scripts/parse_helpers.py --op <op> [args]` 형태

### final_check 2축 분리 (단계 2)
- `final_check_runtime.sh`: **실행 안전**
  - hook 개수 정합 / settings 실파일 존재 / smoke_fast / write_marker / python3 잔존 / block_dangerous / hook_log 참조
- `final_check_docs.sh`: **문서 정합**
  - TASKS/HANDOFF/STATUS 날짜·세션 동기화 / README-STATUS 훅 수 일치 / AGENTS_GUIDE 드리프트
- 기존 `final_check.sh`: **래퍼로 축소** (두 축 순차 호출, exit 코드 OR, 하위호환)

### 마일스톤 3가지 대안

| 순서 | M1 | M2 | M3 | M4 | 특징 |
|------|----|----|----|----|------|
| **A (Claude 추천)** | 헬퍼 신설 + `list_active_hooks.sh` 전환 | `final_check.sh` 헬퍼 전환 | 2축 분리 | `risk_profile_prompt.sh` 전환 | 점진적, 롤백 용이 |
| **B** | 2축 분리 먼저 | 각 축 내 최소 파싱만 유지 | 헬퍼 후속 공통화 | — | 분리 즉효, 헬퍼 범위 최소 |
| **C** | 1 커밋 동시 반영 | — | — | — | 빠르지만 롤백 난도 ↑ |

### 리스크 식별
- **SPOF**: 단일 헬퍼 버그 = 모든 훅 파싱 실패 → 완화: 헬퍼 자체 smoke_test 섹션 추가 + fallback 유지
- **Latency**: subprocess 호출 증가 → hook 지연. 완화: 헬퍼 내부 argparse 경량화 + 결과 캐싱 (write_marker 패턴 응용)
- **Python 의존**: PY_CMD fallback 이미 세션93 반영 완료 → 신규 리스크 없음

## 3자 검토 대상 (GPT에게 질문)
1. 단계 분할 타당성 (SPOF·의존 순서·롤백)
2. 마일스톤 A/B/C 중 최적안
3. 헬퍼 함수 시그니처 누락·과잉 (특히 domain_registry 파싱 대상 적절성)
4. 2축 분리 경계 — `write_marker` / skill_instruction_gate 연관 항목은 어느 축?
5. 위험 완화 추가 조치

## 판정 요청
통과 / 조건부 통과 / 실패 중 하나. 한국어로만.
