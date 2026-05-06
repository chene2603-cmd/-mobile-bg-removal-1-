import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import numpy as np

# RMBG-1.4 要求输入 1024x1024，归一化参数固定
INPUT_SIZE = (1024, 1024)
NORM_MEAN = [0.5, 0.5, 0.5]
NORM_STD = [0.5, 0.5, 0.5]

def preprocess(pil_image: Image.Image) -> torch.Tensor:
    """将 PIL 图像转换为模型输入张量"""
    transform = transforms.Compose([
        transforms.Resize(INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=NORM_MEAN, std=NORM_STD)
    ])
    return transform(pil_image).unsqueeze(0)  # 增加 batch 维度

def postprocess(mask_tensor: torch.Tensor, original_size: tuple) -> Image.Image:
    """
    将模型输出 mask 转为原图尺寸的二值 alpha 通道 PIL 图像
    original_size: (width, height)
    """
    # mask_tensor 尺寸可能是 [H, W] 或 [1, H, W]
    if mask_tensor.dim() == 3:
        mask_tensor = mask_tensor[0]
    # 调整到输入尺寸（1024x1024）
    mask_tensor = mask_tensor.unsqueeze(0).unsqueeze(0)  # [1,1,H,W]
    mask_tensor = F.interpolate(mask_tensor, size=INPUT_SIZE, mode='bilinear', align_corners=False)
    # 再调整到原图尺寸
    mask_tensor = F.interpolate(mask_tensor, size=(original_size[1], original_size[0]), 
                                mode='bilinear', align_corners=False)
    mask = mask_tensor.squeeze().cpu().numpy()  # [H,W]
    # 归一化到 0-255
    mask = (mask * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(mask, mode='L')

def apply_mask(pil_image: Image.Image, mask: Image.Image) -> Image.Image:
    """将 alpha mask 应用到原图，返回 RGBA 透明背景图"""
    img = pil_image.convert('RGBA')
    img.putalpha(mask)
    return img