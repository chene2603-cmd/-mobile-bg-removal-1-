#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工厂屎山挖掘系统 - 主入口（第一阶段仅文件扫描）"""
import sys
from collector.file_scanner import FileScanner

def main():
    print("="*60)
    print("🏭 工厂屎山挖掘系统 v0.1 - 文件扫描单元")
    print("="*60)
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("请输入要扫描的目录路径: ").strip()
    
    if not target_path:
        print("❌ 路径不能为空")
        return 1
    
    scanner = FileScanner(target_path)
    try:
        scanner.run_full_scan()
        scanner.print_summary()
        output_file = scanner.save_findings()
        print(f"\n✅ 扫描完成，详细报告已保存至: {output_file}")
    except Exception as e:
        print(f"❌ 扫描失败: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())