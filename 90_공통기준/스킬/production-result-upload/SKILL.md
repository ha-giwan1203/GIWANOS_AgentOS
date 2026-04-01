---
name: mes-production-upload
description: >
  MES 생산실적 자동 업로드 스킬.
  사용자가 "실적 업로드", "MES 업로드", "생산실적 입력", "BI 업로드",
  "실적 올려", "MES 실적", "생산 데이터 업로드" 등을 언급하면 반드시 이 스킬을 사용할 것.
  BI 엑셀 파일에서 지정 날짜 데이터를 추출하여 MES SaveExcelData.do API로 직접 POST한다.
  기존 수동 업로드(엑셀 다운 → MES 팝업 → 파일 선택 → 저장) 프로세스를 완전 자동화.
---

# MES 생산실적 자동 업로드 (API 직호출)

## 목적
매일 반복되는 MES 생산실적 업로드 업무를 자동화한다.
BI 엑셀 파일에서 데이터를 읽어 MES API로 직접 POST하므로,
수동 엑셀 다운로드 → MES 팝업 열기 → 파일 업로드 → 저장 과정이 필요 없다.

## 기본 설정값
- **BI 파일 경로**: `C:/Users/User/Desktop/업무리스트/05_생산실적/BI실적/대원테크_라인별 생산실적_BI.xlsx`
- **MES URL**: `http://mes-dev.samsong.com:19200`
- **API 엔드포인트**: `/prdtstatus/SaveExcelData.do`
- **업로드 대상**: 사용자 지정 날짜(기본: 오늘)
- **최대 처리 범위**: 한 달치 (31일)

