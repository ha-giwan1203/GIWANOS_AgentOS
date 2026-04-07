---
name: chomul-module-partno
description: "초물표 모듈품번(RSP) 일괄 반영 스킬. 초물표 xls 파일의 공용품번 박스에 모듈품번을 입력/수정하고, 라인코드를 SP3S03에서 SP3M3로 변경하며, 뷰/구분선을 통일한다. '초물표 수정', '모듈품번 입력', '초물표 RSP', 'RSP 반영', '라인코드 변경', '초물표 일괄', 'SP3M3 변경' 등을 언급하면 반드시 이 스킬을 사용할 것. Windows win32com 기반 Excel COM 자동화."
---

# 초물표 모듈품번 일괄 반영

초물표 xls 파일의 공용 품번 박스(AB5:AJ14 영역)에 모듈품번(RSP...)을 반영하고,
라인코드를 SP3S03 → SP3M3로 변경하며, Normal View/구분선을 통일하는 자동화 스킬.

## 작업 폴더

```
C:\Users\User\Desktop\업무리스트\03_품번관리\초물관리
├── _backup/          # 원본 xls 49개 (절대 수정 금지)
├── _output/          # 복사본만 수정
├── SP3M3_모듈품번_최신.xlsx   # 기준정보
└── 초물표_모듈품번_작업가이드.md  # 상세 가이드
```

## 실행 전 확인

1. `_backup/` 폴더에 원본 xls 파일이 있는지 확인
2. `SP3M3_모듈품번_최신.xlsx` 기준정보 파일 존재 확인
3. Windows 환경 + Python + pywin32(win32com) 설치 여부 확인
4. Excel이 백그라운드에서 실행 중이면 먼저 종료

## 기준정보 로드

`SP3M3_모듈품번_최신.xlsx`를 openpyxl로 읽는다.

| 컬럼 | 내용 |
|------|------|
| 1(A) | 차종 |
| 2(B) | 품번 (매칭 키) |
| 3(C) | SUB품번 |
| 4(D) | 모듈품번(RSP) |

품번을 키로 하는 딕셔너리를 만든다. 품번은 정규화(대문자+공백제거+하이픈제거) 후 저장.
동일 품번이 여러 행에 있을 수 있으므로, 품번→RSP 1:1 매핑으로 저장하되 중복 시 마지막 값 사용.

## 매칭 로직

**SUB품번 기준 매칭 금지.** 62건의 SUB 중복이 존재하므로 잘못된 RSP가 매칭된다.

각 시트의 H12 셀(완성품 품번)을 정규화하여 기준정보와 매칭한다.

```python
def normalize(s):
    return str(s).upper().replace(' ','').replace('-','')

def get_h12(ws):
    val = str(ws.Cells(12, 8).Value or '')
    # 멀티라인이면 첫 번째만
    first_line = val.split('\n')[0].strip()
    return normalize(first_line)
```

## AB5 파싱 규칙

```python
def parse_ab5(ws):
    val = str(ws.Cells(5, 28).Value or '')
    lines = [l.strip() for l in val.split('\n') if l.strip()]
    # lines[0] = 라인코드, lines[1] = 공용품번, lines[2] = RSP (있으면)
    has_rsp = len(lines) >= 3 and lines[2].startswith('RSP')
    return lines, has_rsp
```

## 작업 구조 — 2단 분리

### 1단계: 전체 공통 적용 (모든 시트)

뷰와 구분선만 처리. AB5는 건드리지 않는다.

```python
# 각 시트에 대해
win = wb.Windows(1)
win.View = 1  # Normal View
ws.DisplayPageBreaks = False
ws.ResetAllPageBreaks()
# 구분선 통일 (전체 UsedRange 기준)
```

### 2단계: RSP 값 처리 (H12 매칭 후 분기)

| 조건 | 판정 | 처리 |
|------|------|------|
| RSP 없음 + 기준매칭 | **입력** | C안 셀 분리 |
| RSP 있음 + 기준RSP 다름 | **수정** | C안 셀 분리 |
| RSP 있음 + 기준RSP 같음 | **값 유지** | C안 셀 분리 |
| H12 미매칭 | **미매칭** | C안 셀 분리 |

## 케이스별 처리

### [입력] 원본 2줄 → 3줄 추가

기존 AB5 2줄째(공용품번) 값을 먼저 읽어서 그대로 사용한다.

