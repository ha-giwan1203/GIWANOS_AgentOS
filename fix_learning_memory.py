#!/usr/bin/env python3
# VELOS 데이터 무결성 복구 스크립트
# learning_memory.json 파일을 올바른 배열 형태로 변환

import json
import os
from pathlib import Path

def fix_learning_memory_json():
    """learning_memory.json 파일을 배열 형태로 수정"""
    
    root_path = Path("C:\giwanos")
    json_file = root_path / "data" / "memory" / "learning_memory.json"
    
    if not json_file.exists():
        print(f"❌ 파일이 존재하지 않습니다: {json_file}")
        return False
    
    try:
        # 원본 파일 읽기
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 데이터 구조 확인
        if isinstance(data, dict) and 'items' in data:
            print("✅ 객체 형태의 데이터 발견 - items 배열 추출")
            items = data['items']
            
            # 배열 형태로 저장
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 수정 완료: {len(items)}개 항목을 배열 형태로 변환")
            return True
            
        elif isinstance(data, list):
            print("✅ 이미 배열 형태입니다 - 수정 불필요")
            return True
            
        else:
            print(f"❌ 예상하지 못한 데이터 형태: {type(data)}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 처리 중 오류: {e}")
        return False

if __name__ == "__main__":
    print("=== VELOS 데이터 무결성 복구 시작 ===")
    success = fix_learning_memory_json()
    if success:
        print("=== 복구 완료 ===")
    else:
        print("=== 복구 실패 ===")