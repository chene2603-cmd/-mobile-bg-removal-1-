from pathlib import Path
import json
from datetime import datetime
from analyzer.shishen_scorer import batch_score_from_log, rank_results

def generate_report(log_file: str, output_report: str = None):
    """
    生成 Markdown 评估报告
    """
    scored = batch_score_from_log(log_file)
    ranked = rank_results(scored)

    if output_report is None:
        output_report = f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    lines = []
    lines.append("# 背景移除评估报告\n")
    lines.append(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**数据来源**：`{log_file}`\n")
    lines.append(f"**评估图片数量**：{len(ranked)}\n")

    lines.append("## 综合排名\n")
    lines.append("| 排名 | 输入图片 | 推理设备 | 推理时间 (s) | 总分 | 二元性 | 锐度 | 覆盖度 | 性能分 |")
    lines.append("|------|----------|----------|--------------|------|--------|------|--------|--------|")
    for i, item in enumerate(ranked, 1):
        s = item['scores']
        lines.append(f"| {i} | {Path(item['input']).name} | {item['device']} | {item['inference_time_sec']:.2f} | "
                     f"{s['total']:.2f} | {s['binary']:.2f} | {s['sharpness']:.2f} | {s['coverage']:.2f} | {s['performance']:.2f} |")

    # 分数解释
    lines.append("\n## 指标说明\n")
    lines.append("- **二元性**：mask 值集中程度，越接近黑白（非灰色）得分越高。")
    lines.append("- **锐度**：前景边缘的清晰度，发丝等细节保留越好得分越高。")
    lines.append("- **覆盖度**：前景面积合理性，避免漏抠或全图无背景。")
    lines.append("- **性能分**：推理时间评分，≤1s 满分。")
    lines.append("- **总分** = 0.35×二元性 + 0.35×锐度 + 0.2×覆盖度 + 0.1×性能\n")

    # 写入文件
    with open(output_report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"报告已生成：{output_report}")
    return ranked