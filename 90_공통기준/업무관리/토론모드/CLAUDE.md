# CLAUDE.md — 토론모드 프로젝트

## 프로젝트 개요

**프로젝트명**: 토론모드 (debate-mode)
**목적**: Claude가 브라우저에서 ChatGPT 화면을 직접 읽고, 이전 답변을 바탕으로 반박/질문을 생성하여 반자동 AI 대 AI 토론을 이어가는 Cowork 구조
**상태**: 스킬 v1.0 설치 완료 (2026-03-29)

## 핵심 설계 원칙

- API 사용 금지 — 브라우저 자동화만으로 동작
- Notion 등 외부 저장소 불필요 — 로컬 로그 파일 저장
- 완전 무인 자동화 아님 — 실전형 반자동 코워크
- Claude = 비판자/검증자, GPT = 제안자/설계자

## 합의된 핵심 로직 (GPT-Claude 4라운드 토론 결과)

```
완료 감지: read_page 전송버튼 enabled + get_page_text 2회 비교(2초 간격)
답변 추출: read_page → role=assistant → 마지막 visible 블록
aria-busy: 제외 (ChatGPT 실제 노출 불확실)
```

## 사용 방법

"토론모드", "GPT랑 토론해", "AI 토론 시작" → debate-mode 스킬 자동 트리거

## 폴더 구조

```
토론모드/
├─ CLAUDE.md        ← 이 파일 (프로젝트 지침)
├─ STATUS.md        ← 진행 상태
├─ TASKS.md         ← 할 일 목록
├─ skills/
│  └─ debate-mode/
│     └─ SKILL.md   ← 스킬 본체
├─ logs/            ← 토론 로그
│  ├─ debate_*.md
│  └─ errors/
└─ workspace/       ← 임시 작업 공간
```

## 버전 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v1.0 | 2026-03-29 | 최초 작성. GPT-Claude 4라운드 토론으로 핵심 로직 합의 |
