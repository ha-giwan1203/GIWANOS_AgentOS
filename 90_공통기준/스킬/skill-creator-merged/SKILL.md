---
name: skill-creator
description: 재사용 스킬 제작·수정·평가·패키징 — 6 모드 (draft / improve / eval / optimize / package / harness)
trigger: "스킬 만들어줘", "스킬 수정해줘", "이 업무를 스킬로", "스킬 테스트", "스킬 패키징"
grade: B
---

# Skill Creator

> 6 모드 / 패턴 카탈로그 / 도메인 가이드 / 절차는 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 실행 모드 (첫 단계 결정)
| mode | 의미 | 깊이 |
|------|------|------|
| `draft` | 새 스킬 초안 (default) | Lite |
| `improve` | 기존 스킬 수정 | Lite |
| `eval` | 테스트/비교/채점 | Full |
| `optimize` | description/trigger 최적화 | Full |
| `package` | 최종 정리/배포 .skill | Lite |
| `harness` | Planner→Generator→Evaluator 3단계 품질보증 | Full |

## 모드 규칙
- 사용자 미명시 → `draft` + Lite
- `eval`/`optimize` → 사용자 명시 시만
- `harness` → "꼼꼼하게", "평가 포함", "하네스로", "3단계로" 요청 시
- Lite는 전체 benchmark, 비교 평가 루프, 장시간 분석 생략
- "꼼꼼하게", "풀로", "전체 평가" → Full 전환

## 절차 (요약)
1. Capture Intent (의도 캡처: 무엇/언제 트리거/출력 형식/테스트 필요 여부)
2. Interview & Research (엣지케이스, MCP 검색)
3. Select Patterns (`references/pattern-catalog.md` 1~3개 선택)
4. Write SKILL.md (선택 패턴 기반)
5. Test prompts + 평가 (eval 모드)
6. Iterate (사용자 피드백 반영)
7. Description optimizer (선택)

## 도메인 가이드
- 제조업/ERP/정산 → `references/domain-guide-manufacturing.md` 추가 참조 (selector, timing, formula 보존 등)

## verify
- SKILL.md frontmatter 완비 (name, description, trigger, grade)
- 트리거 문구 명확 (사용자 호출 패턴 반영)
- Lite 모드 산출물: 초안 + 사용 예시 + 개선 포인트
- Full 모드 산출물: + grader + HTML 리뷰

## 실패 시
- 모드 미결정 → draft + Lite default
- 사용자 모호 → 1줄 질문
- 상세 → MANUAL.md "Communicating with the user" + "Creating a skill" 단계
