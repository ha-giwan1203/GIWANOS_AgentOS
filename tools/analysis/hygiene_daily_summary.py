# -*- coding: utf-8 -*-
# VELOS 운영 철학 선언문: 판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다.

from __future__ import annotations
import os
import json
import time
from pathlib import Path
from typing import Dict, Any

try:
	import yaml  # type: ignore
except Exception:  # pragma: no cover
	yaml = None


def _root() -> Path:
	root = os.getenv("VELOS_ROOT")
	if root and Path(root).is_dir():
		return Path(root)
	sett = os.getenv("VELOS_SETTINGS") or "/workspace/configs/settings.yaml"
	try:
		if yaml is not None and Path(sett).exists():
			with open(sett, 'r', encoding='utf-8') as f:
				cfg = yaml.safe_load(f)
				if cfg and cfg.get("base_dir"):
					return Path(cfg["base_dir"])
	except Exception:
		pass
	return Path("/workspace") if Path("/workspace").is_dir() else Path.cwd()


ROOT = _root()
REPORTS = ROOT / "data" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RISK = REPORTS / "file_usage_risk_report.json"
MANI = REPORTS / "manifest_sync_report.json"
REFL = REPORTS / "reflection_risk_report.json"


def _now() -> str:
	return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def _load_json(path: Path) -> Dict[str, Any]:
	try:
		return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
	except Exception:
		return {}


def main() -> int:
	risk = _load_json(RISK)
	mani = _load_json(MANI)
	refl = _load_json(REFL)

	summary: Dict[str, Any] = {
		"generated_at": _now(),
		"root": str(ROOT),
		"risk": {
			"KEEP_STRICT": int((risk.get("summary") or {}).get("KEEP_STRICT", 0)),
			"KEEP": int((risk.get("summary") or {}).get("KEEP", 0)),
			"REVIEW": int((risk.get("summary") or {}).get("REVIEW", 0)),
			"QUARANTINE_CANDIDATE": int((risk.get("summary") or {}).get("QUARANTINE_CANDIDATE", 0)),
		},
		"manifest": {"generated_at": mani.get("generated_at")},
		"reflection": {
			"total": int((refl.get("counts") or {}).get("total", 0)),
			"HIGH": int((refl.get("counts") or {}).get("HIGH", 0)),
			"MED": int((refl.get("counts") or {}).get("MED", 0)),
			"LOW": int((refl.get("counts") or {}).get("LOW", 0)),
		},
	}

	outj = REPORTS / "hygiene_daily_summary.json"
	outm = REPORTS / "hygiene_daily_summary.md"

	outj.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
	lines = [
		"# VELOS Hygiene Daily Summary",
		f"- generated_at: {summary['generated_at']}",
		f"- root: `{summary['root']}`",
		"## Risk",
		(
			f"KEEP_STRICT={summary['risk']['KEEP_STRICT']} | KEEP={summary['risk']['KEEP']} | "
			f"REVIEW={summary['risk']['REVIEW']} | QUARANTINE_CANDIDATE={summary['risk']['QUARANTINE_CANDIDATE']}"
		),
		"## Reflection",
		(
			f"total={summary['reflection']['total']} | HIGH={summary['reflection']['HIGH']} | "
			f"MED={summary['reflection']['MED']} | LOW={summary['reflection']['LOW']}"
		),
		"## Manifest",
		f"generated_at: {summary['manifest']['generated_at']}"
	]
	outm.write_text("\n".join(lines), encoding="utf-8")
	print("[OK] hygiene daily summary generated", outj)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
