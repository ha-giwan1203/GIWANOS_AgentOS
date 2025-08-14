"""
VELOS-Cursor Integration Module

VELOS 시스템과 Cursor IDE를 연동하여 자동화된 코드 편집 및 파일 관리를 제공합니다.
"""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime


class CursorIntegrationError(Exception):
    """Cursor 연동 관련 예외"""
    pass


class CursorIntegration:
    """
    VELOS-Cursor 연동 클래스
    
    Cursor API를 통해 파일 생성, 수정, 실행을 자동화합니다.
    """
    
    def __init__(self, velos_root: Path):
        """
        Cursor 연동 초기화
        
        Args:
            velos_root: VELOS 루트 디렉토리 경로
        """
        self.velos_root = velos_root
        self.cursor_config = self._load_cursor_config()
    
    def _load_cursor_config(self) -> Dict:
        """Cursor 설정 파일 로드"""
        config_path = self.velos_root / "configs" / "cursor_config.json"
        
        default_config = {
            "cursor_path": "cursor",
            "auto_commit": True,
            "auto_test": True,
            "workspace_path": str(self.velos_root),
            "git_auto_push": True,
            "file_watch_enabled": True
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
            except Exception as e:
                print(f"Cursor 설정 로드 실패, 기본값 사용: {e}")
                return default_config
        else:
            # 기본 설정 파일 생성
            self._save_cursor_config(default_config)
            return default_config
    
    def _save_cursor_config(self, config: Dict) -> None:
        """Cursor 설정 파일 저장"""
        config_path = self.velos_root / "configs" / "cursor_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def open_workspace(self) -> bool:
        """
        Cursor에서 VELOS 워크스페이스 열기
        
        Returns:
            성공 여부
        """
        try:
            cmd = [self.cursor_config["cursor_path"], str(self.velos_root)]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            raise CursorIntegrationError(f"Cursor 워크스페이스 열기 실패: {e}")
        except FileNotFoundError:
            raise CursorIntegrationError("Cursor가 설치되지 않았거나 PATH에 없습니다.")
    
    def create_file(self, file_path: Union[str, Path], content: str, 
                   file_type: str = "auto") -> bool:
        """
        Cursor를 통해 파일 생성
        
        Args:
            file_path: 생성할 파일 경로
            content: 파일 내용
            file_type: 파일 타입 (auto, python, markdown, json 등)
            
        Returns:
            성공 여부
        """
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.velos_root / file_path
            
            # 디렉토리 생성
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 생성
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Cursor에서 파일 열기
            self._open_file_in_cursor(file_path)
            
            # 자동 커밋
            if self.cursor_config["auto_commit"]:
                self._auto_commit(f"Create {file_path.name}")
            
            return True
        except Exception as e:
            raise CursorIntegrationError(f"파일 생성 실패: {e}")
    
    def modify_file(self, file_path: Union[str, Path], 
                   modifications: List[Dict]) -> bool:
        """
        Cursor를 통해 파일 수정
        
        Args:
            file_path: 수정할 파일 경로
            modifications: 수정 사항 리스트
                [
                    {
                        "type": "replace",  # replace, insert, delete
                        "line": 10,         # 라인 번호
                        "content": "새 내용"  # 수정할 내용
                    }
                ]
            
        Returns:
            성공 여부
        """
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.velos_root / file_path
            
            if not file_path.exists():
                raise CursorIntegrationError(f"파일이 존재하지 않습니다: {file_path}")
            
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 수정 사항 적용
            for mod in modifications:
                mod_type = mod.get("type", "replace")
                line_num = mod.get("line", 1) - 1  # 0-based index
                content = mod.get("content", "")
                
                if mod_type == "replace":
                    if 0 <= line_num < len(lines):
                        lines[line_num] = content + "\n"
                elif mod_type == "insert":
                    lines.insert(line_num, content + "\n")
                elif mod_type == "delete":
                    if 0 <= line_num < len(lines):
                        del lines[line_num]
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            # Cursor에서 파일 열기
            self._open_file_in_cursor(file_path)
            
            # 자동 커밋
            if self.cursor_config["auto_commit"]:
                self._auto_commit(f"Modify {file_path.name}")
            
            return True
        except Exception as e:
            raise CursorIntegrationError(f"파일 수정 실패: {e}")
    
    def execute_command(self, command: str, cwd: Optional[Path] = None) -> Dict:
        """
        Cursor 터미널에서 명령 실행
        
        Args:
            command: 실행할 명령
            cwd: 작업 디렉토리 (기본값: VELOS 루트)
            
        Returns:
            실행 결과
        """
        try:
            if cwd is None:
                cwd = self.velos_root
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            raise CursorIntegrationError(f"명령 실행 실패: {e}")
    
    def run_test(self, test_path: Optional[Union[str, Path]] = None) -> Dict:
        """
        자동 테스트 실행
        
        Args:
            test_path: 테스트할 파일 경로 (None이면 전체 테스트)
            
        Returns:
            테스트 결과
        """
        try:
            if test_path:
                test_path = Path(test_path)
                if not test_path.is_absolute():
                    test_path = self.velos_root / test_path
                
                # Python 파일 테스트
                if test_path.suffix == '.py':
                    result = self.execute_command(f"python -m py_compile {test_path}")
                    if result["success"]:
                        result = self.execute_command(f"python {test_path}")
            else:
                # 전체 프로젝트 테스트
                result = self.execute_command("python -m pytest")
            
            return result
        except Exception as e:
            raise CursorIntegrationError(f"테스트 실행 실패: {e}")
    
    def _open_file_in_cursor(self, file_path: Path) -> None:
        """Cursor에서 파일 열기"""
        try:
            cmd = [self.cursor_config["cursor_path"], str(file_path)]
            subprocess.run(cmd, check=True, capture_output=True)
        except Exception as e:
            print(f"Cursor에서 파일 열기 실패: {e}")
    
    def _auto_commit(self, message: str) -> bool:
        """자동 Git 커밋"""
        try:
            # Git 상태 확인
            status_result = self.execute_command("git status --porcelain")
            if not status_result["stdout"].strip():
                return True  # 변경사항 없음
            
            # 커밋
            commit_result = self.execute_command(f'git add . && git commit -m "{message}"')
            
            # 자동 푸시
            if self.cursor_config["git_auto_push"]:
                push_result = self.execute_command("git push")
                return push_result["success"]
            
            return commit_result["success"]
        except Exception as e:
            print(f"자동 커밋 실패: {e}")
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict:
        """
        파일 정보 조회
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파일 정보
        """
        try:
            file_path = Path(file_path)
            if not file_path.is_absolute():
                file_path = self.velos_root / file_path
            
            if not file_path.exists():
                return {"exists": False}
            
            stat = file_path.stat()
            return {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "extension": file_path.suffix,
                "relative_path": str(file_path.relative_to(self.velos_root))
            }
        except Exception as e:
            raise CursorIntegrationError(f"파일 정보 조회 실패: {e}")
    
    def list_workspace_files(self, pattern: str = "**/*") -> List[Dict]:
        """
        워크스페이스 파일 목록 조회
        
        Args:
            pattern: 파일 패턴 (glob 형식)
            
        Returns:
            파일 목록
        """
        try:
            files = []
            for file_path in self.velos_root.glob(pattern):
                if file_path.is_file():
                    files.append(self.get_file_info(file_path))
            return files
        except Exception as e:
            raise CursorIntegrationError(f"파일 목록 조회 실패: {e}")


def create_cursor_integration() -> CursorIntegration:
    """
    기본 설정으로 Cursor 연동 인스턴스 생성
    
    Returns:
        CursorIntegration 인스턴스
    """
    from modules.report_paths import ROOT
    return CursorIntegration(ROOT)


if __name__ == "__main__":
    # 테스트 코드
    integration = create_cursor_integration()
    
    # 워크스페이스 열기
    print("Cursor 워크스페이스 열기...")
    integration.open_workspace()
    
    # 파일 생성 테스트
    test_content = '''"""
테스트 파일
"""
print("Hello from VELOS-Cursor integration!")
'''
    
    print("테스트 파일 생성...")
    integration.create_file("test_cursor_integration.py", test_content)
    
    # 파일 정보 조회
    info = integration.get_file_info("test_cursor_integration.py")
    print(f"파일 정보: {info}")
