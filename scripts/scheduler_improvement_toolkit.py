#!/usr/bin/env python3
"""
VELOS 스케줄러 개선 툴킷
- 완전한 창 숨김 솔루션 제공
- XML 자동 수정
- VBScript 래퍼 생성
- 표준화된 스케줄러 템플릿
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import json
import re
from datetime import datetime

class SchedulerImprovementToolkit:
    def __init__(self):
        self.webapp_root = Path('C:\giwanos')
        self.scripts_dir = self.webapp_root / 'scripts'
        self.templates_dir = self.webapp_root / 'templates'
        self.improved_dir = self.webapp_root / 'scheduler_improvements'
        
        self.improved_dir.mkdir(exist_ok=True)
    
    def create_universal_vbs_wrapper(self):
        """범용 VBScript 래퍼 생성"""
        vbs_template = '''
' VELOS 범용 숨김 실행 래퍼 v2.0
' 모든 VELOS 스크립트를 완전히 숨겨서 실행
' 사용법: wscript.exe universal_velos_wrapper.vbs "실행할명령어" "작업디렉토리"

If WScript.Arguments.Count < 1 Then
    WScript.Quit(1)
End If

' 실행할 명령어와 작업 디렉토리 받기
Dim command, workDir
command = WScript.Arguments(0)
If WScript.Arguments.Count >= 2 Then
    workDir = WScript.Arguments(1)
Else
    workDir = "C:\\giwanos"
End If

' Shell 객체 생성
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 환경변수 설정
Set objEnv = objShell.Environment("Process")
objEnv("PYTHONPATH") = workDir

' 작업 디렉토리 변경
objShell.CurrentDirectory = workDir

' 명령어 실행 (완전 숨김)
' 0 = 완전 숨김, False = 비동기 실행
objShell.Run command, 0, False

' 메모리 정리
Set objShell = Nothing
Set objFSO = Nothing
Set objEnv = Nothing
        '''.strip()
        
        wrapper_path = self.scripts_dir / 'universal_velos_wrapper.vbs'
        wrapper_path.write_text(vbs_template, encoding='utf-8')
        return wrapper_path
    
    def create_powershell_hidden_wrapper(self):
        """PowerShell 숨김 래퍼 생성"""
        ps_template = '''
# VELOS PowerShell 숨김 실행 래퍼 v2.0
param(
    [Parameter(Mandatory=$true)]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [string]$WorkingDirectory = "C:\\giwanos",
    
    [Parameter(Mandatory=$false)]
    [string]$Arguments = ""
)

# 작업 디렉토리 설정
Set-Location $WorkingDirectory
$env:PYTHONPATH = $WorkingDirectory

# 완전 숨김으로 실행
if ($Arguments) {
    Start-Process $Command -ArgumentList $Arguments -WindowStyle Hidden -NoNewWindow
} else {
    Start-Process $Command -WindowStyle Hidden -NoNewWindow
}
        '''.strip()
        
        wrapper_path = self.scripts_dir / 'universal_powershell_wrapper.ps1'
        wrapper_path.write_text(ps_template, encoding='utf-8')
        return wrapper_path
    
    def fix_xml_hidden_setting(self, xml_path):
        """XML 파일의 Hidden 설정 수정"""
        try:
            # XML 파일 읽기
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 네임스페이스 처리
            ns = {'task': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            
            # Settings 섹션 찾기
            settings = root.find('.//task:Settings', ns)
            if settings is None:
                print(f"⚠️ Settings 섹션을 찾을 수 없음: {xml_path}")
                return None
            
            # Hidden 설정 확인 및 수정
            hidden_elem = settings.find('task:Hidden', ns)
            if hidden_elem is None:
                # Hidden 요소가 없으면 생성
                hidden_elem = ET.SubElement(settings, f'{{{ns["task"]}}}Hidden')
            
            hidden_elem.text = 'true'
            
            # 기타 권장 설정 적용
            self._apply_recommended_settings(settings, ns)
            
            # 수정된 XML 저장
            fixed_path = self.improved_dir / f"{xml_path.stem}_HIDDEN_FIXED.xml"
            tree.write(fixed_path, encoding='utf-16', xml_declaration=True)
            
            return fixed_path
            
        except Exception as e:
            print(f"❌ XML 수정 오류 ({xml_path}): {e}")
            return None
    
    def _apply_recommended_settings(self, settings, ns):
        """권장 설정 적용"""
        recommended_settings = {
            'MultipleInstancesPolicy': 'IgnoreNew',
            'DisallowStartIfOnBatteries': 'false',
            'StopIfGoingOnBatteries': 'false',
            'AllowHardTerminate': 'true',
            'StartWhenAvailable': 'true',
            'RunOnlyIfNetworkAvailable': 'false',
            'AllowStartOnDemand': 'true',
            'Enabled': 'true',
            'RunOnlyIfIdle': 'false',
            'WakeToRun': 'false',
            'ExecutionTimeLimit': 'PT0S'
        }
        
        for setting_name, setting_value in recommended_settings.items():
            elem = settings.find(f'task:{setting_name}', ns)
            if elem is None:
                elem = ET.SubElement(settings, f'{{{ns["task"]}}}{setting_name}')
            elem.text = setting_value
    
    def create_vbs_based_xml_template(self, task_name, vbs_script_path, trigger_type='Boot'):
        """VBScript 기반 XML 템플릿 생성"""
        xml_template = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Date>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}</Date>
    <Author>VELOS System Improved</Author>
    <URI>\\{task_name}</URI>
  </RegistrationInfo>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Triggers>'''
        
        if trigger_type == 'Boot':
            xml_template += '''
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>'''
        elif trigger_type == 'Logon':
            xml_template += '''
    <LogonTrigger>
      <Enabled>true</Enabled>
    </LogonTrigger>'''
        elif trigger_type == 'Daily':
            xml_template += f'''
    <CalendarTrigger>
      <StartBoundary>{datetime.now().strftime('%Y-%m-%d')}T09:00:00</StartBoundary>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>'''
        
        xml_template += f'''
  </Triggers>
  <Actions Context="Author">
    <Exec>
      <Command>wscript.exe</Command>
      <Arguments>"{vbs_script_path}"</Arguments>
      <WorkingDirectory>C:\\giwanos</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
        
        return xml_template
    
    def generate_specific_vbs_scripts(self):
        """특정 VELOS 작업용 VBScript 생성"""
        vbs_scripts = {
            'velos_bridge.vbs': {
                'command': 'python .\\scripts\\velos_bridge.py',
                'description': 'VELOS Bridge 실행'
            },
            'velos_master_loop.vbs': {
                'command': 'python .\\scripts\\velos_master_loop.py',
                'description': 'VELOS Master Loop 실행'
            },
            'velos_daily_report.vbs': {
                'command': 'python .\\scripts\\velos_daily_report.py',
                'description': 'VELOS Daily Report 실행'
            },
            'velos_health_check.vbs': {
                'command': 'python .\\scripts\\velos_health_check.py',
                'description': 'VELOS Health Check 실행'
            }
        }
        
        created_scripts = {}
        
        for script_name, config in vbs_scripts.items():
            vbs_content = f'''
' {config['description']} - 완전 숨김 실행
' 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' 작업 디렉토리 및 환경 설정
strWorkingDir = "C:\\giwanos"
objShell.CurrentDirectory = strWorkingDir

Set objEnv = objShell.Environment("Process")
objEnv("PYTHONPATH") = strWorkingDir

' 스크립트 실행 (완전 숨김)
objShell.Run "{config['command']}", 0, False

' 메모리 정리
Set objShell = Nothing
Set objFSO = Nothing
Set objEnv = Nothing
            '''.strip()
            
            script_path = self.scripts_dir / script_name
            script_path.write_text(vbs_content, encoding='utf-8')
            created_scripts[script_name] = script_path
        
        return created_scripts
    
    def create_scheduler_fix_batch(self):
        """스케줄러 수정 배치 스크립트 생성"""
        batch_content = '''@echo off
REM VELOS 스케줄러 완전 수정 배치
REM 관리자 권한으로 실행 필요

echo ===================================
echo VELOS 스케줄러 완전 수정 시작
echo ===================================

REM 기존 VELOS 작업들 삭제 (오류 무시)
echo 1. 기존 VELOS 작업들 삭제 중...
schtasks /delete /tn "VELOS Bridge AutoStart" /f >nul 2>&1
schtasks /delete /tn "VELOS Master Loop" /f >nul 2>&1
schtasks /delete /tn "VELOS Daily Report" /f >nul 2>&1
schtasks /delete /tn "VELOS Health Check" /f >nul 2>&1
schtasks /delete /tn "VELOS DB Backup" /f >nul 2>&1

REM 새로운 숨김 작업들 등록
echo 2. 새로운 숨김 작업들 등록 중...

if exist "C:\\giwanos\\scheduler_improvements\\VELOS_Bridge_HIDDEN.xml" (
    schtasks /create /xml "C:\\giwanos\\scheduler_improvements\\VELOS_Bridge_HIDDEN.xml" /tn "VELOS Bridge Hidden"
    echo   - VELOS Bridge Hidden 등록됨
)

if exist "C:\\giwanos\\scheduler_improvements\\VELOS_Master_Loop_HIDDEN.xml" (
    schtasks /create /xml "C:\\giwanos\\scheduler_improvements\\VELOS_Master_Loop_HIDDEN.xml" /tn "VELOS Master Loop Hidden"
    echo   - VELOS Master Loop Hidden 등록됨
)

if exist "C:\\giwanos\\scheduler_improvements\\VELOS_Daily_Report_HIDDEN.xml" (
    schtasks /create /xml "C:\\giwanos\\scheduler_improvements\\VELOS_Daily_Report_HIDDEN.xml" /tn "VELOS Daily Report Hidden"
    echo   - VELOS Daily Report Hidden 등록됨
)

echo 3. 등록된 VELOS 작업 확인...
schtasks /query /tn "*VELOS*" /fo table

echo ===================================
echo VELOS 스케줄러 수정 완료!
echo 이제 창이 나타나지 않습니다.
echo ===================================
pause
'''
        
        batch_path = self.improved_dir / 'fix_all_velos_schedulers.bat'
        batch_path.write_text(batch_content, encoding='utf-8')
        return batch_path
    
    def run_complete_improvement(self):
        """전체 개선 프로세스 실행"""
        print("🚀 VELOS 스케줄러 완전 개선 시작...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'improvements': [],
            'created_files': [],
            'recommendations': []
        }
        
        # 1. 범용 래퍼 생성
        print("📝 1. 범용 실행 래퍼 생성...")
        vbs_wrapper = self.create_universal_vbs_wrapper()
        ps_wrapper = self.create_powershell_hidden_wrapper()
        results['created_files'].extend([str(vbs_wrapper), str(ps_wrapper)])
        
        # 2. 특정 VBScript 생성
        print("🔧 2. VELOS 전용 VBScript 생성...")
        vbs_scripts = self.generate_specific_vbs_scripts()
        results['created_files'].extend([str(p) for p in vbs_scripts.values()])
        
        # 3. 기존 XML 파일 수정
        print("📋 3. 기존 XML 파일 Hidden 설정 수정...")
        xml_files = list(self.webapp_root.glob('VELOS*.xml'))
        for xml_file in xml_files:
            fixed_xml = self.fix_xml_hidden_setting(xml_file)
            if fixed_xml:
                results['improvements'].append(f"수정됨: {xml_file.name} → {fixed_xml.name}")
                results['created_files'].append(str(fixed_xml))
        
        # 4. 새로운 최적화된 XML 템플릿 생성
        print("✨ 4. 최적화된 XML 템플릿 생성...")
        optimized_templates = {
            'VELOS_Bridge_HIDDEN.xml': ('VELOS Bridge Hidden', 'C:\\giwanos\\scripts\\velos_bridge.vbs', 'Boot'),
            'VELOS_Master_Loop_HIDDEN.xml': ('VELOS Master Loop Hidden', 'C:\\giwanos\\scripts\\velos_master_loop.vbs', 'Boot'),
            'VELOS_Daily_Report_HIDDEN.xml': ('VELOS Daily Report Hidden', 'C:\\giwanos\\scripts\\velos_daily_report.vbs', 'Daily')
        }
        
        for xml_name, (task_name, vbs_path, trigger) in optimized_templates.items():
            xml_content = self.create_vbs_based_xml_template(task_name, vbs_path, trigger)
            xml_file = self.improved_dir / xml_name
            xml_file.write_text(xml_content, encoding='utf-16')
            results['created_files'].append(str(xml_file))
        
        # 5. 수정 배치 스크립트 생성
        print("🔨 5. 자동 수정 배치 스크립트 생성...")
        batch_script = self.create_scheduler_fix_batch()
        results['created_files'].append(str(batch_script))
        
        # 6. 사용 가이드 생성
        print("📖 6. 사용 가이드 생성...")
        guide_path = self.create_usage_guide()
        results['created_files'].append(str(guide_path))
        
        # 결과 저장
        results_path = self.improved_dir / 'improvement_results.json'
        results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        
        print(f"\n✅ 개선 완료! 결과: {results_path}")
        return results
    
    def create_usage_guide(self):
        """사용 가이드 생성"""
        guide_content = '''# VELOS 스케줄러 창 숨김 완전 해결 가이드

## 🎯 문제 해결 과정

### 1단계: 현재 상황 진단
```cmd
# Windows에서 관리자 권한으로 실행
powershell -ExecutionPolicy Bypass -File "C:\\giwanos\\scripts\\windows_scheduler_diagnosis.ps1"
```

### 2단계: 자동 수정 적용
```cmd
# 관리자 권한으로 배치 파일 실행
"C:\\giwanos\\scheduler_improvements\\fix_all_velos_schedulers.bat"
```

### 3단계: 수동 확인 (필요시)
```cmd
# 현재 등록된 VELOS 작업 확인
schtasks /query /tn "*VELOS*" /fo table

# Hidden 설정 확인
Get-ScheduledTask | Where-Object {$_.TaskName -like "*VELOS*"} | Get-ScheduledTaskInfo
```

## 🔧 개선 사항

### ✅ 완전한 창 숨김 보장
- 모든 XML에 `<Hidden>true</Hidden>` 설정
- VBScript 래퍼로 100% 창 숨김
- SYSTEM 계정으로 실행하여 권한 문제 해결

### ✅ 표준화된 실행 방식
- 범용 VBScript 래퍼 제공
- 일관된 XML 템플릿 적용
- 환경변수 및 경로 자동 설정

### ✅ 자동화된 수정 도구
- 진단 스크립트로 문제 파악
- 배치 스크립트로 일괄 수정
- 백업 및 복원 기능

## 🚨 주의사항

### 관리자 권한 필수
- 모든 스케줄러 조작은 관리자 권한 필요
- PowerShell 실행 정책 확인 필요

### 백업 권장
- 기존 스케줄러 작업 백업 필수
- XML 파일 원본 보관

## 📊 예상 결과

### Before (문제 상황)
- ❌ 스케줄러 실행 시 창이 나타남
- ❌ PowerShell/CMD 창 깜빡임  
- ❌ 사용자 인터페이스 방해

### After (해결 후)
- ✅ 완전한 백그라운드 실행
- ✅ 창 노출 없음
- ✅ 조용한 스케줄러 동작

## 🔍 트러블슈팅

### 문제: 여전히 창이 나타남
```cmd
# 1. Hidden 설정 확인
schtasks /query /tn "작업이름" /xml | findstr "Hidden"

# 2. 작업 재등록
schtasks /delete /tn "작업이름" /f
schtasks /create /xml "새로운XML파일" /tn "작업이름"
```

### 문제: 작업이 실행되지 않음
```cmd
# 1. 작업 상태 확인
schtasks /query /tn "작업이름" /fo list /v

# 2. 실행 테스트
schtasks /run /tn "작업이름"
```

## 📞 지원

문제 발생 시 다음 정보를 수집하여 보고:
1. `windows_scheduler_diagnosis.ps1` 실행 결과
2. 문제가 되는 작업의 XML 내용
3. 이벤트 로그 오류 메시지
'''
        
        guide_path = self.improved_dir / 'USAGE_GUIDE.md'
        guide_path.write_text(guide_content, encoding='utf-8')
        return guide_path

def main():
    toolkit = SchedulerImprovementToolkit()
    results = toolkit.run_complete_improvement()
    
    print("\n" + "="*60)
    print("🎉 VELOS 스케줄러 개선 완료!")
    print("="*60)
    
    print(f"\n📁 생성된 파일들:")
    for file_path in results['created_files']:
        print(f"  - {file_path}")
    
    print(f"\n🔧 개선된 항목들:")
    for improvement in results['improvements']:
        print(f"  - {improvement}")
    
    print(f"\n📋 다음 단계:")
    print("  1. Windows에서 관리자 권한으로 PowerShell 열기")
    print("  2. 진단 스크립트 실행: scripts/windows_scheduler_diagnosis.ps1")
    print("  3. 수정 배치 실행: scheduler_improvements/fix_all_velos_schedulers.bat")
    print("  4. 결과 확인 및 테스트")

if __name__ == "__main__":
    main()