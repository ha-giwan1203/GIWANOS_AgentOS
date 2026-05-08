# gerp-unregistered-check — MANUAL

> 상세 절차 / 결함 후보 / 카테고리 정의 / 실패 조건. SKILL.md는 트리거 + 80줄 요약.

## 목적

매월 정산 빌더(`build_formula_version.py`) 산출물 신뢰성 검증 + GERP 미등록 품번을 ERP 정정 워크플로우에 맞게 5종으로 정밀 분류. 사용자가 4월 오류리스트 양식을 GERP 정정 가이드로 사용하는 워크플로우(2026-05-08 발화) 정착.

## 호출 시점

- 매월 정산 빌더 실행 후 (`build_formula_version.py {MM}` 완료 후)
- 사용자가 오류리스트 신뢰 못 한다 발화 시
- ERP 정정 작업 진입 전 양식 확인

## 본체 파일

`05_생산실적/조립비정산/{MM+1}월/정산_수식버전_{MM}월.xlsx`
- 시트 17개: 정산집계 / GERP_입력 / 구ERP_입력 / 미등록품번_정리 / 라인 10개 / 오류리스트 / 유형별요약
- raw 데이터(GERP_입력·구ERP_입력)가 본체 안에 들어 있어 별도 raw 파일 불필요

## 입력

- `MM`: 정산 대상 월 (01~12)
- 옵션 `--force`: VALUES 사본 강제 재생성

## 워크플로우

### Phase A: 본체 복사 + 값변환

1. `~$정산_수식버전_{MM}월.xlsx` 락 확인 → 락 시 사용자 닫기 안내 후 중단
2. 본체 복사 → `05_생산실적/조립비정산/{MM+1}월/오류리스트_재검증_{YYYYMMDD}/정산_수식버전_{MM}월_VALUES.xlsx`
   (정산 도메인 작업폴더 내부 — 99_임시수집 X)
3. `convert_to_values.py` 실행:
   - pywin32 `DispatchEx`로 별도 Excel 인스턴스 (본체 잠금 영향 X)
   - `Workbook.Open()` → `Application.CalculateFull()` → 모든 시트 `UsedRange.Value = UsedRange.Value`
   - SaveAs → Quit

### Phase B: 행단위 재검증

`verify_error_labels.py` 실행:

1. VALUES 사본 로드 (`data_only=True`)
2. GERP_입력 vendor 매핑 구축 — col 7=품번, col 19=업체코드, col 3=라인코드
3. 라인시트(SD9A01~ISAMS03) col 19 카테고리 IF 수식 결과를 Python으로 재현
   - 미등록 영역(`※ 기준 미등록 GERP 품번` 헤더 이후) 분기 적용
   - 빌더 라벨 vs 재산출 라벨 비교 → 불일치 row 기록
4. 오류리스트 시트 row 5~ 매핑 검증
5. Coverage 검증 + 합계 검증

### Phase C: vendor 정밀 분류 (GERP누락 케이스)

GERP누락 행마다 5종 분류:

```python
all_vendors      = GERP raw 모든 라인에서 발견된 vendor 집합
same_line_vendors = (라인, 품번) 매칭 vendor
all_lines         = GERP raw에서 발견된 라인 집합

if not all_vendors:
    'GERP raw 부재'
elif same_line_vendors:
    if 비-0109만:        '같은라인 비0109'
    elif 0109+비-0109:   '같은라인 0109+비0109'
    elif 0109만:         '같은라인 0109'
else:
    f'다른라인만({"+".join(all_lines)})'
```

### Phase D: 산출물 작성

- `verify_summary.md` — 4종 통과기준 + 빌더 결함 결론 + 세션 진단 정정 + GERP누락 진짜 의미
- `mismatch_rows.xlsx` — 4시트
- `category_distribution.csv`
- `vendor_analysis.csv`

## 빌더 분류 로직 참조 (build_formula_version.py)

### 라인시트 col 19 IF 수식 (line 654~664) 우선순위
정상 → 다중단가분배(정상) → GERP만 → 구ERP만 → 기준단가누락 → 수량차이(다중단가합산검증) → 수량차이(중복확인필요) → 단가차이/기타

