---
name: line-batch-management
description: >
  ERP 라인배치 관리 자동화 스킬. 사용자가 "라인배치", "라인배치 입력", "라인배치 관리",
  "SUB ASSY 배치", "배치 설정", "ERP 배치", "품번 배치", "라인배치 작업", "배치 자동화" 등을
  언급하면 반드시 이 스킬을 사용할 것. SAMSONG G-ERP 라인배치 관리 화면에서 SP3메인서브
  생산지시서의 품번을 순차 검색하고, 하단 SUB ASSY 그리드에 품명 규칙에 따라 조립라인을
  자동 입력 후 저장하는 반복 업무 전체를 자동화한다. 시작 행/진행 위치를 사용자에게
  확인받고 이어서 처리한다.
---

# ERP 라인배치 관리 자동화

## 개요

SAMSONG G-ERP 라인배치 관리 화면에서 SP3 생산지시서의 품번을 순차 처리한다.
각 품번 검색 → 상단 그리드 행 순차 클릭 → 하단 SUB ASSY 품명별 조립라인 입력 → 저장.

**작업 유형:**
- **메인서브 라인** → `searchAndProcess` / `runQueue` (품번 검색 기반)
- **OUTER 라인** → `runOuterLine` (리스트업 기반, 검색 없이 상단 그리드 행 순서대로 처리)

---

## 사전 준비

