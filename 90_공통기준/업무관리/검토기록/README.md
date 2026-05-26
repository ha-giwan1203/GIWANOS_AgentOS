# 검토기록 README

> 목적: Claude 검증과 Codex 실행 사이의 중요 리뷰 결과를 작게 남기는 shadow mode 안내서.
> 비유: 이 폴더는 작업 원장이 아니라, 품질검사 때 남기는 검사표 보관함이다.

## 1. 원칙

- 이 폴더는 **상태 원본이 아니다**.
- 완료/진행/차단 판정은 항상 `90_공통기준/업무관리/TASKS.md`가 우선이다.
- `HANDOFF.md`는 세션 메모, `STATUS.md`는 운영 요약이다.
- 이 폴더는 Claude 검증 또는 Codex Critic 검토를 보조 기록으로 남길 때만 쓴다.

## 2. 적용 범위

- 적용 방식: 로컬 자동 검증대기함. Claude 앱 버전에서는 자동전달 미지원
- 승인 기록: `90_공통기준/업무관리/codex_claude_auto_delivery.json`
- 적용 대상: Codex가 만든 검증 요청 `request.md`를 현재 Claude session에 전달하고 응답을 `review.md`에 기록하는 경우
- 적용 제외: 무한 재시도, 임의 외부 워커 호출, 도메인 의사결정 자동 위임, 사용자 승인 없는 신규 서비스 전송
- 2026-05-25 현재 `claude --resume -p` 외부 Claude session 전송은 tenant 정책으로 차단되어 기본 유효 모드는 `local_review_queue_only`이다.
- 대체 후보인 공식 Channels 기반 `90_공통기준/업무관리/codex_claude_channel/`은 Claude Code CLI 전용이다. Claude 앱 버전 세션에는 붙지 않으므로 현재 운영 자동전달로 보지 않는다.

## 3. 기본 기록 파일

작업별 기본 파일은 `review.md` 1개만 둔다.

```text
90_공통기준/업무관리/검토기록/runs/YYYYMMDD_<slug>/review.md
```

- 단, Codex가 Claude 검증 요청을 넘겨야 하는 작업은 `request.md` 1개를 추가로 둘 수 있다.
- `request.md`는 Claude에게 전달할 검증 요청 원문이고, `review.md`는 실제 판정 또는 전송 차단 기록이다.
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

## 7. 자동전달 판정 기준

자동전달 실행 후 아래를 확인한다.

- 새 세션에서 `review.md`만 읽고 재개 위치를 이해할 수 있는가
- Claude 검증 시간이 줄었는가
- Codex 결과 누락이 줄었는가
- `TASKS/HANDOFF/STATUS`와 상태 충돌이 없는가
- 문서 관리 부담이 늘지 않았는가

전송 실패 시 우회하지 않고 `review.md`에 실패 사유를 남긴다. 성공 시 Claude 응답을 `review.md`에 남기고, commit 승인 여부는 Claude 응답 문구 기준으로 판단한다.

## 8. Codex -> Claude 현재 세션 요청 파일럿

토론모드의 재사용 대상은 브라우저 자동화가 아니라 `요청 -> 응답 -> 판정 -> 기록` 흐름이다.

- 브라우저 경로(`gpt-send`, `gpt-read`, CDP Chrome)는 이 파일럿에 사용하지 않는다.
- 고정 Claude 방을 만들지 않는다.
- 사용자가 열어둔 Claude Code/Claude CLI 세션을 우선 현재 브레인 세션으로 본다.
- 세션 식별은 `claude --continue` 또는 `claude --resume <세션ID>` 계열을 후보로 둔다.
- Claude 현재 세션을 쓰려는 작업은 사용자 진술을 기다리지 않고 Codex가 먼저 세션 존재를 확인한다.
- 일반 sandbox 프로세스 조회에서 창 목록이 비어도 세션 없음으로 확정하지 않는다.
- 입력/제출/응답 회수가 필요한 경우에는 GUI 권한 프로세스 조회까지 수행한 뒤 세션 없음 여부를 판단한다.
- Claude CLI가 Windows Terminal 안에서 실행 중이면 입력 대상은 `claude.exe`가 아니라 `WindowsTerminal.exe`의 실제 HWND다.
- Codex가 Claude CLI에 입력할 때는 `90_공통기준/업무관리/claude_terminal_send.ps1 -DryRun`으로 대상 HWND를 먼저 확인하고, 후보가 1개일 때만 `-Submit` 전송한다.
- `MainWindowTitle='Claude'`, `AppActivate('Claude')`, `claude.exe` PID 기준 전송은 금지한다. 이는 앱/CLI/터미널 구분 오류를 반복시킨다.
- 재확인 뒤에도 세션이 확인되지 않으면 새 세션을 몰래 만들지 않고 `보류`로 기록한다.
- `claude -p` 단발 호출은 Codex stdout으로 돌아오는 검토에는 쓸 수 있지만, 사용자가 보고 있는 Claude 채팅창에 반드시 표시된다고 보지 않는다.
- `claude --resume`/`claude -p`로 작업공간 경로, diff 요약, 검증 요청을 보내는 행위는 외부 Claude 서비스 전송으로 취급한다.
- 직접 전송은 사용자에게 데이터 반출 위험을 알린 뒤 명시 승인이 있을 때만 시도한다.
- 2026-05-25 사용자가 "자동전달 모드로 설정하라고" 명시했으나, tenant 정책이 외부 Claude service 전송을 차단해 `codex_claude_auto_delivery.json`의 `enabled=false`, `effective_mode=local_review_queue_only`로 둔다.
- 공식 대체 경로인 Claude Code Channels는 CLI 세션 전용이다. 앱 버전 Claude 세션에서는 이 절차를 자동전달 PASS 조건으로 쓰지 않는다.
- CLI로 별도 검증할 때만 Claude를 `90_공통기준/업무관리/codex_claude_channel/start_claude_channel.ps1`로 시작하고, Codex는 `send_request.py --request <request.md> --review <review.md>`로 로컬 `127.0.0.1:8791`에 요청한다.
- 표준 실행은 `python 90_공통기준/업무관리/codex_claude_auto_deliver.py --request <request.md> --review <review.md>`이다.
- 안전검토가 차단하면 우회하지 않고 `request.md`와 `review.md`에 차단 사유를 남긴다.
- 차단된 경우 `TASKS.md`에는 owner=Claude 검증 대기 상태와 `request.md` 경로를 남긴다.
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

자동전달 모드에서도 전송 범위는 검증 요청문으로 제한한다. 일반 파일 본문 전체, 원본 업무자료, 인증정보, 비가역 실행 권한은 자동전달 대상이 아니다.
