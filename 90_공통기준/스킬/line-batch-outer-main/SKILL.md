---
name: line-batch-outer-main
description: >
  ERP OUTER/MAIN 라인배치 자동화 스킬. "OUTER 라인배치", "MAIN 라인배치", "아우터 배치",
  "메인 라인 배치", "SP3M3 라인배치", "리스트업 배치" 등을 언급하면 이 스킬을 사용할 것.
  검색 없이 현재 화면 리스트 순서대로 처리하는 리스트업 방식.
  OUTER: runOuterLine / MAIN: runMainLine
---

# ERP OUTER/MAIN 라인배치 자동화

## 개요

검색 없이 상단 그리드 행 순서대로 처리하는 **리스트업 방식**.

| 작업 | 함수 | ERP 화면 조건 |
|---|---|---|
| OUTER 라인 | `runOuterLine(startIdx)` | 라인구분=OUTER, 제품군=RETRACTOR |
| MAIN 라인 | `runMainLine(startIdx)` | 라인구분=MAIN, 조립라인=[SP3M3]SP3 MAIN, 페이지당 10000건 |

- **ERP URL**: `http://erp-dev.samsong.com:19100/partLineBatchMng/viewPartLineBatchMng.do`

---

## 동기화 제한 시간 ⚠️

| 금지 구간 |
|-----------|
| x0:10 ~ x0:13 |
| x0:20 ~ x0:23 |
| x0:30 ~ x0:33 |
| x0:40 ~ x0:43 |
| x0:50 ~ x0:53 |

---

## 입력 규칙

### OUTER 라인 (OUTER_RULES) — v9

| 품명 포함 문구 | 입력값 | 비고 |
|---|---|---|
| WEBBING CUTTING | WABAS01 | WEBBING ASSY보다 먼저 체크 |
| WEBBING ASSY | WAMAS01 | |
| D-RING | DRAAS11 | D-RING ASSY / D-RING DRL 등 모든 패턴 |
| ANCHOR | ANAAS04 | ANCHOR ASSY / ANCHOR BRACKET 등 모든 패턴 |
| SNAP ON | ANAAS04 | 실제 품명 띄어쓰기 |
| LASER MARKING | LTAAS01 | SIDE TONGUE 포함 여부 무관 |
| INNER BALL GUIDE ASSY | SUB LINE 無 | |
| BASE LOCK ASSY | SUB LINE 無 | |
| LOCKING ASSY | SUB LINE 無 | |
| VEHICLE SENSOR ASSY | SUB LINE 無 | |
| INNER SENSOR ASSY | SUB LINE 無 | |
| TORSION ASSY | SUB LINE 無 | |

> row0 = **SD9A01 고정** / row1+ = OUTER_RULES 매핑

### MAIN 라인 (MAIN_RULES) — v10 신규

> 품명이 아닌 **PART_TYPE_NM** 값 기준. LINE_DIV_NM1='MAIN' 행만 적용.

| PART_TYPE_NM | 입력값 |
|---|---|
| 공정품_SUB | SWAMSMA |
| SUB | SUB LINE 無 |

> row0/row1(OUTER행)은 건드리지 않음

---

## STEP 1: JS 함수 등록

