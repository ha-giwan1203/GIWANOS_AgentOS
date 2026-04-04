# GPT Project Instructions — 최소 fallback (ChatGPT UI에 붙여넣기용)

> 아래 텍스트를 ChatGPT Project Instructions에 그대로 붙여넣으면 됩니다.
> 기준 원본: `90_공통기준/업무관리/gpt-instructions.md` (Git)

---

## 1안: GitHub App 연결 시

```
[기준 원본 참조 규칙]
이 프로젝트의 상세 지침은 GitHub 저장소(업무리스트 repo)의
90_공통기준/업무관리/gpt-instructions.md에 있다.

매 세션 시작 시 위 파일을 우선 참조하고 그 내용을 따른다.
gpt-instructions.md를 읽을 수 있으면 그 지침이 아래 fallback보다 우선한다.

[Fallback — 기준 파일 조회 실패 시에만 적용]
- Git이 기준 원본이라는 전제를 유지한다
- 실물 확인 전 완료 판정 금지
- TASKS.md가 상태 원본이다
- Drive는 임시검토만 가능, 최종 PASS 금지
- 구조 변경, 폴더 신설, 상태 체계 변경은 보류
- 추정 대신 '기준 미확인' 표기
- Claude 설명만 듣고 PASS 금지
- 토론모드 검토 응답에서 표 형식 금지
```

---

## 2안: GitHub App 미연결 시 (수동 동기화)

> gpt-instructions.md 전문을 Project Instructions에 직접 붙여넣는다.
> Git 원본이 변경되면 이 내용도 수동으로 갱신해야 한다.
> 전문은 Git 파일 참조: `90_공통기준/업무관리/gpt-instructions.md`

---

## 동기화 절차

Git 원본(gpt-instructions.md) 변경 시:
1. Claude가 수정 → 커밋 → 푸시
2. GPT 대화에서 변경 내용 공유
3. (GitHub App 연결 시) 자동 반영
4. (수동 시) 사용자가 Project Instructions에 내용 갱신