```python
lines, _ = parse_ab5(ws)
existing_sub = lines[1] if len(lines) >= 2 else ''

# 기존 병합 해제
cell = ws.Cells(5, 28)
if cell.MergeCells:
    cell.MergeArea.UnMerge()

# AB5:AJ14 전체 클리어
ws.Range('AB5:AJ14').ClearContents()

# 3분할 재병합
COLOR_BLACK = 0x000000
COLOR_RED = 0x0000FF  # BGR

# 영역1: AB5:AJ9 = SP3M3
rng1 = ws.Range('AB5:AJ9')
rng1.Merge()
rng1.Value = 'SP3M3'
rng1.Font.Size = 85
rng1.Font.Bold = True
rng1.Font.Color = COLOR_BLACK
rng1.Font.Name = 'HY헤드라인M'
rng1.HorizontalAlignment = -4108  # Center
rng1.VerticalAlignment = -4108
rng1.WrapText = False
rng1.ShrinkToFit = False

# 영역2: AB10:AJ12 = 공용품번 (기존 2줄째 원본값, LH빨강/RH파랑)
rng2 = ws.Range('AB10:AJ12')
rng2.Merge()
try:
    rng2.Value = int(existing_sub)
except:
    rng2.Value = existing_sub
rng2.Font.Size = 110
rng2.Font.Bold = True
rng2.Font.Color = COLOR_RED if lhrh == 'LH' else COLOR_DARKBLUE
rng2.Font.Name = 'HY헤드라인M'
rng2.HorizontalAlignment = -4108
rng2.VerticalAlignment = -4108
rng2.WrapText = False
rng2.ShrinkToFit = False

# 영역3: AB13:AJ14 = RSP (부분색상)
rng3 = ws.Range('AB13:AJ14')
rng3.Merge()
rng3.Value = new_rsp
rng3.Font.Size = 80
rng3.Font.Bold = True
rng3.Font.Color = COLOR_BLACK
rng3.Font.Name = 'HY헤드라인M'
rng3.HorizontalAlignment = -4108
rng3.VerticalAlignment = -4108
rng3.WrapText = False
rng3.ShrinkToFit = False

# RSP 부분색상 적용
apply_rsp_color(rng3, new_rsp, lhrh)
```

### [수정] 기존 RSP ≠ 기준 RSP

C안 셀 분리 통일 적용. 입력 케이스와 동일한 3분할 재병합을 수행한다.

```python
lines, _ = parse_ab5(ws)
existing_sub = lines[1] if len(lines) >= 2 else ''

# 기존 병합 해제
cell = ws.Cells(5, 28)
if cell.MergeCells:
    cell.MergeArea.UnMerge()

# AB5:AJ14 전체 클리어
ws.Range('AB5:AJ14').ClearContents()

# 3분할 재병합 (입력 케이스와 동일)
# 영역1: AB5:AJ9 = SP3M3
rng1 = ws.Range('AB5:AJ9')
rng1.Merge()
rng1.Value = 'SP3M3'
rng1.Font.Size = 85
rng1.Font.Bold = True
rng1.Font.Color = COLOR_BLACK
rng1.Font.Name = 'HY헤드라인M'
rng1.HorizontalAlignment = -4108
rng1.VerticalAlignment = -4108
rng1.WrapText = False
rng1.ShrinkToFit = False

# 영역2: AB10:AJ12 = 공용품번 (LH빨강/RH파랑)
rng2 = ws.Range('AB10:AJ12')
rng2.Merge()
try:
    rng2.Value = int(existing_sub)
except:
    rng2.Value = existing_sub
rng2.Font.Size = 110
rng2.Font.Bold = True
rng2.Font.Color = COLOR_RED if lhrh == 'LH' else COLOR_DARKBLUE
rng2.Font.Name = 'HY헤드라인M'
rng2.HorizontalAlignment = -4108
rng2.VerticalAlignment = -4108
rng2.WrapText = False
rng2.ShrinkToFit = False

# 영역3: AB13:AJ14 = RSP (부분색상)
rng3 = ws.Range('AB13:AJ14')
rng3.Merge()
rng3.Value = new_rsp
rng3.Font.Size = 80
rng3.Font.Bold = True
rng3.Font.Color = COLOR_BLACK
rng3.Font.Name = 'HY헤드라인M'
rng3.HorizontalAlignment = -4108
rng3.VerticalAlignment = -4108
rng3.WrapText = False
rng3.ShrinkToFit = False

# RSP 부분색상 적용
apply_rsp_color(rng3, new_rsp, lhrh)
```

### [값 유지 / 미매칭] C안 셀 분리 통일 적용

C안 셀 분리 통일 적용. 입력 케이스와 동일한 3분할 재병합을 수행한다.
값 유지는 기존 RSP를 그대로 사용하고, 미매칭은 기존 RSP(있으면)를 그대로 사용한다.

