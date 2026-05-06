from bg_remover import BgRemovalPipeline
from analyzer.correlator import generate_report
from pathlib import Path
import json

# --------- 第一层：背景移除 ---------
pipeline = BgRemovalPipeline(device='cpu')
input_dir = Path("test_images")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

results = []
for img_path in input_dir.glob("*.jpg"):
    result = pipeline.run(str(img_path), str(output_dir))
    results.append(result)

log_path = output_dir / "processing_log.json"
with open(log_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"处理完成，日志已保存至 {log_path}")

# --------- 第二层：评估与报告 ---------
ranked = generate_report(log_file=str(log_path), output_report="output/report.md")
print(f"最佳图片：{ranked[0]['input']} 总分：{ranked[0]['scores']['total']:.2f}")