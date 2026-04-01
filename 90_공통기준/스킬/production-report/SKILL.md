---
name: production-report
description: 생산실적 집계 자동화 — BI 실적 + 임률단가 + 조립비 API → 생산관리 마스터리스트 자동 생성
version: v1.0
trigger: "생산실적 집계", "BI 실적", "생산관리 마스터리스트", "build_master", "생산 보고서"
author: 하지완
last_updated: 2026-03-31
---

# 생산실적 집계 자동화 스킬

## 목적
BI 실적 데이터, 임률단가, 조립비 시스템 API를 자동으로 합쳐서 `생산관리_마스터리스트.xlsx`를 생성한다.

## 실행 스크립트
`05_생산실적/_자동화/build_master.py`

```bash
PYTHONUTF8=1 python build_master.py
```

## 입력 데이터

| 입력 | 경로 | 설명 |
|------|------|------|
| BI 실적 | `05_생산실적/BI실적/대원테크_라인별 생산실적_BI.xlsx` | 경로 원본: production-result-upload SKILL.md 0단계 |
| 임률단가 | `02_급여단가/임률단가/03_대원테크/임률단가_대원테크_독립계산.xlsx` | 단가 기준 |
| 조립비 API | `http://ax.samsong.com:33200/api/assembly-cost-operation` | 조립비 시스템 실시간 데이터 |
| 라인 API | `http://ax.samsong.com:33200/api/line-operation` | 라인 운영 데이터 |

## 출력
`05_생산실적/생산관리_마스터리스트.xlsx`

## 선행 작업
- BI 실적 파일 최신본 확인 (production-result-upload SKILL.md 0단계에서 자동 갱신)
- 임률단가 파일 최신본 확인

## 관련 스크립트

| 스크립트 | 역할 |
|---------|------|
| *(폐지됨)* | BI 파일 갱신은 production-result-upload SKILL.md 0단계에서 처리 |

## 금지사항
- build_master.py 출력 파일을 직접 수정하지 않는다 (재실행 시 덮어씀)
- BI 원본 파일 구조를 임의 변경하지 않는다
- 임률단가 파일의 단가 컬럼을 검증 없이 수정하지 않는다
