import matplotlib
matplotlib.use('Agg')  # 无图形界面后端
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import List, Dict

class ChartGenerator:
    """生成报告所需图表（热力图、鱼骨图、趋势图、依赖图）"""
    
    def __init__(self, output_dir="output/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def generate_heatmap(self, problem_distribution: Dict[str, int], title="问题热力图（按区域/产线）", filename="heatmap.png"):
        """生成问题热力图：假设输入为 {'产线A':12, '产线B':5, ...}"""
        if not problem_distribution:
            # 生成示例数据
            problem_distribution = {'总装车间': 25, '焊接车间': 18, '涂装车间': 10, '机加车间': 30, '仓库': 5}
        categories = list(problem_distribution.keys())
        values = list(problem_distribution.values())
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, values, color=plt.cm.Reds(np.array(values)/max(values)))
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('区域/产线')
        ax.set_ylabel('问题数量')
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(val), ha='center')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=150)
        plt.close()
        return str(save_path)
    
    def generate_fishbone(self, root_causes: Dict[str, List[str]], title="根因鱼骨图（人机料法环）", filename="fishbone.png"):
        """生成鱼骨图（简化版：用水平箭头文本表示）"""
        # 由于matplotlib原生鱼骨图复杂，这里生成一个清晰的文本+箭头示意图
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.axis('off')
        # 主骨箭头
        ax.annotate('', xy=(0.9, 0.5), xytext=(0.1, 0.5), arrowprops=dict(arrowstyle='->', lw=2))
        ax.text(0.5, 0.55, title, ha='center', fontsize=14, weight='bold')
        # 分类骨头
        categories = ['人', '机', '料', '法', '环']
        y_positions = [0.7, 0.6, 0.5, 0.4, 0.3]
        for cat, y in zip(categories, y_positions):
            ax.plot([0.2, 0.4], [y, 0.5], 'k-', lw=1.5)
            ax.text(0.15, y, cat, fontsize=12, weight='bold', ha='right')
            causes = root_causes.get(cat, ['示例原因'])
            for i, cause in enumerate(causes[:2]):  # 最多显示2条
                ax.text(0.45, y - i*0.03, f'• {cause}', fontsize=9, va='top')
        plt.tight_layout()
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=150)
        plt.close()
        return str(save_path)
    
    def generate_trend(self, history_data: List[int], labels: List[str] = None, title="屎山指数趋势图", filename="trend.png"):
        """生成趋势图，假设history_data为每月屎山指数列表"""
        if not history_data:
            history_data = [45, 52, 48, 59, 58, 62]
        if labels is None:
            labels = [f"M{i+1}" for i in range(len(history_data))]
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(labels, history_data, marker='o', linestyle='-', linewidth=2, color='#FF6B6B')
        ax.fill_between(labels, history_data, alpha=0.2, color='#FF6B6B')
        ax.set_title(title, fontsize=14)
        ax.set_xlabel('月份')
        ax.set_ylabel('屎山指数 (0-100)')
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_ylim(0, 100)
        for i, val in enumerate(history_data):
            ax.text(i, val + 2, str(val), ha='center')
        plt.tight_layout()
        save_path = self.output_dir / filename
        plt.savefig(save_path, dpi=150)
        plt.close()
        return str(save_path)
    
    def generate_dependency_graph(self, nodes: List[Dict], edges: List[tuple], filename="dependency.png"):
        """生成系统依赖关系图（使用networkx，如果没有则提示）"""
        try:
            import networkx as nx
            G = nx.DiGraph()
            for node in nodes:
                G.add_node(node['id'], label=node['label'], color=node.get('color', '#118AB2'))
            for src, tgt in edges:
                G.add_edge(src, tgt)
            pos = nx.spring_layout(G, seed=42)
            plt.figure(figsize=(12, 8))
            nx.draw_networkx_nodes(G, pos, node_color=[G.nodes[n]['color'] for n in G.nodes], node_size=1500)
            nx.draw_networkx_labels(G, pos, labels={n: G.nodes[n]['label'] for n in G.nodes}, font_size=8)
            nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=15, edge_color='gray')
            plt.title("系统依赖关系图（脆弱节点红色标注）")
            plt.axis('off')
            save_path = self.output_dir / filename
            plt.savefig(save_path, dpi=150)
            plt.close()
            return str(save_path)
        except ImportError:
            # 如果没有networkx，生成一个文本说明
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.axis('off')
            text = "依赖关系图需要 networkx 库支持。\n请安装: pip install networkx\n\n当前简化依赖:\n"
            for src, tgt in edges[:10]:
                text += f"  {src} → {tgt}\n"
            ax.text(0.1, 0.5, text, fontsize=10, va='center')
            save_path = self.output_dir / filename
            plt.savefig(save_path, dpi=150)
            plt.close()
            return str(save_path)