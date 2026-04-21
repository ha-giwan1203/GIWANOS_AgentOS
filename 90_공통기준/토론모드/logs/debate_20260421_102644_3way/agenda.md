# 3자 토론 의제 — Notion 동기화 정상화 (세션86)

- 모드: 3way (Claude × GPT × Gemini)
- API 모드: β안-C 범위 (Step 6-2/6-4 단발 검증만 API 병렬, 본론·종합은 웹 UI)
- 기준 시각: 2026-04-21 10:26 KST
- 로그 경로: `90_공통기준/토론모드/logs/debate_20260421_102644_3way/`

## 배경 (실측)

세션45(2026-04-14) 이후 세션86(2026-04-21)까지 **Notion 동기화 7일 / 41세션 미작동**.

- 📁 부모 페이지 (`331fee67...bc07`) — 2026-04-13 세션36 상태로 멈춤
- 📊 STATUS 페이지 (`...94a`) — 세션45 갱신
- ✅ TASKS 페이지 (`...db8`) — 세션45 갱신

## 근본 원인 (진단 결과)

**설계 vs 구현 불일치**:

| 계층 | 상태 | 근거 |
|------|------|------|
| `notion_sync.py` (815줄) | ✅ 완전 구현 | 정상 동작 가능 |
| `notion_config.yaml` | ✅ 토큰·페이지ID 유효 | — |
| `.claude/commands/finish.md:35-39` | "3.5단계 Notion 동기화" 명시 | MCP `notion-update-page` 또는 스크립트 호출 | 
| `.claude/commands/share-result.md` | ❌ **Notion 호출 코드 0줄** | finish가 위임한 경로에 구현 누락 |
| `watch_changes.py:367-386` Phase 5 | 자동 파일 감지 경로에서만 호출 | 수동 `/finish`는 watch_changes 경유 안 함 |

실행 흐름: `/finish` → `share-result` 위임 → (Notion 단계 사라짐) → 사용자 보고.

## 복구안 후보

### A안 — share-result.md에 3.5단계 구현 추가
- 장점: finish.md 설계 원형 유지, 최소 수정
- 단점: `/share-result` 단독 호출 시에도 Notion 동기화 트리거됨 (의도와 다를 수 있음)
- 구현: share-result.md Step 3과 4 사이에 `notion_sync.py` 호출 1블록 삽입

### B안 — finish.md에서 3.5단계를 share-result 위임 밖으로 분리
- 장점: /finish 마감 루틴에서만 Notion 동기화 트리거 (범위 명확)
- 단점: finish.md 리팩터 필요, share-result 단독 호출 시 Notion 미동기화 유지
- 구현: finish.md에 Notion 호출 독립 단계 명시 + share-result 진입 전후 위치 결정

### C안 — watch_changes.py Phase 5를 공통 모듈로 추출 후 /finish에서 재호출
- 장점: 자동(watch_changes)·수동(/finish) 양쪽에서 동일 로직 공유, DRY
- 단점: 리팩터 범위 확대, 3자 토론이 결국 1개 의제로 수렴 안 될 수 있음
- 구현: `notion_sync.py`에 `sync_from_finish()` API 추가 + watch_changes.py에서도 동일 API 호출

## 판정 기준 (각 모델에게 요청)

1. 세 후보 중 어느 안이 현재 저장소 구조·제약에서 가장 적합한가
2. 누락된 경로·파일·조건 있는가 (독립 검증)
3. 3.5단계 실행 시 실패 fallback 정책 필요한가 (토큰 만료·API 레이트리밋·네트워크 단절)
4. 사라진 7일/41세션 분량을 "소급 동기화"할 것인가, "다음 세션부터 정방향"만 적용할 것인가
5. 재발 방지 장치 필요 여부 (smoke_test·hook 경고)

## 절차

1. Round 1 본론: GPT·Gemini 웹 UI 본론 수신 (6-1, 6-3)
2. Round 1 교차 검증: β안-C API 병렬 (6-2, 6-4)
3. Round 1 Claude 종합 (6-5, skip 조건 재검토)
4. pass_ratio ≥ 2/3 시 채택, 미달 시 재라운드 (최대 3회)
5. 채택 시 구현 → git commit → push → 양측 최종 판정 수령
6. 양측 통과 시 Notion 실측 동기화 수행 + 세션 보고
