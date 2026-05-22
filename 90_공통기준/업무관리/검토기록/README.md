# 검토기록 README

> 목적: Claude 검증과 Codex 실행 사이의 중요 리뷰 결과를 작게 남기는 shadow mode 안내서.
> 비유: 이 폴더는 작업 원장이 아니라, 품질검사 때 남기는 검사표 보관함이다.

## 1. 원칙

- 이 폴더는 **상태 원본이 아니다**.
- 완료/진행/차단 판정은 항상 `90_공통기준/업무관리/TASKS.md`가 우선이다.
- `HANDOFF.md`는 세션 메모, `STATUS.md`는 운영 요약이다.
- 이 폴더는 Claude 검증 또는 Codex Critic 검토를 보조 기록으로 남길 때만 쓴다.

## 2. 파일럿 범위

- 적용 방식: shadow mode
- 적용 횟수: 차기 hook/skill/자동화 변경 작업 1건만
- 판정 기한: 첫 파일럿 작성 후 1주일
- 기한 내 효과 판정이 없으면 폴더 폐기 후보로 본다.

## 3. 기본 기록 파일

작업별 기본 파일은 `review.md` 1개만 둔다.

```text
90_공통기준/업무관리/검토기록/runs/YYYYMMDD_<slug>/review.md
```

- `brief.md`는 기본 생성하지 않는다. 작업 목적과 범위는 `TASKS.md` 하네스 줄을 가리킨다.
- `result.md`는 기본 생성하지 않는다. 실행 결과는 `HANDOFF.md`, git diff, commit 해시를 가리킨다.
- `review.md`는 검증 판정과 재개 위치만 남긴다.

## 4. review.md 최소 양식

```markdown
# Review

- 판정: PASS / FAIL / 보류
- 검증자: Claude / Codex Critic / 기타
- 대상 작업:
- TASKS 하네스 줄:
- 관련 HANDOFF:
- 관련 commit:
- 도메인 룰 위반:
- 금지 위반:
- 검증 증거:
- 재개 위치:
- 다음 행동:
```

## 5. 작성 주체

- Claude가 검증 판정을 내린다.
- Codex가 Claude 판정을 받아 `review.md`에 기록한다.
- Codex Critic은 도메인 의사결정을 하지 않는다.
- 외부 AI/워커/Gemini 호출은 `누구 / 왜 / 입력 / 산출물 / 검증`이 명시된 경우에만 허용한다.

## 6. 도입하지 않는 것

- `TASKS.md`를 대체하는 새 상태 파일
- 자동 디스패처
- 무한 재시도 루프
- close-lite/full 같은 새 lane
- 모든 작업마다 무조건 새 폴더 생성
- 사용자 승인 없는 외부 AI/워커 호출

## 7. 파일럿 판정 기준

파일럿 1건 후 아래를 확인한다.

- 새 세션에서 `review.md`만 읽고 재개 위치를 이해할 수 있는가
- Claude 검증 시간이 줄었는가
- Codex 결과 누락이 줄었는가
- `TASKS/HANDOFF/STATUS`와 상태 충돌이 없는가
- 문서 관리 부담이 늘지 않았는가

효과가 없으면 이 폴더는 폐기한다. 효과가 있으면 `CODEX_작업지시_템플릿.md`에 사용 조건 1~2줄만 추가한다.
