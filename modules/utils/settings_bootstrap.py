# [ACTIVE] VELOS 설정 부트스트랩 - 환경 및 경로 초기화
# [ACTIVE] settings_bootstrap.py
# VELOS 설정 부트스트랩 (ENV > YAML > 실패)

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, Callable
import os, json, yaml, unicodedata, logging

# ────────────────────────────────────────────────────────────────
# 로깅
# ────────────────────────────────────────────────────────────────
_LOG_LEVEL = os.environ.get("VELOS_BOOTSTRAP_LOGLEVEL", "WARNING").upper()
logging.basicConfig(
    level=getattr(logging, _LOG_LEVEL, logging.WARNING),
    format="[settings_bootstrap] %(levelname)s: %(message)s",
)

YAML_DEFAULT_PATH = r"C:\giwanos\configs\settings.yaml"
StrPath = Union[str, Path]

# 필수 키
REQUIRED_KEYS = ["VELOS_ROOT", "VELOS_DB_PATH"]

# 스키마 정의
SCHEMA: Dict[str, Dict[str, Any]] = {
    "VELOS_ROOT":        {"type": "path", "required": True,  "normalize": "path"},
    "VELOS_DB_PATH":     {"type": "path", "required": True,  "normalize": "path"},
    "logging.level":     {"type": "str",  "required": False},
    "logging.path":      {"type": "path", "required": False, "normalize": "path"},
    "database.journal_mode": {"type": "str", "required": False},
    "database.synchronous":  {"type": "str", "required": False},
    "vectors.index_dir": {"type": "path", "required": False, "normalize": "path"},
}

# ────────────────────────────────────────────────────────────────
# 유틸
# ────────────────────────────────────────────────────────────────
def _load_yaml(path: StrPath) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _get_dotted(d: Dict[str, Any], key: str) -> Optional[Any]:
    cur = d
    for part in key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur

def _normalize_path(value: StrPath) -> Path:
    p = Path(str(value)).expanduser()
    name_nfc = unicodedata.normalize("NFC", p.name)
    if p.name != name_nfc:
        logging.warning(f"path name not NFC-normalized: {p.name} -> {name_nfc}")
    return p.resolve()

_NORMALIZERS: Dict[str, Callable[[Any], Any]] = {"path": _normalize_path}

def _type_check(value: Any, typ: str) -> bool:
    if typ == "str": return isinstance(value, str)
    if typ == "int": return isinstance(value, int)
    if typ == "bool": return isinstance(value, bool)
    if typ == "path": return isinstance(value, (str, Path))
    return True

# ────────────────────────────────────────────────────────────────
# Settings 클래스
# ────────────────────────────────────────────────────────────────
class Settings:
    def __init__(self, yaml_path: Optional[StrPath] = None):
        self.yaml_path = Path(os.environ.get("VELOS_SETTINGS", yaml_path or YAML_DEFAULT_PATH))
        self.yaml: Dict[str, Any] = _load_yaml(self.yaml_path)

    def resolve(self, key: str, default: Any = None) -> Tuple[Any, str]:
        if key in os.environ:
            return os.environ[key], "ENV"
        val = _get_dotted(self.yaml, key)
        if val is not None:
            return val, "YAML"
        return default, "DEFAULT"

    def resolve_required(self, key: str) -> Tuple[Any, str]:
        val, src = self.resolve(key, None)
        if val in (None, ""):
            raise KeyError(f"Required setting missing: {key}")
        return val, src

    def resolve_path(self, key: str, default: Optional[StrPath] = None, required: bool = False) -> Path:
        val, _ = (self.resolve_required(key) if required else self.resolve(key, default))
        if val in (None, ""):
            raise KeyError(f"Path setting empty: {key}")
        return _normalize_path(val)

    def get_database_config(self) -> Dict[str, Any]:
        db_path = self.resolve_path("VELOS_DB_PATH", required=True)
        journal_mode, _ = self.resolve("database.journal_mode", "WAL")
        synchronous, _ = self.resolve("database.synchronous", "NORMAL")
        return {"path": db_path, "journal_mode": str(journal_mode).upper(), "synchronous": str(synchronous).upper()}

    def get_logging_config(self) -> Dict[str, Any]:
        level, _ = self.resolve("logging.level", "INFO")
        path, _ = self.resolve("logging.path", str(Path(self.resolve_path("VELOS_ROOT", required=True)) / "data" / "logs"))
        return {"level": str(level).upper(), "path": _normalize_path(path)}

