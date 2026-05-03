# line-mapping-validator — MANUAL

> 6 Step 절차 / 비교 원칙 / 판정 코드 / 출력 형식. SKILL.md는 호출 트리거 + 80줄 요약.

## 개요
기준 품번 파일(마스터)과 라인배정 파일(검증 대상) 비교 → 품번 단위 정합성 판정 → 보고서.

핵심 가치:
- 수동 대조 2~3시간 → 10분 이내
- "누락/오기입/컬러확장" 1차 판정
- 판정 근거 제시, 실무자 최종 확인만

## 입력 자료

### 필수
| 항목 | 설명 | 예시 |
|------|------|------|
| 기준 파일 | 마스터 품번 (xlsx/csv) | SP3M3_품번리스트.xlsx (302건) |
| 라인배정 파일 | 검증 대상 (xlsx/csv) | ENDPART라인배정.xlsx (1,476건) |

### 선택 (미제공 시 자동 탐색 + 사용자 확인)
| 항목 | 기본 동작 |
|------|-----------|
| 시트명 | 자동: 데이터 가장 많은 시트 |
| 품번 컬럼 | 헤더에서 "품번", "제품번호", "PART" 탐색 |
| 라인코드 컬럼 | "조립라인", "라인", "LINE" 탐색 |
| 비교 대상 라인 | 전체 |
| 컬러코드 규칙 | 뒤 2~3자리, 사용자 확인 |

### 파일 구조 주의
- **2행 헤더**: 1행 상위 카테고리, 2행 실제 컬럼명
- **병합셀**: openpyxl로 None
- **시트명 공백/특수문자**: `ws = wb.worksheets[0]` 인덱스 접근 안전
- **빈 행 섞임**: None 체크 필수

## 품번 비교 원칙

### 1. 기준 파일이 마스터
기준 = 정답. 라인배정 = 확인 대상. 라인배정에만 있고 기준에 없으면 별도 "기준 미등록".

### 2. 접두어는 안 건드림
접두어(SP3M3-)는 품번의 일부. 다르면 다른 품번.

### 3. 컬러코드 2단계 비교
[모품번]+[컬러코드] 구조. 기준=모품번만, 라인배정=컬러코드 포함 다수.
```
1차: 전체 품번 직접 비교 → 완전 일치
2차: 모품번 기준 확장 → 기준 모품번이 라인배정 앞부분 일치
```
컬러코드 분리 불명확 → 임의로 자르지 않고 사용자 확인.

### 4. 라인 없으면 문제
품번 존재하지만 라인코드 미배정 → "완전누락" 아닌 "라인누락".

### 5. 애매하면 확정 X
- 유사 품번 존재 (1~2자리 차이)
- 모품번 같고 컬러코드만 다름
- 표기 규칙(하이픈/공백/대소문자) 다름
→ "판정유보" 또는 "기준오기입의심" + 사유.

## 판정 코드
| 코드 | 판정 | 의미 | 실무 조치 |
|------|------|------|-----------|
| A | 일치 | 품번·라인코드 모두 일치 | 없음 |
| B | 컬러확장일치 | 모품번 일치 + 컬러 확장 + 라인 일치 | 없음 |
| C | 라인누락 | 품번/모품번 존재하나 대상 라인 없음 | 라인배정 추가 |
| D | 기준오기입의심 | 유사품번 존재 (오타/자릿수) | 기준파일 확인 |
| E | 완전누락 | 직접·모품번·유사 모두 불일치 | 신규 등록 |
| F | 판정유보 | 자료 부족/컬럼 불명확 | 추가 확인 |

## 실행 절차

### Step 1. 파일 구조 파악
```python
import openpyxl

def scan_file(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    for i, name in enumerate(wb.sheetnames):
        ws = wb.worksheets[i]
        print(f"시트 [{i}] '{name}': {ws.max_row}행 x {ws.max_column}열")
        for row in ws.iter_rows(min_row=1, max_row=3, values_only=True):
            print([str(v)[:20] if v else '(빈칸)' for v in row])
```
사용자 확인 필수 — 컬럼 가정 그대로 진행 X.

### Step 2. 품번 정규화
```python
def normalize(part_no):
    if part_no is None:
        return ""
    s = str(part_no).strip().upper()
    s = " ".join(s.split())
    return s

def extract_base(part_no, color_len=0):
    if color_len > 0 and len(part_no) > color_len:
        return part_no[:-color_len]
    return part_no
```
`color_len`은 사용자 확인 후에만 0이 아닌 값.

### Step 3. 1차 직접 비교
```python
ref_parts = {normalize(row[품번열]) for row in 기준시트 if row[품번열]}

assign_map = {}
for row in 배정시트:
    pn = normalize(row[품번열])
    line = normalize(row[라인열])
    if pn:
        assign_map.setdefault(pn, set()).add(line)

for ref_pn in ref_parts:
    if ref_pn in assign_map:
        if 대상라인 in assign_map[ref_pn]:
            판정 = "A"
        else:
            판정 = "C"
    else:
        # 2차로
        pass
```

