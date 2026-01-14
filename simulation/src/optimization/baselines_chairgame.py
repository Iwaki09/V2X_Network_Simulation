#!/usr/bin/env python3
"""
ベースライン手法: 椅子取りゲームフレームワーク

本モジュールは、以下の3つのベースライン手法を「共通の椅子取りゲーム」として統一実装する：
1. Max-SNR (Greedy): 各車両が最大SNRのBSを希望、SNR降順で足切り
2. Nearest-BS (Distance): 各車両が最近接BSを希望、距離昇順で足切り
3. Random: 各車両がランダムにBSを希望、ランダムに足切り

2段階プロセス：
- Step A: 希望選出（Proposal）: 各車両がルールに従って希望BSを1つ選ぶ
- Step B: Admission Control: 各BSの定員C_bを超えた場合、優先順位で足切り

論文での主張点：
- Max-SNR: 利己的な選択で特定BSに集中し、Admission Control でアウトエージが増える
- Nearest: ミリ波では近い≠繋がる（遮蔽でNLOSになる）
- Random: 下限（Lower Bound）としてのサニティチェック
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BaselineConfig:
    """ベースライン実行設定"""
    baseline_name: str  # "max_snr", "nearest", "random"
    bs_capacity: int  # 基地局定員（全BS共通）
    seed: Optional[int] = None  # 乱数シード（Randomベースライン用）


def load_v2i_links(csv_path: Path) -> pd.DataFrame:
    """
    V2Iリンクのみを読み込む

    Args:
        csv_path: theoretical_network_results.csv のパス

    Returns:
        V2IリンクのDataFrame
    """
    print(f"[Load] {csv_path}")
    df = pd.read_csv(csv_path)

    # V2Iリンクのみ抽出（tx_id = BS, rx_id = 車両）
    v2i_df = df[df['link_type'] == 'V2I'].copy()

    print(f"  総リンク数: {len(df)}")
    print(f"  V2Iリンク数: {len(v2i_df)}")
    print(f"  タイムステップ数: {v2i_df['timestamp'].nunique()}")
    print(f"  車両数: {v2i_df['rx_id'].nunique()}")
    print(f"  基地局数: {v2i_df['tx_id'].nunique()}")

    return v2i_df


def load_vehicle_positions(fcd_path: Path, scenario_config) -> pd.DataFrame:
    """
    FCD XMLファイルから車両位置を読み込む

    Args:
        fcd_path: fcd_output.xml のパス
        scenario_config: シナリオ設定（座標変換用）

    Returns:
        車両位置のDataFrame (timestamp, vehicle_id, x, y, z)
    """
    from ..parsers.fcd_parser import parse_fcd_xml

    print(f"[Load Vehicle Positions] {fcd_path}")

    # FCD解析（既存パーサー活用）
    timestep_data_list = parse_fcd_xml(str(fcd_path))

    # DataFrameに変換
    records = []
    for timestep_data in timestep_data_list:
        for vehicle in timestep_data.vehicles:
            # 座標変換（FCD → RT座標系）
            x_rt, y_rt = scenario_config.transform_coordinates(vehicle.x, vehicle.y)
            records.append({
                'timestamp': timestep_data.timestamp,
                'vehicle_id': vehicle.vehicle_id,
                'x': x_rt,
                'y': y_rt,
                'z': vehicle.z
            })

    pos_df = pd.DataFrame(records)
    print(f"  車両位置レコード数: {len(pos_df)}")

    return pos_df


def calculate_distances(v2i_df: pd.DataFrame, pos_df: pd.DataFrame, scenario_config) -> pd.DataFrame:
    """
    車両-BS間の3次元ユークリッド距離を計算

    Args:
        v2i_df: V2IリンクのDataFrame
        pos_df: 車両位置のDataFrame
        scenario_config: シナリオ設定（BS座標取得用）

    Returns:
        距離列を追加したV2IリンクのDataFrame
    """
    print("[Calculate Distances]")

    # BS座標（シナリオ設定から取得）
    bs_position = scenario_config.base_station.position
    bs_x, bs_y, bs_z = bs_position

    print(f"  BS座標: ({bs_x}, {bs_y}, {bs_z})")

    # 車両位置とマージ（rx_id = 車両ID）
    v2i_with_pos = v2i_df.merge(
        pos_df[['timestamp', 'vehicle_id', 'x', 'y', 'z']],
        left_on=['timestamp', 'rx_id'],
        right_on=['timestamp', 'vehicle_id'],
        how='left',
        suffixes=('', '_pos')
    )

    # vehicle_id列を削除（rx_idと重複）
    v2i_with_pos = v2i_with_pos.drop(columns=['vehicle_id'], errors='ignore')

    # 3次元ユークリッド距離を計算
    v2i_with_pos['distance_3d'] = np.sqrt(
        (v2i_with_pos['x'] - bs_x) ** 2 +
        (v2i_with_pos['y'] - bs_y) ** 2 +
        (v2i_with_pos['z'] - bs_z) ** 2
    )

    print(f"  距離範囲: {v2i_with_pos['distance_3d'].min():.2f} - {v2i_with_pos['distance_3d'].max():.2f} m")

    return v2i_with_pos


# ============================================================================
# Step A: 希望選出（Proposal）
# ============================================================================

def proposal_max_snr(v2i_df: pd.DataFrame) -> pd.DataFrame:
    """
    Max-SNR ベースライン: 希望選出

    各車両は候補V2Iリンクのうち SNR が最大のリンクを希望

    Args:
        v2i_df: V2IリンクのDataFrame（snr_db 列が必要）

    Returns:
        希望レコードのDataFrame (timestamp, vehicle_id, desired_bs_id, score)
    """
    print("[Proposal: Max-SNR]")

    # 各 (timestamp, vehicle) ごとに最大SNRのリンクを選択
    idx_max = v2i_df.groupby(['timestamp', 'rx_id'])['snr_db'].idxmax()
    proposals = v2i_df.loc[idx_max].copy()

    # 希望レコードの整形
    proposals = proposals.rename(columns={
        'rx_id': 'vehicle_id',
        'tx_id': 'desired_bs_id',
        'snr_db': 'score'
    })

    proposals['baseline_name'] = 'max_snr'

    print(f"  希望数: {len(proposals)}")

    return proposals[['timestamp', 'vehicle_id', 'desired_bs_id', 'score', 'baseline_name']]


def proposal_nearest(v2i_df: pd.DataFrame) -> pd.DataFrame:
    """
    Nearest-BS ベースライン: 希望選出

    各車両は距離が最小の基地局を希望

    Args:
        v2i_df: V2IリンクのDataFrame（distance_3d 列が必要）

    Returns:
        希望レコードのDataFrame (timestamp, vehicle_id, desired_bs_id, score)
    """
    print("[Proposal: Nearest-BS]")

    # 各 (timestamp, vehicle) ごとに最小距離のリンクを選択
    idx_min = v2i_df.groupby(['timestamp', 'rx_id'])['distance_3d'].idxmin()
    proposals = v2i_df.loc[idx_min].copy()

    # 希望レコードの整形（score = -distance で「大きいほど優先」に統一）
    proposals = proposals.rename(columns={
        'rx_id': 'vehicle_id',
        'tx_id': 'desired_bs_id'
    })
    proposals['score'] = -proposals['distance_3d']  # 近いほど優先
    proposals['baseline_name'] = 'nearest'

    print(f"  希望数: {len(proposals)}")

    return proposals[['timestamp', 'vehicle_id', 'desired_bs_id', 'score', 'baseline_name']]


def proposal_random(v2i_df: pd.DataFrame, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Random ベースライン: 希望選出

    各車両は候補V2Iリンクから一様ランダムに1つ選んで希望

    Args:
        v2i_df: V2IリンクのDataFrame
        seed: 乱数シード

    Returns:
        希望レコードのDataFrame (timestamp, vehicle_id, desired_bs_id, score)
    """
    print("[Proposal: Random]")

    if seed is not None:
        np.random.seed(seed)
        print(f"  乱数シード: {seed}")

    # 各 (timestamp, vehicle) ごとにランダムに1つ選択
    proposals = v2i_df.groupby(['timestamp', 'rx_id']).sample(n=1, random_state=seed).copy()

    # 希望レコードの整形（score = 乱数）
    proposals = proposals.rename(columns={
        'rx_id': 'vehicle_id',
        'tx_id': 'desired_bs_id'
    })
    proposals['score'] = np.random.rand(len(proposals))  # ランダムなscore
    proposals['baseline_name'] = 'random'

    print(f"  希望数: {len(proposals)}")

    return proposals[['timestamp', 'vehicle_id', 'desired_bs_id', 'score', 'baseline_name']]


