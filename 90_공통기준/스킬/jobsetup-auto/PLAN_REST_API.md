# 잡셋업 v3.0 — SmartMES REST API 직호출 (UI 자동화 완전 폐지)

> 상위: `PLAN_API_FEASIBILITY.md` (시나리오 3으로 일단 판정 → 본 plan에서 시나리오 1로 정정)
> 작성: 2026-05-02
> 결과: 17/17 검사항목 등록 PASS (commit-one + commit-all)

## Context

2026-05-01 1차 평가에서 mesclient.exe TCP 연결만 보고 "표준 HTTP 0건 → 시나리오 3 (REST 불가) → pywinauto UIA 차선책"으로 결론. 그러나 사용자 의도는 **"데이터를 API로 한 번에 밀어넣기"**. UI 자동화로 11공정 17항목 일일이 클릭하는 v2.1은 운영 의도 미부합.

2026-05-02 사용자 지시로 **mesclient.exe 자체에서 endpoint·spec 직접 추출** 진행:
1. `MESClient.exe.config` (.NET 표준 XML) — 전체 endpoint + token + DB 정보 평문 노출
2. `MESClient.exe` PE binary strings — 30+개 REST endpoint path 추출
3. `MESClient.exe` reflection (PowerShell `System.Reflection`) — DTO 33 property 전부 식별
4. dnSpy GUI 디컴파일 — `ServiceAgent.SaveJobSetup` 실제 호출 코드 + 헤더 7개 + path prefix `v2/` 확인

→ 시나리오 1 (완전 하이브리드 가능) 확정. v3.0 본체 작성.

## 확정된 spec (재현 가능)

| 항목 | 값 |
|------|-----|
| MES_SERVER | `http://lmes-dev.samsong.com:19220` (= `210.216.217.95` DNS alias) |
| Auth Token | config 평문 32자 hex (32-char) |
| save URL | `POST /v2/checksheet/check-result/jobsetup/save.api` |
| list URL | `POST /v2/checksheet/check-result/jobsetup/list.api` |
| Content-Type | `application/json; charset=UTF-8` |
| Headers | `tid`(uuid32 hex no dash) + `chnl=lmes` + `from=lmes` + `to=LMES` + `lang=ko` + `usrid=LMES` + `token` |
| HTTP_RESULT_OK | `"200"` |
| Body (save) | JobSetupItem 단일 JSON (마스터 11 + 측정값 12 + production 메타 4 + 옵션 6 = 33 property) |

### JobSetupItem 핵심 property (run_jobsetup.py 적용 중)

마스터 (list.api 응답에서 그대로 사용):
- `prdtDa, lineCd, procNo, procCd, mngAriclCd, mngAriclNm, measrRev, cpSheetNo, cpSheetRevNo, stdDivCd, stdDivNm, mngAriclCmnt`

production 컨텍스트 (qry에서 주입):
- `pno, pnoRev, prdtRank, regNo, revNo`

측정값 (A형은 값 + B형은 빈):
- `x1, x2, x3, x1RsltCd/Nm, x2RsltCd/Nm, x3RsltCd/Nm, finalCheckRsltCd/Nm`

미사용/옵션 (필요 시 확장):
- `pid, mngAriclCmnt, actionCtnts/Nm, abnmlCtnts/Nm, note, specCmnt, lmtValue, ulmtValue, llmtValue, x1Barcd, x2Barcd, x3Barcd, measrRev`

### CommonConst 값 (dnSpy 디컴파일)

```csharp
public static readonly string CHNL = "lmes";
public static readonly string FROM = "lmes";
public static readonly string TO = "LMES";
public static readonly string LANG = "ko";
public static readonly string USRID = "LMES";
public static readonly string HTTP_RESULT_OK = "200";
```

### stdDivCd 매핑

- `"02"` = 측정 (A형)
- `"03"` = 기타 (B형 OK/NG)

### spec 정규식 (screen_analysis_20260429.md)

