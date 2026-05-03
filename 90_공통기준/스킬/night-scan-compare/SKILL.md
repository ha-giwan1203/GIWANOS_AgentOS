---
name: night-scan-compare
description: MES 야간스캔실적 조회 → BI 대비 비교 엑셀 자동 생성 (4시트 데이터+수식+양식)
version: v1.1
trigger: "야간스캔", "스캔실적", "야간실적 비교", "night-scan"
grade: B
---

# 야간 스캔실적 비교 스킬

> 6Phase / 핵심 규칙 / 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 절차 (요약)
1. 라인명·월 인수 파싱 + 비교 엑셀 경로 확인
2. BI 최신본 갱신 (Z드라이브 → 로컬)
3. BI 날짜·생산량 추출 + MES API 일괄 조회 (야간 shiftsCd=02)
4. 4시트(생산기준DATA/스캔실적DATA/일자별비교/월간요약) 클리어 후 재대입
5. 양식 3종 세트(테이블 범위 + fill 제거 + 조건부 서식)

## 인수
- 라인명 (필수): SP3M3, SD9A01 등
- 월 (필수): 3, 4 등
- 년 (선택, 기본=현재년)

## verify
- 테이블 범위 = 데이터 행 수
- 개별 fill = None (테이블 스타일 위임)
- 조건부 서식 = 데이터 전체 행
- MES없음: C 빈값 + D "MES데이터없음"
- 고아데이터 0건

## 실패 시
- MES 미로그인 → 사용자 요청 후 대기
- 비교 엑셀 미존재 → 즉시 중단
- 상세 → MANUAL.md "실패 조건" + "되돌리기"
