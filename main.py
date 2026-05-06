#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工厂屎山挖掘系统 v0.3 - 文件系统 + 数据库 + 日志行为扫描"""
import sys
from collector.file_scanner import FileScanner
from collector.db_scanner import DatabaseScanner
from collector.log_scanner import LogScanner

def main():
    print("="*60)
    print("🏭 工厂屎山挖掘系统 v0.3 - 三层采集引擎")
    print("="*60)
    
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("请输入要扫描的目录路径: ").strip()
    
    if not target_path:
        print("❌ 路径不能为空")
        return 1
    
    # 第一层：文件扫描
    print("\n[1/3] 开始文件系统扫描...")
    file_scanner = FileScanner(target_path)
    try:
        file_scanner.run_full_scan()
        file_scanner.print_summary()
        file_output = file_scanner.save_findings()
        print(f"✅ 文件扫描完成，事实保存至: {file_output}")
    except Exception as e:
        print(f"❌ 文件扫描失败: {e}")
    
    # 第二层：数据库扫描
    print("\n[2/3] 开始数据库扫描...")
    db_scanner = DatabaseScanner()
    try:
        db_scanner.scan_all_databases(target_path)
        db_scanner.print_summary()
        db_output = db_scanner.save_findings()
        print(f"✅ 数据库扫描完成，事实保存至: {db_output}")
    except Exception as e:
        print(f"❌ 数据库扫描失败: {e}")
    
    # 第三层：日志行为扫描
    print("\n[3/3] 开始日志行为扫描...")
    log_scanner = LogScanner()
    try:
        log_scanner.run_full_log_scan(target_path, include_windows_events=True)
        log_scanner.print_summary()
        log_output = log_scanner.save_findings()
        print(f"✅ 日志扫描完成，事实保存至: {log_output}")
    except Exception as e:
        print(f"❌ 日志扫描失败: {e}")
    
    print("\n🎉 三层采集完成，原始事实数据已保存到 output/ 目录")
    return 0

if __name__ == "__main__":
    sys.exit(main())