#!/usr/bin/env python3
"""
ベースライン性能可視化スクリプト

理論的最大値（天井）と分散型ベースラインの比較グラフを生成する。

入力:
  - theoretical_network_results.csv (理論的最大値の計算用)
  - baseline_distributed_results.csv (ベースラインの計算用)

出力:
  - baseline_comparison.png (比較グラフ)
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def calculate_theoretical_maximum(csv_path: Path) -> pd.DataFrame:
    """
    理論的総容量（V2I + V2V）を計算

    Args:
        csv_path: theoretical_network_results.csvのパス

    Returns:
        timestamp と theoretical_maximum_mbps の2列を持つDataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"理論的ネットワーク結果: {len(df)} 行")

    # タイムスタンプごとに全リンク（V2I + V2V）のスループット合計を計算
    result_df = df.groupby('timestamp')['theoretical_throughput_mbps'].sum().reset_index()
    result_df.columns = ['timestamp', 'theoretical_maximum_mbps']

    print(f"理論的最大値範囲: {result_df['theoretical_maximum_mbps'].min():.2f} - {result_df['theoretical_maximum_mbps'].max():.2f} Mbps")

    return result_df


def load_baseline_distributed(csv_path: Path) -> pd.DataFrame:
    """
    分散型V2I総容量を読み込む

    Args:
        csv_path: baseline_distributed_results.csvのパス

    Returns:
        読み込んだDataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"分散型ベースライン: {len(df)} 行")
    print(f"V2I総スループット範囲: {df['total_v2i_throughput_mbps'].min():.2f} - {df['total_v2i_throughput_mbps'].max():.2f} Mbps")

    return df


def plot_comparison(theoretical_df: pd.DataFrame, baseline_df: pd.DataFrame, output_path: Path) -> None:
    """
    理論的最大値とベースラインの比較グラフを作成

    Args:
        theoretical_df: 理論的最大値のDataFrame
        baseline_df: 分散型ベースラインのDataFrame
        output_path: 出力画像ファイルのパス
    """
    plt.figure(figsize=(12, 6))

    # グラフ1: 理論的最大値（天井）
    plt.plot(
        theoretical_df['timestamp'],
        theoretical_df['theoretical_maximum_mbps'],
        label='Theoretical Maximum (Global Potential)',
        color='green',
        linewidth=2,
        linestyle='--'
    )

    # グラフ2: 分散型ベースライン
    plt.plot(
        baseline_df['timestamp'],
        baseline_df['total_v2i_throughput_mbps'],
        label='Baseline (Distributed V2I)',
        color='blue',
        linewidth=2
    )

    # ギャップエリアを塗りつぶし
    plt.fill_between(
        theoretical_df['timestamp'],
        baseline_df['total_v2i_throughput_mbps'],
        theoretical_df['theoretical_maximum_mbps'],
        color='gray',
        alpha=0.3,
        label='Optimization Potential'
    )

    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Total Throughput (Mbps)', fontsize=12)
    plt.title('Baseline Performance vs. Theoretical Maximum', fontsize=14, fontweight='bold')
    plt.legend(loc='upper left', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    # 保存
    plt.savefig(output_path, dpi=300)
    print(f"グラフを保存しました: {output_path}")

    # 統計情報を出力
    avg_theoretical = theoretical_df['theoretical_maximum_mbps'].mean()
    avg_baseline = baseline_df['total_v2i_throughput_mbps'].mean()
    gap = avg_theoretical - avg_baseline
    gap_percentage = (gap / avg_theoretical) * 100

    print(f"\n統計情報:")
    print(f"  理論的最大値（平均）: {avg_theoretical:.2f} Mbps")
    print(f"  分散型ベースライン（平均）: {avg_baseline:.2f} Mbps")
    print(f"  改善余地（平均）: {gap:.2f} Mbps ({gap_percentage:.1f}%)")


def main():
    """メイン処理"""
    # パス設定
    script_dir = Path(__file__).parent
    theoretical_csv = script_dir / "output" / "throughput" / "theoretical_network_results.csv"
    baseline_csv = script_dir / "baseline_distributed_results.csv"
    output_png = script_dir / "baseline_comparison.png"

    print("=" * 60)
    print("ベースライン性能可視化")
    print("=" * 60)

    # 1. 理論的最大値を計算
    print("\n[1] 理論的最大値を計算")
    theoretical_df = calculate_theoretical_maximum(theoretical_csv)

    # 2. 分散型ベースラインを読み込む
    print("\n[2] 分散型ベースラインを読み込む")
    baseline_df = load_baseline_distributed(baseline_csv)

    # 3. 比較グラフを作成
    print("\n[3] 比較グラフを作成")
    plot_comparison(theoretical_df, baseline_df, output_png)

    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
