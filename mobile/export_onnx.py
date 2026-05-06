import torch
from bg_remover.model import BgRemover
from bg_remover.utils import INPUT_SIZE

def export_onnx(model_path="rmbg_fp32.onnx", device="cpu"):
    # 加载训练好的 PyTorch 模型
    remover = BgRemover(device=device)
    model = remover.model

    # 创建与预处理一致的虚拟输入
    dummy_input = torch.randn(1, 3, INPUT_SIZE[1], INPUT_SIZE[0]).to(device)

    # 导出
    torch.onnx.export(
        model,
        dummy_input,
        model_path,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {2: "height", 3: "width"},
            "output": {2: "height", 3: "width"}
        },
        opset_version=14,
    )
    print(f"ONNX 模型已导出至 {model_path}")

if __name__ == "__main__":
    export_onnx()