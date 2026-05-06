from typing import List, Dict
from common.logger import setup_logger

class Correlator:
    """跨事实关联推理（如临时文件 + 空表 = 设计混乱）"""
    
    def __init__(self):
        self.logger = setup_logger("Correlator")
    
    def run(self, facts: List[Dict], issues: List[Dict]) -> List[Dict]:
        """执行关联分析，返回关联发现列表"""
        correlations = []
        
        # 关联1：大量临时文件 + 空表 → 数据治理缺失
        temp_count = len([f for f in facts if f.get('type') == 'temp_file'])
        empty_table_count = len([f for f in facts if f.get('type') == 'unused_table'])
        if temp_count > 50 and empty_table_count > 5:
            correlations.append({
                "type": "data_governance_gap",
                "description": f"临时文件({temp_count})与空表({empty_table_count})同时大量存在，表明缺乏数据生命周期管理",
                "recommendation": "建立数据清理策略和自动化归档流程"
            })
        
        # 关联2：高频错误 + 老旧PLC → 设备老化导致稳定性下降
        high_freq_errors = [f for f in facts if f.get('type') == 'high_freq_error']
        old_plc_files = [f for f in facts if f.get('type') == 'old_unused_file' and 'plc' in f.get('path', '').lower()]
        if high_freq_errors and old_plc_files:
            correlations.append({
                "type": "aging_instability",
                "description": f"高频错误({len(high_freq_errors)}种)与老旧PLC相关文件({len(old_plc_files)}个)并存，可能设备老化导致",
                "recommendation": "制定PLC升级或替换计划，并监控错误趋势"
            })
        
        # 关联3：非工作时间操作 + 影子IT → 可能存在规避正规流程的行为
        off_hours = [f for f in facts if f.get('type') == 'off_hours_access']
        shadow_it = [f for f in facts if f.get('type') == 'shadow_it_indicator']
        if off_hours and shadow_it:
            correlations.append({
                "type": "process_bypass",
                "description": f"非工作时间操作({len(off_hours)}次)与影子IT迹象({len(shadow_it)}个)同时出现，可能存在规避正规运维流程的行为",
                "recommendation": "审计相关脚本和计划任务，强化变更管理流程"
            })
        
        self.logger.info(f"关联分析完成，发现 {len(correlations)} 条关联")
        return correlations