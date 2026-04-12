---
name: line-batch-mainsub
description: >
  ERP 메인서브 라인배치 자동화 스킬. "메인서브 라인배치", "메인서브 배치", "SP3 품번 배치",
  "품번 검색 배치", "메인서브 자동화" 등을 언급하면 이 스킬을 사용할 것.
  SP3메인서브 생산지시서 품번을 검색하고, 하단 SUB ASSY 그리드에 조립라인을 자동 입력 후 저장.
  품번 검색 기반 처리 (searchAndProcess / runQueue).
grade: A
---

# ERP 메인서브 라인배치 자동화

## 개요

SP3메인서브 생산지시서 품번을 ERP에서 순차 검색 → 상단 그리드 행 클릭 → 하단 SUB ASSY 조립라인 입력 → 저장.

- **처리 방식**: 품번 검색 기반 (`searchAndProcess` / `runQueue`)
- **ERP URL**: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`
- **기준정보**: 302개 내장 (2026-03-20 기준)

---

## 동기화 제한 시간 ⚠️

**매시 아래 구간에는 검색·저장 절대 금지:**

| 금지 구간 |
|-----------|
| x0:10 ~ x0:13 |
| x0:20 ~ x0:23 |
| x0:30 ~ x0:33 |
| x0:40 ~ x0:43 |
| x0:50 ~ x0:53 |

`waitSyncClear()` 함수가 자동 처리.

---

## 품명 → 조립라인 매핑 규칙 (LINE_RULES)

**PART_TYPE_NM 우선 체크 (품명보다 먼저):**

| PART_TYPE_NM | 선택값 |
|---|---|
| 공정품_SUB | SWAMS04 |

**품명(MBOM_PART_NM) 매핑 (PART_TYPE_NM 해당 없을 때):**

| 품명 포함 문구 | 선택값 | 비고 |
|---|---|---|
| HOLDER,CLR ASSY | HCAMS02 | 반드시 먼저 체크 |
| HOLDER ALR SENSOR ASSY | HASMS02 | |
| RETRACTION SPRING | SUB LINE 無 | |
| INNER BALL GUIDE ASSY | SUB LINE 無 | |
| BASE LOCK ASSY | SUB LINE 無 | |
| LOCKING ASSY | SUB LINE 無 | |
| VEHICLE SENSOR ASSY | SUB LINE 無 | |
| INNER SENSOR ASSY | SUB LINE 無 | |
| WEBBING CUTTING | WABAS01 | WEBBING ASSY보다 먼저 체크 |
| WEBBING ASSY | WAMAS01 | |

## 행별 처리 규칙

| 행 | 처리 |
|---|---|
| row0 | OUTER_LINE_CD 입력 (공란이면 최빈값 fallback) |
| row1 | SP3M3 고정 |
| row2+ | LINE_RULES 매핑, 해당 없으면 건너뜀 |

---

## STEP 1: JS 함수 등록

```javascript
window._refProdNos = new Set(['89870AT000','89880AT000','89870AT200','89880AT200','89870AT500','89880AT500','89870S1100','89880S1100','89870P4500','89880P4500','89870P2200','89880P2200','7460137000','7460137010','7460137500','7460139000','7460139010','7460139500','7460141000','7460141010','7460142500','7460141510','7460237000','7460237010','7460237500','7460239000','7460239010','7460239500','7460241000','7460241010','7460242500','7460241510','7460137100','7460141100','7460237100','7460241100','7460137600','7460237600','7560137000','7560141000','7560141010','7560141020','7560141030','7560237000','7560241000','7560241010','7560241020','7460141500','7460241500','7560144000','7560244000','88810K2000','88820K2000','88810K2100','88820K2100','89870K2100','89880K2100','89870K2000','89880K2000','88810K2300','88820K2300','898216D100','898226D300','898226D100','898216D300','89870CV500','89870XG500','89880CV500','89880XG500','88820G8001','88820G8201','88810T1000','88810JI000','88820T1000','88820JI000','88820T1100','88820T1200','88820JI100','88820JI200','88810T1500','88810JI500','88820T1500','88820JI500','88810T1100','88810T1200','88810JI100','88810JI200','88810T6000','88810T6100','88810T6300','88820T6000','88820T6100','88810T6500','88820T6300','88820T6500','89870T6000','89880T6000','89870T6100','89880T6100','89870T6500','89880T6500','89870T6600','89880T6600','89870T6700','89880T6700','88810AR000','88810AR100','88820AR100','88820AR000','88810AR500','88820AR500','88810AR300','88820AR300','89880AR000','89870AR000','89880AR100','89870AR100','89870AR500','89880AR500','89870AA000','89870AA010','89880AA000','89880AA010','89870AA600','89870AA610','89880AA600','89880AA610','89870AA500','89870AA510','89870T6400','89870T6800','89880T6400','89880T6800','88810CU100','88810CU300','88820CU100','88820CU300','89870CU000','89880CU000','89870CU100','89880CU100','88810DO000','88810DO300','88820DO000','88810DO200','88820DO200','88820DO300','88810DO500','88810XA500','88820DO500','88820XA500','89870DO000','89880DO000','89870DO200','89880DO200','89870DO500','89880DO500','89870XA500','89880XA500','89870XA510','89870DO510','89880XA510','89880DO510','89870P6000','89880P6000','89870P6100','89880P6100','89870P6500','89880P6500','88810R6000','88820R6000','89870R6000','89880R6000','88810GO000','88810GO200','88820GO000','88810GO300','88820GO200','88810GO500','88820GO300','89870GO000','89880GO000','89870GO200','89880GO200','88810TD000','88820TD000','88820GO500','89870GO500','89870TD000','89880GO500','89880TD000','MO89870R6000','MO89880R6000','88810BQ000','88810BQ100','88820BQ000','88820BQ100','89870XH000','89880XH000','89870XH100','89880XH100','89870XH500','89880XH500','88810SZ000','88810SZ100','88820SZ000','88820SZ100','88810P8000','88820P8000','88810P8500','88820P8500','89870P8500','89880P8500','89873P8500','89883P8500','89870SW000','89880SW000','89870SW200','89880SW200','88810X9500','88820X9500','89870X9200','89880X9200','88810BM000','88820BM000','88820BM200','88810BM100','88820BM100','89870BS000','W89870BS000','89880BS000','W89880BS000','89870BS200','89870DE200','W89870BS200','W89870DE200','89880BS200','89880DE200','W89880BS200','W89880DE200','89870BS500','W89870BS500','89880BS500','W89880BS500','89870DN000','89870DN500','89880DN000','89880DN500','89870P8200','89880P8200','89873P8200','89883P8200','89870AT050','89880AT050','89870AT150','89880AT150','88820GG500','88810GG000','88810GG100','88820GG000','88820GG100','89870GG010','89880GG010','89870GG020','89880GG020','88810NT300','88810NT400','88820NT300','88820NT400','89870NT000','89880NT000','88810NV000','89870NV000','89880NV000','88810BT000','88810BT100','88810BT200','88810BT300','88820BT000','88820BT100','88820BT200','88820BT300','89870BT000','89880BT000','88810BN200','88810BN300','88820BN200','88820BN300','89870BN100','89880BN100','89870XV000','89880XV000','89870XV500','89880XV500','89870GJ000','89880GJ000','89870BP000','89880BP000','88810BP000','88820BP000','89870BP100','89880BP100']);

