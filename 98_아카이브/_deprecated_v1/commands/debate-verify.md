# /debate-verify — 3자 토론 합의 서명 수동 검증 (--dry-run)

3자 토론(3way) 산출물의 서명 정합성을 **커밋 전에** 수동으로 미리 확인한다.

## 인자
- 선택: 특정 로그 디렉토리 경로. 미지정 시 최신 `debate_*_3way/` 자동 선택.

## 사용 시점
- 커밋 직전 — 실패를 사전 방지
- debate-mode Step 5 완료 직후 — step5 파일 누락 여부 확인
- Phase 1 경고 incident 재현 확인용

## 실행

```bash
# 1. 대상 디렉토리 결정
TARGET="${1:-}"
if [ -z "$TARGET" ]; then
  TARGET=$(ls -dt "90_공통기준/토론모드/logs"/debate_*_3way 2>/dev/null | head -1)
fi

# 2. gate 스크립트를 직접 호출 (dry-run)
#    - git commit 이벤트를 시뮬레이션
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"[3way] dry-run\""}}' | \
  bash .claude/hooks/debate_verify.sh
EXIT=$?

# 3. 결과 요약
echo "---"
echo "대상: $TARGET"
echo "종료 코드: $EXIT (0=통과, Phase 1은 실패여도 0)"
echo "incident_ledger.jsonl 최근 debate_verify 기록:"
grep '"tag":"debate_verify"' .claude/incident_ledger.jsonl 2>/dev/null | tail -3
```

## 출력 해석
- 통과: `[debate_verify]` 출력 없음 + exit 0
- 실패: `[debate_verify] ⚠️ ...` 라인 출력 + 항목별 결함 + Phase 1이면 exit 0, Phase 2이면 exit 2

## 주의사항
- Phase 1 운영 중에는 경고만 나오고 커밋은 막히지 않는다
- 재현 테스트 시 `incident_ledger.jsonl`에 항목이 누적됨 — 잔여 incident 감시에 반영
- 실물 git commit이 아니라 시뮬레이션이므로 실제 repository 상태는 변경되지 않음
