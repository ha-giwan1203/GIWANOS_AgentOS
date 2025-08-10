import sys
sys.path.append(r"C:\giwanos")
from modules.core.memory_retriever import search
print(search("최근 판단 루프 정상 여부", k=3))
