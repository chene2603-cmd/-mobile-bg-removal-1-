# 业务影响翻译器
class BusinessTranslator:
    """将技术问题映射为工厂业务语言，量化损失"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        # 默认映射（可以从配置文件加载）
        self.mapping = {
            "大量临时文件": {
                "impact_template": "大量临时文件({count}个)占用存储约{size_gb:.1f}GB，导致备份时间增加{backup_hours}小时/月",
                "default_size_gb": 5,
                "default_backup_hours": 2
            },
            "老旧僵尸文件": {
                "impact_template": "超过3年未使用的文件有{count}个，占用{size_gb:.1f}GB，可能包含过时信息引发误用",
                "default_size_gb": 10,
                "risk": "决策依据错误风险升高"
            },
            "数据库空表": {
                "impact_template": "{count}个空表增加维护复杂度，新员工理解数据库需多花费{extra_hours}小时",
                "default_extra_hours": 4
            },
            "高频错误": {
                "impact_template": "错误'{error_preview}'高频出现({occurrences}次/{period})，每次可能延误生产{loss_minutes}分钟",
                "default_loss_minutes": 15
            },
            "非工作时间异常": {
                "impact_template": "非工作时间异常操作{count}次，可能导致安全合规风险，每次审计耗时{audit_hours}小时",
                "default_audit_hours": 1
            },
            "影子IT迹象": {
                "impact_template": "发现{count}个未授权脚本，存在数据不一致风险，每次排错平均{debug_hours}小时",
                "default_debug_hours": 3
            },
            "空文件夹": {
                "impact_template": "{count}个空文件夹使目录浏览时间增加{extra_seconds}秒/天",
                "default_extra_seconds": 30
            }
        }
    
    def translate(self, issue: dict) -> str:
        """根据问题中的规则名和参数，返回业务影响描述"""
        rule_name = issue.get('rule_name', '')
        details = issue.get('details', {})
        
        # 提取关键参数（可以从issue或原始facts中获取）
        template_data = self._extract_params(issue)
        
        mapping = self.mapping.get(rule_name, {})
        template = mapping.get("impact_template", "该问题影响系统稳定性与运维效率，建议尽快处理。")
        
        try:
            return template.format(**template_data)
        except KeyError:
            return template
        
    def _extract_params(self, issue: dict) -> dict:
        """从问题描述中提取影响计算的参数"""
        desc = issue.get('description', '')
        params = {}
        
        # 解析数量
        import re
        count_match = re.search(r'(\d+)', desc)
        if count_match:
            params['count'] = int(count_match.group(1))
        else:
            params['count'] = 1
        
        # 根据规则名补充默认参数
        rule_name = issue.get('rule_name', '')
        if rule_name == "大量临时文件":
            params['size_gb'] = params.get('count', 100) * 0.01  # 假设每个临时文件10MB
            params['backup_hours'] = max(1, params['count'] // 100)
        elif rule_name == "老旧僵尸文件":
            params['size_gb'] = params.get('count', 50) * 0.05
        elif rule_name == "数据库空表":
            params['extra_hours'] = max(1, params['count'] // 5)
        elif rule_name == "高频错误":
            # 尝试从details中获取occurrences
            params['occurrences'] = issue.get('details', {}).get('occurrences', params['count'] * 2)
            params['period'] = issue.get('details', {}).get('period_days', 30)
            params['error_preview'] = issue.get('details', {}).get('error_pattern', '未知错误')[:50]
            params['loss_minutes'] = 15
        elif rule_name == "非工作时间异常":
            params['audit_hours'] = params['count'] * 0.5
        elif rule_name == "影子IT迹象":
            params['debug_hours'] = params['count'] * 1.5
        elif rule_name == "空文件夹":
            params['extra_seconds'] = min(60, params['count'] // 5)
        else:
            params['count'] = params.get('count', 1)
        
        return params