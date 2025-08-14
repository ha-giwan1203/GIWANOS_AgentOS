"""
VELOS Command Processor

VELOS 시스템에서 받은 명령을 처리하고 Cursor 연동을 통해 자동화된 작업을 수행합니다.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union
from datetime import datetime

from modules.core.cursor_integration import CursorIntegration, CursorIntegrationError
from modules.core.memory_adapter import create_memory_adapter


class CommandProcessorError(Exception):
    """명령 처리 관련 예외"""
    pass


class VELOSCommandProcessor:
    """
    VELOS 명령 처리기
    
    자연어 명령을 파싱하고 Cursor 연동을 통해 자동화된 작업을 수행합니다.
    """
    
    def __init__(self):
        """명령 처리기 초기화"""
        from modules.core.cursor_integration import create_cursor_integration
        self.cursor = create_cursor_integration()
        self.memory = create_memory_adapter()
        self.command_history = []
    
    def process_command(self, command: str) -> Dict:
        """
        명령 처리
        
        Args:
            command: 처리할 명령 (자연어)
            
        Returns:
            처리 결과
        """
        try:
            # 명령 기록
            self.command_history.append({
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "status": "processing"
            })
            
            # 명령 파싱
            parsed = self._parse_command(command)
            
            # 명령 실행
            result = self._execute_command(parsed)
            
            # 결과 기록
            self.command_history[-1]["status"] = "completed"
            self.command_history[-1]["result"] = result
            
            return result
        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
            
            # 오류 기록
            if self.command_history:
                self.command_history[-1]["status"] = "failed"
                self.command_history[-1]["result"] = error_result
            
            return error_result
    
    def _parse_command(self, command: str) -> Dict:
        """
        자연어 명령 파싱
        
        Args:
            command: 자연어 명령
            
        Returns:
            파싱된 명령 구조
        """
        command = command.lower().strip()
        
        # 파일 생성 명령
        if any(keyword in command for keyword in ["파일 생성", "파일 만들기", "create file", "make file"]):
            return self._parse_create_file_command(command)
        
        # 파일 수정 명령
        elif any(keyword in command for keyword in ["파일 수정", "파일 편집", "modify file", "edit file"]):
            return self._parse_modify_file_command(command)
        
        # 코드 실행 명령
        elif any(keyword in command for keyword in ["실행", "run", "test", "테스트"]):
            return self._parse_execute_command(command)
        
        # 워크스페이스 열기 명령
        elif any(keyword in command for keyword in ["워크스페이스 열기", "open workspace", "cursor 열기"]):
            return {"type": "open_workspace"}
        
        # 파일 정보 조회 명령
        elif any(keyword in command for keyword in ["파일 정보", "file info", "파일 목록"]):
            return self._parse_file_info_command(command)
        
        # 기본 명령 (도움말)
        else:
            return {"type": "help", "original_command": command}
    
    def _parse_create_file_command(self, command: str) -> Dict:
        """파일 생성 명령 파싱"""
        # 파일 경로 추출
        path_match = re.search(r'([a-zA-Z0-9_\-\.\/\\]+\.(py|md|json|txt|yaml|yml))', command)
        file_path = path_match.group(1) if path_match else "new_file.py"
        
        # 파일 내용 추출 (따옴표 안의 내용)
        content_match = re.search(r'["\']([^"\']+)["\']', command)
        content = content_match.group(1) if content_match else ""
        
        # 파일 타입 추출
        file_type = "auto"
        if ".py" in file_path:
            file_type = "python"
        elif ".md" in file_path:
            file_type = "markdown"
        elif ".json" in file_path:
            file_type = "json"
        
        return {
            "type": "create_file",
            "file_path": file_path,
            "content": content,
            "file_type": file_type
        }
    
    def _parse_modify_file_command(self, command: str) -> Dict:
        """파일 수정 명령 파싱"""
        # 파일 경로 추출
        path_match = re.search(r'([a-zA-Z0-9_\-\.\/\\]+\.(py|md|json|txt|yaml|yml))', command)
        file_path = path_match.group(1) if path_match else ""
        
        # 라인 번호 추출
        line_match = re.search(r'라인\s*(\d+)', command)
        line_num = int(line_match.group(1)) if line_match else 1
        
        # 수정 내용 추출
        content_match = re.search(r'["\']([^"\']+)["\']', command)
        content = content_match.group(1) if content_match else ""
        
        return {
            "type": "modify_file",
            "file_path": file_path,
            "line": line_num,
            "content": content
        }
    
    def _parse_execute_command(self, command: str) -> Dict:
        """실행 명령 파싱"""
        # 파일 경로 추출
        path_match = re.search(r'([a-zA-Z0-9_\-\.\/\\]+\.py)', command)
        file_path = path_match.group(1) if path_match else None
        
        return {
            "type": "execute",
            "file_path": file_path,
            "is_test": "test" in command or "테스트" in command
        }
    
    def _parse_file_info_command(self, command: str) -> Dict:
        """파일 정보 조회 명령 파싱"""
        # 파일 경로 추출
        path_match = re.search(r'([a-zA-Z0-9_\-\.\/\\]+)', command)
        file_path = path_match.group(1) if path_match else None
        
        return {
            "type": "file_info",
            "file_path": file_path,
            "list_all": "목록" in command or "list" in command
        }
    
    def _execute_command(self, parsed: Dict) -> Dict:
        """
        파싱된 명령 실행
        
        Args:
            parsed: 파싱된 명령
            
        Returns:
            실행 결과
        """
        command_type = parsed.get("type")
        
        try:
            if command_type == "create_file":
                return self._execute_create_file(parsed)
            elif command_type == "modify_file":
                return self._execute_modify_file(parsed)
            elif command_type == "execute":
                return self._execute_run_command(parsed)
            elif command_type == "open_workspace":
                return self._execute_open_workspace(parsed)
            elif command_type == "file_info":
                return self._execute_file_info(parsed)
            elif command_type == "help":
                return self._execute_help(parsed)
            else:
                return {
                    "success": False,
                    "error": f"알 수 없는 명령 타입: {command_type}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"명령 실행 실패: {str(e)}"
            }
    
    def _execute_create_file(self, parsed: Dict) -> Dict:
        """파일 생성 실행"""
        try:
            success = self.cursor.create_file(
                parsed["file_path"],
                parsed["content"],
                parsed["file_type"]
            )
            
            if success:
                # 메모리에 기록
                self.memory.append({
                    "body": f"파일 생성: {parsed['file_path']}",
                    "role": "system",
                    "metadata": {
                        "command_type": "create_file",
                        "file_path": parsed["file_path"],
                        "file_type": parsed["file_type"]
                    }
                })
                
                return {
                    "success": True,
                    "message": f"파일이 생성되었습니다: {parsed['file_path']}",
                    "file_path": parsed["file_path"],
                    "file_type": parsed["file_type"]
                }
            else:
                return {
                    "success": False,
                    "error": "파일 생성에 실패했습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"파일 생성 실패: {str(e)}"
            }
    
    def _execute_modify_file(self, parsed: Dict) -> Dict:
        """파일 수정 실행"""
        try:
            modifications = [{
                "type": "replace",
                "line": parsed["line"],
                "content": parsed["content"]
            }]
            
            success = self.cursor.modify_file(parsed["file_path"], modifications)
            
            if success:
                # 메모리에 기록
                self.memory.append({
                    "body": f"파일 수정: {parsed['file_path']} 라인 {parsed['line']}",
                    "role": "system",
                    "metadata": {
                        "command_type": "modify_file",
                        "file_path": parsed["file_path"],
                        "line": parsed["line"]
                    }
                })
                
                return {
                    "success": True,
                    "message": f"파일이 수정되었습니다: {parsed['file_path']} 라인 {parsed['line']}",
                    "file_path": parsed["file_path"],
                    "line": parsed["line"]
                }
            else:
                return {
                    "success": False,
                    "error": "파일 수정에 실패했습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"파일 수정 실패: {str(e)}"
            }
    
    def _execute_run_command(self, parsed: Dict) -> Dict:
        """실행 명령 실행"""
        try:
            if parsed["is_test"]:
                result = self.cursor.run_test(parsed["file_path"])
            else:
                result = self.cursor.execute_command(f"python {parsed['file_path']}")
            
            # 메모리에 기록
            self.memory.append({
                "body": f"명령 실행: {'테스트' if parsed['is_test'] else '실행'} {parsed['file_path']}",
                "role": "system",
                "metadata": {
                    "command_type": "execute",
                    "file_path": parsed["file_path"],
                    "is_test": parsed["is_test"],
                    "result": result
                }
            })
            
            return {
                "success": result["success"],
                "message": f"명령이 실행되었습니다: {parsed['file_path']}",
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "returncode": result.get("returncode", 0)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"명령 실행 실패: {str(e)}"
            }
    
    def _execute_open_workspace(self, parsed: Dict) -> Dict:
        """워크스페이스 열기 실행"""
        try:
            success = self.cursor.open_workspace()
            
            if success:
                return {
                    "success": True,
                    "message": "Cursor 워크스페이스가 열렸습니다."
                }
            else:
                return {
                    "success": False,
                    "error": "워크스페이스 열기에 실패했습니다."
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"워크스페이스 열기 실패: {str(e)}"
            }
    
    def _execute_file_info(self, parsed: Dict) -> Dict:
        """파일 정보 조회 실행"""
        try:
            if parsed["list_all"]:
                files = self.cursor.list_workspace_files()
                return {
                    "success": True,
                    "message": f"총 {len(files)}개의 파일이 있습니다.",
                    "files": files
                }
            else:
                info = self.cursor.get_file_info(parsed["file_path"])
                return {
                    "success": True,
                    "message": "파일 정보를 조회했습니다.",
                    "file_info": info
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"파일 정보 조회 실패: {str(e)}"
            }
    
    def _execute_help(self, parsed: Dict) -> Dict:
        """도움말 실행"""
        help_text = """
