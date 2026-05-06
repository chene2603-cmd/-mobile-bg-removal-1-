from onnxruntime.quantization import quantize_dynamic, QuantType

def quantize_model(input_model="mobile/rmbg_fp32.onnx",
                   output_model="mobile/rmbg_int8.onnx"):
    quantize_dynamic(
        input_model,
        output_model,
        weight_type=QuantType.QInt8  # 权重量化为 int8
    )
    print(f"量化模型已保存至 {output_model}")

if __name__ == "__main__":
    quantize_model()