from pathlib import Path
from PIL import Image
from bg_remover.model import BgRemover
from bg_remover.utils import preprocess, postprocess, apply_mask
import time
import torch

class BgRemovalPipeline:
    def __init__(self, device='cpu'):
        self.remover = BgRemover(device=device)
        self.device = device

    def run(self, input_path: str, output_dir: str, save_mask: bool = True) -> dict:
        """
        处理单张图片，返回结果字典，包含计时和路径信息
        """
        img = Image.open(input_path).convert('RGB')
        original_size = img.size  # (width, height)
        img_tensor = preprocess(img).to(self.device)

        # 计时推理
        start = time.time()
        mask_tensor = self.remover.predict(img_tensor)
        inference_time = time.time() - start

        # 后处理
        mask_pil = postprocess(mask_tensor, original_size)
        result_img = apply_mask(img, mask_pil)

        # 保存结果
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
            "device": self.device
        }