VELOS-Cursor 통합 명령어:

1. 파일 생성:
   - "파일 생성 test.py 'print(\"Hello\")'"
   - "create file example.md '# 제목'"

2. 파일 수정:
   - "파일 수정 test.py 라인 5 '새로운 내용'"
   - "modify file example.py line 10 '수정된 코드'"

3. 코드 실행:
   - "실행 test.py"
   - "test example.py"
   - "run script.py"

4. 워크스페이스 열기:
   - "워크스페이스 열기"
   - "open workspace"
   - "cursor 열기"

5. 파일 정보:
   - "파일 정보 test.py"
   - "파일 목록"
   - "file info example.py"

원본 명령: {original_command}
        """.format(original_command=parsed.get("original_command", ""))
        
        return {
            "success": True,
            "message": "도움말을 표시합니다.",
            "help": help_text
        }
    
    def get_command_history(self) -> List[Dict]:
        """명령 히스토리 조회"""
        return self.command_history
    
    def clear_history(self) -> None:
        """명령 히스토리 초기화"""
        self.command_history.clear()


def create_command_processor() -> VELOSCommandProcessor:
    """
    명령 처리기 인스턴스 생성
    
    Returns:
        VELOSCommandProcessor 인스턴스
    """
    return VELOSCommandProcessor()


if __name__ == "__main__":
    # 테스트 코드
    processor = create_command_processor()
    
    # 테스트 명령들
    test_commands = [
        "파일 생성 test_processor.py 'print(\"Hello from processor!\")'",
        "워크스페이스 열기",
        "파일 정보 test_processor.py",
        "실행 test_processor.py"
    ]
    
    for command in test_commands:
        print(f"\n명령: {command}")
        result = processor.process_command(command)
        print(f"결과: {result}")
    
    # 히스토리 출력
    print(f"\n명령 히스토리: {len(processor.get_command_history())}개")