# ============================================================================
# Step B: Admission Control（足切り）
# ============================================================================

def admission_control(proposals: pd.DataFrame, bs_capacity: int, baseline_name: str) -> pd.DataFrame:
    """
    Admission Control: 各BSの定員を超えた場合、優先順位で足切り

    Args:
        proposals: 希望レコードのDataFrame
        bs_capacity: 基地局定員（全BS共通）
        baseline_name: ベースライン名（"max_snr", "nearest", "random"）

    Returns:
        accepted/rejected が付いたDataFrame
    """
    print(f"[Admission Control: {baseline_name}]")
    print(f"  BS定員: {bs_capacity}")

    results = []

    # タイムステップごとに処理
    for timestamp, ts_group in proposals.groupby('timestamp'):
        # BSごとに希望者を集計
        for bs_id, bs_group in ts_group.groupby('desired_bs_id'):
            n_applicants = len(bs_group)

            if n_applicants <= bs_capacity:
                # 全員接続
                bs_group['accepted'] = 1
                bs_group['assigned_bs_id'] = bs_group['desired_bs_id']
            else:
                # 足切り（優先順位で上位C_bのみaccepted）
                if baseline_name == 'random':
                    # Randomはランダムに選択
                    accepted_indices = bs_group.sample(n=bs_capacity).index
                else:
                    # Max-SNR/Nearestはscore降順で選択
                    accepted_indices = bs_group.nlargest(bs_capacity, 'score').index

                bs_group['accepted'] = 0
                bs_group.loc[accepted_indices, 'accepted'] = 1
                bs_group['assigned_bs_id'] = bs_group['desired_bs_id']
                bs_group.loc[bs_group['accepted'] == 0, 'assigned_bs_id'] = None

            results.append(bs_group)

    result_df = pd.concat(results, ignore_index=True)

    # 統計情報
    n_accepted = (result_df['accepted'] == 1).sum()
    n_rejected = (result_df['accepted'] == 0).sum()

    print(f"  Accepted: {n_accepted} ({n_accepted / len(result_df) * 100:.1f}%)")
    print(f"  Rejected: {n_rejected} ({n_rejected / len(result_df) * 100:.1f}%)")

    return result_df


