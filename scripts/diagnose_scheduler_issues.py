#!/usr/bin/env python3
"""
VELOS 스케줄러 문제 진단 스크립트
- 현재 활성 스케줄러 작업들 분석
- 창 노출 문제 원인 파악
- 개선 방안 제시
"""

import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import re

class SchedulerDiagnostic:
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'active_tasks': [],
            'hidden_issues': [],
            'recommendations': [],
            'summary': {}
        }
    
    def run_powershell_command(self, command):
        """PowerShell 명령 실행"""
        try:
            # Windows에서 실행될 PowerShell 명령어들
            ps_commands = {
                'list_tasks': 'Get-ScheduledTask | Where-Object {$_.TaskName -like "*VELOS*"} | Select-Object TaskName, State, TaskPath | ConvertTo-Json',
                'task_details': 'Get-ScheduledTask -TaskName "{}" | Get-ScheduledTaskInfo | ConvertTo-Json',
                'running_tasks': 'Get-ScheduledTask | Where-Object {$_.State -eq "Running" -and $_.TaskName -like "*VELOS*"} | ConvertTo-Json'
            }
            
            if command in ps_commands:
                return ps_commands[command]
            return command
        except Exception as e:
            print(f"⚠️ PowerShell 명령 생성 오류: {e}")
            return None
    
    def analyze_xml_file(self, xml_path):
        """XML 스케줄러 파일 분석"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # 네임스페이스 처리
            ns = {'task': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            
            analysis = {
                'file': str(xml_path),
                'task_name': '',
                'hidden': False,
                'run_level': '',
                'user_id': '',
                'command': '',
                'arguments': '',
                'triggers': [],
                'issues': []
            }
            
            # Task 이름 추출
            uri_elem = root.find('.//task:RegistrationInfo/task:URI', ns)
            if uri_elem is not None:
                analysis['task_name'] = uri_elem.text.strip('\\')
            
            # Hidden 설정 확인
            hidden_elem = root.find('.//task:Settings/task:Hidden', ns)
            if hidden_elem is not None:
                analysis['hidden'] = hidden_elem.text.lower() == 'true'
            else:
                analysis['issues'].append('Hidden 설정 누락')
            
            # 권한 설정 확인
            user_elem = root.find('.//task:Principal/task:UserId', ns)
            if user_elem is not None:
                analysis['user_id'] = user_elem.text
                if user_elem.text == 'S-1-5-18':
                    analysis['run_level'] = 'SYSTEM'
                else:
                    analysis['run_level'] = 'USER'
            
            # 실행 명령 확인
            command_elem = root.find('.//task:Actions/task:Exec/task:Command', ns)
            if command_elem is not None:
                analysis['command'] = command_elem.text
            
            args_elem = root.find('.//task:Actions/task:Exec/task:Arguments', ns)
            if args_elem is not None:
                analysis['arguments'] = args_elem.text
            
            # 트리거 분석
            for trigger in root.findall('.//task:Triggers/*', ns):
                trigger_type = trigger.tag.split('}')[-1] if '}' in trigger.tag else trigger.tag
                analysis['triggers'].append(trigger_type)
            
            # 문제점 분석
            if not analysis['hidden']:
                analysis['issues'].append('🚨 Hidden=false로 인한 창 노출')
            
            if 'cmd' in analysis['command'].lower() or analysis['command'].endswith('.cmd'):
                analysis['issues'].append('⚠️ CMD 직접 실행으로 인한 창 노출 위험')
            
            if 'WindowStyle Hidden' not in analysis['arguments']:
                if 'powershell' in analysis['command'].lower():
                    analysis['issues'].append('⚠️ PowerShell WindowStyle Hidden 누락')
            
            return analysis
            
        except Exception as e:
            return {
                'file': str(xml_path),
                'error': f'XML 파싱 오류: {e}',
                'issues': ['파일 분석 실패']
            }
    
    def generate_improvement_recommendations(self, analyses):
        """개선 방안 생성"""
        recommendations = []
        
        # 문제별 통계
        hidden_issues = sum(1 for a in analyses if not a.get('hidden', True))
        cmd_issues = sum(1 for a in analyses if 'cmd' in a.get('command', '').lower())
        powershell_issues = sum(1 for a in analyses 
                              if 'powershell' in a.get('command', '').lower() 
                              and 'WindowStyle Hidden' not in a.get('arguments', ''))
        
        if hidden_issues > 0:
            recommendations.append({
                'priority': 'HIGH',
                'issue': f'{hidden_issues}개 작업에서 Hidden 설정 누락',
                'solution': 'XML 파일에 <Hidden>true</Hidden> 추가',
                'impact': '즉시 창 노출 문제 해결'
            })
        
        if cmd_issues > 0:
            recommendations.append({
                'priority': 'MEDIUM',
                'issue': f'{cmd_issues}개 작업이 CMD 직접 실행',
                'solution': 'VBScript 래퍼 또는 PowerShell로 변경',
                'impact': '완전한 창 숨김 보장'
            })
        
        if powershell_issues > 0:
            recommendations.append({
                'priority': 'LOW',
                'issue': f'{powershell_issues}개 PowerShell 작업에서 WindowStyle 누락',
                'solution': '-WindowStyle Hidden 매개변수 추가',
                'impact': 'PowerShell 창 숨김 개선'
            })
        
        # 통합 솔루션 제안
        recommendations.append({
            'priority': 'STRATEGIC',
            'issue': '스케줄러 작업 관리 체계화 필요',
            'solution': '표준 VBScript 래퍼 + 통일된 XML 템플릿 적용',
            'impact': '향후 모든 창 노출 문제 예방'
        })
        
        return recommendations
    
    def generate_powershell_diagnostic_script(self):
        """Windows에서 실행할 PowerShell 진단 스크립트 생성"""
        ps_script = '''
# VELOS 스케줄러 진단 스크립트
Write-Host "=== VELOS 스케줄러 진단 시작 ===" -ForegroundColor Green

# 1. VELOS 관련 활성 작업 조회
Write-Host "`n1. VELOS 관련 스케줄러 작업:" -ForegroundColor Yellow
$velosTasks = Get-ScheduledTask | Where-Object {$_.TaskName -like "*VELOS*"}
$velosTasks | Select-Object TaskName, State, TaskPath | Format-Table -AutoSize

# 2. 현재 실행 중인 VELOS 작업
Write-Host "`n2. 현재 실행 중인 VELOS 작업:" -ForegroundColor Yellow
$runningTasks = Get-ScheduledTask | Where-Object {$_.State -eq "Running" -and $_.TaskName -like "*VELOS*"}
if ($runningTasks.Count -gt 0) {
    $runningTasks | Select-Object TaskName, State | Format-Table -AutoSize
} else {
    Write-Host "현재 실행 중인 VELOS 작업 없음" -ForegroundColor Gray
}

# 3. 최근 실행 이력 (창이 나타난 시점 추적)
Write-Host "`n3. 최근 VELOS 작업 실행 이력:" -ForegroundColor Yellow
foreach ($task in $velosTasks) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName $task.TaskName -ErrorAction SilentlyContinue
    if ($taskInfo) {
        Write-Host "작업: $($task.TaskName)" -ForegroundColor Cyan
        Write-Host "  마지막 실행: $($taskInfo.LastRunTime)"
        Write-Host "  다음 실행: $($taskInfo.NextRunTime)"
        Write-Host "  마지막 결과: $($taskInfo.LastTaskResult)"
    }
}

# 4. Hidden 설정 확인을 위한 XML 내용 검사
Write-Host "`n4. Hidden 설정 검사:" -ForegroundColor Yellow
$taskFolder = "C:\\Windows\\System32\\Tasks"
Get-ChildItem -Path $taskFolder -Recurse -Filter "*VELOS*" -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    $isHidden = $content -match "<Hidden>true</Hidden>"
    $taskName = $_.Name
    if ($isHidden) {
        Write-Host "  ✅ $taskName - Hidden 설정됨" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $taskName - Hidden 설정 안됨 (창 노출 원인!)" -ForegroundColor Red
    }
}

Write-Host "`n=== 진단 완료 ===" -ForegroundColor Green
Write-Host "위 결과를 Claude AI에게 전달하여 정확한 수정 방안을 받으세요." -ForegroundColor Yellow
'''
        return ps_script
    
    def run_diagnosis(self):
        """진단 실행"""
        print("🔍 VELOS 스케줄러 문제 진단 시작...")
        
        # XML 파일들 분석
        xml_files = list(Path('C:\giwanos').glob('**/*.xml'))
        analyses = []
        
        for xml_file in xml_files:
            if 'VELOS' in str(xml_file):
                analysis = self.analyze_xml_file(xml_file)
                analyses.append(analysis)
        
        # 결과 정리
        self.results['xml_analyses'] = analyses
        self.results['recommendations'] = self.generate_improvement_recommendations(analyses)
        
        # 통계 계산
        total_tasks = len(analyses)
        hidden_issues = sum(1 for a in analyses if '창 노출' in ' '.join(a.get('issues', [])))
        
        self.results['summary'] = {
            'total_tasks_analyzed': total_tasks,
            'hidden_issues_count': hidden_issues,
            'severity': 'HIGH' if hidden_issues > 0 else 'LOW'
        }
        
        return self.results
    
    def save_results(self, output_path):
        """결과 저장"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

