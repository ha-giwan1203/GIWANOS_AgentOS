# Round 1 — Claude 종합·설계안

## 양측 합의 (만장일치, pass_ratio_pre = 3/3)

| 쟁점 | Claude R0 | GPT | Gemini | 합의 |
|------|-----------|-----|--------|------|
| H1 | 버림 | 버림 | 버림 | **버림** |
| H2 | 채택(형태 미정) | 조건부 채택 | 채택 | **채택 (구현 형태 합의)** |
| H3 | 부분 채택 | 부분 채택 | 부분 채택 | **부분 채택** |

## H2 구현 형태 (양측 동의)
- **새 hook 추가 금지** (hook 26개 과밀)
- **completion_gate.sh 내부 Stop 단계에 delegation guard Phase 0 최소 복원**
- hook 이벤트: **Stop** (`last_assistant_message` 입력 + `decision: "block"` 반환)
- 정규식 (보수적):
  - 어떻게 할까요 / 진행할까요 / 원하시면 / 선택해 주세요 / A/B 중 선택 / 사용자 결정 대기 / 1단어로 답 / 확인해주시면 진행 / 말씀해주시면 진행
- whitelist (false positive 방지):
  - 토론모드 판정 요청 (통과 / 조건부 / 실패 등)
  - 사용자 명시 선택 요구 ("선택지 줘", "비교해줘", "물어봐")
  - ERP/MES 비가역 1줄 확인 (대상·일자·라인·건수)
- `stop_hook_active=true` 시 무조건 통과 (무한 루프 방지)
- 차단 메시지: "선택 요구로 멈추지 말고, 네 판단을 1줄로 정한 뒤 다음 행동을 제시하라."

## H3 번복 범위 (양측 동의)
- **번복**: "CLAUDE.md 금지 문구 + 메모리 2조건만으로 충분하다"는 하위 가정
- **유지**: R2/R3/R4 폐기, 질문 허용 2조건 축약, C 모드 과승격 완화
- **추가**:
  - SessionStart 짧은 모드 라벨링 (모드 1줄 + 예외 1줄 + 최근 회귀 1줄)
  - CLAUDE.md "1줄 확인 허용" 압축 → "질문 허용은 2개뿐 — ERP/MES 비가역 직전 / 사용자 명시 선택. 그 외 판단 후 진행."

## Gemini 질문 답 (무한 루프 대비)
Stop hook decision:"block" + reason 메시지에 **재응답 가이드라인 동봉**:
```
선택 요구로 멈추지 말고:
1) 현재 모드 [A/B/C/D/E] 다시 출력
2) 네 판단 1줄
3) 다음 행동 1줄
4) (필요 시) ERP/MES 비가역 직전인지 검토
```
- `stop_hook_active=true` 시 2회차 무조건 통과 (Claude 공식 권고)
- 차단 2회 연속 발생 시 incident_ledger 기록 → 정규식 보수화 트리거

## 실행 단계 (plan 갱신)

### Phase 2 (즉시)
1. CLAUDE.md:73 "1줄 확인 허용" 압축 (1조건)
2. SessionStart hook에 모드 라벨링 1줄 등록 (settings.json)

### Phase 3 (단기)
1. `completion_gate.sh` Stop 단계에 delegation guard Phase 0 복원 (정규식 + whitelist + decision:"block" + stop_hook_active 방어)
2. 차단 메시지에 재응답 가이드라인 4줄 동봉
3. 1주일 incident_ledger 측정

### Phase 4 (장기)
1. `feedback_authority_ladder.md` 갱신 (gate 복원 기록 + 세션148 부분 번복)
2. 세션148 합의 재검토 메모리 작성 ("문서만으로 충분 13일 만에 회귀" 실측)
3. commit_gate 캐시 hit 경로 TASKS 갱신 보장 (별건 작업)

## JSON
```json
{
  "turn": 1,
  "mode": "3way",
  "harness": {
    "summary_counts": {"채택": 3, "보류": 0, "버림": 0},
    "채택": [
      {"item": "H1 버림 (자기검열 불충분)", "label": "실증됨", "evidence": "세션148→157 13일 재발", "ref": "feedback_authority_ladder.md"},
      {"item": "H2 채택 (Stop hook + completion_gate 통합 복원)", "label": "실증됨", "evidence": "양측 만장일치 + hook 26개 과밀 실측", "ref": "completion_gate.sh:27~33"},
      {"item": "H3 부분 채택 (세션148 하위 가정만 번복)", "label": "실증됨", "evidence": "양측 동의 + R2-R4 폐기 유지 합리성", "ref": "essentials.md:16~23"}
    ]
  },
  "cross_verification": {
    "gemini_verifies_gpt": {"verdict": "동의", "reason": "신규 훅 증설 없이 completion_gate Stop 복원이 자원·성능 충족"},
    "round_count": 1,
    "max_rounds": 3,
    "skip_65": false,
    "skip_65_reason": "B 분류 (hook gate 신설·정책 분기 변경) 무조건 6-5 유지",
    "claude_delta": "partial",
    "issue_class": "B"
  }
}
```