window._isRefProd = function(prodNo) {
  if (!prodNo) return false;
  if (window._refProdNos.has(prodNo)) return true;
  for (const ref of window._refProdNos) { if (prodNo.startsWith(ref)) return true; }
  return false;
};

window.LINE_RULES = [
  {keyword: 'HOLDER,CLR ASSY',       value: 'HCAMS02'},
  {keyword: 'HOLDER ALR SENSOR ASSY',value: 'HASMS02'},
  {keyword: 'RETRACTION SPRING',     value: 'SUB LINE 無'},
  {keyword: 'INNER BALL GUIDE ASSY', value: 'SUB LINE 無'},
  {keyword: 'BASE LOCK ASSY',        value: 'SUB LINE 無'},
  {keyword: 'LOCKING ASSY',          value: 'SUB LINE 無'},
  {keyword: 'VEHICLE SENSOR ASSY',   value: 'SUB LINE 無'},
  {keyword: 'INNER SENSOR ASSY',     value: 'SUB LINE 無'},
  {keyword: 'WEBBING CUTTING',       value: 'WABAS01'},
  {keyword: 'WEBBING ASSY',          value: 'WAMAS01'},
];

window.getLineValue = function(partNm) {
  if (!partNm) return null;
  for (const rule of window.LINE_RULES) {
    if (partNm.toUpperCase().includes(rule.keyword.toUpperCase())) return rule.value;
  }
  return null;
};

