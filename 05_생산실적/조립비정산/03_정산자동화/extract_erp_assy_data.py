"""
ERP 조립비 현황관리 데이터 일괄 추출
- CDP WebSocket으로 ERP iframe 내부에서 API 직접 호출
- 대원테크(0109) 기준 Hdr 661건 → 각 제품별 Dtl 상세 수집
- 결과: JSON + CSV 저장
"""
import websocket
import json
import urllib.request
import time
import csv
import sys
import os
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

# === 설정 ===
CDP_URL = "http://localhost:9222/json/list"
CMPY_CD = "0109"  # 대원테크
APPL_DA = "2026-04-06"
DELAY_SEC = 0.5  # 요청 간 지연
PAGE_SIZE = 10    # 서버 고정 페이지 크기
CONTEXT_ID = 17   # ERP 조립비 현황관리 iframe

# 출력 경로
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_JSON = os.path.join(OUT_DIR, f"erp_assy_extract_{TIMESTAMP}.json")
OUT_CSV = os.path.join(OUT_DIR, f"erp_assy_extract_{TIMESTAMP}.csv")
CHECKPOINT = os.path.join(OUT_DIR, "erp_assy_checkpoint.json")

# Dtl에서 추출할 컬럼
DTL_COLS = [
    "PROD_NO", "PART_NO", "ASSY_LINE_CD", "ASSY_LINE_NM",
    "ASSY_CMPY_CD", "ASSY_CMPY_NM", "ASSY_COST", "COMP_QTY",
    "UNQCST_DIV_CD", "UNQCST_DIV_NM", "ASSY_LINE_DIV_NM1",
    "ASSY_LINE_DIV_NM2", "LINE_CT", "APPL_BEGIN_DA", "APPL_END_DA",
    "DECIDE_CD", "DECIDE_NM", "PART_NM"
]


def connect_cdp():
    """CDP WebSocket 연결"""
    tabs = json.loads(urllib.request.urlopen(CDP_URL).read())
    erp_tab = next((t for t in tabs if 'erp-dev' in t['url']), None)
    if not erp_tab:
        raise RuntimeError("ERP 탭을 찾을 수 없습니다")
    ws = websocket.create_connection(
        erp_tab['webSocketDebuggerUrl'],
        timeout=30,
        suppress_origin=True
    )
    return ws


def cdp_eval(ws, js_code, msg_id=1):
    """CDP Runtime.evaluate 실행"""
    ws.send(json.dumps({
        'id': msg_id,
        'method': 'Runtime.evaluate',
        'params': {
            'expression': js_code,
            'contextId': CONTEXT_ID,
            'returnByValue': True
        }
    }))
    resp = json.loads(ws.recv())
    result = resp.get('result', {}).get('result', {})
    if result.get('type') == 'string':
        return result['value']
    return json.dumps(result.get('value', ''))


def fetch_hdr_all(ws):
    """상단 Hdr: 대원테크 전체 제품 목록 페이징 수집"""
    products = []
    page = 1
    total = None

    while True:
        js = f'''
(function(){{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/cmAssycostMngNew/selectListCmAssyStatusMngHdrNew.do?searchApplDa={APPL_DA}&pq_curPage={page}&pq_rPP={PAGE_SIZE}&searchCmpyCd={CMPY_CD}', false);
    xhr.send();
    var r = JSON.parse(xhr.responseText);
    return JSON.stringify({{
        total: r.data.pagination.totalRecords,
        list: r.data.list
    }});
}})()
'''
        result = json.loads(cdp_eval(ws, js, msg_id=100 + page))

        if total is None:
            total = result['total']
            max_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
            print(f"[Hdr] 총 {total}건, {max_pages}페이지")

        if not result['list']:
            break

        products.extend(result['list'])
        print(f"  page {page}/{max_pages}: +{len(result['list'])}건 (누적 {len(products)})")

        page += 1
        if page > max_pages:
            break
        time.sleep(0.1)

    print(f"[Hdr] 완료: {len(products)}건 수집")
    return products


def fetch_dtl(ws, prod_no, msg_id=1):
    """하단 Dtl: 제품별 조립품번 상세 조회"""
    js = f'''
(function(){{
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/cmAssycostMngNew/selectListCmAssyStatusMngDtlNew.do?searchProdNo={prod_no}&allFlag=N&searchApplDa={APPL_DA}', false);
    xhr.send();
    if(xhr.status !== 200) return JSON.stringify({{error: xhr.status}});
    var r = JSON.parse(xhr.responseText);
    if(r.statusCode != 200) return JSON.stringify({{error: r.statusCode}});
    return JSON.stringify(r.data.list.map(function(x){{
        var row = {{}};
        var cols = {json.dumps(DTL_COLS)};
        for(var i=0; i<cols.length; i++){{ row[cols[i]] = x[cols[i]]; }}
        return row;
    }}));
}})()
'''
    result = json.loads(cdp_eval(ws, js, msg_id=msg_id))
    if isinstance(result, dict) and 'error' in result:
        return None
    return result


