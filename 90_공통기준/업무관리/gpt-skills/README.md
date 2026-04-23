# gpt-skills — GPT 프로토콜 스킬 모음

> **목적**: GPT가 따르는 프로토콜 파일을 모은 폴더. Claude Code skill과 달리 실행 엔진이 없다. 사용자가 GPT에게 트리거 단어를 입력하면 GPT가 해당 md 파일을 GitHub App으로 조회하고 그대로 실행한다.

## 사용 방식

1. 사용자가 ChatGPT에 트리거 단어 입력 (예: "클로드코드 정밀평가")
2. GPT가 `gpt-instructions.md`의 "GPT 프로토콜 스킬" 섹션에서 매칭되는 프로토콜 파일 경로 확인
3. GitHub App으로 해당 파일 조회
4. 파일의 절차·템플릿·금지 규칙을 그대로 실행

## 등록된 프로토콜

| 파일 | 트리거 | 용도 |
|------|--------|------|
| [claude-code-analysis.md](./claude-code-analysis.md) | "클로드코드 정밀평가" / "/클코평가" / "harness audit" / "정밀평가" | 저장소 하네스·Claude 플랜·Claude Code CLI 일반 정밀평가 (大·中·小 3계층 + 영향반경 5필드) |

## 추가 등록 시 규칙

1. 프로토콜 파일은 자기완결적으로 작성 (별도 문서 없이도 GPT가 실행 가능)
2. 판정 용어·라벨·B분류 조건 등은 기존 정의 재사용 (`gpt-instructions.md`, `90_공통기준/토론모드/CLAUDE.md`, 메모리 `feedback_harness_label_required.md`)
3. 이 README의 "등록된 프로토콜" 표에 1행 추가
4. `gpt-instructions.md` "GPT 프로토콜 스킬" 섹션 표에도 동일 1행 추가
5. Claude Code 쪽 hook/skill 신설 없이 GPT 단독 실행 가능한 범위만 담을 것
