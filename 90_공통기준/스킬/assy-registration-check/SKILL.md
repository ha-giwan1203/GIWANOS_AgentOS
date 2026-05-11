---
name: assy-registration-check
description: 라인 기준정보 파일의 모품번이 ERP 조립비 현황관리(New)에 주라인+짝라인 모두 등록되어 있는지 사전 점검. 누락분 list-up + 사용자 ERP 정정 가이드. 라인별 룰은 lines.json에서 추가.
trigger: "라인 등록 점검", "조립비 라인 등록 누락", "기준정보 ERP 등록 점검", "/assy-registration-check {LINE}"
grade: B
---

# 조립비 라인 등록 누락 점검 (월 작업 사전 점검)

> 상세 절차·라인 페어 정의·예외 룰 추가법은 [MANUAL.md](MANUAL.md). 도메인 룰: `05_생산실적/조립비정산/CLAUDE.md`.
> 첫 케이스: 세션152(2026-05-09) SP3M3 ↔ HCAMS02 검증.

## 절차 (요약)

```bash
cd 90_공통기준/스킬/assy-registration-check
python run_check.py SP3M3                        # 적용일 default = 오늘
python run_check.py SP3M3 --applied 2026-05-11   # 적용일 지정
python run_check.py SP3M3 --master <path>        # 마스터 파일 직접 지정
```

내부 흐름 (자동):
1. `lines.json`에서 `LINE` 룰 로드 → 마스터 파일 경로·시트·헤더·예외 컬럼 결정
2. UNC 경로 read (락 회피 위해 임시 복사 후 openpyxl `data_only=True`)
3. 품번 컬럼 + 예외 컬럼 추출 → unique 모품번 + 면제/일반 플래그
4. ERP 환경 점검 (CDP 9224 + OAuth + 조립비 현황관리 iframe 진입)
5. 모품번별 ERP 검색 (Hdr API) → 컬러별 N건 → 컬러별 라인 등록 (Dtl API)
6. 모품번별 라인코드 합집합 → 분류 (정상 / primary 누락 / paired 누락 / 양쪽 누락 / 미등록 / 컬러 편차)
7. 산출물 (`05_생산실적/조립비정산/{MM+1}월/등록누락점검_{LINE}_{YYYYMMDD}/`)

## 산출물

| 파일 | 역할 |
|------|------|
| `등록누락점검_{LINE}_{YYYYMMDD}.xlsx` | 분류별 시트(일반 4종 + 면제 3종 + 컬러편차 + 정상 + raw) |
| `summary.md` | 분류별 건수 + 차종 분포 + ERP 정정 액션 가이드 |
| `erp_lookup_{LINE}_{YYYYMMDD}.json` (위치: `_cache/`) | ERP raw 응답 캐시 (재실행 시 활용) |

## 분류 정의

먼저 입력 행을 **면제 / 일반**으로 분기 (`exempt_column` 값 == `exempt_value`).

**일반 행 (primary + paired 둘 다 필수)**
| 분류 | 조건 | ERP 정정 |
|------|------|---------|
| 정상 | primary ✓ + paired ✓ | pass |
| primary 누락 | primary ✗ + paired ✓ | primary 라인 추가 등록 |
| paired 누락 | primary ✓ + paired ✗ | paired 라인 추가 등록 |
| 양쪽 누락 | primary ✗ + paired ✗ + 다른라인 등록 | 두 라인 모두 추가 등록 |
| 미등록 | ERP 어느 라인에도 0건 (0109 기준) | 신규 단가 등록 |

**면제 행 (primary만 필수, paired 부재 정상)**
| 분류 | 조건 | ERP 정정 |
|------|------|---------|
| 정상(면제) | primary ✓ (paired 무관) | pass |
| primary 누락(면제) | primary ✗ + 다른라인 등록 | primary 라인 추가 등록 |
| 미등록(면제) | ERP 어느 라인에도 0건 | 신규 단가 등록 |
| 이상(면제+paired 등록) | 면제 표기인데 paired 등록 발견 | 사용자 확인 — 도메인 룰 위배 후보 |

**컬러 편차 (별도 경고)**: 같은 모품번 N개 컬러 중 일부만 라인 등록. 도메인 결함 후보.

## 라인 추가 (다른 라인 활용)

`lines.json`에 신규 엔트리 추가:
```json
{
  "{LINE}": {
    "primary_line_cd": "...",
    "paired_line_cd": "...",   // null이면 단독 라인
    "master_file": "<UNC 또는 로컬 경로 템플릿. {YYYY}/{MM}/{DD}/{YY} placeholder 지원>",
    "sheet_name": "...",
    "header_row": 2,
    "pn_column_header": "...",
    "exempt_column_header": "...",   // 없으면 ""
    "exempt_value": "...",            // 없으면 ""
    "exempt_skips": "paired"          // 면제 시 paired 검증 생략
  }
}
```

## ERP 정정 시간 제약 ⚠️

GERP 매시 5구간 차단(x0:10~13/x0:20~23/x0:30~33/x0:40~43/x0:50~53). 자동 대기 — 사용자 추가 작업 X.

## 실패 시

- UNC 경로 read 실패 → `--master` CLI로 로컬 사본 직접 지정
- pywin32/openpyxl/playwright 미설치 → 안내 후 종료
- CDP 9224 dead → 자체 launch (erp_lookup.py 패턴)
- 본체 락 → 임시 복사로 우회 (자동)
- 상세 → MANUAL.md "실패 조건"

## 분리 — 다른 스킬과 차이

- 본 스킬: 기준정보 파일 → ERP 라인 등록 사전 점검 (월 시작 전·진행 중)
- `gerp-unregistered-check`: 월 마감 후 빌더 산출물 라벨 검증 + ERP 정정 가이드
