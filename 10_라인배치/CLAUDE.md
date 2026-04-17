# 라인배치 작업 규칙

## 기본 원칙
- 기준 파일이 마스터다
- 접두어 유지 (임의 제거 금지)
- 컬러코드 비교는 2단계로 수행한다: 1) 직접 일치 비교 2) 모품번 확장 비교
- 컬러코드 분리 규칙이 불명확하면 사용자 확인 후 적용
- 애매한 경우 확정하지 않고 판정유보 처리

## ERP 연동 규칙
- 셀렉터 우선순위: data-* → id → CSS+위치 → 텍스트
- 셀렉터 실패 시 스크린샷 찍어 사용자 확인
- 대기 조건은 구체적 완료 조건 + 타임아웃 + 실패 시 행동으로 명시
- 중단 작업은 마지막 처리 위치를 기록하고 재개

## 대상 라인
SD9A01(아우터), SP3M3(메인), ANAAS04(앵커), DRAAS11(디링), HASMS02(홀더센스), HCAMS02(홀더CLR), WAMAS01(웨빙ASSY), WABAS01(웨빙스토퍼), WASAS01(웨빙스토퍼2), ISAMS03(이너센스)

## 관련 스킬
- line-batch-management: 라인배치 입력 자동화
- line-batch-mainsub: 메인서브 라인배치
- line-mapping-validator: 라인배정 정합성 검증

## 관련 에이전트 (도메인 지식 vs 정합성 검증)

| 에이전트 | 역할 | 호출 조건 |
|---------|------|---------|
| `line-batch-domain-expert` | 도메인 지식 질의 (NotebookLM 라인배치_대원테크) | 매핑 규칙·ERP 셀렉터·스킬 계약·재개 규칙·금지 시간대 질문 |
| `line-mapping-validator` | 품번-라인배정 정합성 실물 검증 | ERP 입력 후 엑셀 대조, `/line-mapping-validator` |

- 역할 분리 원칙: **에이전트=도메인 지식, 스킬=실행 레시피** (세션55 영상분석 패턴)
- NotebookLM 응답은 저장소 원본이 권위. 불일치 시 저장소 우선
- 통합 소스: `10_라인배치/notebooklm_source_라인배치_v1.txt` (8개 문서 병합, 2,674줄)
- 노트북 URL: https://notebooklm.google.com/notebook/ff23f265-2211-4722-b5fa-d0cdfae73928

## 빈번 조회 데이터

| 항목 | 값 |
|------|-----|
| ERP URL | http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do |
| 라인 수 | 10개 (SD9A01, SP3M3, ANAAS04, DRAAS11, HASMS02, HCAMS02, WAMAS01, WABAS01, WASAS01, ISAMS03) |
| OUTER row0 기본값 | SD9A01 |
| OUTER 주요 매핑 | WEBBING CUTTING→WABAS01, WEBBING ASSY→WAMAS01, D-RING→DRAAS11, ANCHOR ASSY→ANAAS04, SNAP-ON→ANAAS04, LASER MARKING→LTAAS01 |
| SUB LINE 없는 품목 | INNER BALL GUIDE ASSY, BASE LOCK ASSY, LOCKING ASSY, VEHICLE SENSOR ASSY, INNER SENSOR ASSY |
| 동기화 금지 구간 | 매시 x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53 |

## 진행 현황
세부 재개 위치, 동기화 금지 시간대, 최근 실패 이력은 STATUS.md 참조