window.setCellValue = function(rowIndx, val, fallbackVal) {
  const $sub = jQuery('#sub_grid_body');
  $sub.pqGrid('editCell', {rowIndx: rowIndx, dataIndx: 'ASSY_LINE_NM'});
  const sel = document.querySelector('#sub_grid_body .pq-editor-focus');
  if (!sel || sel.tagName !== 'SELECT') return {ok: false, reason: 'no SELECT'};
  sel.value = val;
  if (!sel.value && fallbackVal) sel.value = fallbackVal;
  const actualVal = sel.value;
  sel.dispatchEvent(new Event('change', {bubbles: true}));
  jQuery(sel).trigger('blur');
  return {ok: true, val: actualVal, tried: val};
};

window.checkSyncBlock = function() {
  const min = new Date().getMinutes();
  const blocked = [10,11,12,13,20,21,22,23,30,31,32,33,40,41,42,43,50,51,52,53];
  return {blocked: blocked.includes(min), minute: min};
};

window.waitSyncClear = async function(label) {
  const chk = window.checkSyncBlock();
  if (!chk.blocked) return;
  const allowMins = [4,14,24,34,44,54];
  const now = new Date();
  const curMin = now.getMinutes();
  const nextAllow = allowMins.find(m => m > curMin) || (allowMins[0] + 60);
  const waitMs = ((nextAllow - curMin) * 60 - now.getSeconds()) * 1000 + 1000;
  window._processLog = window._processLog || [];
  window._processLog.push('⏸ 동기화대기(' + (label||'') + ') ' + curMin + '분→' + nextAllow + '분');
  await new Promise(r => setTimeout(r, waitMs));
};

window.saveSubGrid = function() {
  return new Promise(resolve => {
    document.getElementById('btnSubBundleApply').click();
    let confirmClicked = false;
    const iv = setInterval(() => {
      const dlgs = Array.from(document.querySelectorAll('.ui-dialog')).filter(d => d.offsetParent !== null);
      for (const dlg of dlgs) {
        const txt = dlg.innerText || '';
        const okBtn = Array.from(dlg.querySelectorAll('button')).find(b => b.textContent.trim() === 'OK' || b.textContent.trim() === '확인');
        if (!okBtn) continue;
        if (txt.includes('저장하시겠습니까') && !confirmClicked) { okBtn.click(); confirmClicked = true; break; }
        if (txt.includes('정상처리')) { okBtn.click(); clearInterval(iv); resolve('saved'); return; }
        if (txt.includes('변경된 내용이 없습니다')) { okBtn.click(); clearInterval(iv); resolve('no-change'); return; }
        if (confirmClicked) { okBtn.click(); clearInterval(iv); resolve('saved'); return; }
      }
    }, 150);
    setTimeout(() => { clearInterval(iv); resolve('timeout'); }, 10000);
  });
};

