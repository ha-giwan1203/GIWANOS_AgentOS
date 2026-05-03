# token-threshold-warn — MANUAL

> 상세 임계치/구현/실패대응. SKILL.md는 호출 트리거 + 80줄 요약만.

## 배경
세션68(2026-04-18) Claude×GPT×Gemini 3자 토론(pass_ratio 1.00) 합의. 세션79(2026-04-20) Phase 1 실물 구현.

## 목적
- G-ERP 도메인 특성상 TASKS·STATUS 비대화로 Claude 인지율 저하 위험
- 토크나이저 오버헤드 없이 라인수·파일수·바이트로 사전 경고
- 차단 없음 — 제조업 자동화 환경(정산·라인배치·MES)에서 세션 중단 회피

## 임계치 (3자 합의 고정)
| 대상 | 경고 | 강경고 | 단위 |
|------|------|-------|------|
| TASKS.md | 400 | 800 | 라인수 |
| HANDOFF.md | 500 | 800 | 라인수 |
| MEMORY.md 인덱스 | 120 | 200 | 라인수 |
| 메모리 개별 파일 총계 | 60 | 100 | 파일 개수 |
| incident_ledger.jsonl | 1MB | 3MB | 바이트 |

근거: 현재 규모(TASKS 200·HANDOFF 400) 대비 여유 + 모델 지시 100% 인지 가독성 한계선. 1개월 운영 후 재조정.

## 구현 로드맵
| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | SessionStart hook 경고 | 완료 (세션79) |
| 2 | Stop hook 증가량 기록 | 1주 운영 후 진입 |
| 3 | `/context` 공식 명령 통합 (context7 MCP) | 선택 |

## 실행 지점

### Phase 1 — SessionStart
- hook: `.claude/hooks/token_threshold_check.sh`
- 배선: `.claude/hooks/session_start_restore.sh` 내부 (`doctor_lite` 직후)
- 등급: advisory (`hook_advisory` 패턴, exit 0 강제)

### Phase 2 — Stop hook (보류)
- hook: `.claude/hooks/token_threshold_delta.sh` (미구현)
- 종료 시 동일 측정 + 증가량 incident_ledger.jsonl 기록
- 도입 조건: Phase 1 경고 빈도 주간 변동 < 20% 안정기

## 수동 호출
```bash
bash .claude/hooks/token_threshold_check.sh

# 테스트 override
TOKEN_THRESHOLD_TASKS_OVERRIDE=/tmp/mock_tasks.md \
TOKEN_THRESHOLD_HANDOFF_OVERRIDE=/tmp/mock_handoff.md \
TOKEN_THRESHOLD_MEMORY_OVERRIDE=/tmp/mock_memory_dir \
TOKEN_THRESHOLD_INCIDENT_OVERRIDE=/tmp/mock_incident.jsonl \
bash .claude/hooks/token_threshold_check.sh
```

## 출력 형식
```
[token_threshold] ⚠️ 2건 초과:
  [STRONG] TASKS.md: 1981 / 800줄 — 감축 권고: 1181줄. /memory-audit 또는 98_아카이브/ 이동
  [WARN] HANDOFF.md: 620 / 500줄
```
경고 없으면 빈 출력.

## 정책

### MUST
- 경고만, 차단 도입 금지
- 측정: 마크다운 = 라인수, 로그 = 바이트, 디렉토리 = 파일 개수
- SessionStart 빠르게 유지 (토큰 근사치 측정 금지)

### NEVER
- 자동 아카이브 이동 (시스템이 낡은 기록·현 맥락 임의 분리 시 사고)
- 토큰 근사치 계산 (오버헤드, 결정성 부족)
- hook 내부 사용자 승인 요청

### SHOULD
- 강경고 3회 연속 시 `hook_incident doc_drift` 자동 기록
- 강경고 대상 파일별 감축 수단 제안

## 튜닝 가이드
- 경고 빈도 주 3회 이하 안정 → 임계치 상향 불필요
- 정상 운영 중 지속 경고 → 임계치 +20% 또는 정리 우선
- 강경고 1개월 누적 허용 0회 — 즉시 감축

## 수동 호출 우선순위
| 상황 | 권장 조치 |
|------|----------|
| TASKS/HANDOFF strong | 최근 세션 블록만 남기고 98_아카이브 이관 |
| MEMORY 인덱스 strong | `/memory-audit` 중복/구식 통합 |
| 메모리 파일 strong | 같은 주제 통합, 사용 빈도 낮은 항목 삭제 |
| incident strong | `python3 .claude/hooks/incident_repair.py --archive` |

## 실패 대응
- hook 실행 실패(exit 1) 시에도 세션 계속 (advisory)
- 파일 접근 불가 시 조용히 skip (stderr 무시)
- 경로 override 환경변수로 smoke_test 격리

## 관련 문서
- 토론 로그: `90_공통기준/토론모드/logs/debate_20260418_164115_3way/`
- 합의안: `round1_claude_synthesis.md`
- 영상 원본: 2rzKCZ7XvQU (Claude Code 명령어 매뉴얼)
- 관련 규정: `.claude/rules/essentials.md` "hook 등급" 섹션