# ============================================================================
# 評価指標の計算
# ============================================================================

def evaluate_baseline(
    assignment_df: pd.DataFrame,
    v2i_df: pd.DataFrame,
    throughput_col: str = 'throughput_mbps_mcs'
) -> Dict:
    """
    ベースラインの評価指標を計算

    Args:
        assignment_df: Admission Control結果のDataFrame
        v2i_df: 元のV2IリンクのDataFrame（真値のスループットを含む）
        throughput_col: 評価に使用するスループット列

    Returns:
        評価指標の辞書
    """
    print(f"[Evaluate: throughput_col={throughput_col}]")

    # accepted車両のスループット（真値）を取得
    # assignment_df と v2i_df を (timestamp, vehicle_id, assigned_bs_id) でマージ
    eval_df = assignment_df.merge(
        v2i_df[['timestamp', 'rx_id', 'tx_id', throughput_col]],
        left_on=['timestamp', 'vehicle_id', 'assigned_bs_id'],
        right_on=['timestamp', 'rx_id', 'tx_id'],
        how='left'
    )

    # rejectedはスループット0
    eval_df['throughput_truth'] = eval_df[throughput_col].fillna(0.0)

    # 評価指標
    total_links = len(eval_df)
    outage_count = (eval_df['accepted'] == 0).sum()
    outage_rate = outage_count / total_links if total_links > 0 else 0.0

    throughputs = eval_df['throughput_truth'].values
    mean_throughput = float(np.mean(throughputs))
    p05_throughput = float(np.percentile(throughputs, 5))

    # BSごとの接続台数分布
    bs_load = assignment_df[assignment_df['accepted'] == 1].groupby(['timestamp', 'assigned_bs_id']).size()
    bs_load_stats = {
        'mean': float(bs_load.mean()) if len(bs_load) > 0 else 0.0,
        'max': int(bs_load.max()) if len(bs_load) > 0 else 0,
        'min': int(bs_load.min()) if len(bs_load) > 0 else 0
    }

    metrics = {
        'total_links': total_links,
        'outage_count': outage_count,
        'outage_rate': outage_rate,
        'mean_throughput_mbps': mean_throughput,
        'p05_throughput_mbps': p05_throughput,
        'bs_load_mean': bs_load_stats['mean'],
        'bs_load_max': bs_load_stats['max'],
        'bs_load_min': bs_load_stats['min']
    }

    print(f"  アウトエージ率: {outage_rate * 100:.2f}% ({outage_count}/{total_links})")
    print(f"  平均スループット: {mean_throughput:.2f} Mbps")
    print(f"  P05スループット: {p05_throughput:.2f} Mbps")
    print(f"  BS負荷: 平均={bs_load_stats['mean']:.1f}, 最大={bs_load_stats['max']}, 最小={bs_load_stats['min']}")

    # eval_df に throughput_truth, snr_db_truth を追加して返す
    assignment_with_truth = eval_df[[
        'timestamp', 'vehicle_id', 'desired_bs_id', 'assigned_bs_id',
        'accepted', 'baseline_name', 'score', 'throughput_truth'
    ]].copy()

    # snr_db_truth も追加（評価用）
    if 'snr_db' in v2i_df.columns:
        snr_df = v2i_df[['timestamp', 'rx_id', 'tx_id', 'snr_db']].rename(columns={'rx_id': 'vehicle_id', 'tx_id': 'bs_id'})
        assignment_with_truth = assignment_with_truth.merge(
            snr_df,
            left_on=['timestamp', 'vehicle_id', 'assigned_bs_id'],
            right_on=['timestamp', 'vehicle_id', 'bs_id'],
            how='left'
        )
        assignment_with_truth = assignment_with_truth.rename(columns={'snr_db': 'snr_db_truth'})
        assignment_with_truth = assignment_with_truth.drop(columns=['bs_id'], errors='ignore')

    return metrics, assignment_with_truth