### 사용자 5종 매핑 `_map_cat_to_user_type()` (line 988)
- GERP만(구ERP등록필요) / GERP만(마스터+구ERP등록필요) → 구실적누락
- 구ERP만(GERP등록필요) → GERP누락
- 수량차이(다중·중복) → 수량차이
- 단가차이/기타·기준단가누락 → 정산차이
- 정상·다중단가분배(정상) → 오류리스트 제외

### 라인시트 컬럼 (A~S, 1~19)
A=품번 / B=업체코드 / C=라인코드 / D=ASSY / E=Usage / F=품번분류 / G=기준단가 / H=차종 / I=GERP주q / J=GERP야q / K=GERP주amt / L=GERP야amt / M=구ERP주q / N=구ERP야q / O=구ERP주amt / P=구ERP야amt / Q=차이amt / R=차이qty / S=카테고리

## 통과기준 (Phase E)

| # | 기준 | PASS 조건 |
|---|------|-----------|
| 1 | 라벨 정확성 | 빌더라벨 ≡ 재산출라벨 (불일치 0) |
| 2 | 매핑 정합 | err_type 매핑 불일치 0 + 라인시트 미매칭 0 |
| 3 | Coverage | 라인시트 차이≠0 행 ≡ 오류리스트 행 |
| 4 | 합계 정합 | 정산집계 차이 ≡ 오류리스트 차이 |

4/4 PASS = 빌더 정상. 1~3건 FAIL = 빌더 점검 후 재실행.

## 잠재 결함 후보 (FAIL 시 점검 순서)

1. **라벨 불일치** — 미등록 영역(※ 헤더) 분기 누락. 빌더 IF 수식 분기 추가/재정렬
2. **매핑 불일치** — `_map_cat_to_user_type()` 신규 internal 카테고리 매핑 추가
3. **Coverage 차이** — `EXCLUDE_CATS` 동기화 누락 (새 분기 추가 시)
4. **합계 차이** — vendor 필터(0109) 또는 Usage 환산 결함
5. **catch-all '단가차이/기타' 도달 행** — 정의 안 된 케이스 도달 시 분기 추가 필요
6. **GERP누락 = 같은라인 0109** — 같은 라인 GERP에 있는데 SUMIFS 결과 0 → 라인시트 SUMIFS 키(라인,품번,단가) 결함 가능

## 실패 조건

| 증상 | 원인 | 조치 |
|------|------|------|
| `[ERROR] 본체 락` | 사용자 Excel에서 본체 열림 | Excel 닫고 재실행 |
| `pywin32 미설치` | Python 환경 결함 | `pip install pywin32` |
| `[ERROR] 파일 없음` | MM 인자 잘못 / 빌더 미실행 | MM 확인 + `build_formula_version.py {MM}` 선행 |
| 라벨 불일치 다수 | 빌더 IF 수식 변경됨 | recompute_category() 동기화 |
| Coverage 차이 음수 | EXCLUDE_CATS 누락 | EXCLUDE_CATS에 새 분기 추가 |

## ERP 정정 워크플로우 (사용자)

`verify_summary.md` GERP누락 분류 표 보고:

1. **GERP raw 부재 케이스**: GERP 단가관리 → 조립비 현황관리 → 품번 검색 → 라인별 등록 현황 확인 → 미등록이면 신규 등록
2. **다른라인만 케이스**: 이미 다른 라인에 등록됐으니 해당 라인에만 추가 등록
3. **같은라인 비0109**: 협력사 분리 룰에 따라 처리 (사용자 결정)

**시간 제약**: 매시 `x0:10~13/20~23/30~33/40~43/50~53` 조회 차단. 진입 전 시간 체크.

## 변경 이력

- 2026-05-08 (세션148): 신설. 4월 정산 사용자 신뢰 회복 검증 + 세션146 vendor 진단 정정 + 5종 vendor 분류 신설 + ERP 정정 가이드 정착.
