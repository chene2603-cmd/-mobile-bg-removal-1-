import json
from pathlib import Path
from datetime import datetime
from .template_engine import TemplateEngine
from .chart_generator import ChartGenerator
from .business_translator import BusinessTranslator

class ReportBuilder:
    def __init__(self, output_dir="output"):
        self.output_dir = Path(output_dir)
        self.chart_gen = ChartGenerator(output_dir / "charts")
        self.translator = BusinessTranslator()
        self.template_engine = TemplateEngine()
    
    def build(self, analysis_json_path: str, scan_path: str = "未知") -> str:
        """加载分析结果JSON，生成完整HTML报告"""
        with open(analysis_json_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        # 为每个问题添加业务影响翻译
        for issue in analysis.get('issues', []):
            if 'business_impact' not in issue:
                issue['business_impact'] = self.translator.translate(issue)
        
        # 生成图表
        # 热力图数据：从问题中提取路径或产线信息（简化：按规则名称分类计数）
        rule_counts = {}
        for issue in analysis['issues']:
            rule = issue.get('rule_name', '其他')
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
        heatmap_path = self.chart_gen.generate_heatmap(rule_counts, title="问题类型分布热力图")
        
        # 鱼骨图：根因示例（可基于规则推断）
        root_causes = {
            "人": ["手工报表多", "非工作时间操作", "影子IT脚本"],
            "机": ["老旧PLC文件", "高频错误日志"],
            "料": ["临时文件", "空表", "老旧数据"],
            "法": ["命名不规范", "空文件夹", "缺少主键"],
            "环": ["非工作时间异常访问"]
        }
        fishbone_path = self.chart_gen.generate_fishbone(root_causes)
        
        # 趋势图：模拟过去6个月（可从历史数据库读取，这里用当前指数倒退）
        current_index = analysis['shishan_index']
        # 简单生成模拟历史数据（真实系统应读取历史记录）
        history = [max(20, current_index - 10 - i*2) for i in range(5, 0, -1)] + [current_index]
        trend_path = self.chart_gen.generate_trend(history)
        
        # 依赖图：示例节点（可从系统中读取）
        nodes = [
            {'id': 'MES', 'label': 'MES系统', 'color': '#FF6B6B'},
            {'id': 'SCADA', 'label': 'SCADA', 'color': '#FFD166'},
            {'id': 'PLC', 'label': 'PLC', 'color': '#FFD166'},
            {'id': 'DB', 'label': '数据库', 'color': '#06D6A0'},
            {'id': 'Excel', 'label': 'Excel报表', 'color': '#FF6B6B'}
        ]
        edges = [('MES', 'DB'), ('SCADA', 'DB'), ('PLC', 'SCADA'), ('Excel', 'MES')]
        dep_path = self.chart_gen.generate_dependency_graph(nodes, edges)
        
        # 构建路线图（从分析结果和问题自动生成）
        roadmap = [
            {
                "name": "阶段一：紧急止血 (1-2周)",
                "duration": "1-2周",
                "actions": [
                    "清理P0级问题：高频错误和影子IT脚本",
                    "建立关键日志监控告警",
                    "删除最大的临时文件组"
                ],
                "benefit": "减少停机风险，释放存储空间"
            },
            {
                "name": "阶段二：集中清理 (1-3月)",
                "duration": "1-3个月",
                "actions": [
                    "重构命名违规的表，合并空表",
                    "自动化手工Excel流程",
                    "升级老旧PLC相关模块"
                ],
                "benefit": "提升数据一致性和系统稳定性"
            },
            {
                "name": "阶段三：治理常态化 (3-6月)",
                "duration": "3-6个月",
                "actions": [
                    "制定数据生命周期管理规范",
                    "部署屎山指数监控看板",
                    "培训员工规范化操作"
                ],
                "benefit": "长期降低屎山指数至20以下"
            }
        ]
        
        # 渲染模板
        context = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_path": scan_path,
            "shishan_index": analysis['shishan_index'],
            "grade": analysis.get('grade', 'C'),
            "breakdown": analysis['index_breakdown'],
            "issues": analysis['issues'],
            "correlations": analysis.get('correlations', []),
            "roadmap": roadmap,
            "charts": {
                "heatmap": heatmap_path,
                "fishbone": fishbone_path,
                "trend": trend_path,
                "dependency": dep_path
            }
        }
        html_content = self.template_engine.render("shishan_report.html", context)
        
        # 保存HTML
        report_file = self.output_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return str(report_file)