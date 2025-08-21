#!/usr/bin/env python3
# =========================================================
# VELOS 통합 보고서 생성 시스템
# 다양한 보고서 유형을 통합 관리하는 메인 시스템
# =========================================================

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# 경로 설정
HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

# Force correct ROOT path for sandbox environment
REPORT_ROOT = ROOT  # Always use /home/user/webapp in sandbox

class EnhancedReportGenerator:
    """통합 보고서 생성기"""
    
    def __init__(self):
        self.root = REPORT_ROOT
        self.reports_dir = self.root / "data" / "reports"
        self.enhanced_dir = self.reports_dir / "enhanced"
        self.enhanced_dir.mkdir(parents=True, exist_ok=True)
        
        # 보고서 유형 정의
        self.report_types = {
            "health": {
                "name": "시스템 건강 대시보드",
                "module": "modules.reports.system_health_dashboard",
                "function": "generate_system_health_report",
                "frequency": "daily",
                "description": "실시간 시스템 상태 및 긴급 이슈 모니터링"
            },
            "weekly": {
                "name": "주간 운영 요약",
                "module": "modules.reports.weekly_operations_summary", 
                "function": "generate_weekly_operations_report",
                "frequency": "weekly",
                "description": "주간 성과, 안정성, 트렌드 분석"
            },
            "memory": {
                "name": "메모리 인텔리전스",
                "module": "modules.reports.memory_intelligence_report",
                "function": "generate_memory_intelligence_report", 
                "frequency": "weekly",
                "description": "학습 패턴, 지식 증가, 메모리 효율성 분석"
            }
        }
    
    def generate_report(self, report_type: str, **kwargs) -> Dict[str, Any]:
        """개별 보고서 생성"""
        if report_type not in self.report_types:
            raise ValueError(f"지원하지 않는 보고서 유형: {report_type}")
        
        report_config = self.report_types[report_type]
        
        try:
            # 모듈 동적 임포트
            module_name = report_config["module"]
            function_name = report_config["function"]
            
            module = __import__(module_name, fromlist=[function_name])
            generate_func = getattr(module, function_name)
            
            # 보고서 생성
            print(f"[INFO] {report_config['name']} 생성 중...")
            
            if report_type == "memory" and "depth" in kwargs:
                content = generate_func(kwargs["depth"])
            elif report_type == "weekly" and "weeks_back" in kwargs:
                content = generate_func(kwargs["weeks_back"])
            else:
                content = generate_func()
            
            # 파일 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"velos_{report_type}_report_{timestamp}.md"
            file_path = self.enhanced_dir / filename
            
            file_path.write_text(content, encoding="utf-8")
            
            return {
                "success": True,
                "type": report_type,
                "name": report_config["name"],
                "file_path": str(file_path),
                "filename": filename,
                "content": content,
                "timestamp": timestamp,
                "size": len(content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "type": report_type,
                "error": str(e),
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
    
    def generate_all_reports(self, types: Optional[List[str]] = None) -> Dict[str, Any]:
        """모든 보고서 또는 지정된 보고서들 생성"""
        if types is None:
            types = list(self.report_types.keys())
        
        results = {
            "generated_reports": [],
            "failed_reports": [],
            "summary": {},
            "timestamp": datetime.now().isoformat()
        }
        
        for report_type in types:
            if report_type not in self.report_types:
                results["failed_reports"].append({
                    "type": report_type,
                    "error": f"지원하지 않는 보고서 유형: {report_type}"
                })
                continue
            
            result = self.generate_report(report_type)
            
            if result["success"]:
                results["generated_reports"].append(result)
            else:
                results["failed_reports"].append(result)
        
        # 요약 통계
        results["summary"] = {
            "total_requested": len(types),
            "successful": len(results["generated_reports"]),
            "failed": len(results["failed_reports"]),
            "success_rate": f"{len(results['generated_reports'])/len(types)*100:.1f}%"
        }
        
        return results
    
    def create_master_dashboard(self, individual_results: List[Dict[str, Any]]) -> str:
        """개별 보고서들을 통합한 마스터 대시보드 생성"""
        dashboard_lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 제목
        dashboard_lines.append(f"# 🎯 VELOS 통합 대시보드 - {timestamp}")
        dashboard_lines.append("")
        dashboard_lines.append("> 실시간 시스템 상태, 주간 성과, 메모리 인텔리전스를 한눈에")
        dashboard_lines.append("")
        
        # 요약 섹션
        dashboard_lines.append("## 📊 보고서 생성 현황")
        successful_reports = [r for r in individual_results if r["success"]]
        failed_reports = [r for r in individual_results if not r["success"]]
        
        dashboard_lines.append(f"- **생성된 보고서**: {len(successful_reports)}개")
        dashboard_lines.append(f"- **실패한 보고서**: {len(failed_reports)}개")
        
        if successful_reports:
            total_size = sum(r["size"] for r in successful_reports)
            dashboard_lines.append(f"- **총 콘텐츠 크기**: {total_size:,} 문자")
        dashboard_lines.append("")
        
        # 개별 보고서 링크 및 요약
        dashboard_lines.append("## 📋 생성된 보고서들")
        
        for result in successful_reports:
            report_config = self.report_types[result["type"]]
            dashboard_lines.append(f"### {report_config['name']}")
            dashboard_lines.append(f"- **파일**: `{result['filename']}`")
            dashboard_lines.append(f"- **크기**: {result['size']:,} 문자")
            dashboard_lines.append(f"- **설명**: {report_config['description']}")
            dashboard_lines.append("")
            
            # 각 보고서의 핵심 내용 미리보기 (첫 200자)
            content_preview = result["content"][:200].replace('\n', ' ').strip()
            if len(result["content"]) > 200:
                content_preview += "..."
            dashboard_lines.append(f"**미리보기**: {content_preview}")
            dashboard_lines.append("")
        
        # 실패한 보고서
        if failed_reports:
            dashboard_lines.append("## ⚠️ 생성 실패한 보고서")
            for result in failed_reports:
                dashboard_lines.append(f"- **{result.get('type', 'unknown')}**: {result.get('error', 'Unknown error')}")
            dashboard_lines.append("")
        
        # 시스템 권고사항 (각 보고서에서 추출)
        recommendations = self.extract_recommendations_from_reports(successful_reports)
        if recommendations:
            dashboard_lines.append("## 💡 통합 권고사항")
            for rec in recommendations[:5]:  # 상위 5개만
                dashboard_lines.append(f"- {rec}")
            dashboard_lines.append("")
        
        # 다음 보고서 생성 일정
        dashboard_lines.append("## 📅 다음 보고서 일정")
        for report_type, config in self.report_types.items():
            if config["frequency"] == "daily":
                next_gen = "매일 자동 생성"
            elif config["frequency"] == "weekly":
                next_gen = "매주 자동 생성"
            else:
                next_gen = f"{config['frequency']} 주기"
            dashboard_lines.append(f"- **{config['name']}**: {next_gen}")
        dashboard_lines.append("")
        
        # 생성 정보
        dashboard_lines.append("---")
        dashboard_lines.append(f"*생성시간: {timestamp}*")
        dashboard_lines.append("*VELOS 통합 대시보드 시스템 v2.0*")
        
        return "\n".join(dashboard_lines)
    
    def extract_recommendations_from_reports(self, results: List[Dict[str, Any]]) -> List[str]:
        """보고서들에서 권고사항 추출"""
        recommendations = []
        
        for result in results:
            content = result["content"]
            
            # 권고사항 섹션 찾기
            lines = content.split('\n')
            in_recommendations = False
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ["권고사항", "recommendations", "액션 플랜", "조치 필요"]):
                    in_recommendations = True
                    continue
                
                if in_recommendations:
                    if line.startswith('##') or line.startswith('---'):
                        break
                    if line.startswith('- ') and line.strip() != '- ':
                        rec = line[2:].strip()
                        if rec and rec not in recommendations:
                            recommendations.append(rec)
        
        return recommendations
    
    def send_to_dispatch_queue(self, report_info: Dict[str, Any]) -> bool:
        """생성된 보고서를 통합전송 큐에 추가"""
        try:
            dispatch_queue = self.root / "data" / "dispatch" / "_queue"
            dispatch_queue.mkdir(parents=True, exist_ok=True)
            
            message = {
                "title": f"📊 {report_info['name']} 생성 완료",
                "message": f"""새로운 보고서가 생성되었습니다.

📋 **보고서 정보**
- 유형: {report_info['name']}
- 파일: {report_info['filename']}
- 크기: {report_info['size']:,} 문자
- 생성시간: {report_info['timestamp']}

📊 **주요 내용 미리보기**
{report_info['content'][:300]}...

상세 내용은 첨부된 보고서 파일을 확인해주세요.""",
                "file_path": report_info['file_path'],
                "channels": {
                    "slack": {
                        "enabled": True,
                        "channel": "#general",
                        "upload_file": True  # 보고서 파일 업로드
                    },
                    "notion": {
                        "enabled": True,
                        "parent_id": None  # 기본 페이지에 생성
                    },
                    "email": {
                        "enabled": True,
                        "recipients": None,  # 환경변수에서 가져옴
                        "attach_file": True
                    },
                    "pushbullet": {
                        "enabled": True,
                        "attach_file": False  # 메시지만 전송
                    }
                }
            }
            
            # 큐에 메시지 저장
            import time
            queue_file = dispatch_queue / f"report_{report_info['type']}_{int(time.time())}.json"
            queue_file.write_text(json.dumps(message, ensure_ascii=False, indent=2), encoding="utf-8")
            
            print(f"[INFO] 통합전송 큐에 추가: {queue_file.name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] 통합전송 큐 추가 실패: {e}")
            return False

def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="VELOS 통합 보고서 생성 시스템")
    parser.add_argument("--type", "-t", choices=["health", "weekly", "memory"], 
                       help="생성할 보고서 유형")
    parser.add_argument("--all", "-a", action="store_true", 
                       help="모든 보고서 생성")
    parser.add_argument("--dashboard", "-d", action="store_true",
                       help="통합 대시보드 생성")
    parser.add_argument("--notify", "-n", action="store_true",
                       help="통합전송 시스템으로 알림 발송")
    parser.add_argument("--depth", choices=["shallow", "standard", "deep"], 
                       default="deep", help="메모리 분석 깊이")
    parser.add_argument("--weeks", type=int, default=1, 
                       help="주간 보고서 분석 주수")
    
    args = parser.parse_args()
    
    generator = EnhancedReportGenerator()
    
    try:
        if args.type:
            # 개별 보고서 생성
            kwargs = {}
            if args.type == "memory":
                kwargs["depth"] = args.depth
            elif args.type == "weekly":
                kwargs["weeks_back"] = args.weeks
                
            result = generator.generate_report(args.type, **kwargs)
            
            if result["success"]:
                print(f"✅ {result['name']} 생성 완료: {result['filename']}")
                
                if args.notify:
                    generator.send_to_dispatch_queue(result)
            else:
                print(f"❌ 보고서 생성 실패: {result['error']}")
                return 1
                
        elif args.all:
            # 모든 보고서 생성
            results = generator.generate_all_reports()
            
            print(f"📊 보고서 생성 완료: {results['summary']['success_rate']}")
            print(f"   성공: {results['summary']['successful']}개")
            print(f"   실패: {results['summary']['failed']}개")
            
            # 통합 대시보드 생성
            if results["generated_reports"] or args.dashboard:
                dashboard_content = generator.create_master_dashboard(results["generated_reports"])
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dashboard_file = generator.enhanced_dir / f"velos_master_dashboard_{timestamp}.md"
                dashboard_file.write_text(dashboard_content, encoding="utf-8")
                
                print(f"🎯 통합 대시보드 생성: {dashboard_file.name}")
                
                if args.notify:
                    for result in results["generated_reports"]:
                        generator.send_to_dispatch_queue(result)
        
        else:
            # 도움말 표시
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단됨")
        return 1
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())