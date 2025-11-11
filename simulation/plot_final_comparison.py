#!/usr/bin/env python3
"""
最終比較グラフの作成

グローバル最適化（提案手法）と分散型ベースライン（従来手法）の
性能比較グラフを生成する。
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ファイルパス
BASELINE_FILE = Path(__file__).parent / "output" / "baseline" / "baseline_distributed_results.csv"
OPTIMIZATION_FILE = Path(__file__).parent / "output" / "baseline" / "global_optimization_results.csv"
OUTPUT_FILE = Path(__file__).parent / "output" / "visualizations" / "final_performance_comparison.png"


def plot_final_comparison():
    """
    提案手法とベースラインの性能比較グラフを作成
    """
    print("=" * 60)
    print("最終比較グラフの作成")
    print("=" * 60)

    # データ読み込み
    print(f"\n[1] データ読み込み")
    print(f"  - ベースライン: {BASELINE_FILE}")
    baseline_df = pd.read_csv(BASELINE_FILE)
    print(f"    → {len(baseline_df)} レコード")

    print(f"  - 提案手法: {OPTIMIZATION_FILE}")
    optimization_df = pd.read_csv(OPTIMIZATION_FILE)
    print(f"    → {len(optimization_df)} レコード")

    # グラフ作成
    print(f"\n[2] グラフ作成")
    plt.figure(figsize=(12, 6))

    # 提案手法（グローバル最適化）
    plt.plot(
        optimization_df['timestamp'],
        optimization_df['optimized_total_throughput_mbps'],
        label='Proposed (Global Optimization)',
        color='#2E86AB',
        linewidth=2.5,
        marker='o',
        markersize=4,
        markevery=5
    )

    # ベースライン（分散型）
    plt.plot(
        baseline_df['timestamp'],
        baseline_df['total_v2i_throughput_mbps'],
        label='Baseline (Distributed)',
        color='#A23B72',
        linewidth=2.5,
        linestyle='--',
        marker='s',
        markersize=4,
        markevery=5
    )

    # グラフの装飾
    plt.xlabel('Time [s]', fontsize=12, fontweight='bold')
    plt.ylabel('Total Throughput [Mbps]', fontsize=12, fontweight='bold')
    plt.title('Proposed Method vs. Baseline', fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=11, framealpha=0.9)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tight_layout()

    # 統計情報の表示
    print(f"\n[3] 統計情報")
    print(f"  - 提案手法:")
    print(f"    * 平均: {optimization_df['optimized_total_throughput_mbps'].mean():.2f} Mbps")
    print(f"    * 最大: {optimization_df['optimized_total_throughput_mbps'].max():.2f} Mbps")
    print(f"    * 最小: {optimization_df['optimized_total_throughput_mbps'].min():.2f} Mbps")

    print(f"  - ベースライン:")
    print(f"    * 平均: {baseline_df['total_v2i_throughput_mbps'].mean():.2f} Mbps")
    print(f"    * 最大: {baseline_df['total_v2i_throughput_mbps'].max():.2f} Mbps")
    print(f"    * 最小: {baseline_df['total_v2i_throughput_mbps'].min():.2f} Mbps")

    # 性能向上率の計算
    improvement_ratio = (
        optimization_df['optimized_total_throughput_mbps'].mean() /
        baseline_df['total_v2i_throughput_mbps'].mean()
    )
    print(f"\n  - 性能向上率: {improvement_ratio:.2f}x ({(improvement_ratio-1)*100:.1f}% 向上)")

    # グラフ保存
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight')
    print(f"\n[4] 出力ファイル: {OUTPUT_FILE}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("グラフ作成完了")
    print("=" * 60)


if __name__ == "__main__":
    plot_final_comparison()
