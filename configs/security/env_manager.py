# [EXPERIMENT] VELOS 환경 관리자 - 보안 설정 모듈
# -*- coding: utf-8 -*-
"""
VELOS 운영 철학 선언문
"판단은 기록으로 증명한다. 파일명 불변, 경로는 설정/환경으로 주입, 모든 저장은 자가 검증 후 확정한다."

VELOS 통합 환경변수 관리 시스템
- 보안 환경변수 로딩
- 환경별 설정 분리
- 접근 제어 및 로깅
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# VELOS 루트 경로
VELOS_ROOT = Path(r"C:\giwanos")
SECURITY_DIR = VELOS_ROOT / "configs" / "security"
LOGS_DIR = VELOS_ROOT / "data" / "logs"

class SecureEnvManager:
    """보안 환경변수 관리자"""
    
    def __init__(self):
        self.root = VELOS_ROOT
        self.security_dir = SECURITY_DIR
        self.logs_dir = LOGS_DIR
        self.env_file = self.root / "configs" / ".env"
        self.secure_env_file = self.security_dir / ".env.encrypted"
        self.access_log = self.logs_dir / "env_access.log"
        
        # 로그 디렉토리 생성
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def log_access(self, action: str, details: str = ""):
        """접근 로그 기록"""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {action} | {details}\n"
        
        with open(self.access_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def load_dotenv(self):
        """환경변수 파일 로딩"""
        try:
            from dotenv import load_dotenv
            if self.env_file.exists():
                load_dotenv(dotenv_path=self.env_file, override=False, encoding="utf-8")
                self.log_access("load_dotenv", f"Loaded: {self.env_file}")
                return True
        except ImportError:
            pass
        return False
    
    def get_env(self, key: str, default: str = None) -> str:
        """환경변수 조회 (로깅 포함)"""
        value = os.getenv(key, default)
        self.log_access("get_env", f"{key}={value[:10] if value else 'None'}...")
        return value
    
    def set_env(self, key: str, value: str, secure: bool = False):
        """환경변수 설정"""
        if secure:
            # 보안 환경변수는 암호화 저장
            self._set_secure_env(key, value)
        else:
            # 일반 환경변수는 시스템에 설정
            os.environ[key] = value
            self.log_access("set_env", f"{key}=***")
    
    def _set_secure_env(self, key: str, value: str):
        """보안 환경변수 암호화 저장"""
        # 간단한 암호화 (실제로는 더 강력한 암호화 사용)
        encrypted_value = self._simple_encrypt(value)
        
        secure_data = {}
        if self.secure_env_file.exists():
            try:
                with open(self.secure_env_file, 'r', encoding='utf-8') as f:
                    secure_data = json.load(f)
            except:
                secure_data = {}
        
        secure_data[key] = {
            "encrypted": encrypted_value,
            "created_at": datetime.now().isoformat(),
            "hash": hashlib.sha256(value.encode()).hexdigest()
        }
        
        with open(self.secure_env_file, 'w', encoding='utf-8') as f:
            json.dump(secure_data, f, indent=2, ensure_ascii=False)
        
        self.log_access("set_secure_env", f"{key}=***")
    
    def _simple_encrypt(self, value: str) -> str:
        """간단한 암호화 (실제 구현에서는 더 강력한 암호화 사용)"""
        # XOR 기반 간단한 암호화
        key = "VELOS_SECURE_KEY_2025"
        encrypted = ""
        for i, char in enumerate(value):
            key_char = key[i % len(key)]
            encrypted += chr(ord(char) ^ ord(key_char))
        return encrypted.encode().hex()
    
    def _simple_decrypt(self, encrypted_hex: str) -> str:
        """간단한 복호화"""
        key = "VELOS_SECURE_KEY_2025"
        encrypted = bytes.fromhex(encrypted_hex).decode()
        decrypted = ""
        for i, char in enumerate(encrypted):
            key_char = key[i % len(key)]
            decrypted += chr(ord(char) ^ ord(key_char))
        return decrypted
    
    def get_secure_env(self, key: str) -> Optional[str]:
        """보안 환경변수 조회"""
        if not self.secure_env_file.exists():
            return None
        
        try:
            with open(self.secure_env_file, 'r', encoding='utf-8') as f:
                secure_data = json.load(f)
            
            if key in secure_data:
                encrypted_value = secure_data[key]["encrypted"]
                decrypted_value = self._simple_decrypt(encrypted_value)
                self.log_access("get_secure_env", f"{key}=***")
                return decrypted_value
        except Exception as e:
            self.log_access("get_secure_env_error", f"{key}: {str(e)}")
        
        return None
    
    def list_env_vars(self, include_secure: bool = False) -> Dict[str, str]:
        """환경변수 목록 조회"""
        env_vars = {}
        
        # 일반 환경변수
        velos_vars = [
            "VELOS_ROOT", "VELOS_DB_PATH", "VELOS_LOG_PATH", "VELOS_BACKUP",
            "VELOS_LOG_LEVEL", "VELOS_API_TIMEOUT", "VELOS_API_RETRIES",
            "VELOS_MAX_WORKERS", "VELOS_DEBUG"
        ]
        
        for var in velos_vars:
            value = self.get_env(var)
            if value:
                env_vars[var] = value
        
        # 전송 채널 환경변수
        transport_vars = [
            "SLACK_BOT_TOKEN", "SLACK_CHANNEL_ID", "NOTION_TOKEN", 
            "NOTION_DATABASE_ID", "SMTP_HOST", "SMTP_USER", "PUSHBULLET_TOKEN"
        ]
        
        for var in transport_vars:
            if include_secure:
                value = self.get_secure_env(var) or self.get_env(var)
            else:
                value = self.get_env(var)
            if value:
                env_vars[var] = value
        
        # 디스패치 설정
        dispatch_vars = ["DISPATCH_EMAIL", "DISPATCH_SLACK", "DISPATCH_NOTION", "DISPATCH_PUSH"]
        for var in dispatch_vars:
            value = self.get_env(var)
            if value:
                env_vars[var] = value
        
        return env_vars
    
    def verify_integrity(self) -> bool:
        """파일 무결성 검증"""
        try:
            hash_file = self.security_dir / "guard_hashes.json"
            if not hash_file.exists():
                return True
            
            with open(hash_file, 'r', encoding='utf-8') as f:
                hash_data = json.load(f)
            
            for file_info in hash_data.get("files", []):
                file_path = Path(file_info["path"])
                expected_hash = file_info["sha256"]
                
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    actual_hash = hashlib.sha256(content).hexdigest()
                    
                    if actual_hash != expected_hash:
                        self.log_access("integrity_fail", f"{file_path}: hash mismatch")
                        return False
                else:
                    self.log_access("integrity_fail", f"{file_path}: file not found")
                    return False
            
            self.log_access("integrity_pass", "All files verified")
            return True
            
        except Exception as e:
            self.log_access("integrity_error", str(e))
            return False
    
    def setup_velos_env(self):
        """VELOS 기본 환경변수 설정"""
        env_vars = {
            "VELOS_ROOT": str(self.root),
            "VELOS_DB_PATH": str(self.root / "data" / "velos.db"),
            "VELOS_LOG_PATH": str(self.root / "data" / "logs"),
            "VELOS_BACKUP": str(self.root / "data" / "backups"),
            "VELOS_LOG_LEVEL": "INFO",
            "VELOS_API_TIMEOUT": "30",
            "VELOS_API_RETRIES": "3",
            "VELOS_MAX_WORKERS": "4",
            "VELOS_DEBUG": "false",
            "DISPATCH_EMAIL": "1",
            "DISPATCH_SLACK": "1",
            "DISPATCH_NOTION": "1",
            "DISPATCH_PUSH": "1"
        }
        
        for key, value in env_vars.items():
            self.set_env(key, value)
        
        self.log_access("setup_velos_env", f"Set {len(env_vars)} variables")
        return env_vars

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="VELOS 보안 환경변수 관리")
    parser.add_argument("--load", action="store_true", help="환경변수 로딩")
    parser.add_argument("--set-secure", action="store_true", help="보안 환경변수 설정")
    parser.add_argument("--list", action="store_true", help="환경변수 목록 조회")
    parser.add_argument("--verify", action="store_true", help="무결성 검증")
    parser.add_argument("--setup", action="store_true", help="VELOS 기본 환경변수 설정")
    parser.add_argument("--key", type=str, help="환경변수 키")
    parser.add_argument("--value", type=str, help="환경변수 값")
    
    args = parser.parse_args()
    
    manager = SecureEnvManager()
    
    if args.load:
        manager.load_dotenv()
        print("✅ 환경변수 로딩 완료")
    
    elif args.set_secure and args.key and args.value:
        manager.set_env(args.key, args.value, secure=True)
        print(f"✅ 보안 환경변수 설정: {args.key}")
    
    elif args.list:
        env_vars = manager.list_env_vars(include_secure=True)
        print("📋 환경변수 목록:")
        for key, value in env_vars.items():
            if any(sensitive in key.upper() for sensitive in ['TOKEN', 'PASS', 'KEY', 'SECRET']):
                print(f"  {key}: ***")
            else:
                print(f"  {key}: {value}")
    
    elif args.verify:
        if manager.verify_integrity():
            print("✅ 무결성 검증 통과")
        else:
            print("❌ 무결성 검증 실패")
            sys.exit(1)
    
    elif args.setup:
        env_vars = manager.setup_velos_env()
        print("✅ VELOS 기본 환경변수 설정 완료")
        print(f"📊 설정된 변수 수: {len(env_vars)}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

