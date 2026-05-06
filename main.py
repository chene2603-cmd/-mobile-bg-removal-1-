# 在分析层之后添加
from reporter.report_builder import ReportBuilder

# ... 前面采集+分析代码 ...

# 查找最新分析文件
analysis_files = list(Path("output").glob("analysis_*.json"))
if analysis_files:
    latest_analysis = max(analysis_files, key=lambda p: p.stat().st_mtime)
    print("\n[5/5] 生成可视化报告...")
    builder = ReportBuilder()
    report_path = builder.build(str(latest_analysis), scan_path=target_path)
    print(f"✅ 报告已生成: {report_path}")
else:
    print("⚠️ 未找到分析结果，跳过报告生成")