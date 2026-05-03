---
name: mes-production-upload
description: MES 생산실적 자동 업로드 — BI 엑셀 → SaveExcelData.do API 직접 POST. daily-routine 통합 또는 단독
trigger: "실적 업로드", "MES 업로드", "생산실적 입력", "BI 업로드", "실적 올려", "MES 실적"
grade: A
note: 통합 daily-routine/run.py 포함. 단독 실행도 가능 (run.py)
---

# MES 생산실적 자동 업로드

> 0~N단계 절차 / OAuth 자동 로그인 / 데이터 품질 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 시스템
- BI 파일: `C:\Users\User\Desktop\업무리스트\05_생산실적\BI실적\대원테크_라인별 생산실적_BI.xlsx`
- BI 원본: `Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx`
- MES URL: `http://mes-dev.samsong.com:19200`
- API: `POST /prdtstatus/SaveExcelData.do`

## 절차 (요약)
1. **0단계 BI 갱신**: Z드라이브 mtime 비교 → 더 최신이면 로컬 복사
2. CDP 9223 연결 + URL 확인 → auth-dev면 자동 OAuth 로그인 (pyautogui)
3. iframe 동적 탐지 + `/prdtstatus/viewPrdtRsltByLine.do` 로드
4. **데이터 품질 검증**: 생산량(COL15) None/0 검사 → 미통과 시 중단
5. MES 기등록 조회 → 누락일 산출 → 날짜별 1배치로 POST
6. 실패 시 최대 3회 재시도 (새 세션 재로그인)
7. 검증: 건수 + qty 합계 BI 원본 대조

## ⚠️ 핵심 원칙
- **반드시 한 번에 전송** (SaveExcelData는 UPSERT — 분할 전송 시 덮어씀)
- 같은 날짜 데이터는 1배치 (12~15건)
- 기존 데이터 절대 수정·삭제 X — 신규 날짜만 INSERT
- 업로드 전 중복 확인 필수
- 한 번에 최대 31일

## verify
- BI 추출 행 = MES 등록 행
- BI 생산량 합계 = MES qty 합계
- 일요일 데이터 0건

## 실패 시
- BI 생산량 빈값 → 중단 (사용자 명시 "빈 데이터라도 올려" 시만 진행)
- OAuth 실패 → 자동 로그인 → 그래도 실패 시 사용자 보고
- 500 에러 → 새 세션 재로그인 + 최대 3회 재시도
- 되돌리기: MES 화면에서 직접 삭제 또는 동일 날짜 재전송 (UPSERT)
- 상세 → MANUAL.md "안전 원칙" + "데이터 품질 검증" + "네트워크 제약사항"
