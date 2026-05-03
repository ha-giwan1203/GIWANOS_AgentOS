# /map-scope — 사고 품질 선언 (고위험 수정 전 필수)

고위험 수정 작업 전에 영향 범위를 선언한다.
이 커맨드를 실행하면 map_scope.ok 증거가 생성되어 evidence_gate를 통과할 수 있다.

## 실행 절차

1. 아래 3줄을 반드시 출력한다:
   - **변경 대상**: 수정할 파일/함수/구조 목록
   - **연쇄 영향**: 이 변경이 다른 파일/시스템에 미치는 영향
   - **후속 작업**: 변경 후 필요한 검증/갱신/테스트

2. 3줄 출력 후 map_scope.ok 증거를 적립한다:
```bash
source .claude/hooks/hook_common.sh
SESSION_KEY=$(session_key)
mkdir -p "$STATE_EVIDENCE/$SESSION_KEY/proofs"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$STATE_EVIDENCE/$SESSION_KEY/proofs/map_scope.ok"
```

3. 이후 고위험 수정(Write/Edit/MultiEdit) 가능

## 언제 필요한가
- hook/gate/검증 로직 수정
- 기준 문서(CLAUDE.md, settings) 변경
- 구조 변경, 리팩터, 마이그레이션
- 다중 파일 동시 수정
- 파이프라인/스키마/컬럼 변경
