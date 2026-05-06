# factory_shishan_mvp.py
import re
from datetime import datetime
from typing import Dict, List

class ShishanMiningMVP:
    """工厂屎山挖掘最小可行产品"""
    
    def __init__(self):
        # 模式库：关键词 → 扫描策略 & 报告类型
        self.patterns = {
            "manual_excel": {
                "keywords": ["手工", "excel", "报表", "汇总", "合并", "导入导出", "搬运数据"],
                "scan_plan": {
                    "targets": ["所有Excel文件", "共享文件夹", "邮件附件"],
                    "tools": ["文件元数据分析", "内容嗅探"],
                    "metrics": ["文件数", "最后修改时间", "大小", "重复度"]
                },
                "report_type": "process_automation_feasibility",
                "business_impact_template": "每月{hours}小时手工劳动, 可节省{percent}%人力, 减少错误率{error_rate}%"
            },
            "system_slow": {
                "keywords": ["卡顿", "慢", "延迟", "等待", "响应慢", "关账慢"],
                "scan_plan": {
                    "targets": ["数据库慢查询日志", "应用服务器性能计数器", "API响应时间"],
                    "tools": ["执行计划分析", "CPU/内存监控"],
                    "metrics": ["响应时间P95", "CPU峰值", "慢查询数"]
                },
                "report_type": "performance_bottleneck_analysis",
                "business_impact_template": "每次操作等待{minutes}分钟, 日累计{total_min}分钟, 月影响产能{loss}件"
            },
            "old_plc": {
                "keywords": ["老旧plc", "停机", "掉线", "无响应", "西门子", "ab plc", "三菱", "欧姆龙"],
                "scan_plan": {
                    "targets": ["SCADA日志", "设备启停记录", "维护工单", "OPC连接日志"],
                    "tools": ["协议级健康检查(S7/Modbus)"],
                    "metrics": ["单日断连次数", "平均恢复时长", "故障码分布"]
                },
                "report_type": "recurring_issue_root_cause",
                "business_impact_template": "每停机一次损失{loss}元, 月累计停机{downtime_hours}小时"
            }
        }
        
        # 屎山指数初始计算器
        self.shishan_index = 0
        
    def detect_pattern(self, user_input: str) -> str:
        """匹配最可能的屎山模式"""
        user_lower = user_input.lower()
        for pattern_id, pattern in self.patterns.items():
            for kw in pattern["keywords"]:
                if kw in user_lower:
                    return pattern_id
        return "general"  # 未匹配到则通用扫描
    
    def generate_report(self, user_input: str, factory_context: Dict = None) -> Dict:
        """生成MVP级报告（含可视化清单、行动项）"""
        pattern_id = self.detect_pattern(user_input)
        if pattern_id == "general":
            return self._general_report(user_input)
        
        pattern = self.patterns[pattern_id]
        
        # 模拟影响评估参数（真实场景需从数据中提取）
        impact_params = {
            "hours": 2.5,
            "percent": 70,
            "error_rate": 15,
            "minutes": 5,
            "total_min": 120,
            "loss": 8500,
            "downtime_hours": 6
        }
        
        report = {
            "report_id": f"MVP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "problem_summary": self._summarize(user_input),
            "detected_pattern": pattern_id,
            "three_layer_scan": {
                "layer1_static": ["扫描临时文件、未使用的表、命名违规", "发现可能僵尸数据"],
                "layer2_dynamic": ["分析异常访问频次、重复错误日志", "识别影子IT行为"],
                "layer3_correlation": ["校验产产量与能耗矛盾", "定位人工绕开系统的操作"]
            },
            "scan_execution_plan": pattern["scan_plan"],
            "business_impact": pattern["business_impact_template"].format(**impact_params),
            "priority": "P0" if pattern_id == "old_plc" else "P1",
            "recommended_actions": self._get_actions(pattern_id),
            "visualization_required": [
                "system_dependency_graph",  # 系统依赖图
                "problem_heatmap",          # 问题热力图
                "timeline_trend",           # 趋势图
                "fishbone_root_cause"       # 鱼骨根因图
            ],
            "roadmap": {
                "phase1_quick_fix (1-2周)": ["避免高风险操作", "增加监控告警"],
                "phase2_focused_cleanup (1-3月)": ["重构高频调用模块", "自动化手工步骤"],
                "phase3_systematic_governance (3-6月)": ["建立性能基线与治理规范"]
            },
            "next_step": "是否授权启动深度扫描？（将连接OPC/数据库/日志系统）"
        }
        return report
    
    def _summarize(self, text: str) -> str:
        """提取核心问题的简短描述"""
        # MVP 简单截取前80字
        return text[:80] + ("..." if len(text) > 80 else "")
    
    def _get_actions(self, pattern_id: str) -> List[str]:
        actions_map = {
            "manual_excel": [
                "识别前10个最耗时的Excel模板",
                "对接上游系统自动生成基础数据",
                "建立数据校验规则（±5%容差）",
                "移除离职人员遗留的废弃报表"
            ],
            "system_slow": [
                "抓取慢查询TOP 10并添加索引",
                "重启常年未重启的应用服务器",
                "清理历史日志分区",
                "优化月末结算存储过程"
            ],
            "old_plc": [
                "加装通讯看门狗，自动重启死连接",
                "升级故障高发PLC固件",
                "建立PLC日志远程采集通道",
                "制定老旧设备替换预算计划"
            ]
        }
        return actions_map.get(pattern_id, ["人工复核系统清单", "开启全量日志采集"])
    
    def _general_report(self, user_input: str) -> Dict:
        return {
            "message": "未识别到典型屎山模式，将执行通用扫描",
            "suggested_keywords": "请描述更具体的问题，如“手工Excel报表”、“系统卡顿”、“老旧PLC频繁停机”",
            "fallback_action": "采集全系统元数据（表、文件、进程）后输出屎山指数"
        }
    
    def run_interactive(self):
        """简单命令行交互MVP"""
        print("\n" + "="*60)
        print("🏭 工厂屎山挖掘专家系统 MVP (交互模式)")
        print("="*60)
        print("请描述您工厂的问题（输入 q 退出）：")
        while True:
            user_input = input("\n👉 问题描述: ").strip()
            if user_input.lower() in ["q", "quit", "exit"]:
                print("🧹 系统退出，建议保存本次报告作为治理基线。")
                break
            if not user_input:
                continue
            report = self.generate_report(user_input)
            print("\n📋 初步诊断报告")
            print("-"*40)
            if "message" in report:
                print(f"⚠️ {report['message']}")
                if "suggested_keywords" in report:
                    print(f"💡 {report['suggested_keywords']}")
            else:
                print(f"🔍 匹配模式: {report['detected_pattern']}")
                print(f"📊 业务影响: {report['business_impact']}")
                print(f"🚨 优先级: {report['priority']}")
                print(f"\n📌 扫描目标: {', '.join(report['scan_execution_plan']['targets'])}")
                print(f"🛠️ 推荐行动项 (前3条):")
                for i, action in enumerate(report['recommended_actions'][:3], 1):
                    print(f"   {i}. {action}")
                print(f"\n📈 可视化图表: {', '.join(report['visualization_required'][:2])} ...")
                print(f"\n🗺️ 路线图概览: {list(report['roadmap'].keys())}")
            print(f"\n✅ {report.get('next_step', '如需深度扫描，请提供数据库/日志访问方式。')}")
            print("-"*40)


# 启动MVP
if __name__ == "__main__":
    mvp = ShishanMiningMVP()
    mvp.run_interactive()