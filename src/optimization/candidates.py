"""
候補アクション生成モジュール

V2X通信の割当最適化のための候補アクション（Direct/Relay）を生成します。
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Optional


# MCS Table (5G NR like, simplified)
# SNR(dB) -> (MCS index, spectral efficiency bps/Hz)
MCS_TABLE = [
    (-10, 0, 0.15),
    (-5, 1, 0.38),
    (0, 2, 0.88),
    (5, 3, 1.48),
    (10, 4, 2.4),
    (15, 5, 3.3),
    (20, 6, 4.4),
    (25, 7, 5.5),
]


def get_mcs_from_snr(snr_db: float) -> Tuple[int, float]:
    """
    SNR(dB)からMCSインデックスとスペクトル効率を取得

    Args:
        snr_db: SNR in dB

    Returns:
        (mcs_index, spectral_efficiency_bpshz)
    """
    for i in range(len(MCS_TABLE) - 1, -1, -1):
        threshold_db, mcs_idx, spec_eff = MCS_TABLE[i]
        if snr_db >= threshold_db:
            return mcs_idx, spec_eff
    # SNRが最低閾値未満の場合
    return 0, 0.15


def calculate_throughput_from_mcs(snr_db: float, bandwidth_mhz: float = 100.0) -> float:
    """
    SNRからMCSベースのスループットを計算

    Args:
        snr_db: SNR in dB
        bandwidth_mhz: Bandwidth in MHz

    Returns:
        throughput in Mbps
    """
    _, spec_eff = get_mcs_from_snr(snr_db)
    return spec_eff * bandwidth_mhz


def generate_candidates(
    df_network: pd.DataFrame,
    max_bs_candidates: int = 3,
    neighbor_radius_m: float = 200.0,
    max_neighbors: int = 5,
    margin_d_db: float = 6.5,
    margin_k_db: float = 6.5,
    outage_threshold_mbps: float = 0.0,
    bandwidth_mhz: float = 100.0,
) -> pd.DataFrame:
    """
    候補アクション（Direct/Relay）を生成

    Args:
        df_network: theoretical_network_results.csv
        max_bs_candidates: 各車両あたりの最大BS候補数
        neighbor_radius_m: 近傍車の最大距離
        max_neighbors: 各車両あたりの最大近傍車数
        margin_d_db: LOS系（prop_mode=D）のマージン
        margin_k_db: NLOS系（prop_mode=K）のマージン
        outage_threshold_mbps: アウトエージ閾値（これ以下は除外）
        bandwidth_mhz: 帯域幅

    Returns:
        候補DF (timestamp, vehicle_id, action_type, bs_id, relay_id,
                rate_shannon, rate_mcs, rate_dkmcs, truth_rate_mcs)
    """
    # V2IとV2Vに分離
    df_v2i = df_network[df_network['link_type'] == 'V2I'].copy()
    df_v2v = df_network[df_network['link_type'] == 'V2V'].copy()

    # 距離計算のヘルパー（tx_idとrx_idから距離を推定）
    # 注: theoretical_network_results.csvに距離列がない場合、
    # path_lossから逆算するか、座標情報が必要
    # ここでは簡易的にpath_lossを距離の代替として使用
    df_v2v['distance_approx'] = df_v2v['path_loss']

    candidates = []

    # 各タイムスタンプで処理
    for timestamp in sorted(df_network['timestamp'].unique()):
        df_v2i_t = df_v2i[df_v2i['timestamp'] == timestamp]
        df_v2v_t = df_v2v[df_v2v['timestamp'] == timestamp]

        # すべての車両IDを取得（rx_idがwe_*, sn_*, ew_*, ns_*, wn_*, se_*）
        vehicle_ids = set()
        vehicle_ids.update(df_v2i_t['rx_id'].unique())
        vehicle_ids.update(df_v2v_t['tx_id'].unique())
        vehicle_ids.update(df_v2v_t['rx_id'].unique())
        # BSは除外
        vehicle_ids = {v for v in vehicle_ids if not v.startswith('BS_')}

        for vehicle_id in vehicle_ids:
            # === Direct候補の生成 ===
            v2i_links = df_v2i_t[df_v2i_t['rx_id'] == vehicle_id].copy()

            if len(v2i_links) > 0:
                # SNRが高い順にソートしてトップB個を選択
                v2i_links = v2i_links.sort_values('snr_db', ascending=False).head(max_bs_candidates)

                for _, link in v2i_links.iterrows():
                    bs_id = link['tx_id']
                    rate_shannon = link['theoretical_throughput_mbps']
                    rate_mcs = link['throughput_mbps_mcs']

                    # D/K×MCS+margin適用
                    prop_mode = link['prop_mode']
                    margin_db = margin_d_db if prop_mode == 'D' else margin_k_db
                    snr_eff_db = link['snr_db'] - margin_db
                    rate_dkmcs = calculate_throughput_from_mcs(snr_eff_db, bandwidth_mhz)

                    # truthはMCSベース
                    truth_rate_mcs = rate_mcs

                    # アウトエージ閾値チェック
                    if truth_rate_mcs < outage_threshold_mbps:
                        continue

                    candidates.append({
                        'timestamp': timestamp,
                        'vehicle_id': vehicle_id,
                        'action_type': 'direct',
                        'bs_id': bs_id,
                        'relay_id': -1,
                        'rate_shannon': rate_shannon,
                        'rate_mcs': rate_mcs,
                        'rate_dkmcs': rate_dkmcs,
                        'truth_rate_mcs': truth_rate_mcs,
                    })

            # === Relay候補の生成 ===
            # Step 1: v→u (V2V) のリンクを取得（近傍車候補）
            v2v_links_from_v = df_v2v_t[df_v2v_t['tx_id'] == vehicle_id].copy()

            if len(v2v_links_from_v) > 0:
                # 距離が近い順にソートしてトップK個
                # distance_approxが小さい順（path_lossが小さい順 = 距離が近い）
                v2v_links_from_v = v2v_links_from_v.sort_values('distance_approx').head(max_neighbors)

                for _, v2v_link in v2v_links_from_v.iterrows():
                    relay_id = v2v_link['rx_id']

                    # 距離制約チェック（簡易版：path_lossベース）
                    # 実際の距離が必要な場合は座標から計算
                    # ここではpath_lossをそのまま使用（閾値は調整が必要）
                    if v2v_link['distance_approx'] > neighbor_radius_m:
                        continue

                    # Step 2: u→b (V2I) のリンクを取得
                    u2b_links = df_v2i_t[df_v2i_t['rx_id'] == relay_id].copy()

                    if len(u2b_links) > 0:
                        # 各BSについてRelay候補を生成
                        u2b_links = u2b_links.sort_values('snr_db', ascending=False).head(max_bs_candidates)

                        for _, u2b_link in u2b_links.iterrows():
                            bs_id = u2b_link['tx_id']

                            # Relayのレート計算: min(v→u, u→b)
                            # Shannon
                            rate_v2v_shannon = v2v_link['theoretical_throughput_mbps']
                            rate_v2i_shannon = u2b_link['theoretical_throughput_mbps']
                            rate_shannon = min(rate_v2v_shannon, rate_v2i_shannon)

                            # MCS
                            rate_v2v_mcs = v2v_link['throughput_mbps_mcs']
                            rate_v2i_mcs = u2b_link['throughput_mbps_mcs']
                            rate_mcs = min(rate_v2v_mcs, rate_v2i_mcs)

                            # D/K×MCS+margin
                            # v→u側
                            prop_mode_v2v = v2v_link['prop_mode']
                            margin_v2v = margin_d_db if prop_mode_v2v == 'D' else margin_k_db
                            snr_eff_v2v = v2v_link['snr_db'] - margin_v2v
                            rate_v2v_dkmcs = calculate_throughput_from_mcs(snr_eff_v2v, bandwidth_mhz)

                            # u→b側
                            prop_mode_v2i = u2b_link['prop_mode']
                            margin_v2i = margin_d_db if prop_mode_v2i == 'D' else margin_k_db
                            snr_eff_v2i = u2b_link['snr_db'] - margin_v2i
                            rate_v2i_dkmcs = calculate_throughput_from_mcs(snr_eff_v2i, bandwidth_mhz)

                            rate_dkmcs = min(rate_v2v_dkmcs, rate_v2i_dkmcs)

                            # truthはMCSベース
                            truth_rate_mcs = rate_mcs

                            # アウトエージ閾値チェック
                            if truth_rate_mcs < outage_threshold_mbps:
                                continue

                            candidates.append({
                                'timestamp': timestamp,
                                'vehicle_id': vehicle_id,
                                'action_type': 'relay',
                                'bs_id': bs_id,
                                'relay_id': relay_id,
                                'rate_shannon': rate_shannon,
                                'rate_mcs': rate_mcs,
                                'rate_dkmcs': rate_dkmcs,
                                'truth_rate_mcs': truth_rate_mcs,
                            })

    df_candidates = pd.DataFrame(candidates)
    return df_candidates


def get_rate_column(candidates_df: pd.DataFrame, model: str) -> str:
    """
    モデル名からレート列名を取得

    Args:
        candidates_df: 候補DF
        model: "shannon", "mcs", "dkmcs"

    Returns:
        列名
    """
    if model == "shannon":
        return "rate_shannon"
    elif model == "mcs":
        return "rate_mcs"
    elif model == "dkmcs":
        return "rate_dkmcs"
    else:
        raise ValueError(f"Unknown model: {model}")