# ============================================================================
# メイン実行関数
# ============================================================================

def run_baseline_chairgame(
    input_csv: Path,
    fcd_path: Path,
    scenario_config,
    config: BaselineConfig,
    throughput_col: str = 'throughput_mbps_mcs',
    output_dir: Path = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    ベースライン（椅子取りゲーム）を実行

    Args:
        input_csv: theoretical_network_results.csv のパス
        fcd_path: fcd_output.xml のパス（Nearest用）
        scenario_config: シナリオ設定
        config: ベースライン設定
        throughput_col: 評価に使用するスループット列
        output_dir: 出力ディレクトリ

    Returns:
        (assignment_df, metrics)
    """
    print("=" * 80)
    print(f"Baseline: {config.baseline_name.upper()}")
    print(f"BS Capacity: {config.bs_capacity}")
    if config.seed is not None:
        print(f"Seed: {config.seed}")
    print("=" * 80)

    # 1. V2Iリンク読み込み
    v2i_df = load_v2i_links(input_csv)

    # 2. Nearestベースラインの場合は距離計算
    if config.baseline_name == 'nearest':
        pos_df = load_vehicle_positions(fcd_path, scenario_config)
        v2i_df = calculate_distances(v2i_df, pos_df, scenario_config)

    # 3. Step A: 希望選出
    if config.baseline_name == 'max_snr':
        proposals = proposal_max_snr(v2i_df)
    elif config.baseline_name == 'nearest':
        proposals = proposal_nearest(v2i_df)
    elif config.baseline_name == 'random':
        proposals = proposal_random(v2i_df, seed=config.seed)
    else:
        raise ValueError(f"Unknown baseline: {config.baseline_name}")

    # 4. Step B: Admission Control
    assignment_df = admission_control(proposals, config.bs_capacity, config.baseline_name)

    # 5. 評価
    metrics, assignment_with_truth = evaluate_baseline(assignment_df, v2i_df, throughput_col)

    # 6. 出力保存
    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Assignment CSV
        assignment_csv = output_dir / f"baseline_{config.baseline_name}_assignment.csv"
        assignment_with_truth.to_csv(assignment_csv, index=False)
        print(f"\n[Output] {assignment_csv}")

        # Summary CSV
        summary_csv = output_dir / f"baseline_{config.baseline_name}_summary.csv"
        summary_df = pd.DataFrame([{
            'baseline_name': config.baseline_name,
            'bs_capacity': config.bs_capacity,
            'seed': config.seed if config.seed is not None else 'N/A',
            **metrics
        }])
        summary_df.to_csv(summary_csv, index=False)
        print(f"[Output] {summary_csv}")

    print("\n" + "=" * 80)

    return assignment_with_truth, metrics
