---
name: youtube-analysis
description: YouTube 영상 분석 (자동 + 수동 모드). 자막+프레임 추출 → 9개 관점 분석 → A/B/C 판정 → GPT 토론 → 구현/plan
trigger: "영상분석", "유튜브 분석", "영상 요약", "/video"
grade: C
---

# YouTube 영상 분석

> 자동/수동 모드 / 9개 관점 / A/B/C 판정 / Notion+Drive 저장은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 모드 구분
| 입력 | 모드 | 동작 |
|------|------|------|
| "영상분석" 단독 / "영상분석 {주제}" | 자동 | 상태 진단 → 검색 → 분석 → 교차검증 → GPT 토론 → 구현 |
| URL 포함 | 수동 | 해당 영상 자막+프레임 추출 → 분석 → 적용안 |

## 자동 모드 절차 (요약)
1. Step 0: 상태 로드 (TASKS/STATUS/HANDOFF/hooks/rules/스킬/CLAUDE.md/이전 분석 로그)
2. Step 0.5: 실행 가능성 점검 (transcript-api / WebSearch / 토론모드)
3. Step 1: 개선 가설 수립 (5개 관점)
4. Step 2: WebSearch 영상 검색 (영어 우선, 2~5개)
5. Step 3: 자막 추출 (`youtube_transcript.py`)
6. Step 4: 9개 관점 분석 + 공식 문서 교차검증 + A/B/C 판정
7. Step 5: GPT 토론 (A/B 등급만)
8. Step 6: A=즉시 구현 / B=plan.md 생성
9. Step 7: TASKS/HANDOFF/STATUS 갱신 + 커밋 + GPT 공유

## 수동 모드 절차 (요약)
```bash
PYTHONUTF8=1 python "90_공통기준/스킬/youtube-analysis/youtube_analyze.py" "<URL>" --max-frames 15
```
1. 자막 + 영상 다운로드 + 프레임 추출 + manifest.json
2. 프레임을 Read로 직접 열어 시각 분석
3. 9개 관점 분석 + 공식 문서 교차검증 + A/B/C
4. Notion DB upsert + Drive 업로드

## A/B/C 판정 (교차검증 후에만)
- **A** 즉시 구현: 작고 명확 + 공식 문서 확인 + 되돌리기 쉬움
- **B** 계획 후: 복수 파일/도메인 + plan.md 필요
- **C** 참고만: 환경 미스매치 / 보유 / 증거 부족

## verify
- cache/{video_id}/manifest.json 존재
- transcript.txt 또는 대체 자막
- 프레임 ≥ 3장
- A/B/C 근거표 (9개 관점 전수)
- Notion + Drive 저장 완료

## 실패 시
- 자막+프레임 모두 실패 → FAIL
- A 판정인데 공식 문서 교차검증 미수행 → FAIL
- 상세 → MANUAL.md "오류 처리" + "실패 조건" + "되돌리기"
