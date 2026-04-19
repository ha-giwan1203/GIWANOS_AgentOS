---
name: token-threshold-warn
description: >
  저장소 문서 비대화 사전 감시 스킬. TASKS.md / HANDOFF.md / MEMORY.md 인덱스·개별 메모리 파일 수·
  incident_ledger.jsonl 바이트를 세션 시작 시 측정하고 임계치 초과를 경고한다.
  차단하지 않고 권고만 수행한다. Claude Code 내장 /cost(세션 누적 비용)와 보완 관계 —
  이 스킬은 세션 시작 전 정적 문서 무게를 측정한다.
grade: advisory
---

# Token Threshold Warn

세션68(2026-04-18) Claude Code 영상분석 3자 토론(Claude×GPT×Gemini, pass_ratio 1.00)에서 합의된
저장소 문서 비대화 감시 스킬. 세션79(2026-04-20)에 Phase 1 실물 구현.

## 목적

- G-ERP 도메인 특성상 TASKS·STATUS 파일이 비대해져 Claude 지시 인지율 저하 위험
- 토크나이저 오버헤드 없이 **라인수·파일수·바이트** 기준으로 사전 경고
- 차단 없음 — 제조업 자동화 환경(정산·라인배치·MES)에서 세션 중단 리스크 회피

## 임계치 (3자 합의 고정)

| 대상 | 경고 | 강경고 | 단위 |
|------|------|-------|------|
| TASKS.md | 400 | 800 | 라인수 |
| HANDOFF.md | 500 | 800 | 라인수 |
| MEMORY.md 인덱스 | 120 | 200 | 라인수 |
| 메모리 개별 파일 총계 | 60 | 100 | 파일 개수 |
| incident_ledger.jsonl | 1MB | 3MB | 바이트 |

**근거**: 현재 규모(TASKS 200·HANDOFF 400 수준 가정) 대비 여유 확보 + 모델 지시 100% 인지 가독성 한계선 고려. 1개월 운영 후 실제 경고 빈도 기반 재조정.

## 구현 로드맵

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | SessionStart hook 경고 출력 | 완료 (세션79) |
| 2 | Stop hook 증가량 기록 (`token_threshold_delta.sh`) | 1주 운영 후 진입 |
| 3 | `/context` 공식 명령 통합 리포트 (context7 MCP) | 선택 |

## 실행 지점

### Phase 1 — SessionStart (현재)
- hook: `.claude/hooks/token_threshold_check.sh`
- 배선: `.claude/hooks/session_start_restore.sh` 내부(`doctor_lite` 직후)
- 등급: **advisory** (hook_common.sh `hook_advisory` 패턴, `exit 0` 강제)

### Phase 2 — Stop hook (보류)
- hook: `.claude/hooks/token_threshold_delta.sh` (미구현)
- 세션 종료 시 동일 측정 + 증가량 `incident_ledger.jsonl`에 `{"tag":"token_threshold", "file":"...", "delta":"+N줄"}` 기록
- **도입 조건**: Phase 1 운영 로그에서 경고 발생 패턴 안정기 확인 (경고 빈도 주간 변동 < 20%)

## 수동 호출

```bash
# 기본 실행 (실제 파일 측정)
bash .claude/hooks/token_threshold_check.sh

# 테스트 override (실제 파일 건드리지 않고 mock)
TOKEN_THRESHOLD_TASKS_OVERRIDE=/tmp/mock_tasks.md \
TOKEN_THRESHOLD_HANDOFF_OVERRIDE=/tmp/mock_handoff.md \
TOKEN_THRESHOLD_MEMORY_OVERRIDE=/tmp/mock_memory_dir \
TOKEN_THRESHOLD_INCIDENT_OVERRIDE=/tmp/mock_incident.jsonl \
bash .claude/hooks/token_threshold_check.sh
```

## 출력 형식

```
[token_threshold] ⚠️ 2건 초과:
  [STRONG] TASKS.md: 1981 / 800줄 — 감축 권고: 1181줄. /memory-audit 또는 98_아카이브/ 이동 검토
  [WARN] HANDOFF.md: 620 / 500줄
```

경고가 없으면 **빈 출력**(세션 시작이 깨끗하게 유지).

## 정책

### [MUST]
- 경고만, 차단 기능 도입 금지
- 측정: 마크다운·텍스트 = 라인수, 로그·데이터 = 바이트, 디렉토리 = 파일 개수
- SessionStart는 빠르게 유지 (토큰 근사치 측정 같은 오버헤드 금지)

### [NEVER]
- 자동 아카이브 이동 — 시스템이 낡은 기록·현 맥락 임의 분리 시 사고 가능
- 토큰 근사치 계산 — 토크나이저 오버헤드, 결정성 부족
- hook 내부에서 사용자 승인 요청

### [SHOULD]
- 강경고 3회 연속 누적 시 `hook_incident doc_drift` 자동 기록
- 강경고 대상 파일별 감축 수단 제안 (`/memory-audit`, `98_아카이브/`, `incident_repair.py --archive`)

## 튜닝 가이드

- 경고 빈도가 주 3회 이하로 안정되면 임계치 상향 불필요
- 정상 운영 중에도 경고가 지속 출력되면 해당 대상 임계치 상향 (상한 +20%) 또는 정리 작업 우선
- 강경고는 **1개월 누적 허용 0회** 원칙 — 즉시 감축 대상

## 관련 문서

- 토론 로그: [90_공통기준/토론모드/logs/debate_20260418_164115_3way/](../../토론모드/logs/debate_20260418_164115_3way/)
- 합의안: `round1_claude_synthesis.md`
- 영상 원본: 2rzKCZ7XvQU (Claude Code 명령어 매뉴얼)
- 관련 규정: CLAUDE.md "hook 등급" 섹션, `.claude/hooks/README.md`

## 수동 호출 우선순위 (업무 중)

| 상황 | 권장 조치 |
|------|----------|
| TASKS/HANDOFF strong | TASKS 상단 최근 세션 블록만 남기고 98_아카이브로 이관 |
| MEMORY 인덱스 strong | `/memory-audit` 실행 → 중복/구식 메모리 통합 |
| 메모리 파일 strong | 같은 주제 파일 통합, 사용 빈도 낮은 항목 삭제 |
| incident strong | `python3 .claude/hooks/incident_repair.py --archive` |

## 실패 대응

- hook 실행 실패(exit 1) 시에도 세션은 계속 (advisory 등급)
- 파일 접근 불가 시 조용히 skip (stderr 무시)
- 경로 override 환경변수 지원으로 smoke_test 격리 보장
