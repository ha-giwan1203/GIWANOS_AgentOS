# MANUAL — assy-registration-check 상세

## 개요

라인별 기준정보 파일에 등재된 모품번이 ERP **조립비 현황관리(New)** 에 주라인+짝라인 모두 등록되어 있는지 사전 점검. 누락분 list-up + ERP 정정 가이드 산출. 라인별 룰만 `lines.json`에 추가하면 동일 스크립트로 처리.

## 파일 구조

```
assy-registration-check/
├── SKILL.md           스킬 메타
├── MANUAL.md          (이 문서)
├── run_check.py       진입점
├── lookup_lines.py    Hdr+Dtl wrapper (erp_lookup.py 재사용)
├── classify.py        모품번별 라인 합집합 → 분류
├── report.py          xlsx + summary.md
└── lines.json         라인별 룰 config
```

## 핵심 동작

1. `lines.json`에서 LINE 룰 로드 (마스터 경로 템플릿·시트명·헤더 행·품번/예외 컬럼명·예외값)
2. UNC 경로 read-only 시도 → 임시 폴더로 복사 (락 회피)
3. openpyxl `data_only=True, read_only=True`로 시트 read
4. 헤더 행에서 품번/예외/차종 컬럼 자동 감지 (헤더명 매칭, 부분 일치 허용)
5. 모품번 추출 (숫자형 셀도 정규화) + 결측·헤더 잔여 필터 (영숫자 5자 이상)
6. 동일 품번 면제/비면제 충돌 시 첫 행 적용 + WARN
7. ERP 환경 자동 진입 (`erp_lookup.py` 재사용)
8. 모품번별 Hdr API → 컬러별 N건 → 컬러별 Dtl API → 라인 등록 N건
9. blackout 자동 대기 (매시 :10~13 / :20~23 / :30~33 / :40~43 / :50~53)
10. 모품번 라인 합집합 → 분류 (10종 + 컬러편차)
11. xlsx (시트별) + summary.md + raw json 캐시

## lines.json 키 정의

| 키 | 필수 | 의미 |
|----|------|------|
| `primary_line_cd` | ✓ | 주라인 코드 (예: SP3M3) |
| `paired_line_cd` | | 짝라인 코드 (예: HCAMS02). null 또는 빈 문자열이면 단독 라인 |
| `master_file` | ✓ | 마스터 파일 경로 템플릿. placeholder: `{YYYY}/{YY}/{MM}/{DD}` |
| `sheet_name` | ✓ | 시트명 |
| `header_row` | ✓ | 헤더 행 번호 (1-base) |
| `pn_column_header` | ✓ | 품번 컬럼 헤더명 (부분 일치 허용) |
| `exempt_column_header` | | 예외 컬럼 헤더명. 없으면 "" |
| `exempt_value` | | 예외값 (예: "ELR"). 셀 값 부분 일치로 면제 판정 |
| `exempt_skips` | | 면제 시 검증 생략 항목 ("paired" 또는 "primary"). 현재는 "paired"만 지원 |
| `comment` | | 주석 |

## CLI

| 인자 | 의미 |
|------|------|
| `LINE` (positional) | lines.json 키 |
| `--applied YYYY-MM-DD` | ERP 적용일 (default: 오늘) |
| `--master <path>` | 마스터 파일 경로 직접 지정 (템플릿 무시) |
| `--use-cache` | 기존 `_cache/erp_lookup_*.json` 재사용. ERP 조회 skip. 분류·산출만 재생성 |
| `--limit N` | 테스트용 — 모품번 N개로 제한 |

## 산출물

저장 위치: `05_생산실적/조립비정산/{MM+1}월/등록누락점검_{LINE}_{YYYYMMDD}/`

| 파일 | 내용 |
|------|------|
| `등록누락점검_{LINE}_{YYYYMMDD}.xlsx` | 시트 10종 (분류별) + raw요약 |
| `summary.md` | 분류별 건수 + 차종 분포 + 컬러편차 + 다음 행동 |
| `_cache/erp_lookup_{LINE}_{YYYYMMDD}.json` | ERP raw 응답 (재실행 시 `--use-cache`로 활용) |

## 분류 룰

먼저 입력 행을 **면제 / 일반**으로 분기 (`exempt_column` 값에 `exempt_value` 부분 포함).

**일반 행** — primary + paired 둘 다 필수
- 정상 / primary 누락 / paired 누락 / 양쪽 누락 / 미등록

**면제 행** — primary만 필수, paired 부재 정상
- 정상(면제) / primary 누락(면제) / 미등록(면제) / 이상(면제+paired 등록)

**컬러 편차** — 같은 모품번 컬러별로 primary/paired 등록 여부 불일치. 도메인 결함 후보. 위 분류와 별개 시트(중복 가능).

## 실패 조건

| 상황 | 대응 |
|------|------|
| UNC read 실패 | `--master <로컬 경로>` 직접 지정 |
| 시트명 불일치 | `lines.json`의 `sheet_name` 수정 |
| 품번 컬럼 미감지 | `pn_column_header` 수정 — 부분 일치 가능 |
| 헤더 행 불일치 | `header_row` 수정 |
| CDP 9224 dead | erp_lookup.py가 자체 launch — 사용자 추가 작업 X |
| OAuth 정체 | erp_lookup.py 자체 fallback (layout.do 직접 이동) |
| Hdr API 0건 | 모품번이 ERP에 등록 0 — 미등록으로 분류 |
| 분류 합 ≠ unique | 코드 결함 — 즉시 보고 |

## 신규 라인 추가 절차

1. `lines.json`에 새 엔트리 추가 (위 키 정의 참조)
2. 첫 실행: `python run_check.py {LINE} --limit 5` 로 5건만 검증
3. 추출 unique·면제 건수 + 분류 합 일치 확인
4. 결함 없으면 `--limit` 빼고 전체 실행

## 알려진 제약

- erp_lookup.py 재사용 — 본 스킬은 wrapper only. erp_lookup.py가 깨지면 본 스킬도 영향
- 컬러별 라인 등록 편차가 도메인 결함이 아닌 정상 케이스인 경우 컬러편차 시트에 false positive 가능 — 사용자 확인 필요
- 현재 `exempt_skips`는 "paired"만 지원. "primary" 면제는 향후 확장
- ERP 적용일은 단일 — 적용 기간 분기 검증은 향후 확장
