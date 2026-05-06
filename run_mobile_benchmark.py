import json
from pathlib import Path
from bg_remover import BgRemovalPipeline  # 原始 PyTorch 管线
from bg_remover.pipeline import MobileBgRemovalPipeline
from analyzer.correlator import batch_score_from_log, generate_report

# --------- 配置 ---------
test_dir = Path("test_images")
fp32_output = Path("output_fp32")
int8_output = Path("output_int8")
fp32_output.mkdir(exist_ok=True)
int8_output.mkdir(exist_ok=True)

images = list(test_dir.glob("*.jpg"))

# --------- FP32 PyTorch 测试 ---------
print("运行 FP32 (PyTorch) 测试...")
pipeline_fp32 = BgRemovalPipeline(device="cpu")
fp32_results = []
for img in images:
    res = pipeline_fp32.run(str(img), str(fp32_output))
    fp32_results.append(res)

fp32_log = fp32_output / "processing_log.json"
with open(fp32_log, 'w') as f:
    json.dump(fp32_results, f, indent=2)

# --------- INT8 ONNX 测试 ---------
print("运行 INT8 (ONNX Runtime) 测试...")
pipeline_int8 = MobileBgRemovalPipeline("mobile/rmbg_int8.onnx")
int8_results = []
for img in images:
    res = pipeline_int8.run(str(img), str(int8_output))
    int8_results.append(res)

int8_log = int8_output / "processing_log.json"
with open(int8_log, 'w') as f:
    json.dump(int8_results, f, indent=2)

# --------- 评估与对比报告 ---------
print("生成评估报告...")
fp32_report_file = "output_fp32/evaluation_report.md"
int8_report_file = "output_int8/evaluation_report.md"

fp32_scored = generate_report(str(fp32_log), fp32_report_file)
int8_scored = generate_report(str(int8_log), int8_report_file)

# 生成对比报告
compare_md = "output/comparison_report.md"  # 放在主 output 目录
with open(compare_md, 'w', encoding='utf-8') as f:
    f.write("# 移动端 INT8 量化精度-性能对比报告\n\n")
    f.write("| 图片 | FP32 总分 | INT8 总分 | 精度损失 (总分差) | FP32 时间 (ms) | INT8 时间 (ms) | 时间加速比 |\n")
    f.write("|------|-----------|-----------|-------------------|----------------|----------------|------------|\n")
    for fp, i8 in zip(fp32_scored, int8_scored):
        loss = fp['scores']['total'] - i8['scores']['total']
        speedup = fp['inference_time_sec'] / i8['inference_time_sec'] if i8['inference_time_sec'] > 0 else 0
        f.write(f"| {Path(fp['input']).name} | {fp['scores']['total']:.2f} | {i8['scores']['total']:.2f} | "
                f"{loss:.3f} | {fp['inference_time_sec']*1000:.0f} | {i8['inference_time_sec']*1000:.0f} | {speedup:.2f}x |\n")
    # 平均量化损失
    avg_loss = sum(fp['scores']['total'] - i8['scores']['total'] for fp, i8 in zip(fp32_scored, int8_scored)) / len(fp32_scored)
    f.write(f"\n**平均精度损失 (总分)**：{avg_loss:.4f}\n")

print(f"对比报告已保存至 {compare_md}")