# flow-chat-analysis output 운영 규칙

이 폴더는 Flow 대화 분석의 수집물과 2차 가공 산출물을 두는 로컬 작업 공간이다.  
대부분의 `csv/xlsx/json` 계열 파일은 Git 공유 대상이 아니므로, 최종본 여부를 폴더 구조로 구분한다.

## 하위 폴더 기준

- `raw/`
  - 1차 수집 원본
  - 예: Flow 원문 로드, ERP 추출, MES 추출
- `draft/`
  - 검토 전 초안
  - 예: match candidates, report draft, 임시 분류본
- `final/`
  - 검토 후 확정본
  - 예: 확정 관리대장, 확정 보고서, 배포용 workbook
- `debug/`
  - 디버그/실험 로그
  - 예: network dump, DOM 실험, 수집 실패 재현 자료

## 승격 규칙

1. 자동 생성 직후 파일은 기본적으로 `raw/` 또는 `draft/`에 둔다.
2. 사람이 분류와 수치 검토를 끝낸 뒤에만 `final/`로 승격한다.
3. 재현/장애 분석 목적 파일은 `debug/`에 둔다.
4. 루트에 남아 있는 기존 파일은 레거시 산출물이다. 다음 수정 시 적절한 하위 폴더로 이동한다.

## 파일명 권장

- 원본: `YYYY-MM-DD_source_topic.ext`
- 초안: `YYYY-MM-DD_topic_draft.ext`
- 확정: `YYYY-MM-DD_topic_final.ext`
- 디버그: `YYYY-MM-DD_topic_debug.ext`