window.processAllRows = async function(startTopRowIndx) {
  const topData = jQuery('#grid_body').pqGrid('option','dataModel').data;
  const log = [];
  window._processErrors = window._processErrors || [];
  for (let topIdx = startTopRowIndx; topIdx < topData.length; topIdx++) {
    if (window._haltAll || window._stopProcess) { log.push('--- 중지 ---'); break; }
    const topRow = topData[topIdx];
    const prodNo = (topRow.PROD_NO || '').trim();
    const outerLine = topRow.OUTER_LINE_CD || window._fallbackLine || 'SP2A02';
    if (!window._isRefProd(prodNo)) {
      log.push('[' + topIdx + '] SKIP: ' + prodNo);
      window._processLog = window._processLog || [];
      window._processLog.push('[' + topIdx + '] SKIP: ' + prodNo);
      continue;
    }
    let rowEl = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      jQuery('#grid_body').pqGrid('scrollRow', {rowIndx: topIdx});
      await new Promise(r => setTimeout(r, 700 + attempt * 300));
      rowEl = document.getElementById('pq-body-row-u2-' + topIdx + '-right') || document.getElementById('pq-body-row-u2-' + topIdx + '-left');
      if (rowEl) break;
    }
    if (!rowEl) { log.push('[' + topIdx + '] DOM없음: ' + prodNo); window._processErrors.push(prodNo + ':DOM없음'); continue; }
    const cells = rowEl.querySelectorAll('.pq-grid-cell');
    if (cells.length > 1) cells[1].click(); else if (cells[0]) cells[0].click();
    await new Promise(r => setTimeout(r, 2000));
    const subData = jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    if (!subData || subData.length === 0) { log.push('[' + topIdx + '] 하단0행: ' + prodNo); window._processErrors.push(prodNo + ':하단0행'); continue; }
    window.setCellValue(0, outerLine, window._fallbackLine);
    window._processLog = window._processLog || [];
    window._processLog.push('  [' + topIdx + '] ' + prodNo + ' OUTER=' + outerLine);
    if (subData.length > 1) window.setCellValue(1, 'SP3M3', null);
    for (let si = 2; si < subData.length; si++) {
      const nm = subData[si].MBOM_PART_NM || '';
      const pt = (subData[si].PART_TYPE_NM || '').trim();
      let val = null;
      if (pt === '공정품_SUB') val = 'SWAMS04';
      else val = window.getLineValue(nm);
      if (val) { window.setCellValue(si, val, null); window._processLog.push('  row' + si + '[' + nm.substring(0,30) + '|' + pt + ']->' + val); log.push('  row' + si + '->' + val); }
    }
    if (jQuery('#sub_grid_body').pqGrid('isDirty')) {
      await window.waitSyncClear('저장');
      if (window._haltAll) { log.push('--- 중지 ---'); break; }
      const saveResult = await window.saveSubGrid();
      log.push('  저장=' + saveResult);
      window._processLog.push('  저장=' + saveResult);
    } else { log.push('  변경없음'); window._processLog.push('  변경없음'); }
  }
  return log;
};

window.searchAndProcess = async function(prodNo) {
  if (window._haltAll) return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: 'HALTED'};
  await window.waitSyncClear('검색:' + prodNo);
  if (window._haltAll) return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: 'HALTED'};
  const inp = document.getElementById('searchProdNo');
  if (!inp) return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: 'INPUT없음'};
  inp.focus(); inp.value = ''; inp.value = prodNo;
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  const searchBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === '검색');
  if (!searchBtn) return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: '검색버튼없음'};
  searchBtn.click();
  await new Promise(r => setTimeout(r, 2500));
  if (window._haltAll) return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: 'HALTED'};
  const topData = jQuery('#grid_body').pqGrid('option','dataModel').data;
  if (!topData || topData.length === 0) { window._processLog = window._processLog || []; window._processLog.push('[' + prodNo + '] 검색없음'); return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: '검색없음'}; }
  const freq = {};
  topData.forEach(r => { if (r.OUTER_LINE_CD) freq[r.OUTER_LINE_CD] = (freq[r.OUTER_LINE_CD]||0)+1; });
  window._fallbackLine = Object.entries(freq).sort((a,b) => b[1]-a[1])[0]?.[0] || 'SP2A02';
  window._processLog = window._processLog || [];
  window._processLog.push('[' + prodNo + '] ' + topData.length + '행 OUTER=' + window._fallbackLine);
  const logArr = await window.processAllRows(0);
  const saved    = logArr.filter(l => l.includes('저장=saved')).length;
  const noChange = logArr.filter(l => l.includes('변경없음')).length;
  const skip     = logArr.filter(l => l.includes('SKIP')).length;
  const err      = (window._processErrors||[]).length;
  return {prod: prodNo, rows: topData.length, saved, noChange, skip, err};
};

window.runQueue = async function() {
  if (window._runningQueue) { return ['이미 실행중']; }
  window._runningQueue = true;
  window._stopProcess = false;
  window._queueSummary = window._queueSummary || [];
  window._lastQueueResult = null;
  for (const prod of window._prodQueue) {
    if (window._stopProcess || window._haltAll) break;
    const r = await window.searchAndProcess(prod);
    window._queueSummary.push(r);
    window._lastQueueResult = r;
  }
  window._runningQueue = false;
  window._queueDone = true;
  return window._queueSummary;
};