### 필수 정보
- **ERP URL**: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`
- **품번 파일**: `/sessions/intelligent-cool-mayer/mnt/업무리스트/SP3메인서브 생산지시서 (2025.03.20).xlsx`
  - 시트: `SP3 LINE 기준 정보` / C열 = 품번(모품번)
  - 기준정보 목록은 스킬에 내장되어 있음 (302개, 2026-03-20 기준)
  - ⚠️ 기준정보 파일 변경 시 "품번 목록 갱신" 절차 실행 후 스킬 재배포

### 시작 위치 확인
작업 시작 전 사용자에게 반드시 확인:
- 마지막으로 처리 완료한 품번 / 행번호
- 이어서 시작할 품번

### 동기화 제한 시간 ⚠️
**매시 아래 구간에는 ERP 품번 검색 및 저장 절대 금지:**

| 금지 구간 |
|-----------|
| x0:10 ~ x0:13 |
| x0:20 ~ x0:23 |
| x0:30 ~ x0:33 |
| x0:40 ~ x0:43 |
| x0:50 ~ x0:53 |

검색 및 저장 직전 항상 시간 확인 후, 제한 구간이면 x0:14 / x0:24 / x0:34 / x0:44 / x0:54까지 대기.
`waitSyncClear()` 함수가 자동으로 처리함.

---

## 품명 → 조립라인 매핑 규칙

### 메인서브 라인 (LINE_RULES)

| 품명 포함 문구 | 선택값 |
|---|---|
| HOLDER,CLR ASSY | HCAMS02 |
| INNER BALL GUIDE ASSY | SUB LINE 無 |
| BASE LOCK ASSY | SUB LINE 無 |
| LOCKING ASSY | SUB LINE 無 |
| INNER SENSOR ASSY | SUB LINE 無 |
| WEBBING CUTTING | WABAS01 |
| WEBBING ASSY | WAMAS01 |

> WEBBING CUTTING은 WEBBING ASSY보다 먼저 체크
> HOLDER,CLR ASSY → HCAMS02

### OUTER 라인 전용 (OUTER_RULES)

| 품명 포함 문구 | 선택값 | 비고 |
|---|---|---|
| WEBBING CUTTING | WABAS01 | WEBBING ASSY보다 먼저 체크 |
| WEBBING ASSY | WAMAS01 | |
| D-RING | DRAAS11 | D-RING ASSY / D-RING DRL 등 모든 패턴 포함 |
| ANCHOR ASSY | ANAAS04 | |
| SNAP-ON | ANAAS04 | ANCHOR ASSY와 동일 매핑 |
| LASER MARKING | LTAAS01 | SIDE TONGUE 조건 제거 |

> **이너볼가이드(INNER BALL GUIDE ASSY), 베이스락(BASE LOCK ASSY), 락킹(LOCKING ASSY), 비클센서(VEHICLE SENSOR ASSY) → SUB LINE 無 (건드리지 않음, 규칙 적용 제외)**

---

## 하단 그리드 행별 처리 규칙

### 메인서브 라인

| 행 인덱스 | 처리 규칙 |
|---|---|
| row0 (1번행) | 상단 OUTER_LINE_CD 입력. 공란이면 최빈값 fallback. 항상 처리, 생략 금지 |
| row1 (2번행) | 항상 SP3M3 (기준정보 전체 SP3M3 전용) |
| row2 이상 | MBOM_PART_NM 필드로 LINE_RULES 매핑. 해당 없으면 건너뜀 |

### OUTER 라인

| 행 인덱스 | 처리 규칙 |
|---|---|
| row0 (1번행) | 항상 SD9A01 고정 |
| row1 이상 | MBOM_PART_NM으로 OUTER_RULES 매핑. 해당 없으면 건너뜀 |

---

## 자동화 절차

### STEP 1: 메인서브 라인 JS 함수 등록

ERP 탭에서 아래 JS를 실행한다. 기준정보 품번 302개가 자동 내장된다.

```javascript
// =============================================
// 기준정보 품번 목록 (302개, 2026-03-20 기준)
// 파일 변경 시 스킬 갱신 필요
// =============================================
window._refProdNos = new Set(['89870AT000','89880AT000','89870AT200','89880AT200','89870AT500','89880AT500','89870S1100','89880S1100','89870P4500','89880P4500','89870P2200','89880P2200','7460137000','7460137010','7460137500','7460139000','7460139010','7460139500','7460141000','7460141010','7460142500','7460141510','7460237000','7460237010','7460237500','7460239000','7460239010','7460239500','7460241000','7460241010','7460242500','7460241510','7460137100','7460141100','7460237100','7460241100','7460137600','7460237600','7560137000','7560141000','7560141010','7560141020','7560141030','7560237000','7560241000','7560241010','7560241020','7460141500','7460241500','7560144000','7560244000','88810K2000','88820K2000','88810K2100','88820K2100','89870K2100','89880K2100','89870K2000','89880K2000','88810K2300','88820K2300','898216D100','898226D300','898226D100','898216D300','89870CV500','89870XG500','89880CV500','89880XG500','88820G8001','88820G8201','88810T1000','88810JI000','88820T1000','88820JI000','88820T1100','88820T1200','88820JI100','88820JI200','88810T1500','88810JI500','88820T1500','88820JI500','88810T1100','88810T1200','88810JI100','88810JI200','88810T6000','88810T6100','88810T6300','88820T6000','88820T6100','88810T6500','88820T6300','88820T6500','89870T6000','89880T6000','89870T6100','89880T6100','89870T6500','89880T6500','89870T6600','89880T6600','89870T6700','89880T6700','88810AR000','88810AR100','88820AR100','88820AR000','88810AR500','88820AR500','88810AR300','88820AR300','89880AR000','89870AR000','89880AR100','89870AR100','89870AR500','89880AR500','89870AA000','89870AA010','89880AA000','89880AA010','89870AA600','89870AA610','89880AA600','89880AA610','89870AA500','89870AA510','89870T6400','89870T6800','89880T6400','89880T6800','88810CU100','88810CU300','88820CU100','88820CU300','89870CU000','89880CU000','89870CU100','89880CU100','88810DO000','88810DO300','88820DO000','88810DO200','88820DO200','88820DO300','88810DO500','88810XA500','88820DO500','88820XA500','89870DO000','89880DO000','89870DO200','89880DO200','89870DO500','89880DO500','89870XA500','89880XA500','89870XA510','89870DO510','89880XA510','89880DO510','89870P6000','89880P6000','89870P6100','89880P6100','89870P6500','89880P6500','88810R6000','88820R6000','89870R6000','89880R6000','88810GO000','88810GO200','88820GO000','88810GO300','88820GO200','88810GO500','88820GO300','89870GO000','89880GO000','89870GO200','89880GO200','88810TD000','88820TD000','88820GO500','89870GO500','89870TD000','89880GO500','89880TD000','MO89870R6000','MO89880R6000','88810BQ000','88810BQ100','88820BQ000','88820BQ100','89870XH000','89880XH000','89870XH100','89880XH100','89870XH500','89880XH500','88810SZ000','88810SZ100','88820SZ000','88820SZ100','88810P8000','88820P8000','88810P8500','88820P8500','89870P8500','89880P8500','89873P8500','89883P8500','89870SW000','89880SW000','89870SW200','89880SW200','88810X9500','88820X9500','89870X9200','89880X9200','88810BM000','88820BM000','88820BM200','88810BM100','88820BM100','89870BS000','W89870BS000','89880BS000','W89880BS000','89870BS200','89870DE200','W89870BS200','W89870DE200','89880BS200','89880DE200','W89880BS200','W89880DE200','89870BS500','W89870BS500','89880BS500','W89880BS500','89870DN000','89870DN500','89880DN000','89880DN500','89870P8200','89880P8200','89873P8200','89883P8200','89870AT050','89880AT050','89870AT150','89880AT150','88820GG500','88810GG000','88810GG100','88820GG000','88820GG100','89870GG010','89880GG010','89870GG020','89880GG020','88810NT300','88810NT400','88820NT300','88820NT400','89870NT000','89880NT000','88810NV000','89870NV000','89880NV000','88810BT000','88810BT100','88810BT200','88810BT300','88820BT000','88820BT100','88820BT200','88820BT300','89870BT000','89880BT000','88810BN200','88810BN300','88820BN200','88820BN300','89870BN100','89880BN100','89870XV000','89880XV000','89870XV500','89880XV500','89870GJ000','89880GJ000','89870BP000','89880BP000','88810BP000','88820BP000','89870BP100','89880BP100']);

