from bg_remover import BgRemovalPipeline
from pathlib import Path
import json

# 初始化管线（若有 GPU 则改为 'cuda'）
pipeline = BgRemovalPipeline(device='cpu')

# 批量处理目录下所有图片
input_dir = Path("test_images")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

results = []
for img_path in input_dir.glob("*.jpg"):
    result = pipeline.run(str(img_path), str(output_dir))
    results.append(result)
    print(f"✔ {img_path.name} in {result['inference_time_sec']:.2f}s")

# 保存一份完整的处理记录，供 analyzer 读取
with open(output_dir / "processing_log.json", "w") as f:
    json.dump(results, f, indent=2)