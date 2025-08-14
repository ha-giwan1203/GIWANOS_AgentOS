$ErrorActionPreference="Stop"
$ROOT="C:\giwanos"
$LOG ="$ROOT\data\logs\preflight_{0}.log" -f (Get-Date -Format yyyyMMdd)
function Log($m){ "[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"),$m | Out-File -FilePath $LOG -Append -Encoding UTF8 }
# python 존재 확인
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Log "no python"; exit 1 }
# 빠른 문법 체크
Get-ChildItem "$ROOT" -Recurse -Filter *.py | ?{ $_.FullName -notmatch '\\venv\\' } | %{
  & python -m py_compile $_.FullName 2>$null
  if ($LASTEXITCODE -ne 0){ Log "py_compile fail: $($_.FullName)"; exit 1 }
}
# 필수 임포트
& python - << 'PY'
import importlib
for m in ["modules.velos_common","modules.report_paths"]:
    importlib.import_module(m)
print("OK")
PY
if ($LASTEXITCODE -ne 0){ Log "import check failed"; exit 1 }
Log "preflight pass"