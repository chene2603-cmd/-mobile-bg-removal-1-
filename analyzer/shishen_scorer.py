import json
from pathlib import Path
from analyzer.metrics import evaluate_single

def batch_score_from_log(log_path: str) -> list:
    """
    读取 processing_log.json，逐条评估，返回带评分的列表
    """
    with open(log_path, 'r') as f:
        results = json.load(f)

    scored = []
    for item in results:
        if not item.get('output_mask'):
            continue
        scores = evaluate_single(
            image_path=item['input'],
            mask_path=item['output_mask'],
            inference_time=item['inference_time_sec']
        )
        scored.append({**item, 'scores': scores})
    return scored

def rank_results(scored: list) -> list:
    """按总分降序排列"""
    return sorted(scored, key=lambda x: x['scores']['total'], reverse=True)