// =============================================
// prefix 매칭 함수 (ERP 품번에 접미사 포함 대응)
// =============================================
window._isRefProd = function(prodNo) {
  if (!prodNo) return false;
  if (window._refProdNos.has(prodNo)) return true;
  for (const ref of window._refProdNos) {
    if (prodNo.startsWith(ref)) return true;
  }
  return false;
};

// =============================================
// 품명 → 조립라인 매핑 규칙 (메인서브)
// =============================================
window.LINE_RULES = [
  {keyword: 'HOLDER,CLR ASSY',       value: 'HCAMS02'},
  {keyword: 'INNER BALL GUIDE ASSY', value: 'SUB LINE 無'},
  {keyword: 'BASE LOCK ASSY',        value: 'SUB LINE 無'},
  {keyword: 'LOCKING ASSY',          value: 'SUB LINE 無'},
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

// =============================================
// 동기화 구간 체크 및 대기
// =============================================
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
  window._processLog.push('⏸ 동기화대기(' + (label||'') + ') ' + curMin + '분→' + nextAllow + '분 (' + Math.round(waitMs/1000) + '초)');
  await new Promise(r => setTimeout(r, waitMs));
};

// =============================================
// 저장 함수 (메인서브)
// =============================================
window.saveSubGrid = function() {
  return new Promise(resolve => {
    document.getElementById('btnSubBundleApply').click();
    let confirmClicked = false;
    const iv = setInterval(() => {
      const dlgs = Array.from(document.querySelectorAll('.ui-dialog'))
        .filter(d => d.offsetParent !== null);
      for (const dlg of dlgs) {
        const txt = dlg.innerText || '';
        const okBtn = Array.from(dlg.querySelectorAll('button'))
          .find(b => b.textContent.trim() === 'OK' || b.textContent.trim() === '확인');
        if (!okBtn) continue;
        if (txt.includes('저장하시겠습니까') && !confirmClicked) {
          okBtn.click(); confirmClicked = true; break;
        }
        if (txt.includes('정상처리')) {
          okBtn.click(); clearInterval(iv); resolve('saved'); return;
        }
        if (txt.includes('변경된 내용이 없습니다')) {
          okBtn.click(); clearInterval(iv); resolve('no-change'); return;
        }
        if (confirmClicked) {
          okBtn.click(); clearInterval(iv); resolve('saved'); return;
        }
      }
    }, 150);
    setTimeout(() => { clearInterval(iv); resolve('timeout'); }, 10000);
  });
};

