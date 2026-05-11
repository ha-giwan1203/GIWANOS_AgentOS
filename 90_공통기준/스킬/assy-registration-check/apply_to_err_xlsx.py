"""
register_to_master.py가 신규 시퀀스 부여한 결과(registered_rows.json) 만으로
오류리스트 양식 단독 재작성. 사용자가 양식 파일 닫은 후 재시도용.
"""
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

REPO = Path(r"C:\Users\User\Desktop\업무리스트")
ROWS_JSON = REPO / "05_생산실적/조립비정산/05월/_cache/registered_rows.json"

sys.path.insert(0, str(Path(__file__).parent))
import fill_error_list as fel


def main():
    if not ROWS_JSON.exists():
        print(f"[ERR] {ROWS_JSON} 없음 — register_to_master.py 먼저 실행 필요")
        sys.exit(2)
    rows = json.loads(ROWS_JSON.read_text(encoding="utf-8"))
    print(f"신규 시퀀스 결과 load: {len(rows)}행")
    fel.write_to_err_xlsx(rows)
    print(f"오류리스트 양식 재작성 완료: {fel.ERR_XLSX.name}")


if __name__ == "__main__":
    main()
