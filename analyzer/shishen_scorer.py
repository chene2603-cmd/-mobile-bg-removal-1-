from typing import List, Dict

class ShishanScorer:
    """屎山指数计算器 (0-100)"""
    
    def __init__(self):
        self.weights = {
            "P0": 25,   # 每个P0问题25分
            "P1": 10,
            "P2": 3,
            "P3": 1
        }
        self.max_score = 100
    
    def calculate(self, issues: List[Dict]) -> Dict:
        """
        根据问题列表计算屎山指数
        返回: { "total": 0-100, "breakdown": {...}, "grade": "A/B/C/D/F" }
        """
        score = 0
        breakdown = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
        for issue in issues:
            severity = issue.get('severity', 'P3')
            weight = self.weights.get(severity, 1)
            score += weight
            breakdown[severity] = breakdown.get(severity, 0) + 1
        
        # 限制最高分
        total = min(score, self.max_score)
        
        # 等级划分
        if total <= 20:
            grade = "A (健康)"
        elif total <= 40:
            grade = "B (轻微屎山)"
        elif total <= 70:
            grade = "C (中度屎山)"
        else:
            grade = "D (重度屎山)"
        
        return {
            "total": total,
            "breakdown": breakdown,
            "grade": grade
        }