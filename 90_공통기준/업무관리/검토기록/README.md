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

## 8. Codex -> Claude 현재 세션 요청 파일럿

토론모드의 재사용 대상은 브라우저 자동화가 아니라 `요청 -> 응답 -> 판정 -> 기록` 흐름이다.

- 브라우저 경로(`gpt-send`, `gpt-read`, CDP Chrome)는 이 파일럿에 사용하지 않는다.
- 고정 Claude 방을 만들지 않는다.
- 사용자가 열어둔 Claude Code/Claude CLI 세션을 우선 현재 브레인 세션으로 본다.
- 세션 식별은 `claude --continue` 또는 `claude --resume <세션ID>` 계열을 후보로 둔다.
- Claude 현재 세션을 쓰려는 작업은 사용자 진술을 기다리지 않고 Codex가 먼저 세션 존재를 확인한다.
- 일반 sandbox 프로세스 조회에서 창 목록이 비어도 세션 없음으로 확정하지 않는다.
- 입력/제출/응답 회수가 필요한 경우에는 GUI 권한 프로세스 조회까지 수행한 뒤 세션 없음 여부를 판단한다.
- 재확인 뒤에도 세션이 확인되지 않으면 새 세션을 몰래 만들지 않고 `보류`로 기록한다.
- `claude -p` 단발 호출은 Codex stdout으로 돌아오는 검토에는 쓸 수 있지만, 사용자가 보고 있는 Claude 채팅창에 반드시 표시된다고 보지 않는다.
- 실제 호출 전에는 입력/목적/범위/산출물/검증 방법을 검토요청문에 적는다.
- Claude 응답은 Codex가 `review.md` 또는 `HANDOFF.md`에 받아쓴다.

Codex 직접 채팅이 발생했을 때도 역할은 바뀌지 않는다. 실행은 Codex가 끝내고, 판단/설계/검증이 끼면 Claude로 반환한다.

| 상황 | 처리 |
|------|------|
| 파일 패치, 코드 수정, 스크립트 실행, 엑셀/HTML/PDF 산출물 생성 | Codex 계속 |
| 브라우저 수집, 이미지 시안, 반복 스크립트, `TASKS/HANDOFF/STATUS` 갱신, commit/push 실행 | Codex 계속 |
| 룰/`CLAUDE.md`/hook/skill/메모리 설계 변경 | Claude 반환 |
| 정산/라인배치/MES/D0 등 비가역 도메인 판단 가능성 | Claude 반환 |
| 산출물 정합성 검증, 도메인 룰 위반 검출 | Claude 반환 |
| GPT/Gemini 토론, 작업 범위/우선순위 판단 모호 | Claude 반환 |
| 신규 구조 생성 여부 판단 | Claude 반환 |

반환 형식:

```text
[반환] 사유 / 원 요청 / Codex가 본 쟁점
```

Codex 작업지시 종료 마커는 기존 `AGENTS.md`와 맞추기 위해 `[NEEDS_CLARIFICATION]`을 유지한다.

검토요청문 기본형:

```markdown
# Claude 검토 요청

- 요청자: Codex
- 목적:
- 사용자 원지시:
- Codex 판단:
- 변경/검토 대상:
- 금지할 것:
- 필요한 판정: PASS / FAIL / 보류
- Claude에게 받을 것:
```

1차 파일럿은 실제 외부 전송 자동화가 아니라, 다음 hook/skill/자동화 변경 1건에서 위 요청문을 작성하고 Claude 판정을 받아 `review.md`에 남기는 것으로 제한한다.
