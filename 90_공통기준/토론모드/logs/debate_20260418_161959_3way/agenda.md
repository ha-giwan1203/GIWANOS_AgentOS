# 3자 토론 — 의제 1: /schedule 작업 분류 매트릭스

> 세션69, 2026-04-18 16:19 KST
> 진입 경로: 세션68 TASKS.md "검증 후 적용 대기" 항목

## 배경
- 세션68 3자 토론에서 `/schedule` (Claude Code 원격 크론 에이전트)는 "검증 후 적용" 분류로 결정됨
- 이유: 사내망 의존 작업(ERP/Flow/NotebookLM)은 원격 실행 불가
- 선결: 작업을 "로컬 / 사내망 / GitHub-only / 커넥터" 4칸으로 분류하는 매트릭스 수립 필요

## 목적
현 저장소의 반복/정기 작업을 4칸 매트릭스에 분류하여 `/schedule` 이관 가능 범위를 확정한다.

## 산출물
1. 분류 매트릭스 (Markdown 표)
2. `/schedule` 이관 우선순위 (로컬→GitHub-only→커넥터→사내망 순)
3. 사내망 작업의 대체 자동화 방안 (/loop? cron? 수동?)
4. Phase 1 이관 후보 스킬 3~5개 선정

## 쟁점 제기 (양측에 공유)
- `/schedule` 원격 실행 환경: GitHub 저장소 기반, 로컬 bash/PowerShell/Chrome MCP 비가용
- 현재 스킬 37개(+hooks 20개) 중 순수 GitHub-only로 동작 가능한 것은?
- 사내망 의존 확인: G-ERP/Flow/MES/NotebookLM MCP 호출 포함 여부
- 커넥터 기반(Gmail/Slack/Notion MCP)은 원격 가능 여부
