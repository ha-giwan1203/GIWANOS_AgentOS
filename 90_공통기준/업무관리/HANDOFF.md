# HANDOFF — AI 인수인계 문서 (세션 메모 전용)

> **이 파일은 세션 인수인계 메모다. 상태 원본이 아니다.**
> 작업 완료/미완료 판정은 TASKS.md 기준. 이 파일이 TASKS와 충돌하면 TASKS를 따른다.
> 세션 변경사항과 다음 AI 액션만 기록한다. 완료/미완료를 독립 선언하지 않는다.

최종 업데이트: 2026-04-03 — PPT 자동 생성 스킬 MVP 2종 PoC 완료 (b22ef085)
읽기 순서: **TASKS.md → STATUS.md → HANDOFF.md** → CLAUDE.md → 도메인 CLAUDE.md

---

## 1. 이번 세션 작업 목적

PPT 자동 생성 스킬 — GPT 토론 → 공식 스킬 검증 → MVP 2종 PoC → QA PASS → GPT 판정

---

## 2. 실제 변경 사항

| 대상 | 핵심 변경 | 결과 |
|------|----------|------|
| GPT 토론 | PPT 스킬 전략 합의 + 재사용 검증 + PoC 결과 공유 | MVP 2종 엔진 적합성 확보 |
| 공식 스킬 검증 | anthropics/skills + tfriedel 6항목 체크리스트 | python-pptx 유지, QA만 차용 |
| 도구 설치 | python-pptx 1.0.2, matplotlib 3.10.8, markitdown, Pillow | 완료 |
| SKILL.md | 90_공통기준/스킬/pptx-generator/SKILL.md | 3층 아키텍처 + QA 3축 |
| MVP 1 PoC | ncr_generator.py — 품질 대책서 | cfb88dde, QA PASS |
| MVP 2 PoC | monthly_production_generator.py — 월간 생산실적 | b22ef085, QA PASS |

---

## 3. 미해결 / 다음 AI 액션

| 우선순위 | 항목 | 비고 |
|---------|------|------|
| **높** | **실무 투입 준비** | 실제 데이터로 생성 테스트, PowerPoint에서 열어 시각 확인 |
| 중 | 확장 검증 | 사진 삽입, Graphviz 다이어그램, visualize 자동 분기 |
| 중 | verify_xlsm.py COM 실검증 | 다음 xlsm 작업 시 자동 실행 |
| 낮 | domain_read_tracker.sh 백슬래시 처리 조사 | Windows \\ vs \ 잠재 버그, 현재 동작 영향 없음 |