```javascript
// =============================================
// OUTER_RULES (v9)
// =============================================
window.OUTER_RULES = [
  {keyword: 'WEBBING CUTTING',       value: 'WABAS01'},
  {keyword: 'WEBBING ASSY',          value: 'WAMAS01'},
  {keyword: 'D-RING',                value: 'DRAAS11'},
  {keyword: 'ANCHOR',                value: 'ANAAS04'},
  {keyword: 'SNAP ON',               value: 'ANAAS04'},
  {keyword: 'LASER MARKING',         value: 'LTAAS01'},
  {keyword: 'INNER BALL GUIDE ASSY', value: 'SUB LINE 無'},
  {keyword: 'BASE LOCK ASSY',        value: 'SUB LINE 無'},
  {keyword: 'LOCKING ASSY',          value: 'SUB LINE 無'},
  {keyword: 'VEHICLE SENSOR ASSY',   value: 'SUB LINE 無'},
  {keyword: 'INNER SENSOR ASSY',     value: 'SUB LINE 無'},
  {keyword: 'TORSION ASSY',          value: 'SUB LINE 無'},
];

// =============================================
// MAIN_RULES (v10)
// =============================================
window.MAIN_RULES = function(partTypeNm) {
  if (!partTypeNm) return null;
  var t = partTypeNm.trim();
  if (t === '공정품_SUB') return 'SWAMSMA';
  if (t === 'SUB')        return 'SUB LINE 無';
  return null;
};

// =============================================
// 공통 셀 입력 함수 (scrollColumn+350ms+Enter커밋)
// =============================================
window.setLineCell = async function(rowIndx, val) {
  var sub = jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
  if (sub && sub[rowIndx] && sub[rowIndx].ASSY_LINE_NM === val) return true;
  try {
    document.querySelectorAll('#sub_grid_body .pq-editor').forEach(function(el){
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    jQuery('#sub_grid_body').pqGrid('scrollRow',    {rowIndx: rowIndx});
    jQuery('#sub_grid_body').pqGrid('scrollColumn', {dataIndx: 'ASSY_LINE_NM'});
    await new Promise(function(r){ setTimeout(r, 350); });
    jQuery('#sub_grid_body').pqGrid('editCell', {rowIndx: rowIndx, dataIndx: 'ASSY_LINE_NM'});
    var sel = document.querySelector('#sub_grid_body .pq-editor-focus');
    if (!sel || sel.tagName !== 'SELECT') return false;
    sel.value = val;
    var actual = sel.value;
    sel.dispatchEvent(new Event('change', {bubbles: true}));
    sel.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
    sel.dispatchEvent(new KeyboardEvent('keyup',   {key:'Enter', keyCode:13, bubbles:true}));
    await new Promise(function(r){ setTimeout(r, 150); });
    return actual === val;
  } catch(e) {
    console.warn('[setLineCell] row='+rowIndx+' val='+val+' err='+e.message);
    return false;
  }
};

// =============================================
// 공통 저장 함수 (쿨다운 600ms)
// =============================================
window.lineSave = function() {
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
    setTimeout(function() { clearInterval(iv); if (resolved) return; resolve('timeout'); }, 30000);
  });
};

// =============================================
// 동기화 대기
// =============================================
window.waitSync = async function() {
  var blocked=[10,11,12,13,20,21,22,23,30,31,32,33,40,41,42,43,50,51,52,53];
  var min=new Date().getMinutes();
  if (!blocked.includes(min)) return;
  var allow=[14,24,34,44,54];
  var next=allow.find(function(m){return m>min;})||74;
  var waitMs=((next-min)*60-new Date().getSeconds())*1000+1000;
  window._lineLog = window._lineLog || [];
  window._lineLog.push('⏸ 동기화대기 '+min+'분→'+next+'분');
  await new Promise(function(r){setTimeout(r,waitMs);});
};

// =============================================
// runOuterLine: OUTER 라인 리스트업 처리
// startIdx: 0-based (예: 151번=idx150)
// =============================================
window._haltLine = false;
window._lineLog = [];
window._lineErrors = [];
window._lineDone = 0;

window.lineStatus = function() {
  var total = (jQuery('#grid_body').pqGrid('option','dataModel').data||[]).length;
  return new Date().getHours()+':'+String(new Date().getMinutes()).padStart(2,'0')+':'+String(new Date().getSeconds()).padStart(2,'0')+
    ' / done:'+window._lineDone+'/'+total+
    '\n'+(window._lineLog||[]).slice(-6).join('\n');
};

window.runOuterLine = async function(startIdx, endIdx) {
  var topData = jQuery('#grid_body').pqGrid('option','dataModel').data;
  if (!topData) { window._lineLog.push('topData없음'); return; }
  var stopAt = (endIdx !== undefined) ? Math.min(endIdx+1, topData.length) : topData.length;
  window._haltLine = false;
  window._lineDone = startIdx;
  window._lineLog.push('▶ OUTER startIdx='+startIdx+' stopAt='+stopAt);

  for (var i=startIdx; i<stopAt; i++) {
    if (window._haltLine) { window._lineLog.push('⛔ 중지'); break; }
    await window.waitSync();
    if (window._haltLine) break;

    var rowEl=null;
    for (var t=0; t<5; t++) {
      try { jQuery('#grid_body').pqGrid('scrollRow',{rowIndx:i}); } catch(e){}
      await new Promise(function(r){setTimeout(r,1000+t*400);});
      rowEl=document.getElementById('pq-body-row-u2-'+i+'-right')||document.getElementById('pq-body-row-u2-'+i+'-left');
      if (rowEl) break;
    }
    if (!rowEl) { window._lineLog.push('['+i+'] DOM없음'); window._lineErrors.push(i+':DOM없음'); window._lineDone=i+1; continue; }

    var cells=rowEl.querySelectorAll('.pq-grid-cell');
    if (cells.length>1) cells[1].click(); else if(cells[0]) cells[0].click();
    await new Promise(function(r){setTimeout(r,1800);});

    var sub=jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    if (!sub||sub.length===0) { window._lineLog.push('['+i+'] 하단0행'); window._lineDone=i+1; continue; }

    try {
      await window.setLineCell(0, 'SD9A01');
      window._lineLog.push('['+i+'] row0=SD9A01');
      for (var si=1; si<sub.length; si++) {
        var nm=(sub[si].MBOM_PART_NM||'').toUpperCase();
        for (var ri=0; ri<window.OUTER_RULES.length; ri++) {
          if (nm.includes(window.OUTER_RULES[ri].keyword.toUpperCase())) {
            var ok=await window.setLineCell(si, window.OUTER_RULES[ri].value);
            window._lineLog.push('  row'+si+' ['+nm.substring(0,20)+']→'+window.OUTER_RULES[ri].value+(ok?'':' ⚠️'));
            break;
          }
        }
      }
    } catch(e) { window._lineLog.push('['+i+'] 예외: '+e.message); }

    if (jQuery('#sub_grid_body').pqGrid('isDirty')) {
      await window.waitSync();
      if (window._haltLine) break;
      var res=await window.lineSave();
      window._lineLog.push('  저장='+res);
    } else { window._lineLog.push('  ['+i+'] 변경없음'); }
    window._lineDone=i+1;
    await new Promise(function(r){setTimeout(r,400);});
  }
  window._lineLog.push('🏁 OUTER완료: done='+window._lineDone);
};

// =============================================
// runMainLine: MAIN 라인 리스트업 처리
// startIdx: 0-based (예: 151번=idx150)
// =============================================
window.runMainLine = async function(startIdx, endIdx) {
  var topData = jQuery('#grid_body').pqGrid('option','dataModel').data;
  if (!topData) { window._lineLog.push('topData없음'); return; }
  var stopAt = (endIdx !== undefined) ? Math.min(endIdx+1, topData.length) : topData.length;
  window._haltLine = false;
  window._lineDone = startIdx;
  window._lineLog.push('▶ MAIN startIdx='+startIdx+' stopAt='+stopAt);

  for (var i=startIdx; i<stopAt; i++) {
    if (window._haltLine) { window._lineLog.push('⛔ 중지'); break; }
    await window.waitSync();
    if (window._haltLine) break;

    var rowEl=null;
    for (var t=0; t<5; t++) {
      try { jQuery('#grid_body').pqGrid('scrollRow',{rowIndx:i}); } catch(e){}
      await new Promise(function(r){setTimeout(r,800+t*300);});
      rowEl=document.getElementById('pq-body-row-u2-'+i+'-right')||document.getElementById('pq-body-row-u2-'+i+'-left');
      if (rowEl) break;
    }
    if (!rowEl) { window._lineLog.push('['+i+'] DOM없음'); window._lineErrors.push(i+':DOM없음'); window._lineDone=i+1; continue; }

    var cells=rowEl.querySelectorAll('.pq-grid-cell');
    if (cells.length>1) cells[1].click(); else if(cells[0]) cells[0].click();
    await new Promise(function(r){setTimeout(r,1800);});

    var sub=jQuery('#sub_grid_body').pqGrid('option','dataModel').data;
    if (!sub||sub.length===0) { window._lineLog.push('['+i+'] 하단0행'); window._lineDone=i+1; continue; }

    try {
      for (var si=0; si<sub.length; si++) {
        if ((sub[si].LINE_DIV_NM1||'').trim() !== 'MAIN') continue;
        var val=window.MAIN_RULES(sub[si].PART_TYPE_NM);
        if (!val) continue;
        var ok=await window.setLineCell(si, val);
        window._lineLog.push('  ['+i+'] row'+si+' '+sub[si].PART_TYPE_NM+'→'+val+(ok?'':' ⚠️'));
      }
    } catch(e) { window._lineLog.push('['+i+'] 예외: '+e.message); }

    if (jQuery('#sub_grid_body').pqGrid('isDirty')) {
      await window.waitSync();
      if (window._haltLine) break;
      var res=await window.lineSave();
      window._lineLog.push('  저장='+res);
    } else { window._lineLog.push('  ['+i+'] 변경없음'); }
    window._lineDone=i+1;
    await new Promise(function(r){setTimeout(r,400);});
  }
  window._lineLog.push('🏁 MAIN완료: done='+window._lineDone);
};

'✅ OUTER/MAIN 함수 등록 완료 v10';
```

