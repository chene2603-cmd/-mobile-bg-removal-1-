import onnxruntime as ort
import numpy as np
import time
from pathlib import Path
from PIL import Image
from bg_remover.utils import preprocess, postprocess, apply_mask, INPUT_SIZE

class MobileBgRemovalPipeline:
    def __init__(self, onnx_model_path: str):
        # 使用 CPU 执行提供程序，模拟移动端 CPU 环境
        self.session = ort.InferenceSession(
            onnx_model_path,
            providers=['CPUExecutionProvider']
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def run(self, input_path: str, output_dir: str, save_mask: bool = True) -> dict:
        # 预处理与原 pipeline 完全一致
        img = Image.open(input_path).convert('RGB')
        original_size = img.size
        img_tensor = preprocess(img)  # [1, 3, 1024, 1024]

        # ONNX Runtime 推理（numpy 输入）
        ort_inputs = {self.input_name: img_tensor.numpy()}

        # 计时
        start = time.time()
        ort_outputs = self.session.run(None, ort_inputs)
        inference_time = time.time() - start

        # 后处理：mask 形状与 PyTorch 输出对齐
        mask_np = ort_outputs[0][0][0]  # 预期 [1,1,H,W] → [H,W]
        mask_tensor = torch.from_numpy(mask_np)
        mask_pil = postprocess(mask_tensor, original_size)
        result_img = apply_mask(img, mask_pil)

        # 保存
        input_stem = Path(input_path).stem
        out_rgba = Path(output_dir) / f"{input_stem}_nobg.png"
        out_mask = Path(output_dir) / f"{input_stem}_mask.png"
        result_img.save(out_rgba)
        if save_mask:
            mask_pil.save(out_mask)

        return {
            "input": input_path,
            "output_rgba": str(out_rgba),
            "output_mask": str(out_mask) if save_mask else None,
            "inference_time_sec": inference_time,
            "device": "ONNX_Runtime_CPU"
        }