- A1 대칭: `^([-+]?\d+(?:\.\d+)?)\s*[±]\s*(\d+(?:\.\d+)?)\s*\w*$`
- A2/A3 비대칭: `([-+]?\d+(?:\.\d+)?)\s*\+(\d+(?:\.\d+)?)\s*\w*\s*,?\s*-(\d+(?:\.\d+)?)\s*\w*` (1회 이상)
- A3 = A2 다중 매칭 → 교집합 (`lo=max`, `hi=min`)
- 그 외 = B형 fallback (안전)

## 검증 (2026-05-02)

| 단계 | 결과 |
|------|-----|
| list-only | 17 검사항목 + 11 공정 정확히 회수 (screen_analysis_20260429.md 일치) |
| dry-run | A1/A2/A3 정규분포 난수 정상, A3 교집합 작동 |
| commit-one | `[210/000073] 보더링 후 높이` 1건 → `성공하였습니다.lmes` |
| **commit-all** | **나머지 16건 → saved=16 failed=0** = 17/17 등록 |

총 소요 시간: 17건 / ~30초 (UI 자동화 1건 ~10초 대비 17배 효율).

## v 시리즈 매핑 (보존 정책)

| 파일 | 역할 |
|------|------|
| `run_jobsetup.py` | **v3.0 본체** (REST API) |
| `run_jobsetup_v22.py` | v3.0 PoC 사본 (transition) |
| `run_jobsetup_v21.py` | v2.1 UI 다중 순회 PoC (race 미해결, 폐기 후보) |
| `run_jobsetup_v20.py` | v2.0 pywinauto UI 자동화 본체 (legacy fallback) |
| `run_jobsetup_v2.py` | v2.0 transition 사본 |
| `run_jobsetup_legacy.py` | v1.0 좌표·numpad (legacy fallback) |

REST 인프라 장애 시 v2.0 또는 v1으로 폴백 가능 (boot launcher + UI 본체 그대로).

## 안전 가드

- 기본값 `list-only` (저장 0)
- 4모드 명시: `list-only` → `dry-run` → `commit-one` → `commit-all`
- list.api로 미등록 항목만 자동 필터링 (`finalCheckRsltCd` 빈 것만 commit)
- A형 spec 매칭 실패 시 자동 B형 fallback (안전)
- NG 자동 체크 금지 (사람 판정만)
- 무인 자동 실행은 사용자 입회 시에만

## chain 활성 (Phase 2)

`/d0-plan` SP3M3 morning 종료 후 자동 호출:
```
python run_jobsetup.py --mode commit-all
```

prdtDa는 default(오늘), pno/pnoRev/prdtRank는 morning에서 결정된 첫 서열 인자로 전달 (xlsm 또는 D0 응답에서 추출). morning 정상 종료 후 자동 진행. 사용자 입회 monitor 첫 1회 권장.

## 후속

- v3.1: 다른 라인 (SP3M1, SP3M2 등) 지원 (현재 SP3M3 default만)
- v3.2 [부분 완료, 2026-05-02 세션135]: prod 환경 endpoint 적용 — config 외부화 + `--env dev|prod` flag + 환경변수/config.json/dev_default 3순위 fallback 구조 완성. prod 실값(server·token)은 사용자가 prod MESClient.exe.config 제공 시 채워넣으면 즉시 사용 가능. 검증: dev list-only 17 items + prod 미설정 abort + 환경변수 override PASS
- v3.3: 첫 서열 품번 자동 회수 (GetProductionSchedule API)

## 잔여 위험

- token 평문 저장 (mesclient.exe.config)
- dev 환경 lmes-dev 검증, prod 환경(lmes.samsong.com 등) 미검증
- A3 교집합 정책 검증 1회만 (스크류 C/D)
- B형 fallback이 너무 광범위 (`이물 없을 것` 같은 spec도 자동 OK 처리). 운영 정책 확인 필요
