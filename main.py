#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""工厂屎山挖掘系统 v0.4 - 采集 + 分析层（规则引擎+屎山指数）"""
import sys
import json
from pathlib import Path
from collector.file_scanner import FileScanner
from collector.db_scanner import DatabaseScanner
from collector.log_scanner import LogScanner
from analyzer import RuleEngine, ShishanScorer, Correlator
from analyzer.analysis_result import AnalysisResult

def load_all_facts(output_dir="output"):
    """加载所有采集层生成的 JSON Lines 事实文件"""
    facts = []
    out_path = Path(output_dir)
    for jsonl_file in out_path.glob("*.jsonl"):
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    facts.append(json.loads(line))
    return facts

def main():
    print("="*60)
    print("🏭 工厂屎山挖掘系统 v0.4 - 采集 + 分析层")
    print("="*60)
    
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("请输入要扫描的目录路径: ").strip()
    
    if not target_path:
        print("❌ 路径不能为空")
        return 1
    
    # ========== 采集层 ==========
    # 第一层
    print("\n[1/4] 文件系统扫描...")
    file_scanner = FileScanner(target_path)
    try:
        file_scanner.run_full_scan()
        file_scanner.save_findings()
    except Exception as e:
        print(f"❌ 文件扫描失败: {e}")
    
    # 第二层
    print("\n[2/4] 数据库扫描...")
    db_scanner = DatabaseScanner()
    try:
        db_scanner.scan_all_databases(target_path)
        db_scanner.save_findings()
    except Exception as e:
        print(f"❌ 数据库扫描失败: {e}")
    
    # 第三层
    print("\n[3/4] 日志行为扫描...")
    log_scanner = LogScanner()
    try:
        log_scanner.run_full_log_scan(target_path, include_windows_events=True)
        log_scanner.save_findings()
    except Exception as e:
        print(f"❌ 日志扫描失败: {e}")
    
    # ========== 分析层 ==========
    print("\n[4/4] 分析层处理...")
    # 加载所有事实
    facts = load_all_facts()
    print(f"   加载事实总数: {len(facts)}")
    
    # 规则引擎
    engine = RuleEngine()
    issues = engine.run(facts)
    print(f"   发现问题数: {len(issues)}")
    
    # 屎山指数计算
    scorer = ShishanScorer()
    score_result = scorer.calculate(issues)
    print(f"   屎山指数: {score_result['total']}/100 ({score_result['grade']})")
    
    # 关联推理
    correlator = Correlator()
    correlations = correlator.run(facts, issues)
    
    # 汇总分析结果
    analysis = AnalysisResult()
    analysis.issues = issues
    analysis.shishan_index = score_result['total']
    analysis.index_breakdown = score_result['breakdown']
    analysis.correlations = correlations
    
    # 保存分析结果
    output_path = Path("output")
    output_path.mkdir(exist_ok=True)
    analysis_file = output_path / f"analysis_{analysis.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    analysis.save_json(str(analysis_file))
    print(f"\n✅ 分析结果已保存至: {analysis_file}")
    
    print("\n🎉 采集+分析完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())