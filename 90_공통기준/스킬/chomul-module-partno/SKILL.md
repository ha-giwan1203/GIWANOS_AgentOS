---
name: chomul-module-partno
description: 초물표 모듈품번(RSP) 일괄 반영 — AB5:AJ14 박스에 RSP 입력/수정 + 라인코드 SP3S03→SP3M3 + 뷰·구분선 통일. Windows Excel COM
trigger: "초물표 수정", "모듈품번 입력", "초물표 RSP", "RSP 반영", "라인코드 변경", "초물표 일괄", "SP3M3 변경"
grade: A
---

# 초물표 모듈품번 일괄 반영

> Excel COM 자동화 코드 / 케이스별 처리 / 검증은 [MANUAL.md](MANUAL.md). 용어는 ../GLOSSARY.json.

## 작업 폴더
```
C:\Users\User\Desktop\업무리스트\03_품번관리\초물관리
├── _backup/                       # 원본 xls 49개 (절대 수정 금지)
├── _output/                       # 복사본만 수정
├── SP3M3_모듈품번_최신.xlsx       # 기준정보
└── 초물표_모듈품번_작업가이드.md   # 상세 가이드
```

## 매칭 키 (핵심)
- ❌ SUB품번 기준 매칭 금지 — 62건 SUB 중복으로 잘못된 RSP 매칭
- ✅ **각 시트 H12(완성품 품번) 정규화 (대문자+공백제거+하이픈제거) → 기준정보 매칭**

## 절차 (요약)
1. `_backup/` xls 49개 + 기준정보 파일 확인
2. 기준정보 (`SP3M3_모듈품번_최신.xlsx`) 로드 — A차종/B품번/C SUB/D RSP
3. 각 시트마다:
   - 1단계: 뷰(Normal=1) + 구분선(DisplayPageBreaks=False, ResetAllPageBreaks)
   - 2단계: AB5 파싱 + H12 매칭 → 분기 (입력/수정/유지/미매칭)
4. 입력·수정 시: AB5:AJ14 클리어 → 3분할 재병합
   - AB5:AJ9 = "SP3M3" (검정, 85pt)
   - AB10:AJ12 = 공용품번 (LH 빨강 / RH 파랑, 110pt)
   - AB13:AJ14 = RSP (검정, 80pt + RSP 부분색상)

## 케이스 분기
| 조건 | 판정 | 처리 |
|------|------|------|
| RSP 없음 + 기준매칭 | 입력 | 3분할 재병합 |
| RSP 있음 + 기준 다름 | 수정 | 3분할 재병합 |
| RSP 있음 + 기준 같음 | 유지 | 3분할 재병합 (포맷 통일만) |
| H12 미매칭 | 미매칭 | 3분할 재병합 (RSP 빈값) + 보고 |

## verify
- _backup/ 원본 미수정 (mtime 비교)
- _output/ 복사본만 수정
- 각 시트 AB5:AJ14 3분할 병합 + 폰트/색상/크기 통일
- H12 매칭 결과 표 (입력/수정/유지/미매칭)

## 실패 시
- pywin32 미설치 / Excel 백그라운드 실행 중 → FAIL (선결조건)
- H12 미매칭 다수 → 기준정보 점검 후 재실행
- 되돌리기: `_backup/`에서 _output/ 재복사 후 재실행
- 상세 → MANUAL.md "케이스별 처리" + "검증" + "되돌리기"