### Step 4. 2차 모품번 비교
```python
base_map = {}
for pn in assign_map:
    base = extract_base(pn, color_len)
    base_map.setdefault(base, []).append(pn)

for ref_pn in 불일치목록:
    ref_base = extract_base(ref_pn, color_len)
    if ref_base in base_map:
        expanded = base_map[ref_base]
        lines = set()
        for epn in expanded:
            lines.update(assign_map.get(epn, set()))
        if 대상라인 in lines:
            판정 = "B"
        else:
            판정 = "C"
    else:
        # 3차로
        pass
```

### Step 5. 유사품번 탐색
```python
from difflib import SequenceMatcher

def find_similar(target, candidates, threshold=0.85):
    results = []
    for c in candidates:
        ratio = SequenceMatcher(None, target, c).ratio()
        if ratio >= threshold:
            results.append((c, ratio))
    return sorted(results, key=lambda x: -x[1])

for ref_pn in 여전히_불일치:
    similar = find_similar(ref_pn, assign_map.keys())
    if similar:
        판정 = "D"
        사유 = f"유사품번: {similar[0][0]} (유사도 {similar[0][1]:.0%})"
    else:
        판정 = "E"
```

### Step 6. 판정 확정 + 결과 정리

## 출력 형식

### 1. 요약
```
■ 검증 결과 요약
- 기준 품번 수: XXX건
- A. 일치: XXX건 (XX.X%)
- B. 컬러확장일치: XXX건 (XX.X%)
- C. 라인누락: XXX건 (XX.X%) ← 라인배정 추가
- D. 기준오기입의심: XXX건 (XX.X%) ← 기준파일 확인
- E. 완전누락: XXX건 (XX.X%) ← 신규 등록
- F. 판정유보: XXX건 (XX.X%) ← 추가 확인
```

### 2. 상세표
문제 항목(C, D, E, F)만. 일치(A, B)는 건수만.

| 기준품번 | 모품번 | 라인배정품번 | 라인배정모품번 | 대상라인 | 확인라인 | 판정 | 판정사유 | 조치의견 |

### 3. 개선안
- 기준파일 수정 필요 항목
- 라인배정 추가 필요 항목
- 비교 규칙 보완 필요 항목

### 4. 3줄 인사이트

### 5. 엑셀 보고서 (선택)
사용자 요청 시 xlsx. 시트: 요약 / 상세(C·D·E·F) / 전체목록 / 판정기준

## 검증 기준
- 기준 품번 총 건수 명시
- 판정별 건수 합계 = 기준 품번 총 건수 (전수 처리)
- 모든 C·D·E·F에 판정사유 + 조치의견
- 접두어 임의 제거 X
- 컬러코드 사용자 확인 없이 제거 X
- 사용자 미확인 가정에 "⚠️ 가정" 표시

## 오류 대응
| 상황 | 대응 |
|------|------|
| 파일 열기 실패 | 형식/경로 확인. xlsm/xls는 xlsx 변환 |
| 헤더 인식 실패 | 첫 5행 출력 후 사용자에게 컬럼 지정 요청 |
| 병합셀 문제 | `ws.merged_cells.ranges` 확인 후 병합 해제 |
| 빈 행 대량 | max_row 대신 실제 마지막 행 탐색 |
| 품번 0건 일치 | 정규화/컬럼 오류 가능, 원본 샘플 제시 |

## 금지
- 접두어 임의 제거
- 컬러코드 사용자 확인 없이 제거
- 라인배정을 마스터로 삼기
- 유사품번 존재 시 즉시 "완전누락" 확정
- 판정사유 없는 결과표
- 원본 파일 직접 수정
- 컬럼 사용자 확인 없이 임의 결정

## 기존 스킬 연동

### line-batch-management 흐름
1. line-batch-management로 ERP 라인배치 입력
2. line-mapping-validator로 결과 정합성 검증
3. 발견 누락 품번을 line-batch-management로 추가 배치

### 관련 파일
- `02_생산관리/생산_SP3M3_품번리스트.xlsx` → 기준 302건
- `03_라인배치/라인배치_ENDPART라인배정.xlsx` → 검증 대상 1,476건
- `03_라인배치/라인배치_정합성검증.xlsx` → 이전 결과 (참고)
- `02_생산관리/실적_GERP_실적현황.xlsx` → 실적 기반 라인매핑 10,871건

## 실패 조건
- openpyxl 열기 불가
- 헤더 인식 실패 (첫 5행 컬럼 없음)
- A+B = 0건 (정규화/컬럼 오류 가능)
- 판정별 건수 합계 ≠ 기준 총 건수

## 중단 기준
- 기준 파일 경로 미존재
- 병합셀로 헤더 None 과반
- 컬럼 사용자 확인 없이 임의 결정 시도
- 컬러코드 분리 등 구조 변경 필요 → 사용자 확인 전까지

## 검증 항목
- 기준 품번 총 건수 결과표 명시
- 판정별 합계 = 기준 총 건수 (전수)
- C·D·E·F에 판정사유+조치의견
- 접두어 미제거 / 컬러코드 보존
- 미확인 가정에 "⚠️ 가정"

## 되돌리기
- 읽기 전용 → 원본 파일 변경 X
- 결과 엑셀 재생성으로 복구
- 원본 미수정 → 되돌리기 불필요
