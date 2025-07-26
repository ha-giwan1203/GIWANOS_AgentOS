import importlib.util

def module_exists(module_path: str) -> bool:
    try:
        return importlib.util.find_spec(module_path) is not None
    except Exception:
        return False

def main():
    targets = [
        "giwanos.memory.memory_health_check_all",
        "giwanos.memory.memory_self_check",
    ]

    for mod in targets:
        if module_exists(mod):
            print(f"✅ 모듈 찾음: {mod}")
        else:
            print(f"❌ 모듈 못 찾음: {mod}")

if __name__ == "__main__":
    main()
