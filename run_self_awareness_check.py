import os
import json

GIWANOS_ROOT = "C:/giwanos"
EXPECTED_STRUCTURE = [
    ".github",
    "advanced_modules",
    "automation",
    "code_docs",
    "config",
    "core",
    "data",
    "evaluation",
    "github_release_bundle",
    "interface",
    "logs",
    "memory",
    "notifications",
    "notion_integration",
    "run",
    "scheduling",
    "security",
    "vector_cache",
    "run_giwanos_master_loop.py",
    "giwanos_agentos_final_architecture.md",
    "requirements.txt",
    "setup_giwanos_scheduler.ps1"
]

def check_structure():
    missing_items = []
    for item in EXPECTED_STRUCTURE:
        path = os.path.join(GIWANOS_ROOT, item)
        if not os.path.exists(path):
            missing_items.append(item)
    return missing_items

def load_identity_memory():
    memory_path = os.path.join(GIWANOS_ROOT, "memory/identity_memory.json")
    if not os.path.exists(memory_path):
        return "identity_memory.json missing"
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            identity_memory = json.load(f)
        return identity_memory
    except json.JSONDecodeError:
        return "identity_memory.json corrupted"

def run_self_awareness_check():
    structure_issues = check_structure()
    memory_status = load_identity_memory()
    
    report = {
        "structure_issues": structure_issues,
        "memory_status": memory_status
    }

    print(json.dumps(report, indent=4, ensure_ascii=False))

if __name__ == "__main__":
    run_self_awareness_check()