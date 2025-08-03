import builtins, importlib.util, runpy, pathlib, sys
seen=set(); orig=builtins.__import__
def hook(name,*a,**k):
    spec=importlib.util.find_spec(name)
    if spec and spec.origin and "\\interface\\" in spec.origin:
        seen.add(spec.origin)
    return orig(name,*a,**k)
builtins.__import__=hook
runpy.run_path("scripts/run_giwanos_master_loop.py", run_name="__main__")
print("\n=== 실제 import 된 대시보드 파일 ===")
for p in sorted(seen): print(p)
