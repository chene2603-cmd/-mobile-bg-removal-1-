import json
from pathlib import Path

class ConfigLoader:
    def __init__(self, config_dir="config"):
        self.config_dir = Path(config_dir)
    
    def load_keywords(self, filename):
        filepath = self.config_dir / filename
        if not filepath.exists():
            # 返回默认值
            return self._default_keywords(filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    
    def _default_keywords(self, filename):
        if "temp_keywords" in filename:
            return ["tmp_", "temp_", "~", ".bak", ".old", "_backup", "废弃", "暂存", "副本"]
        elif "ignore_paths" in filename:
            return ["$Recycle.Bin", "System Volume Information", "Windows", "Program Files", "Program Files (x86)"]
        return []
    
    def load_business_mapping(self):
        # 第一层暂不需要完整映射，返回空
        return {}