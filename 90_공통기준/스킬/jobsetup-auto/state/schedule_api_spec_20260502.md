# schedule API spec (v3.3 근거) — 2026-05-02

> dnSpy 디컴파일 + 라이브 실측 검증
> 출처: `ServiceAgent.GetProductionSchedule` (MESClient.exe)

## endpoint

| 항목 | 값 |
|------|-----|
| Method | POST |
| Path | `/v2/prdt/schdl/list.api` |
| Server (dev) | `http://lmes-dev.samsong.com:19220` |
| Content-Type | `application/json; charset=UTF-8` |
| Headers | `tid`(uuid32) + `chnl=lmes` + `from=lmes` + `to=LMES` + `lang=ko` + `usrid=LMES` + `token` |

## request body

```json
{"prdtDa": "YYYYMMDD", "lineCd": "SP3M3"}
```

`AddJsonBody(new { param.prdtDa, param.lineCd })` 만 직렬화 (다른 필드는 무시됨).

## response (ScheduleDTO)

```json
{
  "statusCode": "200",
  "statusMsg": "...",
  "rslt": {
    "items": [
      {
        "prdtRank": 1,
        "pno": "RSP3SC0646",
        "pnoRev": "A",
        "lineCd": "SP3M3",
        "prdtDa": "20260501",
        "regNo": <int|null>,
        "revNo": "...",
        "incngQty": <int|null>,
        // ... (33+ properties — pfCd / ficSheetNo / procNo / cartypeCd 등)
      }
      // ... rank 2, 3, ...
    ],
    "itemCnt": <int>,
    "rsltCnt": <int>
  }
}
```

## 라이브 검증 (2026-05-02 토요일)

| date | line | items | rank=1 |
|------|------|-------|--------|
| 20260502 (토) | SP3M3 | 0 | (휴일 — 자동 abort) |
| 20260501 (금) | SP3M3 | 22 | RSP3SC0646_A ✅ (morning xlsm 일치) |
| 20260430 (목) | SP3M3 | 38 | RSP3PC0129_A ✅ (HANDOFF 세션132 일치) |
| 20260429 (수) | SP3M3 | 32 | RSP3SC0383_A ✅ (screen_analysis 일치) |

3 일자 모두 morning xlsm 추출 + chain 인자 주입 결과와 100% 일치 — schedule API가 SmartMES 마스터 데이터 원본임을 확인.

## v3.3 적용 위치

`run_jobsetup.py`:
- `call_schedule(prdtDa, lineCd)` — POST + 응답 파싱 + prdtRank 정렬
- `resolve_first_sequence(prdtDa, lineCd)` — rank=1 항목 회수, 없으면 None
- `--auto-resolve-pno` flag — 자동 회수 + 사용자 인자 cross-check (불일치 시 abort)
- 사용자 `--pno` 명시 + auto-resolve 동시 사용 + 값 동일 → OK
- 사용자 `--pno` 명시 + auto-resolve 동시 + 값 다름 → ABORT

## 운영 사용 예

```bash
# 매일 morning chain (xlsm 추출 의존성 제거)
python run_jobsetup.py --mode commit-all --auto-resolve-pno

# 검증 (xlsm 결과와 cross-check)
python run_jobsetup.py --mode list-only --auto-resolve-pno --pno <xlsm_pno>

# 휴일 테스트 (abort 정상 동작)
python run_jobsetup.py --mode list-only --auto-resolve-pno --prdt-da 20260502
```
