#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工厂屎山挖掘系统 v0.2 - 文件扫描 + 数据库扫描"""
import sys
from collector.file_scanner import FileScanner
from collector.db_scanner import DatabaseScanner

def main():
    print("="*60)
    print("🏭 工厂屎山挖掘系统 v0.2 - 文件系统 + 数据库扫描")
    print("="*60)
    
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("请输入要扫描的目录路径: ").strip()
    
    if not target_path:
        print("❌ 路径不能为空")
        return 1
    
    # 第一层：文件扫描
    print("\n[1/2] 开始文件系统扫描...")
    file_scanner = FileScanner(target_path)
    try:
        file_scanner.run_full_scan()
        file_scanner.print_summary()
        file_output = file_scanner.save_findings()
        print(f"✅ 文件扫描完成，事实保存至: {file_output}")
    except Exception as e:
        print(f"❌ 文件扫描失败: {e}")
    
    # 第二层：数据库扫描
    print("\n[2/2] 开始数据库扫描...")
    db_scanner = DatabaseScanner()
    try:
        db_scanner.scan_all_databases(target_path)
        db_scanner.print_summary()
        db_output = db_scanner.save_findings()
        print(f"✅ 数据库扫描完成，事实保存至: {db_output}")
    except Exception as e:
        print(f"❌ 数据库扫描失败: {e}")
    
    print("\n🎉 扫描流程结束")
    return 0

if __name__ == "__main__":
    sys.exit(main())