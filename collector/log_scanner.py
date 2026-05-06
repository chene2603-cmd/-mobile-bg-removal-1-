import os
import re
import json
import datetime
from pathlib import Path
from collections import Counter
from typing import List, Dict, Optional, Tuple, Any
from common.logger import setup_logger

# 尝试导入 Windows 事件日志库（仅在 Windows 上可用）
try:
    import win32evtlog
    import win32evtlogutil
    WINDOWS_EVT_AVAILABLE = True
except ImportError:
    WINDOWS_EVT_AVAILABLE = False

class LogScanner:
    """日志行为扫描器 - 采集层第三单元"""
    
    def __init__(self, output_dir="output"):
        self.logger = setup_logger("LogScanner")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.findings = []
        
        # 配置参数
        self.error_keywords = ["error", "fail", "exception", "timeout", "crash", "停机", "故障", "失败"]
        self.off_hours_start = 22  # 晚上10点
        self.off_hours_end = 6     # 早上6点
        self.freq_threshold = 3     # 同一错误类型月频次 >3 视为高频
        self.suspicious_processes = ["python", "powershell", "cmd", "未签名应用", "未知exe"]
        
    def _emit_finding(self, source: str, log_type: str, issue_type: str, 
                      details: dict, timestamp: datetime.datetime = None):
        """标准化事实输出"""
        if timestamp is None:
            timestamp = datetime.datetime.now()
        fact = {
            "layer": "collection",
            "scanner": "log",
            "source": source,
            "log_type": log_type,       # windows_event, text_log
            "type": issue_type,         # high_freq_error, off_hours_access, repeated_failure, shadow_it_indicator
            "timestamp": timestamp.isoformat(),
            "details": details
        }
        self.findings.append(fact)
        self.logger.debug(f"{source}: {issue_type}")
    
    # ---------- Windows 事件日志扫描 ----------
    def scan_windows_event_logs(self, log_names: List[str] = None, days_back: int = 30):
        """
        扫描 Windows 事件日志
        :param log_names: 日志名列表，如 ['Application', 'System', 'Security']
        :param days_back: 回溯天数
        """
        if not WINDOWS_EVT_AVAILABLE:
            self.logger.warning("pywin32 未安装，跳过 Windows 事件日志扫描。如需支持，请安装: pip install pywin32")
            return
        
        if log_names is None:
            log_names = ['Application', 'System']
        
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days_back)
        
        for log_name in log_names:
            try:
                hand = win32evtlog.OpenEventLog(None, log_name)
                events = win32evtlog.ReadEventLog(hand, win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ, 0)
                
                error_counter = Counter()
                off_hours_counter = Counter()
                
                for event in events:
                    # 事件时间
                    event_time = event.TimeGenerated
                    if event_time < cutoff_time:
                        continue
                    
                    # 只关注错误/警告事件 (EventType: 1=Error, 2=Warning)
                    if event.EventType in (1, 2):
                        # 提取事件字符串（可能包含错误信息）
                        msg = win32evtlogutil.SafeFormatMessage(event, log_name)
                        msg_lower = msg.lower()
                        
                        # 高频错误检测：按事件ID + 来源计数
                        key = f"{event.SourceName}_{event.EventID}"
                        error_counter[key] += 1
                        
                        # 非工作时间操作检测
                        hour = event_time.hour
                        if hour >= self.off_hours_start or hour < self.off_hours_end:
                            off_hours_counter[key] += 1
                            # 如果非工作时间同一类型错误出现多次，记录
                            if off_hours_counter[key] >= 2:
                                self._emit_finding(
                                    source=f"{log_name}/{event.SourceName}",
                                    log_type="windows_event",
                                    issue_type="off_hours_access",
                                    details={
                                        "event_id": event.EventID,
                                        "time": event_time.isoformat(),
                                        "message_preview": msg[:200],
                                        "occurrences_off_hours": off_hours_counter[key]
                                    },
                                    timestamp=event_time
                                )
                
                # 高频错误检测（总频次超阈值）
                for key, count in error_counter.items():
                    if count >= self.freq_threshold:
                        source_name, event_id = key.split('_', 1)
                        self._emit_finding(
                            source=f"{log_name}/{source_name}",
                            log_type="windows_event",
                            issue_type="high_freq_error",
                            details={
                                "event_id": int(event_id),
                                "occurrences_total": count,
                                "period_days": days_back,
                                "threshold": self.freq_threshold
                            }
                        )
                win32evtlog.CloseEventLog(hand)
            except Exception as e:
                self.logger.error(f"扫描事件日志 {log_name} 失败: {e}")
    
    # ---------- 文本日志文件扫描 ----------
    def scan_text_logs(self, root_path: str, log_patterns: List[str] = None):
        """
        扫描指定路径下的文本日志文件（.log, .txt, .out, 特定工控日志）
        """
        if log_patterns is None:
            log_patterns = ["*.log", "*.txt", "*.out", "*.err", "*.trace", "scada*.log", "opc*.log"]
        
        root = Path(root_path)
        log_files = []
        for pattern in log_patterns:
            log_files.extend(root.rglob(pattern))
        
        self.logger.info(f"发现 {len(log_files)} 个文本日志文件")
        
        # 用于跨文件统计高频错误模式
        error_pattern_counter = Counter()
        error_last_seen = {}  # pattern -> last_datetime
        repeated_failure_details = []
        
        # 正则模式：行时间戳 + 错误关键词
        # 常见时间戳格式
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # 2026-02-08 14:30:00
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',  # 02/08/2026 14:30:00
            r'\d{4}\d{2}\d{2} \d{2}:\d{2}:\d{2}',    # 20260208 14:30:00
            r'\[\d{2}:\d{2}:\d{2}\]'                 # [14:30:00]
        ]
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception as e:
                self.logger.warning(f"无法读取日志文件 {log_file}: {e}")
                continue
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                # 是否有错误关键词
                if any(kw in line_lower for kw in self.error_keywords):
                    # 尝试提取时间戳
                    line_time = None
                    for pattern in timestamp_patterns:
                        match = re.search(pattern, line)
                        if match:
                            try:
                                # 简单解析，可能失败则忽略
                                line_time = self._parse_timestamp(match.group())
                            except:
                                pass
                            break
                    
                    # 简化错误模式：取前50个字符作为模式（去除时间戳）
                    simplified = re.sub(r'\d+', '#', line_lower[:100])  # 模糊匹配数字
                    error_pattern_counter[simplified] += 1
                    
                    # 记录重复故障（同一文件同一模式出现多次且时间接近）
                    if line_time:
                        last = error_last_seen.get(simplified)
                        if last and (line_time - last).total_seconds() < 3600:  # 1小时内重复
                            repeated_failure_details.append({
                                "file": str(log_file),
                                "line": line_num,
                                "pattern": simplified[:80],
                                "time": line_time.isoformat()
                            })
                        error_last_seen[simplified] = line_time
            
            # 单文件内高频错误检出
            for pattern, count in error_pattern_counter.items():
                if count >= self.freq_threshold:
                    self._emit_finding(
                        source=str(log_file),
                        log_type="text_log",
                        issue_type="high_freq_error",
                        details={
                            "error_pattern": pattern[:100],
                            "occurrences": count,
                            "sample_line": pattern[:200]
                        }
                    )
            
            # 重复故障检出
            for fail in repeated_failure_details[:20]:  # 限制数量
                self._emit_finding(
                    source=fail["file"],
                    log_type="text_log",
                    issue_type="repeated_failure",
                    details={
                        "line": fail["line"],
                        "pattern": fail["pattern"],
                        "time": fail["time"]
                    }
                )
    
    def _parse_timestamp(self, ts_str: str) -> datetime.datetime:
        """尝试解析常见时间戳格式"""
        # 简化版，支持 YYYY-MM-DD HH:MM:SS
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y%m%d %H:%M:%S"):
            try:
                return datetime.datetime.strptime(ts_str, fmt)
            except:
                continue
        raise ValueError(f"无法解析时间戳: {ts_str}")
    
    # ---------- 影子 IT 迹象扫描 ----------
    def scan_shadow_it_indicators(self, root_path: str):
        """
        扫描可能代表影子IT的迹象：
        - 未经授权的脚本文件（.ps1, .vbs, .py）在共享目录
        - 未知的exe文件
        - 计划任务或服务中的非标准条目（需额外权限，简化）
        """
        root = Path(root_path)
        # 可疑脚本文件
        script_extensions = ["*.ps1", "*.vbs", "*.bat", "*.cmd", "*.py", "*.js"]
        suspicious_files = []
        for ext in script_extensions:
            suspicious_files.extend(root.rglob(ext))
        
        for sf in suspicious_files:
            # 如果文件在普通共享目录且不是系统标准位置
            if any(p in str(sf).lower() for p in ["共享", "share", "temp", "用户", "users"]):
                self._emit_finding(
                    source=str(sf),
                    log_type="file_system",
                    issue_type="shadow_it_indicator",
                    details={
                        "file_type": sf.suffix,
                        "size_bytes": sf.stat().st_size if sf.exists() else 0,
                        "reason": "未授权的脚本文件位于共享目录"
                    }
                )
        
        # 可选：扫描计划任务（需要管理员权限，这里仅提示）
        self.logger.info("影子IT扫描完成，发现 %d 个可疑脚本文件", len(suspicious_files))
    
    # ---------- 综合入口 ----------
    def run_full_log_scan(self, root_path: str, include_windows_events=True, days_back=30):
        """执行完整日志扫描（Windows事件 + 文本日志 + 影子IT）"""
        self.logger.info(f"开始日志行为扫描，根路径: {root_path}")
        
        if include_windows_events and WINDOWS_EVT_AVAILABLE:
            self.scan_windows_event_logs(days_back=days_back)
        elif include_windows_events and not WINDOWS_EVT_AVAILABLE:
            self.logger.warning("跳过Windows事件日志（pywin32未安装）")
        
        self.scan_text_logs(root_path)
        self.scan_shadow_it_indicators(root_path)
        
        self.logger.info(f"日志扫描完成，共发现 {len(self.findings)} 个问题事实")
        return self.findings
    
    def save_findings(self, filename=None):
        if filename is None:
            filename = f"log_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        output_path = self.output_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            for finding in self.findings:
                f.write(json.dumps(finding, ensure_ascii=False) + '\n')
        self.logger.info(f"日志扫描事实已保存至 {output_path}")
        return str(output_path)
    
    def print_summary(self):
        type_count = {}
        for f in self.findings:
            t = f['type']
            type_count[t] = type_count.get(t, 0) + 1
        print("\n📊 日志扫描结果汇总")
        for t, cnt in type_count.items():
            print(f"   {t}: {cnt}")
        print(f"   总计问题事实: {len(self.findings)}")

# 独立测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = input("请输入要扫描的路径: ").strip()
    
    scanner = LogScanner()
    scanner.run_full_log_scan(target, include_windows_events=True)
    scanner.print_summary()
    scanner.save_findings()