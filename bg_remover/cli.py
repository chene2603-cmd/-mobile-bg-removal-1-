import argparse
from pathlib import Path
from bg_remover import BgRemovalPipeline
from bg_remover.pipeline import MobileBgRemovalPipeline
from analyzer.correlator import generate_report
import json

def main():
    parser = argparse.ArgumentParser(description="Mobile BG Removal Toolkit")
    subparsers = parser.add_subparsers(dest="command")

    # 子命令：去除背景
    remove_parser = subparsers.add_parser("remove", help="Remove background from images")
    remove_parser.add_argument("input", help="Image file or directory")
    remove_parser.add_argument("--output", default="output", help="Output directory")
    remove_parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    remove_parser.add_argument("--engine", default="torch", choices=["torch", "onnx"], 
                                 help="Inference engine")
    remove_parser.add_argument("--onnx-model", help="Path to ONNX model (when engine=onnx)")

    # 子命令：评估
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate results from a processing log")
    eval_parser.add_argument("log_file", help="Path to processing_log.json")
    eval_parser.add_argument("--output", default="evaluation_report.md", help="Report output path")

    # 子命令：一键基准测试
    bench_parser = subparsers.add_parser("benchmark", help="Run full benchmark: FP32 vs INT8")
    bench_parser.add_argument("input_dir", help="Directory containing test images")
    bench_parser.add_argument("--fp32-output", default="output_fp32")
    bench_parser.add_argument("--int8-output", default="output_int8")
    bench_parser.add_argument("--onnx-model", default="mobile/rmbg_int8.onnx")

    args = parser.parse_args()

    if args.command == "remove":
        input_path = Path(args.input)
        if input_path.is_dir():
            images = list(input_path.glob("*.jpg")) + list(input_path.glob("*.png"))
        else:
            images = [input_path]

        if args.engine == "torch":
            pipeline = BgRemovalPipeline(device=args.device)
        else:
            if not args.onnx_model:
                raise ValueError("--onnx-model required for ONNX engine")
            pipeline = MobileBgRemovalPipeline(args.onnx_model)

        out_dir = Path(args.output)
        out_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for img_path in images:
            res = pipeline.run(str(img_path), str(out_dir))
            results.append(res)
            print(f"✔ {img_path.name}")

        log_path = out_dir / "processing_log.json"
        with open(log_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Log saved to {log_path}")

    elif args.command == "evaluate":
        generate_report(args.log_file, args.output)

    elif args.command == "benchmark":
        # 直接调用 run_mobile_benchmark 中的逻辑（可抽取为函数）
        from run_mobile_benchmark import run_benchmark
        run_benchmark(args.input_dir, args.fp32_output, args.int8_output, args.onnx_model)

    else:
        parser.print_help()