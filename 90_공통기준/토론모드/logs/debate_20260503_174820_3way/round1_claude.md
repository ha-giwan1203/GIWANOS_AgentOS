# Round 1 — Claude 독자 답안 (선행 작성, 6-0)

> NEVER 생략. GPT/Gemini 본론 수령 전 작성.
> 작성 시각: 2026-05-03 17:48 KST

## 의제

Claude Code의 sandbox/permission 영구 해제(`defaultMode: bypassPermissions` + `skipDangerousModePermissionPrompt: true`)를 진행해야 하는가?

## 결론 1줄

**영구 해제 보류. 단계적 해법 권고: (1) `additionalDirectories` 시도 → (2) 실패 시 세션 한정 `--dangerously-skip-permissions` → (3) 영구 해제는 최후.**

## 주장 (5개 + 라벨 + 증거)

### 주장 1 — 영구 bypass는 본 환경(ERP/MES 비가역 작업)에 부적합

- 라벨: **환경미스매치**
- 증거:
  - CLAUDE.md "삭제 금지 목록" — 운영 중 .bat·.ps1·.py / 기준 원본 엑셀 / 최종 제출본 / 98_아카이브 / 마이그레이션 증적
  - `90_공통기준/erp-mes-recovery-protocol.md` 존재 — 비가역 사고 복구 프로토콜이 별도 운영됨
  - 메모리 `feedback_settlement_mistakes.md` — 정산 작업 실수 누적 기록
- 함의: "삭제·이동·rm·git push --force" 등 비가역 명령의 prompt 자동 통과는 사고 확률을 직접 증가시킨다.

### 주장 2 — 셀프 escalation 차단은 정상 동작

- 라벨: **실증됨**
- 증거: 직전 시도에서 거부 사유 "Self-modification of agent's global settings to set defaultMode bypassPermissions — disables approval gates globally"
- 함의: AI가 자기 권한 게이트를 스스로 푸는 것은 보안 모델 전체를 무너뜨림. 사용자 직접 수정만 인정하는 것은 의도된 설계.

### 주장 3 — 사용자 진의는 "이번 작업 막힘"이지 "영구 bypass"가 아닐 수 있음

- 라벨: **일반론** (사용자 의도 추정)
- 증거: 사용자 발화 변천
  - "내가 설정해 뒸는대 왜 안되지?" — 권한 설정의 동작 기대
  - "이렇게 되면 작업하기가 너무 불편한대" — 일반화된 불편함 표명
  - 영구 해제를 명시 요청한 발화는 "3"(옵션 선택) 1회뿐이며, 옵션 자체가 Claude가 제시한 것
- 함의: 권위 사다리 비대칭 메모리(`feedback_authority_ladder.md`)에 따르면 사용자 명시 발화는 1순위지만, 옵션 선택형 응답은 "기존 정책 먼저 확인 후 결정 요청"(`feedback_check_existing_policy_first.md`) 위반 가능.

### 주장 4 — `additionalDirectories`가 정확한 해결책일 가능성

- 라벨: **구현경로미정**
- 증거: `~/.claude/settings.json` 스키마에 `permissions.additionalDirectories: ["/extra/dir"]` 존재. 작업 디렉토리 외 추가 디렉토리를 sandbox scope에 포함시키는 옵션.
- 미검증: Windows 환경 + Claude Code sandbox 레이어와의 상호작용. 실증 필요.
- 함의: bypass 없이도 사용자가 원하는 디렉토리(예: 다른 게임 폴더)만 추가 허용 가능하면 글로벌 위험 없이 해결.

### 주장 5 — 단계적 해법이 cost/risk 균형에 맞음

- 라벨: **과잉설계 회피**
- 증거: 본 토론 의제 자체가 "영구 vs 현재" 이분법. 그러나 스키마는 더 세밀한 옵션 제공:
  - `additionalDirectories` (좁은 범위 추가)
  - `--dangerously-skip-permissions` 플래그 (세션 한정)
  - `defaultMode: "acceptEdits"` (편집만 자동 통과, 위험 명령은 prompt 유지)
  - `defaultMode: "bypassPermissions"` (전부 통과)
- 함의: 위험도-편의성 trade-off 곡선에서 "최우측(bypass)"으로 직행하지 말고 "최좌측(현재)"에서 한 단계씩 이동.

## 반대 안 예상 약점

- **영구 해제 안 (사용자 직접 옵션)**:
  - 권위 사다리 메모리: 사용자 명시 발화 = 1순위. Claude가 "위험합니다"로 거부할 명분 약함
  - 사용자가 자기 PC 권한을 푸는 결정 — 본인 영역
- **일회성 플래그 안**:
  - 매번 재시작 부담. 사용자 "불편하다" 표명과 정면 충돌
  - 본 의제(파운데이션/뮤뮤 검색) 자체가 1회성 작업이라면 적합하지만, 향후 비슷한 요구가 빈번하면 비효율
- **additionalDirectories 안**:
  - sandbox 레이어와의 상호작용 미검증 → 실패 가능
  - "어느 디렉토리를 추가해야 하는지" 사용자가 지정해야 함 (현재 파운데이션/뮤뮤 위치 모름)

## 착수/완료/검증 조건

- **착수 조건**: 사용자가 단계적 해법 또는 영구 해제 중 명시 선택
- **완료 조건**: 선택한 해법으로 작업 디렉토리 외부 검색 PASS
- **검증 조건**:
  - 1차: 권한 설정 변경 후 `Get-ChildItem` 등 외부 경로 접근 명령 출력 확인
  - 2차: hook 게이트(`block_dangerous`, `protect_files`)가 해제 이후에도 정상 동작하는지 확인 (안전망 잔존 여부)
  - 3차: ERP/MES 작업 시뮬레이션에서 비가역 명령이 prompt 없이 통과되는지 확인 (riske 실증)

## 메타 코멘트

본 의제는 **매우 메타적**이다 — Claude가 자기 권한 풀기를 GPT/Gemini와 토론. 실제 결정권은 사용자에게만 있고, 두 외부 모델이 검증할 수 있는 것은 "단계적 해법의 합리성"과 "ERP 환경에서의 위험도 평가"다. claude_delta 측정 시 양측 답변에 종속되지 않은 독립 의견(본 문서)을 기준선으로 삼는다.
