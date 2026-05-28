# 20260528 P-BOM Guard Review

## 요약

- 대상: `90_공통기준/스킬/d0-production-plan/run.py`
- 목적: Phase 5 `final_save` MES 일괄 거부 전에 P-BOM 미등록 품번을 자동 제외
- 결론: 구현 PASS. 실제 MES 송신은 하지 않고, 함수 단위 dry-run 시뮬레이션으로 검증 완료
- commit: Claude 검증 통과 조건이므로 보류

## 변경 내용

| 구분 | 내용 |
|---|---|
| Phase 1 | 추출 직후 기존 `--exclude` 적용 후 PROD_NO 목록 수집 로그 추가 |
| Phase 5 | `sendMesFlag='N'` preflight 호출 후 `P-BOM 등록 안됨. [LINE, PNO]` 패턴 파싱 |
| 자동 제외 | 미등록 PROD_NO를 누적 제외하고 preflight를 반복 |
| 실제 저장 | preflight PASS 후 `sendMesFlag='Y'` 본 저장은 1회만 호출 |
| fallback | `--no-pbom-guard` 옵션 추가 |
| 적용 범위 | morning/evening, SP3M3/SD9A01, HTTP-only/browser 경로 |

## endpoint 판단

| 항목 | 판단 |
|---|---|
| 전용 P-BOM 조회 API | 정확 endpoint 확정 불가 |
| 선택한 방식 | 기존 Phase 5 `final_save` payload를 `sendMesFlag='N'`으로 사전 호출 |
| 이유 | SmartMES API 가이드 없이도 실제 저장 경로의 MES 검증 메시지를 그대로 사용 가능 |

## 검증

| 검증 항목 | 결과 |
|---|---|
| Python compile | PASS |
| P-BOM 메시지 파싱 | PASS: `RSP3SC0245`, `RSP3SC0246` 검출 |
| 17건 시뮬레이션 | PASS: 2건 제외, 15건 통과 |
| 정상 케이스 | PASS: 제외 0건, 17건 유지 |
| 본 저장 호출 횟수 | PASS: `sendMesFlag='Y'` 1회 |
| 실제 MES 송신 | 미실행: 로컬 함수 dry-run 검증만 수행 |

## 확인 명령

```powershell
python -m py_compile '90_공통기준\스킬\d0-production-plan\run.py'
```

```powershell
@'
# final_save_via_http monkeypatch dry-run:
# - sendMesFlag=N: RSP3SC0245, RSP3SC0246 순차 반환
# - sendMesFlag=Y: 최종 1회만 성공 반환
'@ | python -
```

## 남은 쟁점

| 쟁점 | 상태 |
|---|---|
| 실제 SmartMES P-BOM endpoint | 미확정. 현재 방식은 endpoint 없이 동작하는 보수적 fallback |
| 실서버 연동 검증 | Claude 검증 또는 현장 실행 시 확인 필요 |
| commit | Claude 검증 후 진행 |

