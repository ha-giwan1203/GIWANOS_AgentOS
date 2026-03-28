#!/usr/bin/env python3
import os, sys
from pathlib import Path
# Ensure project root on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.core.path_manager import get_data_path

def main():
    cache_dir = get_data_path('vector_cache')
    os.makedirs(cache_dir, exist_ok=True)
    readme = os.path.join(cache_dir, 'README.md')
    if not os.path.exists(readme):
        with open(readme, 'w', encoding='utf-8') as f:
            f.write('# Vector Cache\n\nInitialized by CI.\n')
    print('[init_vector_cache] done:', cache_dir)

if __name__ == '__main__':
    main()
