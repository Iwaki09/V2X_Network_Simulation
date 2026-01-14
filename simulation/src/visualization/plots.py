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


def plot_all_baselines_vs_theoretical(
    theoretical_csv: str,
    baseline_distributed_csv: str,
    baseline_chairgame_dir: str,
    output_png: str,
    eval_throughput_col: str = 'throughput_mbps_mcs'
):
    """
    理論的最大値 vs 全ベースライン（distributed + chairgame 3種）の時系列比較

    Args:
        theoretical_csv: 理論的ネットワーク結果CSV
        baseline_distributed_csv: 分散型ベースライン結果CSV
        baseline_chairgame_dir: 椅子取りゲームベースライン結果ディレクトリ
        output_png: 出力PNGファイルパス
        eval_throughput_col: 評価用スループット列名
    """
    print("\n" + "=" * 80)
    print("全ベースライン vs 理論的最大値の時系列比較")
    print("=" * 80)

    # 1. 理論的最大値を計算（V2Iのみ）
    print("[1] 理論的最大値を計算（V2Iのみ）")
    df = pd.read_csv(theoretical_csv)
    v2i_df = df[df['link_type'] == 'V2I'].copy()
    theoretical_df = v2i_df.groupby('timestamp')[eval_throughput_col].sum().reset_index()
    theoretical_df.columns = ['timestamp', 'theoretical_maximum_mbps']
    print(f"  理論的最大値範囲: {theoretical_df['theoretical_maximum_mbps'].min():.2f} - {theoretical_df['theoretical_maximum_mbps'].max():.2f} Mbps")

    # 2. 分散型ベースライン
    print("[2] 分散型ベースライン（Distributed）")
    distributed_df = pd.read_csv(baseline_distributed_csv)
    print(f"  範囲: {distributed_df['total_v2i_throughput_mbps'].min():.2f} - {distributed_df['total_v2i_throughput_mbps'].max():.2f} Mbps")

    # 3. 椅子取りゲームベースライン（3種）
    print("[3] 椅子取りゲームベースライン")
    baseline_chairgame_dir = Path(baseline_chairgame_dir)

    chairgame_data = {}
    for baseline_name in ['max_snr', 'nearest', 'random']:
        assignment_csv = baseline_chairgame_dir / f'baseline_{baseline_name}_assignment.csv'
        if not assignment_csv.exists():
            print(f"  ⚠️ {baseline_name}: ファイルが見つかりません")
            continue

        # assignment データを読み込み、timestampごとにacceptedの真値スループットを集計
        assign_df = pd.read_csv(assignment_csv)

        # truth_throughputがない場合は、theoretical_csvとjoin
        if 'throughput_truth' in assign_df.columns:
            truth_col = 'throughput_truth'
        else:
            # theoretical_csvから取得
            theo_df = pd.read_csv(theoretical_csv)
            v2i_df = theo_df[theo_df['link_type'] == 'V2I'].copy()
            assign_df = assign_df.merge(
                v2i_df[['timestamp', 'rx_id', 'tx_id', eval_throughput_col]],
                left_on=['timestamp', 'vehicle_id', 'assigned_bs_id'],
                right_on=['timestamp', 'rx_id', 'tx_id'],
                how='left'
            )
            assign_df = assign_df.drop(columns=['rx_id', 'tx_id'], errors='ignore')
            truth_col = eval_throughput_col

        # acceptedのみの真値スループット（rejectedは0）
        assign_df[truth_col] = assign_df[truth_col].fillna(0.0)

        # timestampごとに集計
        ts_sum = assign_df.groupby('timestamp')[truth_col].sum().reset_index()
        ts_sum.columns = ['timestamp', 'total_throughput_mbps']

        chairgame_data[baseline_name] = ts_sum
        print(f"  {baseline_name}: {ts_sum['total_throughput_mbps'].mean():.2f} Mbps (平均)")

    # 4. プロット
    print("[4] グラフ作成")
    fig, ax = plt.subplots(figsize=(12, 7))

    # 理論的最大値（背景、薄く）
    ax.plot(theoretical_df['timestamp'], theoretical_df['theoretical_maximum_mbps'],
            label='Theoretical Maximum (V2I Upper Bound)', color='gray', linewidth=2,
            linestyle=':', alpha=0.5, zorder=1)

    # 分散型ベースライン（既存）
    ax.plot(distributed_df['timestamp'], distributed_df['total_v2i_throughput_mbps'],
            label='Distributed (Legacy Baseline)', color='#6C757D', linewidth=2,
            linestyle='--', marker='s', markersize=3, markevery=5, alpha=0.8, zorder=2)

    # 椅子取りゲームベースライン（3種）
    colors = {'max_snr': '#2E86AB', 'nearest': '#A23B72', 'random': '#F18F01'}
    labels = {'max_snr': 'Max-SNR (Greedy)', 'nearest': 'Nearest-BS (Distance)', 'random': 'Random (Lower Bound)'}
    linestyles = {'max_snr': '-', 'nearest': '--', 'random': '-.'}
    markers = {'max_snr': 'o', 'nearest': '^', 'random': 'x'}

    for baseline_name, data_df in chairgame_data.items():
        ax.plot(data_df['timestamp'], data_df['total_throughput_mbps'],
                label=labels[baseline_name], color=colors[baseline_name],
                linewidth=2, linestyle=linestyles[baseline_name],
                marker=markers[baseline_name], markersize=3, markevery=5,
                alpha=0.9, zorder=3)

    ax.set_xlabel('Time [s]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Total Throughput [Mbps]', fontsize=12, fontweight='bold')
    ax.set_title('All Baselines vs. Theoretical Maximum', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95, ncol=1)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def plot_all_methods_comparison(
    theoretical_csv: str,
    baseline_distributed_csv: str,
    baseline_chairgame_dir: str,
    optimization_csv: str,
    output_png: str,
    eval_throughput_col: str = 'throughput_mbps_mcs'
):
    """
    提案手法 vs 全ベースライン（distributed + chairgame 3種）の時系列比較

    Args:
        theoretical_csv: 理論的ネットワーク結果CSV
        baseline_distributed_csv: 分散型ベースライン結果CSV
        baseline_chairgame_dir: 椅子取りゲームベースライン結果ディレクトリ
        optimization_csv: グローバル最適化結果CSV
        output_png: 出力PNGファイルパス
        eval_throughput_col: 評価用スループット列名
    """
    print("\n" + "=" * 80)
    print("提案手法 vs 全ベースラインの時系列比較")
    print("=" * 80)

    # 1. 提案手法（グローバル最適化）
    print("[1] 提案手法（Global Optimization）")
    opt_df = pd.read_csv(optimization_csv)
    print(f"  範囲: {opt_df['optimized_total_throughput_mbps'].min():.2f} - {opt_df['optimized_total_throughput_mbps'].max():.2f} Mbps")

    # 2. 分散型ベースライン
    print("[2] 分散型ベースライン（Distributed）")
    distributed_df = pd.read_csv(baseline_distributed_csv)
    print(f"  範囲: {distributed_df['total_v2i_throughput_mbps'].min():.2f} - {distributed_df['total_v2i_throughput_mbps'].max():.2f} Mbps")

    # 3. 椅子取りゲームベースライン（3種）
    print("[3] 椅子取りゲームベースライン")
    baseline_chairgame_dir = Path(baseline_chairgame_dir)

    chairgame_data = {}
    for baseline_name in ['max_snr', 'nearest', 'random']:
        assignment_csv = baseline_chairgame_dir / f'baseline_{baseline_name}_assignment.csv'
        if not assignment_csv.exists():
            print(f"  ⚠️ {baseline_name}: ファイルが見つかりません")
            continue

        # assignment データを読み込み、timestampごとにacceptedの真値スループットを集計
        assign_df = pd.read_csv(assignment_csv)

        # truth_throughputがない場合は、theoretical_csvとjoin
        if 'throughput_truth' in assign_df.columns:
            truth_col = 'throughput_truth'
        else:
            # theoretical_csvから取得
            theo_df = pd.read_csv(theoretical_csv)
            v2i_df = theo_df[theo_df['link_type'] == 'V2I'].copy()
            assign_df = assign_df.merge(
                v2i_df[['timestamp', 'rx_id', 'tx_id', eval_throughput_col]],
                left_on=['timestamp', 'vehicle_id', 'assigned_bs_id'],
                right_on=['timestamp', 'rx_id', 'tx_id'],
                how='left'
            )
            assign_df = assign_df.drop(columns=['rx_id', 'tx_id'], errors='ignore')
            truth_col = eval_throughput_col

        # acceptedのみの真値スループット（rejectedは0）
        assign_df[truth_col] = assign_df[truth_col].fillna(0.0)

        # timestampごとに集計
        ts_sum = assign_df.groupby('timestamp')[truth_col].sum().reset_index()
        ts_sum.columns = ['timestamp', 'total_throughput_mbps']

        chairgame_data[baseline_name] = ts_sum
        print(f"  {baseline_name}: {ts_sum['total_throughput_mbps'].mean():.2f} Mbps (平均)")

    # 4. プロット（既存のスタイルに合わせて統一）
    print("[4] グラフ作成")
    fig, ax = plt.subplots(figsize=(12, 7))

    # 提案手法（最上位、強調）
    ax.plot(opt_df['timestamp'], opt_df['optimized_total_throughput_mbps'],
            label='Proposed (Global Optimization)', color='#E63946', linewidth=2.5,
            marker='o', markersize=4, markevery=5, alpha=0.95, zorder=10)

    # 分散型ベースライン（既存）
    ax.plot(distributed_df['timestamp'], distributed_df['total_v2i_throughput_mbps'],
            label='Distributed (Legacy Baseline)', color='#6C757D', linewidth=2.0,
            linestyle='--', marker='^', markersize=4, markevery=5, alpha=0.7, zorder=2)

    # 椅子取りゲームベースライン（3種）
    colors = {'max_snr': '#2E86AB', 'nearest': '#A23B72', 'random': '#F18F01'}
    labels = {'max_snr': 'Max-SNR (Greedy)', 'nearest': 'Nearest-BS (Distance)', 'random': 'Random (Lower Bound)'}
    linestyles = {'max_snr': '-', 'nearest': '--', 'random': '-.'}
    markers = {'max_snr': 's', 'nearest': 'D', 'random': 'x'}

    for baseline_name, data_df in chairgame_data.items():
        ax.plot(data_df['timestamp'], data_df['total_throughput_mbps'],
                label=labels[baseline_name], color=colors[baseline_name],
                linewidth=2.0, linestyle=linestyles[baseline_name],
                marker=markers[baseline_name], markersize=4, markevery=5,
                alpha=0.8, zorder=3)

    ax.set_xlabel('Time [s]', fontsize=14, fontweight='bold')
    ax.set_ylabel('Total Throughput [Mbps]', fontsize=14, fontweight='bold')
    ax.set_title('Proposed Method vs. All Baselines\nMusical Chairs Framework',
                 fontsize=16, fontweight='bold', pad=15)
    ax.legend(loc='upper left', fontsize=10, framealpha=0.95, ncol=1)
    ax.grid(True, alpha=0.3, linestyle='--')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def plot_baselines_chairgame_comparison(
    baseline_dir: str = None,
    output_png: str = None,
    bs_capacity: int = 10
):
    """
    ベースライン手法（椅子取りゲーム）の比較グラフを生成

    Args:
        baseline_dir: ベースライン結果ディレクトリ
        output_png: 出力PNGファイルパス
        bs_capacity: 基地局定員（グラフタイトル用）
    """
    import numpy as np

    # パス設定
    script_dir = Path(__file__).parent.parent.parent
    if baseline_dir is None:
        baseline_dir = str(script_dir / 'output/scenarios/corner_intersection/baseline_chairgame')
    baseline_dir = Path(baseline_dir)

    if output_png is None:
        output_png = str(baseline_dir / 'baselines_chairgame_comparison.png')

    print("=" * 80)
    print("ベースライン手法（椅子取りゲーム）比較グラフ生成")
    print("=" * 80)
    print(f"入力ディレクトリ: {baseline_dir}")
    print(f"BS定員: {bs_capacity}")
    print()

    # 3つのベースラインのサマリーCSVを読み込む
    baselines = ['max_snr', 'nearest', 'random']
    baseline_labels = ['Max-SNR\n(Greedy)', 'Nearest-BS\n(Distance)', 'Random\n(Lower Bound)']
    baseline_data = {}

    for baseline_name in baselines:
        summary_csv = baseline_dir / f'baseline_{baseline_name}_summary.csv'
        if not summary_csv.exists():
            print(f"⚠️  警告: {summary_csv} が見つかりません。スキップします。")
            continue

        df = pd.read_csv(summary_csv)
        baseline_data[baseline_name] = df.iloc[0].to_dict()
        print(f"✅ {baseline_name.upper()}: 読み込み完了")

    if len(baseline_data) == 0:
        print("❌ エラー: ベースラインデータが見つかりません。")
        return

    print()

    # グラフ作成（2行2列のサブプロット）
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Baseline Comparison: Musical Chairs Framework (BS Capacity = {bs_capacity})',
                 fontsize=16, fontweight='bold', y=0.995)

    # カラー設定
    colors = ['#2E86AB', '#A23B72', '#F18F01']  # Blue, Purple, Orange

    # (1) アウトエージ率
    ax1 = axes[0, 0]
    outage_rates = [baseline_data[b]['outage_rate'] * 100 for b in baselines if b in baseline_data]
    bars1 = ax1.bar(range(len(outage_rates)), outage_rates, color=colors[:len(outage_rates)], alpha=0.8, edgecolor='black')
    ax1.set_ylabel('Outage Rate (%)', fontsize=12, fontweight='bold')
    ax1.set_title('(a) Outage Rate', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(baseline_labels)))
    ax1.set_xticklabels([baseline_labels[i] for i in range(len(outage_rates))], fontsize=10)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    ax1.set_ylim(0, max(outage_rates) * 1.2)

    # 値をバーの上に表示
    for i, (bar, val) in enumerate(zip(bars1, outage_rates)):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # (2) 平均スループット
    ax2 = axes[0, 1]
    mean_throughputs = [baseline_data[b]['mean_throughput_mbps'] for b in baselines if b in baseline_data]
    bars2 = ax2.bar(range(len(mean_throughputs)), mean_throughputs, color=colors[:len(mean_throughputs)],
                    alpha=0.8, edgecolor='black')
    ax2.set_ylabel('Mean Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax2.set_title('(b) Mean Throughput', fontsize=13, fontweight='bold')
    ax2.set_xticks(range(len(baseline_labels)))
    ax2.set_xticklabels([baseline_labels[i] for i in range(len(mean_throughputs))], fontsize=10)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    ax2.set_ylim(0, max(mean_throughputs) * 1.2)

    # 値をバーの上に表示
    for i, (bar, val) in enumerate(zip(bars2, mean_throughputs)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # (3) P05スループット
    ax3 = axes[1, 0]
    p05_throughputs = [baseline_data[b]['p05_throughput_mbps'] for b in baselines if b in baseline_data]
    bars3 = ax3.bar(range(len(p05_throughputs)), p05_throughputs, color=colors[:len(p05_throughputs)],
                    alpha=0.8, edgecolor='black')
    ax3.set_ylabel('P05 Throughput (Mbps)', fontsize=12, fontweight='bold')
    ax3.set_title('(c) P05 Throughput (5th Percentile)', fontsize=13, fontweight='bold')
    ax3.set_xticks(range(len(baseline_labels)))
    ax3.set_xticklabels([baseline_labels[i] for i in range(len(p05_throughputs))], fontsize=10)
    ax3.grid(axis='y', alpha=0.3, linestyle='--')

    # 値をバーの上に表示
    for i, (bar, val) in enumerate(zip(bars3, p05_throughputs)):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # (4) BS負荷統計
    ax4 = axes[1, 1]
    bs_load_means = [baseline_data[b]['bs_load_mean'] for b in baselines if b in baseline_data]
    bs_load_maxs = [baseline_data[b]['bs_load_max'] for b in baselines if b in baseline_data]

    x = np.arange(len(baselines))
    width = 0.35
    bars4_mean = ax4.bar(x - width/2, bs_load_means, width, label='Mean', color='#6A994E', alpha=0.8, edgecolor='black')
    bars4_max = ax4.bar(x + width/2, bs_load_maxs, width, label='Max', color='#BC4749', alpha=0.8, edgecolor='black')

    ax4.set_ylabel('BS Load (# of vehicles)', fontsize=12, fontweight='bold')
    ax4.set_title('(d) BS Load Distribution', fontsize=13, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels([baseline_labels[i] for i in range(len(baselines))], fontsize=10)
    ax4.legend(loc='upper right', fontsize=10)
    ax4.grid(axis='y', alpha=0.3, linestyle='--')
    ax4.set_ylim(0, max(bs_load_maxs) * 1.2)

    # 定員ラインを追加
    ax4.axhline(y=bs_capacity, color='red', linestyle='--', linewidth=2, label=f'Capacity ({bs_capacity})')
    ax4.legend(loc='upper right', fontsize=10)

    # 値をバーの上に表示
    for bar in bars4_mean:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=9)
    for bar in bars4_max:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ グラフ保存完了: {output_png}")
    print()

    # 統計情報を表示
    print("【統計情報】")
    for i, baseline_name in enumerate(baselines):
        if baseline_name not in baseline_data:
            continue
        data = baseline_data[baseline_name]
        print(f"\n{baseline_labels[i].replace(chr(10), ' ')}:")
        print(f"  - アウトエージ率: {data['outage_rate']*100:.2f}%")
        print(f"  - 平均スループット: {data['mean_throughput_mbps']:.2f} Mbps")
        print(f"  - P05スループット: {data['p05_throughput_mbps']:.2f} Mbps")
        print(f"  - BS負荷（平均/最大）: {data['bs_load_mean']:.1f} / {int(data['bs_load_max'])}")

    print("\n" + "=" * 80)
    print("完了")
    print("=" * 80)

    plt.close(fig)


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
        elif sys.argv[1] == "chairgame":
            plot_baselines_chairgame_comparison()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python plots.py [network|baseline|final|chairgame]")
    else:
        print("Usage: python plots.py [network|baseline|final|chairgame]")