```python
lines, has_rsp = parse_ab5(ws)
existing_sub = lines[1] if len(lines) >= 2 else ''
existing_rsp = lines[2] if has_rsp else ''

# 기존 병합 해제
cell = ws.Cells(5, 28)
if cell.MergeCells:
    cell.MergeArea.UnMerge()

# AB5:AJ14 전체 클리어
ws.Range('AB5:AJ14').ClearContents()

# 3분할 재병합 (입력 케이스와 동일)
# 영역1: AB5:AJ9 = SP3M3
rng1 = ws.Range('AB5:AJ9')
rng1.Merge()
rng1.Value = 'SP3M3'
rng1.Font.Size = 85
rng1.Font.Bold = True
rng1.Font.Color = COLOR_BLACK
rng1.Font.Name = 'HY헤드라인M'
rng1.HorizontalAlignment = -4108
rng1.VerticalAlignment = -4108
rng1.WrapText = False
rng1.ShrinkToFit = False

# 영역2: AB10:AJ12 = 공용품번 (LH빨강/RH파랑)
rng2 = ws.Range('AB10:AJ12')
rng2.Merge()
try:
    rng2.Value = int(existing_sub)
except:
    rng2.Value = existing_sub
rng2.Font.Size = 110
rng2.Font.Bold = True
rng2.Font.Color = COLOR_RED if lhrh == 'LH' else COLOR_DARKBLUE
rng2.Font.Name = 'HY헤드라인M'
rng2.HorizontalAlignment = -4108
rng2.VerticalAlignment = -4108
rng2.WrapText = False
rng2.ShrinkToFit = False

# 영역3: AB13:AJ14 = RSP (부분색상, 기존값 유지)
rng3 = ws.Range('AB13:AJ14')
rng3.Merge()
if existing_rsp:
    rng3.Value = existing_rsp
    rng3.Font.Size = 80
    rng3.Font.Bold = True
    rng3.Font.Color = COLOR_BLACK
    rng3.Font.Name = 'HY헤드라인M'
    rng3.HorizontalAlignment = -4108
    rng3.VerticalAlignment = -4108
    rng3.WrapText = False
    rng3.ShrinkToFit = False
    # RSP 부분색상 적용
    apply_rsp_color(rng3, existing_rsp, lhrh)
else:
    # RSP 없는 미매칭: 영역3 빈 상태로 병합만
    rng3.Font.Size = 80
    rng3.Font.Bold = True
    rng3.Font.Name = 'HY헤드라인M'
    rng3.HorizontalAlignment = -4108
    rng3.VerticalAlignment = -4108
```

## RSP 부분색상

중간 영문 코드별 고유 색상 (LH/RH 무관):

| 코드 | 색상 | BGR값 |
|------|------|-------|
| SC | 빨강 | 0x0000FF |
| SE | 초록 | 0x008000 |
| PC | 보라 | 0x800080 |
| HE | 주황 | 0x0080FF |
| AC | 갈색 | 0x004080 |

```python
MID_COLORS = {
    'SC': 0x0000FF,   # 빨강
    'SE': 0x008000,   # 초록
    'PC': 0x800080,   # 보라
    'HE': 0x0080FF,   # 주황
    'AC': 0x004080,   # 갈색
}

def apply_rsp_color(rng, rsp):
    """중간 영문 코드별 고유 색상 적용"""
    mid_start = 4  # RSP3 이후
    mid_end = mid_start
    for ch in rsp[mid_start:]:
        if ch.isdigit():
            break
        mid_end += 1

    if mid_end > mid_start:
        mid_text = rsp[mid_start:mid_end]
        color = MID_COLORS.get(mid_text, 0x000000)
        chars = rng.GetCharacters(mid_start + 1, mid_end - mid_start)
        chars.Font.Color = color

def get_lhrh(h12_normalized):
    prefix = h12_normalized[:5]
    if prefix in ('88810', '89870'):
        return 'LH'
    elif prefix in ('88820', '89880'):
        return 'RH'
    return None
```

## 배경색 규칙

```python
# 공용품번 헤더: 하늘색
ws.Range("AB1:AJ4").Interior.Color = 0xFFCC99  # ColorIndex 37

# 공용품번 내용: 흰색
ws.Range("AB5:AJ14").Interior.Color = 0xFFFFFF
```

## 안쪽 구분선 제거

3분할 영역 사이 경계선 없음:
```python
for idx in [11, 12]:  # InsideHorizontal, InsideVertical
    ws.Range("AB5:AJ14").Borders(idx).LineStyle = -4142  # xlNone
```

## 미매칭 empty 처리

공용품번이 비어있는 시트는 시트명을 공용품번으로 사용:
```python
if not existing_sub:
    existing_sub = ws.Name  # 시트명 사용
```

## 구분선 표준안

전체 시트 UsedRange 기준으로 통일한다. 파일별 개별 추출 금지.

