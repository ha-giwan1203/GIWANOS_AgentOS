# 스킬 사용 기준표 (v1 운영 기준)

| 스킬 | 사용 시점 | 쓰면 안 되는 경우 |
|------|----------|----------------|
| skill-creator | 새 스킬 설계/수정/평가/패키징 요청 | 일반 업무 자동화 요청 |
| adversarial-review | 초안/정책/구조/의사결정 비판적 검토 | 단순 요약이나 설명 요청 |
| line-mapping-validator | 기준 품번 vs 라인배정 정합성 검증 | 일반 품번 조회 |
| line-batch-management | ERP 라인배치 입력 자동화 | 라인배치 검증 (validator 사용) |
| line-batch-mainsub | 메인서브 품번 검색 기반 배치 | OUTER 라인 배치 |
| assembly-cost-settlement | 조립비 정산 DB 채우기/리포트 | 일반 엑셀 작업 |
| zdm-daily-inspection | ZDM 일상점검 자동 입력 | 점검 기준 문의 |
| xlsx/docx/pdf/pptx | 해당 파일 형식 작업 | 단순 내용 질문 |
| youtube-analysis | YouTube URL → 자막 자동 추출 + 분석 | 자막 없는 영상, 단순 URL 확인 |
| flow-chat-analysis | Flow 채팅 품질·설비 이슈 월별 분류/보고 | 일반 채팅 질문, ERP 데이터 기반 보고 |

# 하네스 검증 원칙

- 하네스는 새 스킬 생성·수정·패키지 변경 후 품질 검증이 필요할 때 사용한다.
- 단순 요약, 일반 질의, 단순 문서 편집에는 하네스를 사용하지 않는다.
- 하네스 검증은 Planner → Generator → Evaluator의 3단계 역할 분리 원칙을 유지한다.
- Known Exception은 명시된 경로에 등록된 경우에만 예외로 인정한다.
- FAIL 발생 시 피드백 루프를 통해 재작업한다. 최대 3회, 동일 실패 반복 시 BLOCKED.