// =============================================
// 상단 그리드 전체 행 처리 (메인서브)
// =============================================
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
      log.push('[' + topIdx + '] SKIP(기준정보없음): ' + prodNo);
      window._processLog = window._processLog || [];
      window._processLog.push('[' + topIdx + '] SKIP(기준정보없음): ' + prodNo);
      continue;
    }

    let rowEl = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      jQuery('#grid_body').pqGrid('scrollRow', {rowIndx: topIdx});
      await new Promise(r => setTimeout(r, 700 + attempt * 300));
      rowEl = document.getElementById('pq-body-row-u2-' + topIdx + '-right') ||
              document.getElementById('pq-body-row-u2-' + topIdx + '-left');
      if (rowEl) break;
    }
    if (!rowEl) {
      log.push('[' + topIdx + '] !! DOM없음: ' + prodNo);
      window._processErrors.push(prodNo + ':DOM없음');
      continue;
    }

    const cells = rowEl.querySelectorAll('.pq-grid-cell');
    if (cells.length > 1) cells[1].click(); else if (cells[0]) cells[0].click();
    await new Promise(r => setTimeout(r, 2000));

    const subData = jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    if (!subData || subData.length === 0) {
      log.push('[' + topIdx + '] !! 하단0행: ' + prodNo);
      window._processErrors.push(prodNo + ':하단0행');
      continue;
    }

    window.setCellValue(0, outerLine, window._fallbackLine);
    window._processLog = window._processLog || [];
    window._processLog.push('  [' + topIdx + '] ' + prodNo + ' OUTER=' + outerLine);
    log.push('  [' + topIdx + '] row0=' + outerLine);

    if (subData.length > 1) window.setCellValue(1, 'SP3M3', null);

    for (let si = 2; si < subData.length; si++) {
      const nm = subData[si].MBOM_PART_NM || '';
      const val = window.getLineValue(nm);
      if (val) {
        window.setCellValue(si, val, null);
        window._processLog.push('  row' + si + '[' + nm.substring(0,30) + ']->' + val);
        log.push('  row' + si + '[' + nm.substring(0,30) + ']->' + val);
      }
    }

    if (jQuery('#sub_grid_body').pqGrid('isDirty')) {
      await window.waitSyncClear('저장');
      if (window._haltAll) { log.push('--- 중지 ---'); break; }
      const saveResult = await window.saveSubGrid();
      log.push('  저장=' + saveResult);
      window._processLog.push('  저장=' + saveResult);
    } else {
      log.push('  변경없음');
      window._processLog.push('  변경없음');
    }

    await new Promise(r => setTimeout(r, 500));
    const subAfter = jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    const row0After = subAfter && subAfter[0] ? (subAfter[0].ASSY_LINE_NM || subAfter[0].ASSY_LINE_CD || '') : '';
    window._processLog.push('  검증OK row0=' + row0After);
    log.push('  검증OK row0=' + row0After);
  }

  log.push('===== 완료 =====');
  log.push('SKIP: ' + log.filter(l => l.includes('SKIP')).length + '건');
  log.push('오류: ' + (window._processErrors||[]).length + '건');
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
  if (!topData || topData.length === 0) {
    window._processLog = window._processLog || [];
    window._processLog.push('[' + prodNo + '] 검색없음');
    return {prod: prodNo, rows: 0, saved: 0, noChange: 0, skip: 0, err: 0, note: '검색없음'};
  }
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

'함수 등록 완료 v7 — 메인서브 기준정보 302개 내장';
```

---

### STEP 1-B: OUTER 라인 전용 JS 함수 등록

리스트업 방식 (검색 없이 상단 그리드 행 순서대로 처리). ERP 화면에서 라인구분=OUTER 필터 적용 후 실행.

```javascript
// =============================================
// OUTER 라인 매핑 규칙
// D-RING은 'D-RING ASSY' / 'D-RING DRL' 등 모든 패턴 커버
// 이너볼가이드/베이스락/락킹/비클센서 → 건드리지 않음(SUB LINE 無)
// =============================================
window.OUTER_RULES = [
  {keyword: 'WEBBING CUTTING',            value: 'WABAS01'},
  {keyword: 'WEBBING ASSY',               value: 'WAMAS01'},
  {keyword: 'D-RING',                     value: 'DRAAS11'},
  {keyword: 'ANCHOR ASSY',   value: 'ANAAS04'},
  {keyword: 'SNAP-ON',       value: 'ANAAS04'},
  {keyword: 'LASER MARKING', value: 'LTAAS01'},
];

