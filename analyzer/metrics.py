import cv2
import numpy as np
from PIL import Image
from typing import Tuple, Dict

def load_image(path: str, mode: str = 'RGB') -> np.ndarray:
    """统一加载为 numpy array"""
    img = Image.open(path).convert(mode)
    return np.array(img)

def mask_binary_score(mask: np.ndarray) -> float:
    """
    mask 二元性评分 (0~1)
    衡量预测 mask 的确定程度：值越接近 0 或 255 越好，中间值少则得分高。
    实际：计算 (mask/255) 的方差，mask 范围 [0,255]
    """
    if mask.max() <= 1:
        mask = mask * 255
    mask_norm = mask.astype(np.float32) / 255.0
    # 二值图像方差最大为 0.25（当均值为0.5时），方差越大越模糊
    # 我们用 1 - (std * 2) 映射到 [0,1]
    std = np.std(mask_norm)
    score = max(0, 1 - 2 * std)
    return score

def edge_sharpness(mask: np.ndarray) -> float:
    """
    边缘锐度评分 (0~1)
    计算 mask 的边缘梯度幅值，锐利边缘梯度大，模糊边缘梯度小。
    """
    mask_uint8 = mask.astype(np.uint8) if mask.dtype != np.uint8 else mask
    edges = cv2.Canny(mask_uint8, 50, 150)
    # 边缘像素比例
    edge_ratio = np.sum(edges > 0) / edges.size
    # 边缘数量不是越多越好，取对数压缩，并设定理想范围
    # 皮肤/发丝复杂度不同，这里简单处理：边缘密度适中得分高
    if edge_ratio < 0.005:
        sharp = 0.3
    elif edge_ratio > 0.15:
        sharp = 0.7
    else:
        sharp = 1.0 - abs(edge_ratio - 0.05) / 0.05
    return max(0, min(sharp, 1.0))

def foreground_coverage(mask: np.ndarray) -> float:
    """
    前景覆盖评分：前景面积不能为0，也不能全图都是前景（说明未移除背景）
    返回值在 0~1 之间，理想前景面积占比在 10%~90%
    """
    binary = mask > 127
    fg_ratio = np.sum(binary) / binary.size
    if fg_ratio < 0.05 or fg_ratio > 0.95:
        return 0.1
    elif 0.3 <= fg_ratio <= 0.7:
        return 1.0
    else:
        # 稍微偏离理想区间的线性衰减
        return 1.0 - abs(fg_ratio - 0.5) / 0.5

def inference_performance(inference_time_sec: float) -> float:
    """
    推理速度评分 (0~1)，目标 < 1.0s 满分，超过 5s 为差
    """
    if inference_time_sec <= 1.0:
        return 1.0
    elif inference_time_sec >= 5.0:
        return 0.1
    else:
        return 1.0 - (inference_time_sec - 1.0) / 4.0

def evaluate_single(image_path: str, mask_path: str, inference_time: float) -> Dict:
    """综合评估单张图片结果"""
    img = load_image(image_path, 'RGB')
    mask = load_image(mask_path, 'L')  # 灰度图

    scores = {
        'binary': mask_binary_score(mask),
        'sharpness': edge_sharpness(mask),
        'coverage': foreground_coverage(mask),
        'performance': inference_performance(inference_time)
    }
    # 加权总分 (binary 和 sharpness 最重要)
    weights = {'binary': 0.35, 'sharpness': 0.35, 'coverage': 0.2, 'performance': 0.1}
    total = sum(scores[k] * weights[k] for k in weights)
    scores['total'] = total
    return scores