def main():
    diagnostic = SchedulerDiagnostic()
    
    # 진단 실행
    results = diagnostic.run_diagnosis()
    
    # 결과 출력
    print("\n" + "="*60)
    print("📊 VELOS 스케줄러 진단 결과")
    print("="*60)
    
    print(f"\n📋 분석된 작업 수: {results['summary']['total_tasks_analyzed']}")
    print(f"🚨 창 노출 문제: {results['summary']['hidden_issues_count']}개")
    print(f"⚠️ 심각도: {results['summary']['severity']}")
    
    print(f"\n🔍 문제가 발견된 작업들:")
    for analysis in results['xml_analyses']:
        if analysis.get('issues'):
            print(f"  📁 {analysis.get('task_name', 'Unknown')}")
            for issue in analysis['issues']:
                print(f"    - {issue}")
    
    print(f"\n💡 개선 권장사항:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. [{rec['priority']}] {rec['issue']}")
        print(f"     해결: {rec['solution']}")
        print(f"     효과: {rec['impact']}")
        print()
    
    # PowerShell 진단 스크립트 생성
    ps_script = diagnostic.generate_powershell_diagnostic_script()
    ps_script_path = Path('C:\giwanos/scripts/windows_scheduler_diagnosis.ps1')
    ps_script_path.write_text(ps_script, encoding='utf-8')
    
    print(f"📝 Windows 진단 스크립트 생성됨: {ps_script_path}")
    print("   이 스크립트를 Windows에서 관리자 권한으로 실행하세요.")
    
    # JSON 결과 저장
    results_path = Path('C:\giwanos/data/scheduler_diagnosis_results.json')
    results_path.parent.mkdir(exist_ok=True)
    diagnostic.save_results(results_path)
    
    print(f"📊 상세 결과 저장됨: {results_path}")
    
    return results

if __name__ == "__main__":
    main()