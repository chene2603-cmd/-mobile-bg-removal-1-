import json
import datetime
from typing import List, Dict

class AnalysisResult:
    """统一的分析结果模型"""
    
    def __init__(self):
        self.timestamp = datetime.datetime.now()
        self.issues = []          # 每个问题: {rule_id, severity, description, business_impact, facts_refs}
        self.shishan_index = 0    # 0-100
        self.index_breakdown = {} # 各维度得分
        self.correlations = []    # 关联发现
    
    def add_issue(self, issue: Dict):
        self.issues.append(issue)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "shishan_index": self.shishan_index,
            "index_breakdown": self.index_breakdown,
            "issues_count": len(self.issues),
            "issues": self.issues,
            "correlations": self.correlations
        }
    
    def save_json(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)