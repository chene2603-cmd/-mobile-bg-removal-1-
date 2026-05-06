import torch
from transformers import AutoModelForImageSegmentation

class BgRemover:
    def __init__(self, model_name: str = "briaai/RMBG-1.4", device: str = "cpu"):
        self.device = device
        self.model = AutoModelForImageSegmentation.from_pretrained(
            model_name, trust_remote_code=True
        ).to(device).eval()

    @torch.no_grad()
    def predict(self, image_tensor: torch.Tensor) -> torch.Tensor:
        """
        输入归一化后的张量 [1, 3, H, W]，返回 mask [H, W]
        """
        output = self.model(image_tensor)
        # RMBG-1.4 返回列表，取第一张图的第一个输出
        if isinstance(output, list):
            return output[0][0].squeeze()  
        # 其他模型可能直接返回张量
        return output.squeeze()