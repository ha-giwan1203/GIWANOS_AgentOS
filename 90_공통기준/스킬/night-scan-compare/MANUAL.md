# night-scan-compare — MANUAL

> 상세 6Phase / 실패조건 / 검증. SKILL.md는 호출 트리거 + 80줄 요약.

## 목적
BI 생산실적과 MES 스캔실적을 일자별 비교하여 차이 자동 분석. 대상 라인/야간구분 지정 → BI 추출 → MES API 조회 → 비교 엑셀 대입.

## 대상 파일
| 역할 | 경로 |
|------|------|
| BI 원본 | `05_생산실적/BI실적/대원테크_라인별 생산실적_BI.xlsx` |
| 비교 엑셀 | `05_생산실적/조립비정산/{MM}월/야간_생산_{라인명}.xlsx` |

## 비교 엑셀 시트
| 시트 | 역할 |
|------|------|
| 생산기준DATA | BI 생산실적 (자동/붙여넣기) |
| 스캔실적DATA | MES 스캔실적 입력 |
| 일자별비교 | 생산량 vs 스캔실적 수식 비교표 |
| 월간요약 | KPI + 차트 데이터 |

## 총 차이 산식
- 총 차이 = SUM(생산량 - 스캔실적) where 스캔실적 ≠ 빈값
- 스캔미입력 날짜 자동 제외 (수식: `=IF(D="","",C-D)`)

## 실행 단계

### Phase 0: 인수 파싱
1. 라인명·월 분리. 인수 없으면 사용자에게 질문
2. 년도는 현재 연도 (시스템 시간)
3. 비교 엑셀 경로 결정
4. 파일 미존재 시 중단

### Phase 1: BI 최신본 갱신
1. Z드라이브 원본 확인
2. 로컬 파일과 수정일자 비교
3. Z 최신이면 로컬 복사 (production-result-upload 0단계 재사용)
4. Z 접근 불가 시 로컬 사용 + 경고

### Phase 2: 날짜 추출
1. BI에서 대상 라인/야간/월 조건으로 실적 있는 날짜 목록
2. openpyxl `data_only=True`로 생산량 함께 읽기

### Phase 3: MES 스캔실적 조회
1. CDP `cdp_tabs.py`로 MES 탭 로그인 검증
2. CDP `cdp_exec.py`로 iframe 내부 PqGrid API 엔드포인트 확인
3. MES API 직접 호출 (전체 날짜 일괄)
   - 엔드포인트: `/prdtstatus/selectPrdtRsltLine.do?prdtDa={YYYYMMDD}`
   - 응답: `json.data.list[]` → `lineCd`, `shiftsCd`(02=야간), `prdtQty`
4. 대상 라인 + 야간(shiftsCd=02) 필터링
5. 데이터 없는 날짜 식별 → 빈값 처리

### Phase 4: 엑셀 대입
1. openpyxl `data_only=False` (수식 보존)
2. 생산기준DATA: 클리어 후 BI 데이터 재대입 (A~K)
3. 스캔실적DATA: 클리어 후 날짜(A)/라인(B)/스캔실적(C)/비고(D). MES없음 → C 빈값 + D "MES데이터없음"
4. 일자별비교: 날짜(A)/라인(B) + C~H 수식 행별 생성 + Row 3 합계 수식 갱신
5. 월간요약: 날짜(F), 수식(G~I) 갱신

### Phase 5: 양식 통일
1. 테이블 객체 범위 확장 (tbl_scan, tbl_compare ref 갱신)
2. 개별 셀 fill 제거 → `PatternFill(fill_type=None)`
3. 조건부 서식: 백업 → 삭제 → 새 범위 재적용
   - 불일치: `FFFCE4D6` (주황)
   - 일치: `FFE2EFDA` (초록)
   - 스캔미입력: `FFF2F2F2` (회색)
4. 셀 서식 통일: 기준 행의 font/alignment/border/number_format 복사

### Phase 6: 검증
1. 테이블 범위 일치
2. 개별 fill = None
3. 조건부 서식 범위 = 데이터 행 전체
4. MES없음 날짜 빈값
5. 월간요약 행 수/수식
6. 고아데이터 없음

## 핵심 규칙
- CDP 기본 사용 (Chrome MCP는 토론모드만)
- MES 로그인 필수 검증 → 안 되어있으면 사용자 요청
- API 직접 호출 (UI 조작 X) — `fetch()` + iframe contentWindow
- `data_only=False` 수식 보존
- 양식 3종 세트 함께 처리 (테이블 + fill + 조건부 서식)
- 빈값 vs 0: MES없음 = `None` (0 아님)

## 인수
| 인수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| 라인명 | O | - | SP3M3, SD9A01 등 |
| 월 | O | - | 3, 4 등 |
| 년 | X | 현재년 | 조회 대상 년도 |

## 산출물
- `야간_생산_{라인명}.xlsx` — 4시트 데이터+수식+양식 완비
- 터미널 요약 (총 생산량, 총 스캔실적, 차이, 차이 발생일)

## 실패 조건
- 비교 엑셀 미존재 (Phase 0)
- MES 로그인 만료 (CDP 탭 미감지)
- MES API 빈 배열인데 해당 월 실적 있어야 함
- BI 대상 라인/월 데이터 0건

## 중단 기준
- 비교 엑셀 미존재 → 즉시 중단 (Phase 0)
- MES 미로그인 → 사용자 요청 후 대기 (자동 진행 금지)
- openpyxl 열기 실패 → 중단 (파일 손상)
- BI 시트 구조 예상과 다름 → 중단 → 컬럼 확인

## 검증 항목
- 테이블 범위 = 데이터 행 수
- 개별 fill = None
- 조건부 서식 범위 = 데이터 전체
- MES없음: C 빈값 + D "MES데이터없음"
- 월간요약 수식 참조 정상
- 고아데이터 0건

## 되돌리기
- 비교 엑셀은 매 실행 시 클리어 후 재입력 → 재실행이 곧 복구
- BI/MES 원본 읽기 전용 — 복구 불필요
- 비교 엑셀 수식 파괴 시: 템플릿에서 빈 엑셀 재복사 후 재실행

## 관련 스킬
- `production-result-upload` — MES 실적 업로드
- `assembly-cost-settlement` — 조립비 정산
- `cdp-wrapper` — CDP 브라우저 래퍼
