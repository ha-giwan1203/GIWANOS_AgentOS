import importlib.util

REQUIRED_MODULES = [
    "giwanos.memory.memory_health_check_all",
    "giwanos.memory.memory_self_check",
    "giwanos.memory.memory_filter",
    "giwanos.reflection.generate_reflection",
    "giwanos.reflection.judge_agent",
    "giwanos.reflection.weekly_summary_generator",
    "giwanos.reporting.send_reflection_md",
    "giwanos.reporting.agent_logger",
    "giwanos.reporting.notion_upload_summary",
    "giwanos.system.system_integrity_check",
]

def check_module(path: str) -> bool:
    try:
        return importlib.util.find_spec(path) is not None
    except Exception:
        return False

def main():
    print("🧠 GIWANOS 모듈 헬스 체크 시작\n")

    for mod in REQUIRED_MODULES:
        if check_module(mod):
            print(f"✅  {mod}")
        else:
            print(f"❌  {mod} [NOT FOUND]")

    print("\n✅ 체크 완료")

if __name__ == "__main__":
    main()