// =============================================
// setOuterCell: async, scrollColumn+350ms+Enter커밋
// ⚠️ 핵심: scrollColumn 후 반드시 350ms 대기 후 editCell 호출
//    Enter 키로 commit해야 isDirty=true 보장
// =============================================
window.setOuterCell = async function(rowIndx, val) {
  var sub = jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
  if (sub && sub[rowIndx] && sub[rowIndx].ASSY_LINE_NM === val) {
    return true; // 이미 동일값 → skip
  }
  try {
    document.querySelectorAll('#sub_grid_body .pq-editor').forEach(function(el){
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    // 수직+수평 스크롤 후 렌더 대기 (생략 시 .focus() 에러)
    jQuery('#sub_grid_body').pqGrid('scrollRow',    {rowIndx: rowIndx});
    jQuery('#sub_grid_body').pqGrid('scrollColumn', {dataIndx: 'ASSY_LINE_NM'});
    await new Promise(function(r){ setTimeout(r, 350); });

    jQuery('#sub_grid_body').pqGrid('editCell', {rowIndx: rowIndx, dataIndx: 'ASSY_LINE_NM'});
    var sel = document.querySelector('#sub_grid_body .pq-editor-focus');
    if (!sel || sel.tagName !== 'SELECT') return false;

    sel.value = val;
    var actual = sel.value;
    sel.dispatchEvent(new Event('change', {bubbles: true}));

    // Enter 키로 pqGrid commit (blur/removeChild 방식은 isDirty=false 문제 발생)
    sel.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
    sel.dispatchEvent(new KeyboardEvent('keyup',   {key:'Enter', keyCode:13, bubbles:true}));

    await new Promise(function(r){ setTimeout(r, 150); });
    return actual === val;
  } catch(e) {
    console.warn('[setOuterCell] row='+rowIndx+' val='+val+' err='+e.message);
    return false;
  }
};

// =============================================
// outerSave: 쿨다운(600ms) 방식 저장
// =============================================
window.outerSave = function() {
  return new Promise(function(resolve) {
    document.getElementById('btnSubBundleApply').click();
    var confirmed=false, finished=false, resolved=false, lastClick=0, COOL=600;
    var iv = setInterval(function() {
      if (resolved) { clearInterval(iv); return; }
      var now = Date.now();
      if (now - lastClick < COOL) return;
      var dlgs = Array.from(document.querySelectorAll('.ui-dialog')).filter(function(d){ return d.offsetParent!==null; });
      for (var i=0; i<dlgs.length; i++) {
        var dlg=dlgs[i], txt=dlg.innerText||'';
        var btn=Array.from(dlg.querySelectorAll('button')).find(function(b){ var t=b.textContent.trim(); return (t==='OK'||t==='확인')&&!b.disabled; });
        if (!btn) continue;
        if (txt.includes('저장하시겠습니까') && !confirmed) { btn.click(); confirmed=true; lastClick=now; break; }
        if (txt.includes('정상처리') && !finished)          { btn.click(); finished=true; lastClick=now; clearInterval(iv); resolved=true; resolve('saved'); return; }
        if (txt.includes('변경된 내용이 없습니다') && !finished) { btn.click(); finished=true; lastClick=now; clearInterval(iv); resolved=true; resolve('no-change'); return; }
        if (confirmed && !finished)                         { btn.click(); finished=true; lastClick=now; clearInterval(iv); resolved=true; resolve('saved'); return; }
      }
    }, 200);
    setTimeout(function() {
      clearInterval(iv); if (resolved) return;
      var dlg=Array.from(document.querySelectorAll('.ui-dialog')).find(function(d){return d.offsetParent!==null;});
      if (dlg) { var btn=Array.from(dlg.querySelectorAll('button')).find(function(b){return (b.textContent.trim()==='OK'||b.textContent.trim()==='확인')&&!b.disabled;}); if(btn){btn.click();resolve('saved(late)');return;} }
      resolve('timeout');
    }, 30000);
  });
};

// =============================================
// runOuterLine: 리스트업 방식 메인 처리
// startIdx: 0-based 인덱스 (120번 = idx119)
// =============================================
window._outerInstId = 0;
window.runOuterLine = async function(startIdx) {
  var myId = ++window._outerInstId;
  var topData = jQuery('#grid_body').pqGrid('option','dataModel').data;
  window._outerLog=[]; window._outerErrors=[]; window._outerDone=0;
  window._outerTotal=topData.length-startIdx; window._outerRunning=true; window._haltAll=false;
  window._outerLog.push('▶ id='+myId+' idx='+startIdx+' 총='+window._outerTotal);

  for (var i=startIdx; i<topData.length; i++) {
    if (window._outerInstId!==myId || window._haltAll) { window._outerLog.push('⛔ 중지'); window._outerRunning=false; return; }
    var prodNo=(topData[i].PROD_NO||topData[i].ITEM_NO||'').trim();
    window._currentProd=prodNo;

    // 상단 행 DOM 클릭 (5회 재시도)
    var rowEl=null;
    for (var t=0; t<5; t++) {
      try { jQuery('#grid_body').pqGrid('scrollRow',{rowIndx:i}); } catch(e){}
      await new Promise(function(r){setTimeout(r,1000+t*400);});
      rowEl=document.getElementById('pq-body-row-u2-'+i+'-right')||document.getElementById('pq-body-row-u2-'+i+'-left');
      if (rowEl) break;
    }
    if (!rowEl) { window._outerLog.push('['+i+'] DOM없음: '+prodNo); window._outerErrors.push(i+':'+prodNo); window._outerDone++; continue; }

    var cells=rowEl.querySelectorAll('.pq-grid-cell');
    if (cells.length>1) cells[1].click(); else if(cells[0]) cells[0].click();
    await new Promise(function(r){setTimeout(r,1800);});

    var sub=jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    if (!sub||sub.length===0) { window._outerLog.push('['+i+'] 하단0행: '+prodNo); window._outerDone++; continue; }

    try {
      // row0: 항상 SD9A01
      await window.setOuterCell(0,'SD9A01');
      window._outerLog.push('['+i+'] '+prodNo+' row0=SD9A01');

      // row1+: OUTER_RULES 매핑
      for (var si=1; si<sub.length; si++) {
        var nm=(sub[si].MBOM_PART_NM||'').toUpperCase();
        for (var ri=0; ri<window.OUTER_RULES.length; ri++) {
          if (nm.includes(window.OUTER_RULES[ri].keyword.toUpperCase())) {
            var ok = await window.setOuterCell(si, window.OUTER_RULES[ri].value);
            window._outerLog.push('  row'+si+' ['+nm.substring(0,22)+'] → '+window.OUTER_RULES[ri].value+(ok?'':' ⚠️'));
            break;
          }
        }
      }
    } catch(e) {
      window._outerLog.push('['+i+'] 셀입력 예외: '+e.message);
    }

    if (jQuery('#sub_grid_body').pqGrid('isDirty')) {
      var res=await window.outerSave();
      window._outerLog.push('  저장='+res);
    } else { window._outerLog.push('  변경없음'); }
    window._outerDone++;
  }
  window._outerRunning=false;
  window._outerLog.push('🏁 완료 id='+myId+': '+window._outerDone+'/'+window._outerTotal);
};

// 상태 확인
window.outerStatus = function() {
  return new Date().getHours()+':'+String(new Date().getMinutes()).padStart(2,'0')+':'+String(new Date().getSeconds()).padStart(2,'0')+
    ' / done:'+window._outerDone+'/'+window._outerTotal+' / prod:'+window._currentProd+
    '\n에디터:'+document.querySelectorAll('#sub_grid_body .pq-editor').length+'개'+
    '\n'+(window._outerLog||[]).slice(-5).join('\n');
};

'✅ OUTER 라인 함수 등록 완료 v9';
```

---

### STEP 2: 메인서브 큐 설정 및 실행

```javascript
// 전체 302개 처리 (처음부터)
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
// 특정 품번부터 이어서 처리
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

### STEP 2-B: OUTER 라인 실행

```javascript
// 1번(idx0)부터 전체 처리
window._haltAll = false;
window.runOuterLine(0);

// N번부터 처리 (예: 120번 = idx119)
window._haltAll = false;
window.runOuterLine(119);
```

---

### STEP 3: 진행 상황 확인

```javascript
// 메인서브 진행 확인
var s = window._queueSummary||[];
JSON.stringify({
  done: s.length + '/' + window._prodQueue.length,
  totalSaved: s.reduce((a,r) => a+(r.saved||0), 0),
  last: window._lastQueueResult,
  running: window._runningQueue,
  time: new Date().toLocaleTimeString()
})

// OUTER 라인 진행 확인
window.outerStatus();
```

### STEP 4: 중지 / 재개

```javascript
// 즉시 중지 (메인서브/OUTER 공통)
window._haltAll = true;
window._outerInstId = 9999; // OUTER 전용 강제 종료

// 메인서브 재개
var done = new Set((window._queueSummary||[]).map(r => r.prod));
window._prodQueue = window._prodQueue.filter(p => !done.has(p));
window._queueSummary = [];
window._haltAll = false;
window._stopProcess = false;
window._runningQueue = false;
window.runQueue();

// OUTER 라인 재개 (중지된 idx 확인 후)
window._haltAll = false;
window.runOuterLine(/* 재개할 idx */);
```

---

## 기준정보 품번 목록 갱신 방법

기준정보 파일 변경 시에만 실행. 평상시 불필요.

```python
import openpyxl
path = "/sessions/intelligent-cool-mayer/mnt/업무리스트/SP3메인서브 생산지시서 (2025.03.20).xlsx"
wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
ws = wb['SP3 LINE 기준 정보']
prod_nos = []
for row in ws.iter_rows(min_col=3, max_col=3, values_only=True):
    val = row[0]
    if val:
        v = str(val).strip()
        if len(v) >= 8 and any(c.isdigit() for c in v):
            prod_nos.append(v)
wb.close()
seen = set()
unique = [x for x in prod_nos if not (x in seen or seen.add(x))]
print(f"총 {len(unique)}개")
print("'" + "','".join(unique) + "'")
```

결과를 STEP 1 JS의 `window._refProdNos = new Set([...])` 배열에 교체 후 스킬 재배포.

---

## 기술 환경

| 항목 | 값 |
|---|---|
| 그리드 라이브러리 | PQ Grid (jQuery 기반) |
| 상단 그리드 ID | grid_body |
| 하단 그리드 ID | sub_grid_body |
| 저장 버튼 ID | btnSubBundleApply (ID로만 찾을 것) |
| 상단 행 DOM ID | pq-body-row-u2-{rowIndx}-right (없으면 -left fallback) |
| 하단 행 DOM ID | pq-body-row-u9-{rowIndx}-right (없으면 -left fallback) |
| 하단 품명 필드 | MBOM_PART_NM |
| Viewport | 2133x954 CSS px |

---

## 핵심 주의사항

### 공통
1. 동기화 구간(x0:10~13, x0:20~23, x0:30~33, x0:40~43, x0:50~53)에는 검색·저장 모두 금지
2. 저장 버튼은 `btnSubBundleApply` ID로만 — class로 찾으면 검색 버튼이 잡힘
3. `_haltAll` 플래그로 즉시 강제 중단 가능

### 메인서브 라인
4. `waitSyncClear()` — 검색 직전·저장 직전 양쪽에서 자동 호출됨
5. ERP 품번은 접미사 포함(예: 89870T64002BL) — prefix 매핑 `_isRefProd()` 사용
6. row0: OUTER_LINE_CD / row1: SP3M3 고정 / row2+: LINE_RULES 매핑
7. HOLDER,CLR ASSY → **HCAMS02**
8. 하단 그리드 로드 대기 2000ms

### OUTER 라인
9. **setOuterCell은 반드시 async/await로 호출** — 내부에 350ms 딜레이 포함
10. **scrollColumn 후 350ms 대기 필수** — 생략 시 `.focus()` 에러 (수평 가상 스크롤 렌더 타이밍 문제)
11. **Enter 키 커밋 필수** — blur/removeChild 방식은 `isDirty=false`로 저장 안 됨
12. D-RING 키워드는 `'D-RING'` (D-RING ASSY, D-RING DRL 등 모든 패턴 매칭)
13. 이너볼가이드/베이스락/락킹/비클센서 → 건드리지 않음 (SUB LINE 無)
14. row0: SD9A01 고정
15. 상단 행 DOM 5회 재시도 (가상 스크롤 대응)
16. `_outerInstId` 인스턴스 ID로 중복 실행 방지

---

## 실패 조건
- ERP 라인배치 관리 화면 미접속 (URL 로드 실패 또는 세션 만료)
- 품번 검색 결과 0건 (상단 그리드 빈 상태)
- 하단 SUB ASSY 그리드 로드 실패 (`sub_grid_body` DOM 미생성, 2000ms 대기 후)
- SELECT 엘리먼트 미존재 — 조립라인 드롭다운 생성 실패
- 저장 후 ERP 에러 다이얼로그 발생

## 중단 기준
- 동기화 제한 구간(x0:10~13 등) 진입 시 즉시 중단 → `waitSyncClear()` 자동 대기
- `window._haltAll = true` 설정 시 즉시 강제 중단
- 상단 행 DOM 5회 재시도 실패 시 중단 (가상 스크롤 렌더 불가)
- 기준정보 파일 버전 불일치 감지 시 중단 → 품번 목록 갱신 후 재시작

## 검증 항목
- 처리 건수 = 대상 품번 수 (건너뛴 품번 없음)
- 각 품번별 row0(OUTER/SD9A01) + row1(SP3M3) + row2+(LINE_RULES 매핑) 정상 입력
- 저장 성공 확인 (에러 다이얼로그 미발생)
- 동기화 구간 위반 0건 (로그 확인)

## 되돌리기 방법
- ERP 라인배치는 품번별 독립 저장이므로 개별 품번 재처리 가능
- 잘못 입력된 품번: ERP에서 해당 품번 검색 → 하단 그리드 수동 수정 → 저장
- 전체 재실행: 시작 행/품번을 지정하여 `runQueue`로 이어서 처리
- `_haltAll` 후 재개: 마지막 처리 품번 확인 → 다음 품번부터 재시작

## 변경 이력

| 일자 | 버전 | 변경 내용 |
|---|---|---|
| 2026-03-28 | v9 | SNAP-ON→ANAAS04 추가, LASER MARKING 키워드 단축(SIDE TONGUE 조건 제거), VEHICLE SENSOR ASSY SUB LINE 無 명시 |
| 2026-03-21 | v7 | OUTER 라인 전용 섹션 신규 추가. OUTER_RULES(D-RING→'D-RING'확장, ANCHOR ASSY, SIDE TONGUE LASER MARKING 추가). setOuterCell async+scrollColumn+350ms+Enter커밋 방식. outerSave 쿨다운 방식. runOuterLine 리스트업 방식. 이너볼가이드/베이스락/락킹/비클센서 SUB LINE 無 명시 |
| 2026-03-20 | v6 | HCAMS03→HCAMS02, DOM -right 우선, prefix 매칭(_isRefProd), MBOM_PART_NM 필드 명시, 동기화 구간 검색도 금지(waitSyncClear), saveSubGrid 다이얼로그 개선, searchAndProcess/runQueue 함수 추가, 중지/재개 절차 추가 |
| 2026-03-20 | v5 | 기준정보 302개 스킬 내장 — 매 세션 Python 추출 불필요 |
| 2026-03-20 | v4 | 기준정보 검증 로직 추가, HCAMS02->HCAMS03, row1 SP3M3 고정, 전체 C열 탐색, scrollRow 3회 재시도, row0 사후검증 |
| 최초 | v1 | 초기 작성 |
