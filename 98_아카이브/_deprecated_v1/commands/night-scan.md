# /night-scan — 야간 스캔실적 비교

BI 생산실적과 MES 스캔실적을 비교하여 엑셀에 자동 대입한다.

## 인수
- `$ARGUMENTS` — `{라인명} {월}` (예: `SP3M3 3`, `SD9A01 4`)

## 실행 순서

### Phase 0: 인수 파싱
1. 라인명과 월을 분리한다. 인수가 없으면 사용자에게 질문한다.
2. 년도는 현재 연도 사용 (시스템 시간 확인)
3. 비교 엑셀 경로 결정: `05_생산실적/조립비정산/{MM}월/야간_생산_{라인명}.xlsx`
4. 비교 엑셀 존재 여부 확인. 없으면 사용자에게 알림 후 중단.

### Phase 1: BI 최신본 갱신
1. Z드라이브 원본(`Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx`) 수정일자 확인
2. 로컬보다 최신이면 복사. 접근 불가 시 로컬 사용 + 경고.

### Phase 2: BI 날짜 추출
1. BI 파일(`05_생산실적/BI실적/대원테크_라인별 생산실적_BI.xlsx`) 열기
2. '대원테크' 시트에서 라인명(E열) + 야간(F열) + 년월(H열) 필터
3. 실적 있는 날짜 목록 + 생산량 추출

### Phase 3: MES 스캔실적 조회
1. CDP로 MES 탭 확인 (`cdp_tabs.py --match-url mes-dev`)
2. MES 로그인 상태 검증. 미로그인 시 사용자에게 로그인 요청 후 대기.
3. CDP JS 실행으로 MES API 일괄 호출:
   ```
   fetch('/prdtstatus/selectPrdtRsltLine.do?prdtDa={YYYYMMDD}')
   → json.data.list[] 에서 lineCd={라인명} & shiftsCd='02' 필터
   ```
4. 날짜별 스캔실적 수집, MES 데이터 없는 날짜 식별

### Phase 4: 엑셀 대입
1. 비교 엑셀 openpyxl로 열기 (data_only=False)
2. 생산기준DATA: 기존 데이터 전체 클리어 → BI 데이터 재대입 (재실행 시 고아방지)
3. 스캔실적DATA: 날짜/라인/스캔실적/비고 입력 (MES없음 → 빈값 + "MES데이터없음")
3. 일자별비교: 날짜/라인 + C~H수식 생성, 합계 수식 범위 갱신
4. 월간요약: 날짜/수식 갱신

### Phase 5: 양식 통일
1. 테이블 객체(tbl_scan, tbl_compare) 범위를 데이터 행 수에 맞춰 확장
2. 전 데이터 행 개별 fill 제거 (`PatternFill(fill_type=None)`)
3. 조건부 서식: 기존 규칙 백업 → ConditionalFormattingList 교체 → 새 범위 적용
4. 셀 서식(font/alignment/border/number_format) 기준 행에서 복사 적용

### Phase 6: 검증
1. 테이블 범위 = 데이터 행 전체
2. 개별 fill = None (전 행)
3. 조건부 서식 범위 = 데이터 행 전체
4. MES없음 날짜 = 빈값
5. 월간요약 행 수/수식 정상
6. 고아데이터 없음

### Phase 7: 결과 보고
```
총 생산량(BI): {N} ea
총 스캔실적(MES): {N} ea
총 차이: {N} ea
차이 발생일: {N}일 / 스캔미입력: {N}일
파일: {경로}
```

## 주의사항
- CDP 기본 사용. Chrome MCP 사용 금지.
- MES API는 iframe contentWindow의 fetch()로 호출 (동일 origin 필요)
- 엑셀 파일이 열려있으면 저장 실패 → 사용자에게 닫기 요청
- 수식/참조 구조 보존 (data_only=False)
- 양식 3종(테이블범위 + fill제거 + 조건부서식) 반드시 함께 처리