## 실행 전 확인사항
- CDP 브라우저(`--remote-debugging-port=9222`, 프로필 `.flow-chrome-debug`)가 실행 중이거나 자동 실행 가능해야 함
- MES System에 이미 로그인되어 있어야 함 (프로필에 세션 유지)
- Z드라이브(`Z:\★ 라인별 생산실적\`)에 접근 가능해야 함

## CDP 브라우저 실행/종료

**실행:**
```python
subprocess.Popen([
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "--remote-debugging-port=9222",
    r"--user-data-dir=C:\Users\User\.flow-chrome-debug",
    "http://mes-dev.samsong.com:19200/layout/layout.do",
    "--no-first-run", "--no-default-browser-check"
])
```

**종료 (필수 — 아래 방식만 사용):**
```python
cdp = browser.contexts[0].pages[0].context.new_cdp_session(browser.contexts[0].pages[0])
cdp.send("Browser.close")
```

**금지:** `taskkill //F //IM chrome.exe` 사용 금지 — 기존 브라우저까지 종료되고 복구 팝업 발생

## BI 파일 자동 갱신 (0단계 — 업로드 전 필수)

> **이 섹션이 BI 파일 경로의 단일 원본이다.** production-report 등 다른 스킬은 여기를 참조한다.

BI 파일은 별도 스케줄러 없이 **업로드 실행 시 자동으로 최신본을 가져온다.**

| 항목 | 값 |
|------|-----|
| 원본 | `Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx` |
| 로컬 | `C:\Users\User\Desktop\업무리스트\05_생산실적\BI실적\대원테크_라인별 생산실적_BI.xlsx` |

```python
import os, shutil

SRC = r"Z:\★ 라인별 생산실적\대원테크_라인별 생산실적_BI.xlsx"
DST = r"C:\Users\User\Desktop\업무리스트\05_생산실적\BI실적\대원테크_라인별 생산실적_BI.xlsx"

if not os.path.exists(SRC):
    print("ERROR: Z드라이브 원본 접근 불가 — 네트워크 확인 필요")
    # 로컬 파일이 있으면 경고 후 로컬로 진행, 없으면 중단
else:
    src_mtime = os.path.getmtime(SRC)
    dst_mtime = os.path.getmtime(DST) if os.path.exists(DST) else 0
    if src_mtime > dst_mtime:
        shutil.copy2(SRC, DST)
        print(f"BI 파일 갱신 완료 (원본: {src_mtime}, 기존: {dst_mtime})")
    else:
        print("BI 파일 이미 최신")
```

- Z드라이브 접근 불가 시 → 로컬 파일로 진행하되 **"원본 미갱신 상태"** 경고 표시
- 원본이 더 새로우면 복사 후 진행
- 이미 최신이면 스킵

## 네트워크 제약사항
- CDP 브라우저의 MES 세션을 활용하여 iframe jQuery로 API 호출
- Playwright `connect_over_cdp('http://localhost:9222')` → `page.evaluate()` 방식
- **운영 표준: iframe 내부 jQuery $.ajax 사용** (fetch/requests 직접 호출은 500 에러 발생 — 실증 확인됨)

## 안전 원칙
- **기존 데이터 절대 수정/삭제 안 함** — 신규 날짜만 INSERT
- 업로드 전 반드시 MES 기존 데이터 조회하여 **중복 확인**
- 중복 발견 시 사용자 확인 없이 진행하지 않음
- 한 번에 최대 한 달치(31일)까지만 처리

## ★ 데이터 품질 검증 (업로드 전 필수)

BI 추출 후 반드시 아래 검증을 통과해야 업로드 진행:

1. **생산량(COL15) None/0 검사**: 전체 행 중 생산량이 None 또는 0인 행이 있으면
   → "BI 데이터 미완성 (생산량 없음)" 안내 후 **업로드 중단**
   → 사용자가 명시적으로 "빈 데이터라도 올려" 요청한 경우에만 진행
2. **핵심값 존재 확인**: 업체명(COL1), 라인(COL5), 날짜(COL8), 생산량(COL15) 중 하나라도 비면 해당 행 제외
3. **건수 비교만으로 검증 PASS 판정 금지**: 업로드 후 MES 조회 시 건수뿐 아니라 **생산량 합계**를 BI 원본과 대조

검증 코드 예시:
```python
# BI 추출 후 품질 검사
empty_qty = [r for r in items if r.get('COL15') in (None, '', '0', 'None')]
if empty_qty:
    print(f"⚠ 생산량 없는 행: {len(empty_qty)}/{len(items)}건 — 업로드 중단")
    # 사용자 확인 없이 진행하지 않음
```

---

## ★ 중요: 반드시 한 번에 전송

**SaveExcelData.do는 배치 단위로 UPSERT 처리한다.**
분할 전송 시 나중 배치가 이전 배치의 같은 라인+날짜 데이터를 덮어쓴다.
따라서 **같은 날짜의 모든 데이터를 반드시 하나의 요청으로 보내야 한다.**

- 하루치 데이터가 보통 12~15건이므로 분할 불필요
- 여러 날짜를 업로드할 때도 **날짜별로 한 번씩** 전송
- 절대로 같은 날짜 데이터를 여러 배치로 나누지 않는다

---

## 실행 절차

### 0단계: MES 탭 확인 + iframe 사전 로드 (필수)

API 호출 전 반드시 iframe을 먼저 로드해야 한다. iframe이 없으면 jQuery 참조 에러 발생.

```
1. tabs_context_mcp(createIfEmpty=true) — 실패 시 한 번 더 재시도
2. MES 탭 확인 (mes-dev.samsong.com 포함 탭 검색)
3. 없으면 새 탭 → http://mes-dev.samsong.com:19200/layout/layout.do 이동
4. iframe 사전 로드 (JS 실행):
```

```javascript
document.querySelector('iframe[name="iframe-1"]').src = '/prdtstatus/viewPrdtRsltByLine.do';
```

5. 2초 대기 후 iframe.contentWindow.$ 존재 확인
6. Tab no longer exists 에러 시 → 1번부터 재시도

**이 단계를 건너뛰면 SaveExcelData.do 호출 시 iframe null 에러 발생.**

### 1단계: 사용자 의도 파악

사용자에게 확인할 사항:
- **업로드 날짜**: 특정 날짜 또는 날짜 범위 (기본: 당일 제외 전일까지)
- "실적 올려줘" → BI 최신일 ~ MES 미등록 날짜 자동 계산 (당일 제외)
- "3/20~3/23 실적 올려" → 해당 범위
- "이번 주 실적" → 월~금 범위 자동 계산 (당일 제외)

날짜 범위가 31일 초과하면 거부하고 범위를 좁히도록 안내한다.
**당일 데이터는 입력 대상 아님** — 사용자가 명시적으로 요청하지 않는 한 제외.

### 2단계: BI 파일에서 데이터 추출 (Python)

```python
import openpyxl
import json
from datetime import datetime

BI_PATH = "C:/Users/User/Desktop/업무리스트/05_생산실적/BI실적/대원테크_라인별 생산실적_BI.xlsx"
TARGET_DATE = "2026-03-23"  # 사용자 지정 날짜 (단일)
# 범위 처리 시: TARGET_FROM = "2026-03-20", TARGET_TO = "2026-03-23"

wb = openpyxl.load_workbook(BI_PATH, data_only=True, read_only=True)
ws = wb.active

# 날짜별로 그룹핑하여 추출
by_date = {}
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    date_val = row[7]  # COL8 = 날짜
    if date_val is None:
        continue
    date_str = str(date_val)[:10]

    # 단일 날짜
    if date_str != TARGET_DATE:
        continue
    # 범위 처리 시: if not (TARGET_FROM <= date_str <= TARGET_TO): continue

    item = {}
    for i in range(22):
        val = row[i]
        if val is None:
            val = ""
        elif isinstance(val, datetime):
            val = val.strftime("%Y-%m-%d")
        elif isinstance(val, float):
            if val == int(val):
                val = str(int(val))
            else:
                val = str(round(val, 6))
        else:
            val = str(val)
        item[f"COL{i+1}"] = val

    if date_str not in by_date:
        by_date[date_str] = []
    by_date[date_str].append(item)

wb.close()

# 결과 저장 (날짜별 그룹)
output_path = "/sessions/wonderful-eager-albattani/mes_upload_data.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(by_date, f, ensure_ascii=False)

for d, items in sorted(by_date.items()):
    print(f"{d}: {len(items)}건")
print(f"저장: {output_path}")
```

### 3단계: MES 탭 확인

Chrome 탭 중 MES가 열려있는지 확인한다.
없으면 새 탭에서 `http://mes-dev.samsong.com:19200/` 으로 이동한다.

### 4단계: MES 기존 데이터 조회 (중복 확인)

업로드 전 해당 날짜의 기존 대원테크 데이터를 조회하여 중복을 확인한다.

```javascript
(async () => {
  const FROM = '2026-03-23';
  const TO = '2026-03-23';

  const params = new URLSearchParams({
    S_FROM: FROM,
    S_TO: TO,
    S_CMPY_NM: '대원테크',
    pq_curPage: '1',
    pq_rPP: '1000'
  });

  const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?' + params);
  const result = await resp.json();
  const rows = result.data.list;

  return `기존 대원테크 데이터: ${rows.length}건 (${FROM} ~ ${TO})`;
})()
```

**중복 판단:**
- 기존 데이터가 있으면 → 사용자에게 "이미 N건 존재합니다. 덮어쓸까요?" 확인
- 기존 데이터가 없으면 → 바로 업로드 진행

### 5단계: MES API로 업로드 (핵심)

**반드시 iframe의 jQuery를 사용하고, contentType을 application/json으로 지정해야 한다.**

```javascript
(async () => {
  const iframe = document.querySelector('iframe[name="iframe-1"]');
  const $ = iframe.contentWindow.$;

  // ★ 같은 날짜의 데이터는 반드시 하나의 배열로 한 번에 전송
  const data = PYTHON_EXTRACTED_DATA;  // Python에서 추출한 해당 날짜의 excelList 배열

  const payload = JSON.stringify({"excelList": data});

  return new Promise((resolve) => {
    $.ajax({
      url: "/prdtstatus/SaveExcelData.do",
      type: "post",
      data: payload,
      contentType: "application/json; charset=utf-8",
      success: function(res) {
        resolve(`업로드 결과: ${res.statusCode} - ${res.statusTxt} (${data.length}건)`);
      },
      error: function(xhr, status, err) {
        resolve(`실패: ${status} - ${err}`);
      }
    });
  });
})()
```

**여러 날짜 업로드 시:**
날짜별로 순차 전송한다. 같은 날짜 데이터는 절대 분할하지 않는다.

```javascript
(async () => {
  const iframe = document.querySelector('iframe[name="iframe-1"]');
  const $ = iframe.contentWindow.$;

  // 날짜별 데이터 객체 { "2026-03-20": [...], "2026-03-21": [...] }
  const byDate = PYTHON_EXTRACTED_BY_DATE;
  const dates = Object.keys(byDate).sort();
  const results = [];

  for (const date of dates) {
    const data = byDate[date];
    const payload = JSON.stringify({"excelList": data});

    const res = await new Promise((resolve) => {
      $.ajax({
        url: "/prdtstatus/SaveExcelData.do",
        type: "post",
        data: payload,
        contentType: "application/json; charset=utf-8",
        success: function(r) { resolve(r); },
        error: function(x, s, e) { resolve({statusCode: "500", statusTxt: s + ' ' + e}); }
      });
    });

    results.push(`${date}: ${res.statusCode} (${data.length}건)`);
  }

  return results.join('\n');
})()
```

### 6단계: 결과 검증

업로드 후 MES에서 해당 날짜를 다시 조회하여 건수를 확인한다.

```javascript
(async () => {
  const FROM = '2026-03-23';
  const TO = '2026-03-23';

  const params = new URLSearchParams({
    S_FROM: FROM,
    S_TO: TO,
    S_CMPY_NM: '대원테크',
    pq_curPage: '1',
    pq_rPP: '1000'
  });

  const resp = await fetch('/prdtstatus/selectPrdtRsltByLine.do?' + params);
  const result = await resp.json();
  const rows = result.data.list;

  const summary = rows.map(r => `${r.LINE_CD}/${r.WORK_CYCLE} qty:${r.RESULT_QUANTITY}`).join(', ');
  return `검증: 대원테크 ${rows.length}건\n${summary}`;
})()
```

BI 추출 건수와 MES 조회 건수가 일치하는지 확인한다.

### 7단계: 완료 보고

```
MES 생산실적 업로드 완료 ({날짜})
- BI 추출: {N}건
- MES 업로드: 성공
- 검증: MES 조회 {N}건 일치
- 방식: SaveExcelData.do API 직호출
```

---

## BI 파일 → MES COL 매핑표

| COL | BI 열 | 헤더명 | DB 컬럼 | 데이터 예시 |
|-----|-------|--------|---------|------------|
| COL1 | A | 업체명 | ASSY_COMPANY | 대원테크 |
| COL2 | B | 유형 | LINE_DIV | 메인서브 |
| COL3 | C | 기종구분 | PF_CD | RETRACTOR |
| COL4 | D | 대표기종 | MODEL_CD | SP3 |
| COL5 | E | 라인명 | LINE_CD | SP3M3 |
| COL6 | F | 야간구분 | WORK_CYCLE | 주간 |
| COL7 | G | 생산인원 | LINE_PERSON | 6 |
| COL8 | H | 날짜 | TRX_DA | 2026-03-23 |
| COL9 | I | 표준UPH | STANDARD_UPH | 340 |
| COL10 | J | C/T | CYCLE_TIME | 9 |
| COL11 | K | 적용효율 | YIELD_RATE | 0.85 |
| COL12 | L | 근무시간(h) | WORK_TIME | 10 |
| COL13 | M | 비가동(h) | WORK_DOWNTIME | 0.5 |
| COL14 | N | 실가동시간(h) | REAL_TIME | 9.5 |
| COL15 | O | 생산량(ea) | RESULT_QUANTITY | 3504 |
| COL16 | P | 품번수(ea) | ORDER_ITEM_COUNT | 9 |
| COL17 | Q | 목표수량(ea) | TARGET_REAL_QUANTITY | 3230 |
| COL18 | R | 실적UPH | RESULT_UPH | 350.4 |
| COL19 | S | UPMH | RESULT_PER_UPH | 58.4 |
| COL20 | T | 실가동UPH | WORKTIME_UPH | 368.84 |
| COL21 | U | 가동효율 | RESULT_EFFICIENCY | 0.876 |
| COL22 | V | 순가동효율 | WORKTIME_EFFICIENCY | 0.922 |

## API 전송 형식 (핵심)

```
메서드: POST
URL: /prdtstatus/SaveExcelData.do
Content-Type: application/json; charset=utf-8
X-Requested-With: XMLHttpRequest (선택)
Body: {"excelList": [{COL1~COL22}, ...]}
```

**반드시 iframe 내부의 jQuery $.ajax를 사용해야 한다.**
fetch API로 보내면 Content-Type 처리 차이로 500 에러 발생.

```javascript
// 올바른 방법
const iframe = document.querySelector('iframe[name="iframe-1"]');
const $ = iframe.contentWindow.$;
$.ajax({
  url: "/prdtstatus/SaveExcelData.do",
  type: "post",
  data: JSON.stringify({"excelList": data}),
  contentType: "application/json; charset=utf-8",
  success: function(res) { /* ... */ }
});
```

## 조회 API

```
메서드: GET
URL: /prdtstatus/selectPrdtRsltByLine.do
파라미터:
  S_FROM: 시작일 (YYYY-MM-DD)
  S_TO: 종료일 (YYYY-MM-DD)
  S_CMPY_NM: 업체명 (대원테크)
  pq_curPage: 1
  pq_rPP: 1000
응답: { data: { list: [...] }, statusCode, statusTxt }
```

---

## 오류 대응

| 상황 | 대응 |
|------|------|
| Chrome 연결 안 됨 | "Claude in Chrome 확장 프로그램을 연결해주세요" 안내 |
| MES 로그인 안 됨 | 직접 로그인 요청 후 재실행 |
| 403 에러 | 로그인 세션 만료 → 브라우저에서 MES 새로고침 후 재실행 |
| 500 에러 (SaveExcelData) | Content-Type 확인, iframe jQuery 사용 여부 확인 |
| BI 파일에 해당 날짜 없음 | "BI 파일에 {날짜} 데이터가 없습니다" 안내 |
| 중복 데이터 존재 | 사용자 확인 후 진행 여부 결정 (덮어쓰기) |
| 31일 초과 요청 | "최대 한 달치까지만 처리 가능합니다" 안내 |
| 생산량 빈 값 | 해당 날짜 BI 데이터 미완성 → "BI 데이터가 아직 채워지지 않았습니다" 안내 |
| iframe null 에러 | 0단계(iframe 사전 로드) 미실행 → iframe src 설정 후 2초 대기 후 재시도 |
| Tab no longer exists | tabs_context_mcp 재호출 → 탭 새로 열기 → 0단계부터 재시도 |
| Grouping not supported | tabs_context_mcp 한 번 더 재시도 |
| BLOCKED: Cookie | 결과를 변수에 저장하고 건수만 반환하는 방식으로 우회 |
| 당일 데이터 요청 | "당일 데이터는 입력 대상이 아닙니다" 안내 (명시 요청 시만 진행) |

## 커스터마이징

- **BI 파일 경로**: 다른 위치의 파일 사용 가능
- **업체명 필터**: 기본 "대원테크", 다른 업체 지정 가능
- **라인 필터**: 특정 라인만 업로드 가능 (Python 추출 시 필터 추가)