'✅ 메인서브 함수 등록 완료 v10';
```

---

## STEP 2: 실행

```javascript
// 전체 302개 처음부터
var all = Array.from(window._refProdNos).sort();
window._prodQueue = all;
window._queueSummary = [];
window._processLog = [];
window._processErrors = [];
window._haltAll = false;
window._stopProcess = false;
window._runningQueue = false;
window.runQueue();
```

```javascript
// 특정 품번부터 이어서
var all = Array.from(window._refProdNos).sort();
var idx = all.indexOf('89870T6400'); // 시작 품번
window._prodQueue = all.slice(idx);
window._queueSummary = [];
window._processLog = [];
window._processErrors = [];
window._haltAll = false;
window._stopProcess = false;
window._runningQueue = false;
window.runQueue();
```

## STEP 3: 진행 확인 / 중지 / 재개

```javascript
// 진행 확인
var s = window._queueSummary||[];
JSON.stringify({done: s.length+'/'+window._prodQueue.length, last: window._lastQueueResult, running: window._runningQueue, time: new Date().toLocaleTimeString()});

// 중지
window._haltAll = true;
window._stopProcess = true;

// 재개
var done = new Set((window._queueSummary||[]).map(r => r.prod));
window._prodQueue = window._prodQueue.filter(p => !done.has(p));
window._queueSummary = [];
window._haltAll = false;
window._stopProcess = false;
window._runningQueue = false;
window.runQueue();
```

---

## 핵심 주의사항

1. 동기화 구간 검색·저장 금지 — `waitSyncClear()` 자동 처리
2. 저장 버튼은 `btnSubBundleApply` ID로만
3. row0: OUTER_LINE_CD / row1: SP3M3 고정 / row2+: LINE_RULES 매핑
4. HOLDER,CLR ASSY → HCAMS02 (LINE_RULES 최우선)
5. ERP 품번 접미사 포함 → `_isRefProd()` prefix 매핑

---

## 실패 조건

다음 중 하나라도 해당하면 **실행 실패**로 판정한다:

| 조건 | 판정 |
|------|------|
| 검색 결과 0건 (품번 미존재) | 해당 품번 SKIP (전체 FAIL 아님) |
| DOM 미발견 (3회 재시도 후) | 해당 행 FAIL → `_processErrors` 기록 |
| SELECT 요소 미출현 (셀 편집 실패) | 해당 행 FAIL |
| 저장 timeout (10초 초과) | 해당 행 FAIL |
| `_processErrors` 배열에 1건 이상 존재 | 전체 결과 **부분 실패** |
| ERP 페이지 로딩 실패 / 세션 만료 | 전체 FAIL |

## 중단 기준

다음 상황에서는 **즉시 중단** (`_haltAll = true`):

1. ERP 세션 만료 또는 로그아웃 감지 (검색 버튼 미존재 등)
2. 연속 3품번 이상 `DOM없음` 에러 — 페이지 구조 이상 의심
3. 동기화 금지 구간에서 예외 발생
4. `searchProdNo` 입력 필드 미존재 — 화면 이탈
5. 사용자 수동 중지 (`_haltAll = true` / `_stopProcess = true`)

## 검증 항목

실행 완료 후 반드시 확인:

- [ ] `_queueSummary` 전체 → `err` 합계 = 0
- [ ] 처리 완료 품번수 = 대상 품번수 (`_prodQueue.length`)
- [ ] `_processErrors` 빈 배열 확인
- [ ] 무작위 3개 품번 ERP에서 직접 확인 — `ASSY_LINE_NM` 값 정상
- [ ] row0: OUTER_LINE_CD / row1: SP3M3 / row2+: LINE_RULES 매핑 일치

## 되돌리기 방법

| 범위 | 방법 |
|------|------|
| 특정 품번 | ERP에서 해당 품번 검색 → SUB ASSY 조립라인을 공란으로 변경 → 저장 |
| 부분 롤백 | `_processErrors` 기록 품번만 수동 확인/수정 |
| 전체 롤백 | **이전 값 미보존** — ERP 변경 이력 조회 필요 |
| 변경 행 추적 | `_processLog`에서 저장=saved 행 목록 추출 가능 |

> 주의: ERP 저장은 비가역적 — 이전 값을 자동 복원하는 기능 없음. 대량 롤백 시 ERP 관리자 지원 필요.

---

## 변경 이력

| 일자 | 버전 | 내용 |
|---|---|---|
| 2026-03-21 | v10 | 스킬 분리 — 메인서브 전용으로 독립 |
| 2026-03-20 | v6 | HCAMS03→HCAMS02, prefix 매핑, 동기화 구간 처리 등 |
