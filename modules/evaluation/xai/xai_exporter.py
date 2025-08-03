import json, pathlib, datetime
def export(data):
    ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    p_json = pathlib.Path(f"data/reports/xai_{ts}.json")
    p_json.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    p_md = p_json.with_suffix(".md")
    p_md.write_text(f"# XAI Report {ts}\\n\\n```json\\n{json.dumps(data,ensure_ascii=False,indent=2)}\\n```")
    return p_json, p_md
