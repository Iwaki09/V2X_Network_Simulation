#!/usr/bin/env python3
"""
ベースライン手法（椅子取りゲーム）詳細可視化モジュール

論文用の詳細な比較プロットを生成：
- Plot A: Outage Rate（棒グラフ）
- Plot B: Throughput CDF（0含む）
- Plot C: BS負荷分布（箱ひげ図）
- Plot D: Nearest距離 vs 品質（散布図）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def load_and_merge_baseline_data(
    baseline_assignment_csv: Path,
    theoretical_csv: Path,
    eval_throughput_col: str = 'throughput_mbps_mcs'
) -> pd.DataFrame:
    """
    baseline_assignment.csv と theoretical_network_results.csv を結合し、
    真値スループットを付与

    Args:
        baseline_assignment_csv: ベースライン割当結果CSV
        theoretical_csv: 理論値ネットワーク結果CSV
        eval_throughput_col: 評価用スループット列名

    Returns:
        結合されたDataFrame（truth_throughput列を含む）
    """
    print(f"[Data Merge] Loading baseline assignment: {baseline_assignment_csv}")
    assignment_df = pd.read_csv(baseline_assignment_csv)

    print(f"[Data Merge] Loading theoretical results: {theoretical_csv}")
    theo_df = pd.read_csv(theoretical_csv)

    # V2Iリンクのみ抽出
    v2i_df = theo_df[theo_df['link_type'] == 'V2I'].copy()

    print(f"[Data Merge] Assignment records: {len(assignment_df)}")
    print(f"[Data Merge] V2I links: {len(v2i_df)}")

    # acceptedの車両について、truth throughputを取得
    # (timestamp, vehicle_id, assigned_bs_id) を (timestamp, rx_id, tx_id) とマッチ
    merged_df = assignment_df.merge(
        v2i_df[['timestamp', 'rx_id', 'tx_id', eval_throughput_col, 'snr_db', 'is_line_of_sight']],
        left_on=['timestamp', 'vehicle_id', 'assigned_bs_id'],
        right_on=['timestamp', 'rx_id', 'tx_id'],
        how='left'
    )

    # 列名を整理
    merged_df = merged_df.drop(columns=['rx_id', 'tx_id'], errors='ignore')
    merged_df = merged_df.rename(columns={eval_throughput_col: 'truth_throughput'})

    # rejectedはtruth_throughput=0
    merged_df['truth_throughput'] = merged_df['truth_throughput'].fillna(0.0)

    print(f"[Data Merge] Merged records: {len(merged_df)}")
    print(f"[Data Merge] Accepted: {(merged_df['accepted'] == 1).sum()}")
    print(f"[Data Merge] Rejected (outage): {(merged_df['accepted'] == 0).sum()}")

    return merged_df


def plot_outage_rate_comparison(
    baseline_dirs: Dict[str, Path],
    output_png: Path,
    baseline_labels: Optional[Dict[str, str]] = None
):
    """
    Plot A: ベースライン別のOutage Rate（棒グラフ）

    Args:
        baseline_dirs: {baseline_name: baseline_dir} の辞書
        output_png: 出力PNGファイルパス
        baseline_labels: ベースライン表示名の辞書（オプション）
    """
    if baseline_labels is None:
        baseline_labels = {
            'max_snr': 'Max-SNR\n(Greedy)',
            'nearest': 'Nearest-BS\n(Distance)',
            'random': 'Random\n(Lower Bound)'
        }

    print("\n" + "=" * 80)
    print("Plot A: Outage Rate Comparison")
    print("=" * 80)

    # データ読み込み
    outage_data = {}
    for baseline_name, baseline_dir in baseline_dirs.items():
        summary_csv = baseline_dir / f'baseline_{baseline_name}_summary.csv'
        if not summary_csv.exists():
            print(f"⚠️  Warning: {summary_csv} not found, skipping {baseline_name}")
            continue

        df = pd.read_csv(summary_csv)
        outage_data[baseline_name] = df.iloc[0]['outage_rate'] * 100  # %変換
        print(f"✅ {baseline_name}: {outage_data[baseline_name]:.2f}%")

    if len(outage_data) == 0:
        print("❌ Error: No baseline data found")
        return

    # プロット
    fig, ax = plt.subplots(figsize=(10, 6))

    baseline_names = list(outage_data.keys())
    outage_rates = list(outage_data.values())
    labels = [baseline_labels.get(b, b) for b in baseline_names]

    colors = ['#2E86AB', '#A23B72', '#F18F01']  # Blue, Purple, Orange
    bars = ax.bar(range(len(outage_rates)), outage_rates,
                  color=colors[:len(outage_rates)], alpha=0.8, edgecolor='black', linewidth=1.5)

    ax.set_ylabel('Outage Rate (%)', fontsize=14, fontweight='bold')
    ax.set_title('(a) Outage Rate Comparison\nMusical Chairs Framework',
                 fontsize=15, fontweight='bold', pad=15)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=12)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, max(outage_rates) * 1.15)

    # 値をバーの上に表示
    for bar, val in zip(bars, outage_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def plot_throughput_cdf_comparison(
    baseline_dirs: Dict[str, Path],
    theoretical_csv: Path,
    output_png: Path,
    eval_throughput_col: str = 'throughput_mbps_mcs',
    xmax_mbps: Optional[float] = None,
    baseline_labels: Optional[Dict[str, str]] = None
):
    """
    Plot B: ベースライン別のThroughput CDF（0含む）

    Args:
        baseline_dirs: {baseline_name: baseline_dir} の辞書
        theoretical_csv: 理論値ネットワーク結果CSV
        output_png: 出力PNGファイルパス
        eval_throughput_col: 評価用スループット列名
        xmax_mbps: CDF x軸の上限（Mbps）
        baseline_labels: ベースライン表示名の辞書（オプション）
    """
    if baseline_labels is None:
        baseline_labels = {
            'max_snr': 'Max-SNR (Greedy)',
            'nearest': 'Nearest-BS (Distance)',
            'random': 'Random (Lower Bound)'
        }

    print("\n" + "=" * 80)
    print("Plot B: Throughput CDF Comparison")
    print("=" * 80)

    # データ読み込み＆結合
    throughput_data = {}
    for baseline_name, baseline_dir in baseline_dirs.items():
        assignment_csv = baseline_dir / f'baseline_{baseline_name}_assignment.csv'
        if not assignment_csv.exists():
            print(f"⚠️  Warning: {assignment_csv} not found, skipping {baseline_name}")
            continue

        merged_df = load_and_merge_baseline_data(assignment_csv, theoretical_csv, eval_throughput_col)
        throughput_data[baseline_name] = merged_df['truth_throughput'].values

        # 統計情報
        n_total = len(merged_df)
        n_zero = (merged_df['truth_throughput'] == 0).sum()
        mean_tp = merged_df['truth_throughput'].mean()
        p05_tp = np.percentile(merged_df['truth_throughput'], 5)
        p50_tp = np.percentile(merged_df['truth_throughput'], 50)

        print(f"✅ {baseline_name}:")
        print(f"   Total: {n_total}, Zero (outage): {n_zero} ({n_zero/n_total*100:.1f}%)")
        print(f"   Mean: {mean_tp:.2f} Mbps, P05: {p05_tp:.2f} Mbps, P50: {p50_tp:.2f} Mbps")

    if len(throughput_data) == 0:
        print("❌ Error: No baseline data found")
        return

    # プロット
    fig, ax = plt.subplots(figsize=(10, 7))

    colors = {'max_snr': '#2E86AB', 'nearest': '#A23B72', 'random': '#F18F01'}
    linestyles = {'max_snr': '-', 'nearest': '--', 'random': '-.'}

    for baseline_name, throughputs in throughput_data.items():
        # CDFを計算
        sorted_tp = np.sort(throughputs)
        cdf = np.arange(1, len(sorted_tp) + 1) / len(sorted_tp)

        label = baseline_labels.get(baseline_name, baseline_name)
        ax.plot(sorted_tp, cdf,
                color=colors.get(baseline_name, 'gray'),
                linestyle=linestyles.get(baseline_name, '-'),
                linewidth=2.5, label=label, alpha=0.9)

    ax.set_xlabel('Throughput (Mbps)', fontsize=14, fontweight='bold')
    ax.set_ylabel('CDF', fontsize=14, fontweight='bold')
    ax.set_title('(b) Throughput CDF Comparison (including outage = 0 Mbps)\nMusical Chairs Framework',
                 fontsize=15, fontweight='bold', pad=15)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='lower right', fontsize=12, framealpha=0.9)

    if xmax_mbps:
        ax.set_xlim(0, xmax_mbps)

    ax.set_ylim(0, 1.05)

    # P05とP50の参照線
    ax.axhline(y=0.05, color='red', linestyle=':', linewidth=1, alpha=0.5, label='P05')
    ax.axhline(y=0.50, color='green', linestyle=':', linewidth=1, alpha=0.5, label='P50')

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def plot_bs_load_distribution(
    baseline_dirs: Dict[str, Path],
    output_png: Path,
    bs_capacity: Optional[int] = None,
    baseline_labels: Optional[Dict[str, str]] = None
):
    """
    Plot C: BS負荷分布（箱ひげ図）

    Args:
        baseline_dirs: {baseline_name: baseline_dir} の辞書
        output_png: 出力PNGファイルパス
        bs_capacity: 基地局定員（参照線用）
        baseline_labels: ベースライン表示名の辞書（オプション）
    """
    if baseline_labels is None:
        baseline_labels = {
            'max_snr': 'Max-SNR',
            'nearest': 'Nearest-BS',
            'random': 'Random'
        }

    print("\n" + "=" * 80)
    print("Plot C: BS Load Distribution")
    print("=" * 80)

    # データ読み込み
    load_data = {}
    for baseline_name, baseline_dir in baseline_dirs.items():
        assignment_csv = baseline_dir / f'baseline_{baseline_name}_assignment.csv'
        if not assignment_csv.exists():
            print(f"⚠️  Warning: {assignment_csv} not found, skipping {baseline_name}")
            continue

        df = pd.read_csv(assignment_csv)

        # 各timestampでのBS別接続台数を集計
        accepted_df = df[df['accepted'] == 1]
        bs_loads = accepted_df.groupby(['timestamp', 'assigned_bs_id']).size().values

        load_data[baseline_name] = bs_loads

        print(f"✅ {baseline_name}:")
        print(f"   Mean load: {bs_loads.mean():.2f}, Std: {bs_loads.std():.2f}")
        print(f"   Min: {bs_loads.min()}, Max: {bs_loads.max()}")

    if len(load_data) == 0:
        print("❌ Error: No baseline data found")
        return

    # プロット
    fig, ax = plt.subplots(figsize=(10, 7))

    baseline_names = list(load_data.keys())
    labels = [baseline_labels.get(b, b) for b in baseline_names]
    data = [load_data[b] for b in baseline_names]

    colors = ['#2E86AB', '#A23B72', '#F18F01']

    bp = ax.boxplot(data, labels=labels, patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))

    # 各箱に色を付ける
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)

    ax.set_ylabel('BS Load (# of vehicles per timestamp)', fontsize=14, fontweight='bold')
    ax.set_title('(c) BS Load Distribution\nMusical Chairs Framework',
                 fontsize=15, fontweight='bold', pad=15)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_xticklabels(labels, fontsize=12)

    # 定員ラインを追加
    if bs_capacity:
        ax.axhline(y=bs_capacity, color='red', linestyle='--', linewidth=2,
                   label=f'BS Capacity ({bs_capacity})', alpha=0.8)
        ax.legend(loc='upper right', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def plot_nearest_distance_vs_quality(
    nearest_assignment_csv: Path,
    theoretical_csv: Path,
    fcd_path: Path,
    scenario_config,
    output_png: Path,
    eval_throughput_col: str = 'throughput_mbps_mcs'
):
    """
    Plot D: Nearest距離 vs 品質（散布図）

    Args:
        nearest_assignment_csv: Nearestベースライン割当結果CSV
        theoretical_csv: 理論値ネットワーク結果CSV
        fcd_path: FCD XMLファイルパス（座標取得用）
        scenario_config: シナリオ設定（座標変換用）
        output_png: 出力PNGファイルパス
        eval_throughput_col: 評価用スループット列名
    """
    print("\n" + "=" * 80)
    print("Plot D: Nearest Distance vs Quality")
    print("=" * 80)

    # データ読み込み＆結合
    merged_df = load_and_merge_baseline_data(nearest_assignment_csv, theoretical_csv, eval_throughput_col)

    # acceptedのみ抽出
    accepted_df = merged_df[merged_df['accepted'] == 1].copy()
    print(f"Accepted links for Nearest: {len(accepted_df)}")

    # 距離を計算（baselines_chairgame.pyと同じロジック）
    from ..parsers.fcd_parser import parse_fcd_xml

    # FCD解析
    timestep_data_list = parse_fcd_xml(str(fcd_path))

    # 車両位置をDataFrameに変換
    records = []
    for timestep_data in timestep_data_list:
        for vehicle in timestep_data.vehicles:
            x_rt, y_rt = scenario_config.transform_coordinates(vehicle.x, vehicle.y)
            records.append({
                'timestamp': timestep_data.timestamp,
                'vehicle_id': vehicle.vehicle_id,
                'x': x_rt,
                'y': y_rt,
                'z': vehicle.z
            })
    pos_df = pd.DataFrame(records)

    # BS座標
    bs_position = scenario_config.base_station.position
    bs_x, bs_y, bs_z = bs_position

    # acceptedデータに座標を結合
    accepted_with_pos = accepted_df.merge(
        pos_df,
        on=['timestamp', 'vehicle_id'],
        how='left'
    )

    # 3D距離を計算
    accepted_with_pos['distance_3d'] = np.sqrt(
        (accepted_with_pos['x'] - bs_x) ** 2 +
        (accepted_with_pos['y'] - bs_y) ** 2 +
        (accepted_with_pos['z'] - bs_z) ** 2
    )

    print(f"Distance range: {accepted_with_pos['distance_3d'].min():.2f} - {accepted_with_pos['distance_3d'].max():.2f} m")

    # プロット（2つのサブプロット：距離 vs SNR、距離 vs Throughput）
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # LOS/NLOS別に色分け
    los_mask = accepted_with_pos['is_line_of_sight'] == True
    nlos_mask = ~los_mask

    # (1) 距離 vs SNR
    ax1 = axes[0]
    ax1.scatter(accepted_with_pos.loc[los_mask, 'distance_3d'],
               accepted_with_pos.loc[los_mask, 'snr_db'],
               c='#2E86AB', alpha=0.6, s=30, label='LOS', edgecolors='black', linewidth=0.5)
    ax1.scatter(accepted_with_pos.loc[nlos_mask, 'distance_3d'],
               accepted_with_pos.loc[nlos_mask, 'snr_db'],
               c='#F18F01', alpha=0.6, s=30, label='NLOS', marker='x', linewidths=2)

    ax1.set_xlabel('Distance to BS (m)', fontsize=13, fontweight='bold')
    ax1.set_ylabel('SNR (dB)', fontsize=13, fontweight='bold')
    ax1.set_title('(d-1) Nearest-BS: Distance vs SNR\n(mmWave: "Near ≠ Good")',
                  fontsize=14, fontweight='bold', pad=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best', fontsize=11)

    # (2) 距離 vs Throughput
    ax2 = axes[1]
    ax2.scatter(accepted_with_pos.loc[los_mask, 'distance_3d'],
               accepted_with_pos.loc[los_mask, 'truth_throughput'],
               c='#2E86AB', alpha=0.6, s=30, label='LOS', edgecolors='black', linewidth=0.5)
    ax2.scatter(accepted_with_pos.loc[nlos_mask, 'distance_3d'],
               accepted_with_pos.loc[nlos_mask, 'truth_throughput'],
               c='#F18F01', alpha=0.6, s=30, label='NLOS', marker='x', linewidths=2)

    ax2.set_xlabel('Distance to BS (m)', fontsize=13, fontweight='bold')
    ax2.set_ylabel('Throughput (Mbps)', fontsize=13, fontweight='bold')
    ax2.set_title('(d-2) Nearest-BS: Distance vs Throughput\n(NLOS causes low throughput even at short distance)',
                  fontsize=14, fontweight='bold', pad=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='best', fontsize=11)

    plt.tight_layout()
    plt.savefig(output_png, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_png}")
    plt.close(fig)


def generate_all_baseline_plots(
    baseline_dir: Path,
    theoretical_csv: Path,
    fcd_path: Path,
    scenario_config,
    output_dir: Path,
    eval_throughput_col: str = 'throughput_mbps_mcs',
    bs_capacity: Optional[int] = None,
    xmax_mbps: Optional[float] = None
):
    """
    全てのベースライン詳細プロットを生成

    Args:
        baseline_dir: ベースライン結果ディレクトリ
        theoretical_csv: 理論値ネットワーク結果CSV
        fcd_path: FCD XMLファイルパス
        scenario_config: シナリオ設定
        output_dir: 出力ディレクトリ
        eval_throughput_col: 評価用スループット列名
        bs_capacity: 基地局定員
        xmax_mbps: CDF x軸の上限
    """
    print("\n" + "=" * 80)
    print("Generating All Baseline Detail Plots")
    print("=" * 80)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_dir = Path(baseline_dir)

    # ベースラインディレクトリの辞書を作成
    baseline_dirs = {}
    for baseline_name in ['max_snr', 'nearest', 'random']:
        # 同じディレクトリに3つのベースラインが含まれている
        baseline_dirs[baseline_name] = baseline_dir

    # Plot A: Outage Rate
    plot_outage_rate_comparison(
        baseline_dirs=baseline_dirs,
        output_png=output_dir / 'outage_rate_by_baseline.png'
    )

    # Plot B: Throughput CDF
    plot_throughput_cdf_comparison(
        baseline_dirs=baseline_dirs,
        theoretical_csv=theoretical_csv,
        output_png=output_dir / 'throughput_cdf_by_baseline.png',
        eval_throughput_col=eval_throughput_col,
        xmax_mbps=xmax_mbps
    )

    # Plot C: BS Load Distribution
    plot_bs_load_distribution(
        baseline_dirs=baseline_dirs,
        output_png=output_dir / 'bs_load_distribution.png',
        bs_capacity=bs_capacity
    )

    # Plot D: Nearest Distance vs Quality
    nearest_assignment_csv = baseline_dir / 'baseline_nearest_assignment.csv'
    if nearest_assignment_csv.exists():
        plot_nearest_distance_vs_quality(
            nearest_assignment_csv=nearest_assignment_csv,
            theoretical_csv=theoretical_csv,
            fcd_path=fcd_path,
            scenario_config=scenario_config,
            output_png=output_dir / 'nearest_distance_vs_quality.png',
            eval_throughput_col=eval_throughput_col
        )
    else:
        print(f"⚠️  Warning: {nearest_assignment_csv} not found, skipping Plot D")

    print("\n" + "=" * 80)
    print("✅ All baseline detail plots generated successfully")
    print("=" * 80)