```python
def apply_border_standard(ws):
    used = ws.UsedRange
    last_row = used.Row + used.Rows.Count - 1
    last_col = min(used.Column + used.Columns.Count - 1, 36)  # AJ=36

    full_range = ws.Range(ws.Cells(1, 2), ws.Cells(last_row, last_col))

    # 전체 내부선 Thin
    for idx in [11, 12]:
        b = full_range.Borders(idx)
        b.LineStyle = 1
        b.Weight = 2
        b.Color = 0x000000

    # 전체 외곽선 Medium
    for idx in [7, 8, 9, 10]:
        b = full_range.Borders(idx)
        b.LineStyle = 1
        b.Weight = -4138
        b.Color = 0x000000
```

## 자체검증 (수정 케이스)

적용 직후 즉시 확인:

```python
def verify_modification(ws, expected_sub, expected_rsp):
    lines, _ = parse_ab5(ws)
    ok = True
    if lines[0] != 'SP3M3':
        ok = False
    if lines[1] != str(expected_sub):
        ok = False
    if len(lines) >= 3 and lines[2] != expected_rsp:
        ok = False
    return ok
```

실패 시 해당 시트 FAIL 처리하고 다음 시트로 진행한다.

## 실행 흐름 (전체)

```
1. 기준정보 로드 (SP3M3_모듈품번_최신.xlsx)
2. _backup 파일 목록 순회
3. 각 파일을 _output으로 복사
4. COM으로 _output 파일 열기
5. 각 시트에 대해:
   a. 1단계: 뷰/구분선 공통 적용
   b. H12 매칭 → 판별
   c. 2단계: 케이스별 처리
   d. 자체검증 (수정 케이스)
6. 저장 → 닫기
7. 결과 로그 출력
```

## 보고 형식

처리 완료 후 아래 형식으로 보고:

```
파일: JW1 초물표.xls
  901: 수정 RSP3SC0255→RSP3SC0509 PASS
  902: 수정 RSP3SC0254→RSP3SC0510 PASS
  911(추석PT): 미매칭 라인코드만 PASS
  921(추석PT): 미매칭 라인코드만 PASS
```

## 주의사항

1. `_backup` 원본은 절대 수정하지 않는다
2. SUB품번으로 매칭하지 않는다 (H12 품번 기준만 사용)
3. AB5 2줄째 공용품번은 시트명이 아니라 기존 값을 읽어서 그대로 사용한다
4. 모든 케이스(입력/수정/값유지/미매칭)에서 C안 셀 분리(AB5:AJ9/AB10:AJ12/AB13:AJ14) 통일 적용한다
5. 값 유지/미매칭 케이스에서도 기존 병합을 해제하고 C안 3분할로 재병합한다
6. `작업가이드.md`를 반드시 먼저 읽고 규칙을 확인한다
7. 배경색: AB1:AJ4=하늘색(0xFFCC99), AB5:AJ14=흰색(0xFFFFFF)
8. 공용품번 박스 안쪽 구분선 제거 (InsideH/V = xlNone)
9. 미매칭 empty는 시트명을 공용품번으로 사용

## 실패 조건
- COM 연결 실패 (Excel Application 생성 불가)
- 기준정보 파일(`SP3M3_모듈품번_최신.xlsx`) 미존재 또는 로드 실패
- H12 셀 품번 파싱 실패 (병합셀/빈값으로 매칭 불가)
- 자체검증(`verify_modification`) 실패 — 적용값과 기대값 불일치

## 중단 기준
- `_backup` 원본 파일에 쓰기가 감지되면 즉시 중단 (원본 보호 위반)
- COM 에러 연속 3회 발생 시 중단 → Excel 프로세스 상태 점검
- 기준정보 RSP 매칭률이 50% 미만이면 중단 → 기준정보 버전 확인

## 검증 항목
- 각 시트 자체검증: `verify_modification()` PASS 여부
- 처리 결과 집계: 입력/수정/유지/미매칭/실패 건수 합계 = 전체 시트 수
- 배경색 적용: AB1:AJ4=하늘색, AB5:AJ14=흰색 전시트 확인
- Normal View 전환: 모든 시트 view 설정 확인
- `_output` 폴더에만 결과 파일 존재, `_backup`은 변경 없음

## 되돌리기 방법
- `_output` 결과 파일 삭제 후 `_backup`에서 재복사하여 재실행
- 개별 시트 실패 시: 해당 시트만 FAIL 처리, 다음 시트로 진행 (부분 복구 불필요)
- `_backup` 원본은 항상 보존되므로 전체 재실행 가능

## 1차 완료 현황 (2026-03-26)

- 49파일 315시트 전체 적용
- SP3M3 315/315, 배경색 315/315, Normal View 315/315
- 입력 22 / 수정 9 / 유지 171 / 미매칭 101 / 실패 0
- **1차 PASS**