---

## STEP 2: 실행

```javascript
// OUTER 라인 — 1번(idx0)부터
window._haltLine = false;
window.runOuterLine(0);

// OUTER 라인 — N번부터 (예: 120번=idx119)
window._haltLine = false;
window.runOuterLine(119);

// MAIN 라인 — 151번(idx150)부터
window._haltLine = false;
window.runMainLine(150);

// MAIN 라인 — N번부터
window._haltLine = false;
window.runMainLine(/* idx */);
```

## STEP 3: 진행 확인 / 중지 / 재개

```javascript
// 진행 확인
window.lineStatus();

// 중지
window._haltLine = true;

// 재개 (현재 위치 확인 후)
window._haltLine = false;
window.runOuterLine(/* 재개 idx */);
// 또는
window.runMainLine(/* 재개 idx */);
```

---

## 핵심 주의사항

**OUTER 공통:**
1. `setLineCell` — scrollColumn 후 **350ms 대기 필수**
2. Enter 키 커밋 필수 — blur 방식은 isDirty=false
3. row0 = SD9A01 고정
4. 상단 행 DOM 5회 재시도

**MAIN 전용:**
5. LINE_DIV_NM1='MAIN' 행만 처리
6. PART_TYPE_NM 기준 판단 (품명 아님)
7. row0/row1(OUTER행) 건드리지 않음
8. 페이지당 10000건 설정 후 실행

---

## 변경 이력

| 일자 | 버전 | 내용 |
|---|---|---|
| 2026-03-21 | v10 | 스킬 분리 — OUTER+MAIN 전용으로 독립. MAIN 라인 신규(MAIN_RULES: 공정품_SUB→SWAMSMA, SUB→SUB LINE 無). setLineCell/lineSave/waitSync 공통화 |
| 2026-03-21 | v9 | OUTER_RULES: ANCHOR 확장, SNAP ON, LASER MARKING, TORSION ASSY 추가, runOuterLine 검증/재시도 |
