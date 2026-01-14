#!/usr/bin/env python3
"""
最小追加分析スクリプト（論文締めくくり用）

theoretical_network_results.csv（Default/Corner）を読み込み、以下の3点を分析:
A) 距離CDF（tx-rx距離の累積分布）
B) SNR CDF（snr_dbの累積分布）
C) MCS分布（特にNLOSでのmcs_index分布）

距離算出:
- FCDファイルから車両位置を取得
- V2I: BS位置（固定）と車両位置で距離計算
- V2V: 車両A位置と車両B位置で距離計算

条件別フィルタ: LOS/NLOS、prop_mode=D/K

使用方法:
    python scripts/analyze_minimal_additional.py \\
        --input-default path/to/default/theoretical_network_results.csv \\
        --input-corner path/to/corner/theoretical_network_results.csv \\
        --outdir path/to/output
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import math

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.parsers.fcd_parser import parse_fcd_xml, get_vehicle_positions
from src.scenarios.default import DefaultScenarioConfig
from src.scenarios.corner_intersection import CornerIntersectionConfig

# 日本語フォント設定
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 定数
DEFAULT_RMIN_MBPS = 50.0
MIN_SAMPLE_COUNT = 5  # 図を出すための最小サンプル数


def get_scenario_config(scenario_name: str):
    """シナリオ名に基づいて設定を取得"""
    if scenario_name == "default":
        return DefaultScenarioConfig()
    elif scenario_name == "corner_intersection":
        return CornerIntersectionConfig()
    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")


def calculate_distance_3d(pos1: List[float], pos2: List[float]) -> float:
    """3次元ユークリッド距離を計算"""
    return math.sqrt(
        (pos1[0] - pos2[0])**2 +
        (pos1[1] - pos2[1])**2 +
        (pos1[2] - pos2[2])**2
    )


def load_vehicle_positions_from_fcd(fcd_path: Path, scenario_config) -> Dict[float, Dict[str, List[float]]]:
    """
    FCDファイルから車両位置を読み込み、timestamp別に整理

    Returns:
        {timestamp: {vehicle_id: [x, y, z], ...}, ...}
    """
    print(f"  FCDファイル読み込み: {fcd_path}")

    if not fcd_path.exists():
        raise FileNotFoundError(f"FCDファイルが見つかりません: {fcd_path}")

    timestep_data_list = parse_fcd_xml(str(fcd_path))

    # timestamp別に車両位置を整理
    positions_by_time = {}
    for timestep_data in timestep_data_list:
        timestamp = timestep_data.timestamp
        vehicle_positions = {}

        for vehicle in timestep_data.vehicles:
            # SUMO座標をシナリオ座標に変換
            x_transformed, y_transformed = scenario_config.transform_coordinates(
                vehicle.x, vehicle.y
            )
            vehicle_positions[vehicle.vehicle_id] = [
                x_transformed,
                y_transformed,
                vehicle.z
            ]

        positions_by_time[timestamp] = vehicle_positions

    print(f"    タイムステップ数: {len(positions_by_time)}")
    return positions_by_time


def add_distance_column(
    df: pd.DataFrame,
    positions_by_time: Dict[float, Dict[str, List[float]]],
    bs_position: List[float]
) -> pd.DataFrame:
    """
    theoretical_network_results.csvに距離列を追加

    Args:
        df: theoretical_network_results.csv のDataFrame
        positions_by_time: FCDから読み込んだ車両位置 {timestamp: {vehicle_id: [x,y,z]}}
        bs_position: 基地局位置 [x, y, z]

    Returns:
        距離列が追加されたDataFrame
    """
    distances = []
    skipped_count = 0

    for idx, row in df.iterrows():
        timestamp = row['timestamp']
        link_type = row['link_type']
        tx_id = row['tx_id']
        rx_id = row['rx_id']

        # timestampの車両位置を取得
        if timestamp not in positions_by_time:
            distances.append(np.nan)
            skipped_count += 1
            continue

        vehicle_positions = positions_by_time[timestamp]

        try:
            if link_type == 'V2I':
                # V2I: BS-車両間の距離
                # tx_id = BS_*, rx_id = vehicle_*
                vehicle_id = rx_id
                if vehicle_id not in vehicle_positions:
                    distances.append(np.nan)
                    skipped_count += 1
                    continue

                vehicle_pos = vehicle_positions[vehicle_id]
                distance = calculate_distance_3d(bs_position, vehicle_pos)
                distances.append(distance)

            elif link_type == 'V2V':
                # V2V: 車両間の距離
                # tx_id = vehicle_*, rx_id = vehicle_*
                if tx_id not in vehicle_positions or rx_id not in vehicle_positions:
                    distances.append(np.nan)
                    skipped_count += 1
                    continue

                tx_pos = vehicle_positions[tx_id]
                rx_pos = vehicle_positions[rx_id]
                distance = calculate_distance_3d(tx_pos, rx_pos)
                distances.append(distance)

            else:
                distances.append(np.nan)
                skipped_count += 1

        except Exception as e:
            print(f"    警告: 距離計算エラー (row {idx}): {e}")
            distances.append(np.nan)
            skipped_count += 1

    df['distance_m'] = distances

    if skipped_count > 0:
        print(f"    警告: {skipped_count}/{len(df)} 行で距離計算をスキップ（データ不足）")

    # NaNを除外した統計
    valid_distances = df['distance_m'].dropna()
    print(f"    有効な距離データ: {len(valid_distances)}/{len(df)} 行")
    if len(valid_distances) > 0:
        print(f"    距離範囲: {valid_distances.min():.2f}m - {valid_distances.max():.2f}m")

    return df


def plot_cdf(ax, data: np.ndarray, label: str, color: str, linestyle: str = '-'):
    """CDFをプロット"""
    if len(data) == 0:
        return
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.plot(sorted_data, cdf, label=label, color=color, linestyle=linestyle, linewidth=2)


def calculate_statistics(data: pd.Series, rmin_mbps: Optional[float] = None) -> dict:
    """統計量を計算"""
    stats = {
        'count': len(data),
        'mean': data.mean() if len(data) > 0 else np.nan,
        'median': data.median() if len(data) > 0 else np.nan,
        'p05': data.quantile(0.05) if len(data) > 0 else np.nan,
        'p50': data.quantile(0.50) if len(data) > 0 else np.nan,
        'p95': data.quantile(0.95) if len(data) > 0 else np.nan,
    }

    # アウテージ率（オプション）
    if rmin_mbps is not None and len(data) > 0:
        stats['outage_rate'] = (data < rmin_mbps).mean()

    return stats


def get_condition_filters():
    """
    条件別フィルタ関数のリストを返す

    Returns:
        List[(条件名, フィルタ関数)]
    """
    return [
        ('All', lambda df: df),
        ('LOS', lambda df: df[df['is_line_of_sight'] == True]),
        ('NLOS', lambda df: df[df['is_line_of_sight'] == False]),
        ('prop_mode=D', lambda df: df[df['prop_mode'] == 'D']),
        ('prop_mode=K', lambda df: df[df['prop_mode'] == 'K']),
        ('LOS & D', lambda df: df[(df['is_line_of_sight'] == True) & (df['prop_mode'] == 'D')]),
        ('LOS & K', lambda df: df[(df['is_line_of_sight'] == True) & (df['prop_mode'] == 'K')]),
        ('NLOS & D', lambda df: df[(df['is_line_of_sight'] == False) & (df['prop_mode'] == 'D')]),
        ('NLOS & K', lambda df: df[(df['is_line_of_sight'] == False) & (df['prop_mode'] == 'K')]),
    ]


def generate_distance_cdf(
    df_default: pd.DataFrame,
    df_corner: pd.DataFrame,
    output_dir: Path
) -> None:
    """
    A) 距離CDF（Default vs Corner）

    - 図A1: All の距離CDF
    - 図A2: LOS と NLOS の距離CDF
    """
    print("\n[A] 距離CDF生成")

    # 図A1: All の距離CDF
    fig, ax = plt.subplots(figsize=(10, 6))

    dist_default = df_default['distance_m'].dropna()
    dist_corner = df_corner['distance_m'].dropna()

    if len(dist_default) > 0:
        plot_cdf(ax, dist_default.values, f'Default (n={len(dist_default)})', 'blue', '-')
    if len(dist_corner) > 0:
        plot_cdf(ax, dist_corner.values, f'Corner (n={len(dist_corner)})', 'red', '--')

    ax.set_xlabel('Distance (m)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('Distance CDF: Default vs Corner (All Links)', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    output_path = output_dir / 'figA1_distance_cdf_all.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図A1保存: {output_path}")

    # 図A2: LOS/NLOS の距離CDF
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # LOS
    ax = axes[0]
    dist_default_los = df_default[df_default['is_line_of_sight'] == True]['distance_m'].dropna()
    dist_corner_los = df_corner[df_corner['is_line_of_sight'] == True]['distance_m'].dropna()

    if len(dist_default_los) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, dist_default_los.values, f'Default (n={len(dist_default_los)})', 'blue', '-')
    if len(dist_corner_los) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, dist_corner_los.values, f'Corner (n={len(dist_corner_los)})', 'red', '--')

    ax.set_xlabel('Distance (m)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('LOS: Distance CDF', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    # NLOS
    ax = axes[1]
    dist_default_nlos = df_default[df_default['is_line_of_sight'] == False]['distance_m'].dropna()
    dist_corner_nlos = df_corner[df_corner['is_line_of_sight'] == False]['distance_m'].dropna()

    if len(dist_default_nlos) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, dist_default_nlos.values, f'Default (n={len(dist_default_nlos)})', 'blue', '-')
    if len(dist_corner_nlos) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, dist_corner_nlos.values, f'Corner (n={len(dist_corner_nlos)})', 'red', '--')

    ax.set_xlabel('Distance (m)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('NLOS: Distance CDF', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    output_path = output_dir / 'figA2_distance_cdf_los_nlos.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図A2保存: {output_path}")


def generate_snr_cdf(
    df_default: pd.DataFrame,
    df_corner: pd.DataFrame,
    output_dir: Path
) -> None:
    """
    B) SNR CDF（Default vs Corner）

    - 図B1: All の snr_db CDF
    - 図B2: LOS と NLOS の snr_db CDF
    """
    print("\n[B] SNR CDF生成")

    # 図B1: All の snr_db CDF
    fig, ax = plt.subplots(figsize=(10, 6))

    snr_default = df_default['snr_db'].dropna()
    snr_corner = df_corner['snr_db'].dropna()

    if len(snr_default) > 0:
        plot_cdf(ax, snr_default.values, f'Default (n={len(snr_default)})', 'blue', '-')
    if len(snr_corner) > 0:
        plot_cdf(ax, snr_corner.values, f'Corner (n={len(snr_corner)})', 'red', '--')

    ax.set_xlabel('SNR (dB)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('SNR CDF: Default vs Corner (All Links)', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    output_path = output_dir / 'figB1_snr_cdf_all.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図B1保存: {output_path}")

    # 図B2: LOS/NLOS の snr_db CDF
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # LOS
    ax = axes[0]
    snr_default_los = df_default[df_default['is_line_of_sight'] == True]['snr_db'].dropna()
    snr_corner_los = df_corner[df_corner['is_line_of_sight'] == True]['snr_db'].dropna()

    if len(snr_default_los) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, snr_default_los.values, f'Default (n={len(snr_default_los)})', 'blue', '-')
    if len(snr_corner_los) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, snr_corner_los.values, f'Corner (n={len(snr_corner_los)})', 'red', '--')

    ax.set_xlabel('SNR (dB)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('LOS: SNR CDF', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    # NLOS
    ax = axes[1]
    snr_default_nlos = df_default[df_default['is_line_of_sight'] == False]['snr_db'].dropna()
    snr_corner_nlos = df_corner[df_corner['is_line_of_sight'] == False]['snr_db'].dropna()

    if len(snr_default_nlos) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, snr_default_nlos.values, f'Default (n={len(snr_default_nlos)})', 'blue', '-')
    if len(snr_corner_nlos) >= MIN_SAMPLE_COUNT:
        plot_cdf(ax, snr_corner_nlos.values, f'Corner (n={len(snr_corner_nlos)})', 'red', '--')

    ax.set_xlabel('SNR (dB)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('NLOS: SNR CDF', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    output_path = output_dir / 'figB2_snr_cdf_los_nlos.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図B2保存: {output_path}")


def generate_mcs_histogram(
    df_default: pd.DataFrame,
    df_corner: pd.DataFrame,
    output_dir: Path
) -> None:
    """
    C) MCS分布（Default vs Corner）

    - 図C1: NLOS の mcs_index ヒストグラム
    - 図C2: prop_mode別（D vs K）の mcs_index ヒストグラム
    """
    print("\n[C] MCS分布生成")

    # 図C1: NLOS の mcs_index ヒストグラム
    fig, ax = plt.subplots(figsize=(10, 6))

    mcs_default_nlos = df_default[df_default['is_line_of_sight'] == False]['mcs_index'].dropna()
    mcs_corner_nlos = df_corner[df_corner['is_line_of_sight'] == False]['mcs_index'].dropna()

    bins = np.arange(-0.5, 9, 1)  # MCS 0-7 + 余裕

    if len(mcs_default_nlos) >= MIN_SAMPLE_COUNT:
        ax.hist(mcs_default_nlos, bins=bins, alpha=0.6, label=f'Default NLOS (n={len(mcs_default_nlos)})',
                color='blue', edgecolor='black')
    if len(mcs_corner_nlos) >= MIN_SAMPLE_COUNT:
        ax.hist(mcs_corner_nlos, bins=bins, alpha=0.6, label=f'Corner NLOS (n={len(mcs_corner_nlos)})',
                color='red', edgecolor='black')

    ax.set_xlabel('MCS Index', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('MCS Index Distribution: NLOS Links (Default vs Corner)', fontsize=14)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_xticks(range(0, 8))

    plt.tight_layout()
    output_path = output_dir / 'figC1_mcs_histogram_nlos.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図C1保存: {output_path}")

    # 図C2: prop_mode別（D vs K）の mcs_index ヒストグラム（Cornerのみ）
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Corner の D/K
    mcs_corner_d = df_corner[df_corner['prop_mode'] == 'D']['mcs_index'].dropna()
    mcs_corner_k = df_corner[df_corner['prop_mode'] == 'K']['mcs_index'].dropna()

    # prop_mode=D
    ax = axes[0]
    if len(mcs_corner_d) >= MIN_SAMPLE_COUNT:
        ax.hist(mcs_corner_d, bins=bins, alpha=0.7, label=f'Corner D (n={len(mcs_corner_d)})',
                color='green', edgecolor='black')
    ax.set_xlabel('MCS Index', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('prop_mode=D: MCS Distribution (Corner)', fontsize=14)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_xticks(range(0, 8))

    # prop_mode=K
    ax = axes[1]
    if len(mcs_corner_k) >= MIN_SAMPLE_COUNT:
        ax.hist(mcs_corner_k, bins=bins, alpha=0.7, label=f'Corner K (n={len(mcs_corner_k)})',
                color='orange', edgecolor='black')
    else:
        ax.text(0.5, 0.5, f'サンプル不足 (n={len(mcs_corner_k)} < {MIN_SAMPLE_COUNT})',
                ha='center', va='center', transform=ax.transAxes, fontsize=12)
    ax.set_xlabel('MCS Index', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)
    ax.set_title('prop_mode=K: MCS Distribution (Corner)', fontsize=14)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_xticks(range(0, 8))

    plt.tight_layout()
    output_path = output_dir / 'figC2_mcs_histogram_prop_mode.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"  ✅ 図C2保存: {output_path}")


def generate_summary_csv(
    df: pd.DataFrame,
    scenario_name: str,
    output_path: Path,
    rmin_mbps: float
) -> pd.DataFrame:
    """
    条件別の統計量を集計してCSVに出力
    """
    results = []

    condition_filters = get_condition_filters()

    for cond_name, filter_func in condition_filters:
        filtered_df = filter_func(df)
        if len(filtered_df) == 0:
            continue

        # 距離統計
        distance_data = filtered_df['distance_m'].dropna()
        distance_stats = calculate_statistics(distance_data) if len(distance_data) > 0 else {}

        # SNR統計
        snr_data = filtered_df['snr_db'].dropna()
        snr_stats = calculate_statistics(snr_data) if len(snr_data) > 0 else {}

        # MCS統計
        mcs_data = filtered_df['mcs_index'].dropna()
        mcs_stats = {}
        if len(mcs_data) > 0:
            mcs_stats = {
                'count': len(mcs_data),
                'mode': mcs_data.mode()[0] if len(mcs_data.mode()) > 0 else np.nan,
                'p50': mcs_data.quantile(0.50),
                'p95': mcs_data.quantile(0.95),
            }

        # スループット統計（Shannon/MCS）
        shannon_data = filtered_df['theoretical_throughput_mbps'].dropna()
        mcs_throughput_data = filtered_df['throughput_mbps_mcs'].dropna()
        shannon_stats = calculate_statistics(shannon_data, rmin_mbps) if len(shannon_data) > 0 else {}
        mcs_throughput_stats = calculate_statistics(mcs_throughput_data, rmin_mbps) if len(mcs_throughput_data) > 0 else {}

        results.append({
            'scenario': scenario_name,
            'condition': cond_name,
            'count': len(filtered_df),
            # 距離
            'distance_mean_m': distance_stats.get('mean', np.nan),
            'distance_p05_m': distance_stats.get('p05', np.nan),
            'distance_median_m': distance_stats.get('median', np.nan),
            'distance_p95_m': distance_stats.get('p95', np.nan),
            # SNR
            'snr_db_mean': snr_stats.get('mean', np.nan),
            'snr_db_p05': snr_stats.get('p05', np.nan),
            'snr_db_median': snr_stats.get('median', np.nan),
            'snr_db_p95': snr_stats.get('p95', np.nan),
            # MCS
            'mcs_index_mode': mcs_stats.get('mode', np.nan),
            'mcs_index_p50': mcs_stats.get('p50', np.nan),
            'mcs_index_p95': mcs_stats.get('p95', np.nan),
            # スループット
            'mean_shannon_mbps': shannon_stats.get('mean', np.nan),
            'mean_mcs_mbps': mcs_throughput_stats.get('mean', np.nan),
            'mcs_shannon_ratio': (mcs_throughput_stats.get('mean', 0) / shannon_stats.get('mean', 1))
                                 if shannon_stats.get('mean', 0) > 0 else np.nan,
        })

    summary_df = pd.DataFrame(results)
    summary_df.to_csv(output_path, index=False)
    print(f"  ✅ 集計CSV保存: {output_path}")
    return summary_df


def generate_comparison_csv(
    summary_default: pd.DataFrame,
    summary_corner: pd.DataFrame,
    output_path: Path
) -> None:
    """
    Default vs Corner の比較CSV生成
    """
    print("\n[比較CSV生成]")

    # 条件名でマージ
    merged = pd.merge(
        summary_default,
        summary_corner,
        on='condition',
        suffixes=('_default', '_corner')
    )

    # 差分計算
    merged['distance_mean_diff_m'] = merged['distance_mean_m_corner'] - merged['distance_mean_m_default']
    merged['snr_db_mean_diff'] = merged['snr_db_mean_corner'] - merged['snr_db_mean_default']
    merged['mcs_index_mode_diff'] = merged['mcs_index_mode_corner'] - merged['mcs_index_mode_default']
    merged['mean_shannon_diff_mbps'] = merged['mean_shannon_mbps_corner'] - merged['mean_shannon_mbps_default']
    merged['mean_mcs_diff_mbps'] = merged['mean_mcs_mbps_corner'] - merged['mean_mcs_mbps_default']

    merged.to_csv(output_path, index=False)
    print(f"  ✅ 比較CSV保存: {output_path}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='最小追加分析: 距離CDF、SNR CDF、MCS分布',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--input-default',
        type=str,
        required=False,
        help='Default シナリオの theoretical_network_results.csv パス'
    )
    parser.add_argument(
        '--input-corner',
        type=str,
        required=False,
        help='Corner シナリオの theoretical_network_results.csv パス'
    )
    parser.add_argument(
        '--outdir',
        type=str,
        default=None,
        help='出力ディレクトリ（デフォルト: simulation/output/scenarios/default/analysis）'
    )
    parser.add_argument(
        '--rmin-mbps',
        type=float,
        default=DEFAULT_RMIN_MBPS,
        help=f'アウテージ判定閾値 (Mbps). デフォルト: {DEFAULT_RMIN_MBPS}'
    )
    parser.add_argument(
        '--link-type',
        type=str,
        default='all',
        choices=['all', 'v2i', 'v2v'],
        help='リンクタイプフィルタ（all, v2i, v2v）。デフォルト: all'
    )

    args = parser.parse_args()

    # シナリオ設定を取得
    config_default = get_scenario_config('default')
    config_corner = get_scenario_config('corner_intersection')

    # 入力ファイルパス（引数優先、なければシナリオ設定から）
    input_default = Path(args.input_default) if args.input_default else config_default.throughput_output_path
    input_corner = Path(args.input_corner) if args.input_corner else config_corner.throughput_output_path

    # 出力ディレクトリ（引数優先、なければデフォルトシナリオの analysis）
    output_dir = Path(args.outdir) if args.outdir else config_default.analysis_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("最小追加分析: 距離CDF、SNR CDF、MCS分布")
    print("=" * 70)
    print(f"  入力 (Default): {input_default}")
    print(f"  入力 (Corner):  {input_corner}")
    print(f"  出力ディレクトリ: {output_dir}")
    print(f"  アウテージ閾値 (Rmin): {args.rmin_mbps} Mbps")
    print(f"  リンクタイプフィルタ: {args.link_type}")

    # データ読み込み
    print("\n[1] データ読み込み")

    if not input_default.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_default}")
        sys.exit(1)
    if not input_corner.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_corner}")
        sys.exit(1)

    print("  Default シナリオ:")
    df_default = pd.read_csv(input_default)
    print(f"    読み込み完了: {len(df_default)} レコード")

    print("  Corner シナリオ:")
    df_corner = pd.read_csv(input_corner)
    print(f"    読み込み完了: {len(df_corner)} レコード")

    # リンクタイプフィルタ
    if args.link_type != 'all':
        link_type_filter = args.link_type.upper()
        df_default = df_default[df_default['link_type'] == link_type_filter]
        df_corner = df_corner[df_corner['link_type'] == link_type_filter]
        print(f"  リンクタイプフィルタ適用: {link_type_filter}")
        print(f"    Default: {len(df_default)} レコード")
        print(f"    Corner: {len(df_corner)} レコード")

    # 距離列を追加
    print("\n[2] 距離計算")

    print("  Default シナリオ:")
    positions_default = load_vehicle_positions_from_fcd(
        config_default.fcd_output_path,
        config_default
    )
    df_default = add_distance_column(
        df_default,
        positions_default,
        config_default.base_station.position
    )

    print("  Corner シナリオ:")
    positions_corner = load_vehicle_positions_from_fcd(
        config_corner.fcd_output_path,
        config_corner
    )
    df_corner = add_distance_column(
        df_corner,
        positions_corner,
        config_corner.base_station.position
    )

    # 図の生成
    print("\n[3] 図の生成")

    # A) 距離CDF
    generate_distance_cdf(df_default, df_corner, output_dir)

    # B) SNR CDF
    generate_snr_cdf(df_default, df_corner, output_dir)

    # C) MCS分布
    generate_mcs_histogram(df_default, df_corner, output_dir)

    # 集計CSV生成
    print("\n[4] 集計CSV生成")

    summary_default = generate_summary_csv(
        df_default,
        'default',
        output_dir / 'summary_minimal_additional_default.csv',
        args.rmin_mbps
    )

    summary_corner = generate_summary_csv(
        df_corner,
        'corner_intersection',
        output_dir / 'summary_minimal_additional_corner.csv',
        args.rmin_mbps
    )

    # 比較CSV生成
    generate_comparison_csv(
        summary_default,
        summary_corner,
        output_dir / 'summary_minimal_additional_compare.csv'
    )

    print("\n" + "=" * 70)
    print("✅ 分析完了")
    print("=" * 70)
    print(f"\n生成ファイル:")
    print(f"  図:")
    print(f"    - {output_dir / 'figA1_distance_cdf_all.png'}")
    print(f"    - {output_dir / 'figA2_distance_cdf_los_nlos.png'}")
    print(f"    - {output_dir / 'figB1_snr_cdf_all.png'}")
    print(f"    - {output_dir / 'figB2_snr_cdf_los_nlos.png'}")
    print(f"    - {output_dir / 'figC1_mcs_histogram_nlos.png'}")
    print(f"    - {output_dir / 'figC2_mcs_histogram_prop_mode.png'}")
    print(f"  集計CSV:")
    print(f"    - {output_dir / 'summary_minimal_additional_default.csv'}")
    print(f"    - {output_dir / 'summary_minimal_additional_corner.csv'}")
    print(f"    - {output_dir / 'summary_minimal_additional_compare.csv'}")


if __name__ == "__main__":
    main()
