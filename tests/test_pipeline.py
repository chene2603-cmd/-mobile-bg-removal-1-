import pytest
from pathlib import Path
from PIL import Image
from bg_remover import BgRemovalPipeline

def test_pipeline_preprocess():
    dummy_img = Image.new('RGB', (300, 200), color='red')
    pipeline = BgRemovalPipeline(device='cpu')
    # 仅测试预处理不崩溃（不加载大模型）
    from bg_remover.utils import preprocess
    tensor = preprocess(dummy_img)
    assert tensor.shape == (1, 3, 1024, 1024)