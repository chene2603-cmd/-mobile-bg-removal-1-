import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Generator
from common.logger import setup_logger
from common.config_loader import ConfigLoader

class FileScanner:
    """文件系统扫描器 - 采集层第一单元"""
    
    def __init__(self, root_path: str, config_dir="config", output_dir="output"):
        self.root_path = Path(root_path).resolve()
        self.config = ConfigLoader(config_dir)
        self.logger = setup_logger("FileScanner")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.temp_keywords = self.config.load_keywords("temp_keywords.txt")
        self.ignore_paths = self.config.load_keywords("default_ignore_paths.txt")
        # 老旧文件阈值（天）
        self.old_threshold_days = 3 * 365  # 默认3年
        
        # 发现列表（标准化事实）
        self.findings = []  # 每个元素是一个dict，符合统一事实格式
        
    def _should_ignore(self, path: Path) -> bool:
        """检查路径是否应忽略（系统目录、隐藏文件夹等）"""
        path_str = str(path)
        for ignore in self.ignore_paths:
            if ignore in path_str:
                return True
        # 忽略隐藏文件夹（以.开头）
        if any(part.startswith('.') for part in path.parts):
            return True
        return False
    
    def _is_temp_file(self, filename: str) -> bool:
        """根据关键词判断是否为临时文件"""
        name_lower = filename.lower()
        return any(kw in name_lower for kw in self.temp_keywords)
    
    def _get_file_age_years(self, mtime: float) -> float:
        """获取文件最后修改时间距今天数（年）"""
        dt = datetime.datetime.fromtimestamp(mtime)
        delta = datetime.datetime.now() - dt
        return delta.days / 365.25
    
    def _emit_finding(self, type_name: str, path: str, details: dict):
        """标准化事实输出"""
        fact = {
            "layer": "collection",
            "scanner": "file_system",
            "type": type_name,   # 如 "temp_file", "old_file", "empty_dir"
            "timestamp": datetime.datetime.now().isoformat(),
            "path": path,
            "details": details
        }
        self.findings.append(fact)
        self.logger.debug(f"发现 {type_name}: {path}")
    
    def scan_files(self) -> List[Dict]:
        """遍历文件系统，收集临时文件和老旧文件"""
        if not self.root_path.exists():
            raise FileNotFoundError(f"路径不存在: {self.root_path}")
        
        total_files = 0
        for file_path in self.root_path.rglob("*"):
            if not file_path.is_file():
                continue
            if self._should_ignore(file_path):
                continue
            
            total_files += 1
            try:
                stat = file_path.stat()
                mtime = stat.st_mtime
                filename = file_path.name
                
                # 临时文件检测
                if self._is_temp_file(filename):
                    self._emit_finding("temp_file", str(file_path), {
                        "size_bytes": stat.st_size,
                        "mtime": datetime.datetime.fromtimestamp(mtime).isoformat()
                    })
                
                # 老旧未修改文件检测
                age_years = self._get_file_age_years(mtime)
                if age_years > self.old_threshold_days / 365.25:
                    self._emit_finding("old_unused_file", str(file_path), {
                        "size_bytes": stat.st_size,
                        "last_modified_years": round(age_years, 1),
                        "mtime": datetime.datetime.fromtimestamp(mtime).isoformat()
                    })
                    
            except (OSError, PermissionError) as e:
                self.logger.warning(f"无法访问文件 {file_path}: {e}")
        
        self.logger.info(f"扫描完成，共检查 {total_files} 个文件，发现 {len(self.findings)} 个问题事实")
        return self.findings
    
    def scan_empty_dirs(self) -> List[Dict]:
        """扫描空文件夹"""
        for dir_path in self.root_path.rglob("*"):
            if not dir_path.is_dir():
                continue
            if self._should_ignore(dir_path):
                continue
            try:
                if not any(dir_path.iterdir()):
                    self._emit_finding("empty_directory", str(dir_path), {})
            except PermissionError:
                self.logger.warning(f"无法访问目录 {dir_path}")
        self.logger.info(f"空文件夹扫描完成，发现 {len([f for f in self.findings if f['type']=='empty_directory'])} 个")
        return self.findings
    
    def run_full_scan(self) -> List[Dict]:
        """执行完整扫描（文件+空目录）"""
        self.logger.info(f"开始扫描路径: {self.root_path}")
        self.scan_files()
        self.scan_empty_dirs()
        return self.findings
    
    def save_findings(self, filename=None):
        """保存标准化事实到 JSON Lines 文件"""
        if filename is None:
            filename = f"file_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            for finding in self.findings:
                f.write(json.dumps(finding, ensure_ascii=False) + '\n')
        self.logger.info(f"事实数据已保存至 {output_path}")
        return str(output_path)
    
    def print_summary(self):
        """打印简要统计"""
        temp_count = len([f for f in self.findings if f['type'] == 'temp_file'])
        old_count = len([f for f in self.findings if f['type'] == 'old_unused_file'])
        empty_count = len([f for f in self.findings if f['type'] == 'empty_directory'])
        print(f"\n📊 文件扫描结果汇总")
        print(f"   临时文件: {temp_count}")
        print(f"   老旧文件(>{self.old_threshold_days/365}年): {old_count}")
        print(f"   空文件夹: {empty_count}")
        print(f"   总计问题事实: {len(self.findings)}")

# 独立运行测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("请输入要扫描的路径: ").strip()
    
    scanner = FileScanner(target)
    scanner.run_full_scan()
    scanner.print_summary()
    scanner.save_findings()