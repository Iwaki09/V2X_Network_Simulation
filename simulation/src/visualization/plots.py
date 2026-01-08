#!/usr/bin/env python3
"""
グラフ生成モジュール

シミュレーション結果を可視化するためのグラフ生成機能を提供します。
- ネットワーク性能サマリー
- ベースライン比較
- 最終性能比較
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def plot_network_summary(input_csv: str = None, output_png: str = None, output_dir: str = None):
    """
    時系列での総スループットをプロット

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_png: 出力PNGファイルパス (network_performance_summary.png)
        output_dir: 出力ディレクトリ（output_pngより優先度低い）
    """
    # パス設定
    script_dir = Path(__file__).parent.parent.parent
    if input_csv is None:
        input_csv = str(script_dir / 'output/scenarios/default/throughput/theoretical_network_results.csv')
    if output_png is None:
        if output_dir is not None:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_png = str(Path(output_dir) / 'throughput_summary.png')
        else:
            output_png = str(script_dir / 'output/scenarios/default/figures/throughput_summary.png')

    print("=" * 70)
    print("ネットワーク性能サマリー可視化")
    print("=" * 70)
    print()
    print(f"入力ファイル: {input_csv}")
    print()

    # CSVファイルを読み込む
    df = pd.read_csv(input_csv)
    print(f"✅ データ読み込み完了: {len(df)} レコード")
    print()

    # タイムスタンプごとにグループ化してスループット合計を計算
    print("【計算中】タイムスタンプごとのスループット合計を計算...")
    throughput_summary = df.groupby('timestamp')['theoretical_throughput_mbps'].sum().reset_index()
    throughput_summary.rename(columns={'theoretical_throughput_mbps': 'total_throughput_mbps'}, inplace=True)

    print(f"✅ 計算完了: {len(throughput_summary)} タイムステップ")
    print()

    # 統計情報を表示
    print("【統計情報】")
    print(f"  総スループット (Mbps):")
    print(f"    - 平均: {throughput_summary['total_throughput_mbps'].mean():.2f} Mbps")
    print(f"    - 最小: {throughput_summary['total_throughput_mbps'].min():.2f} Mbps")
    print(f"    - 最大: {throughput_summary['total_throughput_mbps'].max():.2f} Mbps")
    print()

    # グラフの作成
    print("【可視化中】グラフを生成...")
    fig, ax = plt.subplots(figsize=(12, 6))

    # 折れ線グラフをプロット
    ax.plot(throughput_summary['timestamp'],
            throughput_summary['total_throughput_mbps'],
            linewidth=2, color='steelblue', marker='o', markersize=3)

    # グラフの装飾
    ax.set_xlabel('Time [s]', fontsize=12)
    ax.set_ylabel('Total Theoretical Throughput [Mbps]', fontsize=12)
    ax.set_title('Network Performance Summary (V2I + V2V)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # 平均値のラインを追加（破線）
    mean_throughput = throughput_summary['total_throughput_mbps'].mean()
    ax.axhline(y=mean_throughput, color='red', linestyle='--', linewidth=1.5,
               label=f'Average: {mean_throughput:.2f} Mbps')

    # 凡例を表示
    ax.legend(loc='upper right', fontsize=10)

    # レイアウトの調整
    plt.tight_layout()

    # PNGファイルとして保存
    plt.savefig(output_png, dpi=150)
    print(f"✅ グラフ保存完了: {output_png}")
    print()
    print("=" * 70)

    plt.close(fig)


def plot_baseline_comparison(theoretical_csv: str = None, baseline_csv: str = None, output_png: str = None, output_dir: str = None):
    """
    理論的最大値とベースラインの比較グラフを作成

    Args:
        theoretical_csv: 理論的ネットワーク結果CSVファイルパス
        baseline_csv: ベースライン分散型結果CSVファイルパス
        output_png: 出力画像ファイルのパス
        output_dir: 出力ディレクトリ（output_pngより優先度低い）
    """
    # パス設定
    script_dir = Path(__file__).parent.parent.parent
    if theoretical_csv is None:
        theoretical_csv = str(script_dir / "output" / "scenarios" / "default" / "throughput" / "theoretical_network_results.csv")
    if baseline_csv is None:
        baseline_csv = str(script_dir / "output" / "scenarios" / "default" / "optimization" / "baseline_distributed_results.csv")
    if output_png is None:
        if output_dir is not None:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_png = str(Path(output_dir) / "theoretical_potential.png")
        else:
            output_png = str(script_dir / "output" / "scenarios" / "default" / "figures" / "theoretical_potential.png")

    print("=" * 60)
    print("ベースライン性能可視化")
    print("=" * 60)

    # 1. 理論的最大値を計算
    print("\n[1] 理論的最大値を計算")
    df = pd.read_csv(theoretical_csv)
    print(f"理論的ネットワーク結果: {len(df)} 行")

    theoretical_df = df.groupby('timestamp')['theoretical_throughput_mbps'].sum().reset_index()
    theoretical_df.columns = ['timestamp', 'theoretical_maximum_mbps']
    print(f"理論的最大値範囲: {theoretical_df['theoretical_maximum_mbps'].min():.2f} - {theoretical_df['theoretical_maximum_mbps'].max():.2f} Mbps")

    # 2. 分散型ベースラインを読み込む
    print("\n[2] 分散型ベースラインを読み込む")
    baseline_df = pd.read_csv(baseline_csv)
    print(f"分散型ベースライン: {len(baseline_df)} 行")
    print(f"V2I総スループット範囲: {baseline_df['total_v2i_throughput_mbps'].min():.2f} - {baseline_df['total_v2i_throughput_mbps'].max():.2f} Mbps")

    # 3. 比較グラフを作成
    print("\n[3] 比較グラフを作成")
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
    plt.savefig(output_png, dpi=300)
    print(f"グラフを保存しました: {output_png}")

    # 統計情報を出力
    avg_theoretical = theoretical_df['theoretical_maximum_mbps'].mean()
    avg_baseline = baseline_df['total_v2i_throughput_mbps'].mean()
    gap = avg_theoretical - avg_baseline
    gap_percentage = (gap / avg_theoretical) * 100

    print(f"\n統計情報:")
    print(f"  理論的最大値（平均）: {avg_theoretical:.2f} Mbps")
    print(f"  分散型ベースライン（平均）: {avg_baseline:.2f} Mbps")
    print(f"  改善余地（平均）: {gap:.2f} Mbps ({gap_percentage:.1f}%)")

    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)

    plt.close()


def plot_final_comparison(baseline_csv: str = None, optimization_csv: str = None, output_png: str = None, output_dir: str = None):
    """
    提案手法とベースラインの性能比較グラフを作成

    Args:
        baseline_csv: ベースライン分散型結果CSVファイルパス
        optimization_csv: グローバル最適化結果CSVファイルパス
        output_png: 出力画像ファイルのパス
        output_dir: 出力ディレクトリ（output_pngより優先度低い）
    """
    # パス設定
    script_dir = Path(__file__).parent.parent.parent
    if baseline_csv is None:
        baseline_csv = str(script_dir / "output" / "scenarios" / "default" / "optimization" / "baseline_distributed_results.csv")
    if optimization_csv is None:
        optimization_csv = str(script_dir / "output" / "scenarios" / "default" / "optimization" / "global_optimization_results.csv")
    if output_png is None:
        if output_dir is not None:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            output_png = str(Path(output_dir) / "method_comparison.png")
        else:
            output_png = str(script_dir / "output" / "scenarios" / "default" / "figures" / "method_comparison.png")

    print("=" * 60)
    print("最終比較グラフの作成")
    print("=" * 60)

    # データ読み込み
    print(f"\n[1] データ読み込み")
    print(f"  - ベースライン: {baseline_csv}")
    baseline_df = pd.read_csv(baseline_csv)
    print(f"    → {len(baseline_df)} レコード")

    print(f"  - 提案手法: {optimization_csv}")
    optimization_df = pd.read_csv(optimization_csv)
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
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"\n[4] 出力ファイル: {output_png}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("グラフ作成完了")
    print("=" * 60)

    plt.close()


if __name__ == "__main__":
    # テスト用
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "network":
            plot_network_summary()
        elif sys.argv[1] == "baseline":
            plot_baseline_comparison()
        elif sys.argv[1] == "final":
            plot_final_comparison()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python plots.py [network|baseline|final]")
    else:
        print("Usage: python plots.py [network|baseline|final]")
