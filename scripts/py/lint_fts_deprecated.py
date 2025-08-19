# [ACTIVE] VELOS FTS 구식 참조 탐지 스크립트
import re
from pathlib import Path


def check_deprecated_fts_references():
    """구식 FTS 컬럼 참조 탐지"""
    patterns = [
        r'(?i)\bmemory_fts\b.*\btext\b(?!.*#)',  # 주석 제외
        r'SELECT\s+text\s+FROM\s+memory_fts',
        r't\.text_norm.*memory_fts',
        r'memory_fts.*JOIN.*text',
        r'INSERT\s+INTO\s+memory_fts.*text'
    ]
    
    # 패턴 자체는 제외
    exclude_patterns = [
        r'patterns\s*=\s*\[',
        r'r\'.*memory_fts.*text.*\'',
        r'r\'.*INSERT.*memory_fts.*text.*\''
    ]
    
    search_paths = [
        'scripts/**/*.py',
        'modules/**/*.py',
        'interface/**/*.py'
    ]
    
    found_issues = []
    
    for pattern in patterns:
        regex = re.compile(pattern, re.IGNORECASE)
        
        for search_path in search_paths:
            root_path = Path('.')
            if '**' in search_path:
                base_path, glob_pattern = search_path.split('**/')
                files = root_path.glob(search_path)
            else:
                files = [Path(search_path)]
            
            for file_path in files:
                if file_path.is_file() and file_path.suffix == '.py':
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            # 패턴 정의 라인은 제외
                            if (regex.search(line) and 
                                not line.strip().startswith('#') and
                                not 'patterns = [' in line and
                                not 'r\'' in line):
                                found_issues.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
    
    if found_issues:
        print("❌ Found deprecated FTS references:")
        for issue in found_issues:
            print(f"  {issue['file']}:{issue['line']} - {issue['content']}")
        return False
    else:
        print("✅ No deprecated FTS references found")
        return True


if __name__ == "__main__":
    import sys
    success = check_deprecated_fts_references()
    sys.exit(0 if success else 1)
