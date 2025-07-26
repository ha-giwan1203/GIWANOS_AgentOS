from importlib.util import find_spec

REQUIRED_MODULES = [
    "giwanos.memory.memory_health_check_all",
    "giwanos.memory.memory_self_check",
]

def module_exists(mod: str) -> bool:
    try:
        return find_spec(mod) is not None
    except Exception:
        return False

def run():
    print("🔍 GIWANOS 핵심 모듈 헬스 체크 실행")

    all_ok = True
    for mod in REQUIRED_MODULES:
        if module_exists(mod):
            print(f"✅ {mod}")
        else:
            print(f"❌ {mod} NOT FOUND")
            all_ok = False

    if all_ok:
        print("\n✅ 모든 필수 모듈 정상 확인됨")
    else:
        print("\n❌ 일부 모듈이 누락되었습니다.")

if __name__ == "__main__":
    run()
