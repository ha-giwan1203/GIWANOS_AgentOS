# Round 1 — Claude 독자 답안 (Step 6-0 선행 작성)

## 의제
D0 스케줄러 사후 검증 + 원인 분류 + 자동 재실행 정책 — plan 합의 후 즉시 구현

## 결론 1줄
**원인 분류 5종 + RETRY_OK 백오프(즉시/5분/15분/30분) + RETRY_NO 0회 + 선행 dedupe + lock 파일은 합리적이나, race condition 방지를 위해 schtasks 상태 확인 선행 필수 + UNKNOWN 1회 재시도는 너무 약함(2회 권장).**

## 주장 5개 + 라벨 + 증거 + 약점

### 주장 1 — 원인 분류 5종은 충분, 단 추가 1종 검토 필요
- **라벨**: 실증됨
- **증거**: 본 저장소 실증 5종(timeout/5xx/네트워크/OAuth 정착/Chrome CDP 미기동) + xlsx 미존재 + 마스터 불일치 = 7종 모두 세션115·121·124·121·115 등에서 실증
- **추가 후보**: ERP 응답 200인데 ERROR_FLAG=Y (세션104 xlsx 포맷 버그 패턴) — RETRY_OK인지 RETRY_NO인지 모호. 보수적으로 RETRY_NO + 알림 권장
- **약점**: "마스터 정보 불일치"는 분류 어려움 (로그에 "품번 매칭 실패" 같은 일관 키워드 없음)

### 주장 2 — 백오프 즉시/5/15/30분 적정, 누적 50분 한계
- **라벨**: 실증됨
- **증거**: ERP 일시 부하 회복 시간은 통상 5~15분. 30분 시도 후에도 실패하면 영구 원인 가능성 ↑
- **약점**: morning 07:10 + 검증 07:30 + 재시도 4회(즉시·5·15·30) = 누적 시도 종료 08:25. 업무 시작 시간(09:00) 전 사용자 인지 가능

### 주장 3 — UNKNOWN 1회 재시도는 부족, 2회로 늘리는 것이 안전
- **라벨**: 환경미스매치
- **증거**: 분류 실패 = 새 패턴 가능성. 1회 재시도로 안 풀리면 정말 영구 원인일 가능성 + 재시도 가치 있는 일시적 원인일 가능성 5:5. 1회 재시도는 후자에 너무 보수적
- **권장**: UNKNOWN 2회 재시도 (즉시 + 5분 후) → 그 후 즉시 알림으로 사용자가 분류 가능
- **약점**: 2회로 늘려도 ERP 부하 누적은 미미하나, "분류기 개선 동기" 측면에선 1회가 더 자극적

### 주장 4 — dedupe 선행은 필수지만 race condition 방지를 위해 schtasks 상태 확인 선행 필수
- **라벨**: 실증됨
- **증거**: morning 07:10 작업이 ERP 5xx 응답으로 selectList 단계에서 멈춰 진행 중인 상태에서 verify 07:30이 dedupe + 재실행하면 morning이 늦게 응답해서 중복 등록 가능
- **방법**: schtasks /query /TN "D0_SP3M3_Morning" /v 결과에서 "Last Run Time" + "Last Result" + "Status" 확인. Status="Running"이면 verify 5분 추가 대기 후 재확인. 그래도 Running이면 morning 작업 강제 종료 후 dedupe + 재실행
- **약점**: schtasks 강제 종료(schtasks /end)는 morning 작업이 ERP 통신 중간에 끊는 것이라 추가 잔존 위험 ↑

### 주장 5 — lock 파일 atomic은 Windows에서 까다로움 — Python `os.O_EXCL` 권장
- **라벨**: 일반론
- **증거**: 파일 존재 체크 + 생성은 race condition (Python에서 if not exists then create 사이 다른 프로세스 끼어듦). `os.open(path, os.O_CREAT | os.O_EXCL)`이 atomic
- **약점**: Windows에서도 작동하나 SMB 마운트 등 일부 파일시스템에서 보장 안 됨. 본 저장소는 로컬 NTFS이므로 무관

## 보완 방향 — 구체 설계 (모드 C plan)

### Phase 1 — 즉시 구현
1. `90_공통기준/스킬/d0-production-plan/verify_run.py` (Python ~250줄)
2. argparse: `--session morning|night --line SP3M3 [--max-retry 4] [--max-elapsed-min 50] [--dry-run]`
3. 로직:
   - schtasks 상태 확인 (Running이면 5분 대기 1회, 그래도 Running이면 강제 종료 + 알림)
   - 로그 파일 존재 + 마커 검증
   - 원인 분류 (grep 기반)
   - 정책별 재시도 (백오프)
   - 매 재시도 전 dedupe 1회
   - lock 파일 (`os.O_CREAT | os.O_EXCL`)
   - 알림 (Slack MCP — `mcp__8d2abc6d-9827-4a8a-91b9-99dce8a2ee5d__slack_send_message`)
4. 사용자 안내: README 또는 SKILL.md "Phase 7 Verify" 섹션에 schtasks /create 명령 1줄

### Phase 2 — 1주 운영 후 결정 (이월)
- 분류기 개선 (UNKNOWN 패턴 누적 시 신규 분류 추가)
- 야간 작업 verify 추가 (Phase 1은 morning만)

## 반대 안 예상 약점 / 양측 반박 가능성

- **GPT 예상 반박**: "morning 작업이 진행 중일 때 schtasks /end로 강제 종료는 비가역 ERP 통신 단절. dedupe로도 안 잡히는 잔존 가능성. lock·강제 종료 대신 verify는 점검만 하고 사용자 알림으로 종결하는 게 안전"
- **Gemini 예상 반박**: "원인 분류 5종은 grep 기반이라 false positive 위험. 차라리 LastResult 종류만으로 RETRY_OK/NO 분기하고 분류기 자체를 단순화"
- **공통 반박**: "백오프 간격 30분이 너무 짧음. 같은 5xx 원인이면 30분으론 회복 안 될 수도. 최대 시도 횟수 4회면 60분으론 부족"

## 착수·완료·검증 조건
- **착수**: pass_ratio ≥ 2/3 채택 시 모드 C plan 파일화 + 즉시 구현
- **완료**: verify_run.py 작성 + smoke (--dry-run) 통과 + commit + push + 사용자 schtasks 등록 안내
- **검증**: 다음 morning 07:10 + verify 07:30 1주 운영 → hook_log에 발화 패턴 누적 → 1주 후 분류기 정합성 보고

## claude_delta 예상
- 양측 본론 수령 전 partial/major 가능성

## issue_class
- **B** — 새 스크립트·새 스케줄러·새 알림 경로 = 시스템 흐름·판정 변경