# ────────────────────────────────────────────────────────────────
# 스키마 검증 + 부트스트랩
# ────────────────────────────────────────────────────────────────
def validate_schema(s: Settings) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for req in REQUIRED_KEYS:
        s.resolve_required(req)
    for key, rule in SCHEMA.items():
        val, src = s.resolve(key, None)
        if val in (None, ""):
            if rule.get("required"): raise KeyError(f"Missing: {key}")
            else: continue
        if rule.get("type") and not _type_check(val, rule["type"]):
            raise TypeError(f"Invalid type for {key}")
        if rule.get("normalize"):
            val = _NORMALIZERS[rule["normalize"]](val)
        cur = out
        parts = key.split(".")
        for p in parts[:-1]: cur = cur.setdefault(p, {})
        cur[parts[-1]] = val
    return out

def bootstrap(yaml_path: Optional[StrPath] = None) -> Dict[str, Any]:
    s = Settings(yaml_path=yaml_path)
    velos_root = s.resolve_path("VELOS_ROOT", required=True)
    db_cfg = s.get_database_config()
    log_cfg = s.get_logging_config()
    schema_out = validate_schema(s)
    result = {"VELOS_ROOT": velos_root, "database": db_cfg, "logging": log_cfg}
    for k, v in schema_out.items():
        if k in result and isinstance(result[k], dict): result[k].update(v)
        else: result[k] = v
    if not os.environ.get("VELOS_ALLOW_MULTIDB"):
        _ensure_single_db(result)
    return result

def _ensure_single_db(cfg: Dict[str, Any]) -> None:
    root: Path = cfg["VELOS_ROOT"]
    db_path: Path = cfg["database"]["path"]
    found = {p.resolve() for p in root.rglob("velos.db")}
    found.add(db_path.resolve())
    if len(found) != 1:
        raise RuntimeError(f"Multiple velos.db detected: {sorted(map(str, found))}")

# ────────────────────────────────────────────────────────────────
# 기존 호환 API
# ────────────────────────────────────────────────────────────────
def resolve(key: str, default: Any = None) -> Any:
    return Settings().resolve(key, default)[0]

def resolve_path(key: str, default: Optional[StrPath] = None) -> Path:
    return Settings().resolve_path(key, default)

# 전역 설정
try:
    _cfg = bootstrap()
    VELOS_ROOT = _cfg["VELOS_ROOT"]
    DB_PATH = _cfg["database"]["path"]
    LOG_PATH = _cfg["logging"]["path"]
except Exception:
    VELOS_ROOT = Path(r"C:\giwanos")
    DB_PATH = VELOS_ROOT / "data" / "velos.db"
    LOG_PATH = VELOS_ROOT / "data" / "logs"

# ────────────────────────────────────────────────────────────────
# 스모크 테스트
# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cfg = bootstrap()
    print(json.dumps({
        "VELOS_ROOT": str(cfg["VELOS_ROOT"]),
        "database": {"path": str(cfg["database"]["path"]),
                     "journal_mode": cfg["database"]["journal_mode"],
                     "synchronous": cfg["database"]["synchronous"]},
        "logging": {"level": cfg["logging"]["level"], "path": str(cfg["logging"]["path"])},
        "vectors": {k: str(v) if isinstance(v, Path) else v for k, v in cfg.get("vectors", {}).items()}
    }, ensure_ascii=False, indent=2))