def load_checkpoint():
    """체크포인트 로드"""
    if os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "dtl_data": []}


def save_checkpoint(ckpt):
    """체크포인트 저장"""
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump(ckpt, f, ensure_ascii=False)


def main():
    print(f"=== ERP 조립비 현황관리 데이터 추출 ===")
    print(f"대상: 대원테크({CMPY_CD}), 적용일: {APPL_DA}")
    print()

    # 1. CDP 연결
    ws = connect_cdp()
    print("[CDP] 연결 성공")

    # 2. 체크포인트 로드
    ckpt = load_checkpoint()
    completed_set = set(ckpt["completed"])
    all_dtl = ckpt["dtl_data"]
    print(f"[체크포인트] 기존 완료: {len(completed_set)}건, 기존 Dtl: {len(all_dtl)}건")

    # 3. Hdr 전체 수집
    products = fetch_hdr_all(ws)

    # 4. Dtl 수집 (체크포인트 기반 재개)
    remaining = [p for p in products if p['PROD_NO'] not in completed_set]
    print(f"\n[Dtl] 수집 대상: {len(remaining)}건 (전체 {len(products)} - 완료 {len(completed_set)})")

    errors = []
    for i, prod in enumerate(remaining):
        prod_no = prod['PROD_NO']
        try:
            dtl_list = fetch_dtl(ws, prod_no, msg_id=1000 + i)
            if dtl_list is None:
                errors.append(prod_no)
                print(f"  [{i+1}/{len(remaining)}] {prod_no} → ERROR")
            else:
                # Hdr 정보 병합
                for row in dtl_list:
                    row['HDR_OUTER_LINE_CD'] = prod.get('OUTER_LINE_CD', '')
                    row['HDR_CARTYPE_NM'] = prod.get('CARTYPE_NM', '')
                    row['HDR_ASSY_COST'] = prod.get('ASSY_COST', '')
                all_dtl.extend(dtl_list)
                completed_set.add(prod_no)
                if (i + 1) % 50 == 0:
                    print(f"  [{i+1}/{len(remaining)}] {prod_no} → {len(dtl_list)}건 (누적 Dtl: {len(all_dtl)})")
        except Exception as e:
            errors.append(prod_no)
            print(f"  [{i+1}/{len(remaining)}] {prod_no} → EXCEPTION: {e}")
            # 재연결 시도
            try:
                ws.close()
            except:
                pass
            time.sleep(2)
            ws = connect_cdp()

        # 50건마다 체크포인트 저장
        if (i + 1) % 50 == 0:
            ckpt["completed"] = list(completed_set)
            ckpt["dtl_data"] = all_dtl
            save_checkpoint(ckpt)

        time.sleep(DELAY_SEC)

    ws.close()

    # 5. 결과 저장
    print(f"\n[결과] 총 Dtl: {len(all_dtl)}건, 에러: {len(errors)}건")
    if errors:
        print(f"  에러 제품: {errors[:20]}{'...' if len(errors) > 20 else ''}")

    # JSON 저장
    result = {
        "extract_date": datetime.now().isoformat(),
        "cmpy_cd": CMPY_CD,
        "appl_da": APPL_DA,
        "hdr_count": len(products),
        "dtl_count": len(all_dtl),
        "error_count": len(errors),
        "errors": errors,
        "hdr_data": products,
        "dtl_data": all_dtl
    }
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[저장] JSON: {OUT_JSON}")

    # CSV 저장 (Dtl만, 대원테크 필터)
    dtl_0109 = [r for r in all_dtl if r.get('ASSY_CMPY_CD') == CMPY_CD]
    print(f"[필터] 대원테크 Dtl: {len(dtl_0109)}건 / 전체 {len(all_dtl)}건")

    if dtl_0109:
        fieldnames = DTL_COLS + ['HDR_OUTER_LINE_CD', 'HDR_CARTYPE_NM', 'HDR_ASSY_COST']
        with open(OUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(dtl_0109)
        print(f"[저장] CSV: {OUT_CSV}")

    # 체크포인트 정리
    if os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)

    print(f"\n=== 추출 완료 ===")


if __name__ == "__main__":
    main()
