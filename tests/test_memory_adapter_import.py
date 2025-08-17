import importlib

def test_memory_adapter_resolves():
    importlib.import_module("modules.core.memory_adapter").MemoryAdapter
