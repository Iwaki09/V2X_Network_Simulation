"""
Random/Greedy割当手法

最適化を使わない簡易的な割当手法を実装します。
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List


def random_assignment(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
    seed: int = 42,
) -> pd.DataFrame:
    """
    ランダム割当

    各車両がランダムに1つのアクションを希望し、BS定員超過時はランダムに採択

    Args:
        candidates_df: 候補DF
        bs_capacity: 各BSの容量
        seed: 乱数シード

    Returns:
        割当結果DF
    """
    np.random.seed(seed)
    results = []

    for timestamp in sorted(candidates_df['timestamp'].unique()):
        df_t = candidates_df[candidates_df['timestamp'] == timestamp]
        vehicles_t = df_t['vehicle_id'].unique()

        # 各車両がランダムに1つのアクションを希望
        requests = []
        for vehicle_id in vehicles_t:
            df_v = df_t[df_t['vehicle_id'] == vehicle_id]
            if len(df_v) > 0:
                # ランダムに1つ選択
                selected = df_v.sample(n=1, random_state=seed).iloc[0]
                requests.append({
                    'vehicle_id': vehicle_id,
                    'bs_id': selected['bs_id'],
                    'action_type': selected['action_type'],
                    'relay_id': selected['relay_id'],
                    'truth_rate_mcs': selected['truth_rate_mcs'],
                    'rate_mcs': selected['rate_mcs'],
                })

        # BS定員管理
        bs_assignments = {}
        for req in requests:
            bs_id = req['bs_id']
            if bs_id not in bs_assignments:
                bs_assignments[bs_id] = []
            bs_assignments[bs_id].append(req)

        # 各BSで定員超過時はランダムに採択
        accepted_vehicles = set()
        for bs_id, reqs in bs_assignments.items():
            if len(reqs) <= bs_capacity:
                # 全員採択
                for req in reqs:
                    accepted_vehicles.add(req['vehicle_id'])
            else:
                # ランダムにbs_capacity個だけ採択
                np.random.shuffle(reqs)
                for req in reqs[:bs_capacity]:
                    accepted_vehicles.add(req['vehicle_id'])

        # 結果を生成
        for vehicle_id in vehicles_t:
            if vehicle_id in accepted_vehicles:
                # 採択された
                req = next(r for r in requests if r['vehicle_id'] == vehicle_id)
                results.append({
                    'timestamp': timestamp,
                    'vehicle_id': vehicle_id,
                    'selected_action_type': req['action_type'],
                    'selected_bs_id': req['bs_id'],
                    'selected_relay_id': req['relay_id'],
                    'accepted': 1,
                    'opt_rate_used': req['rate_mcs'],
                    'truth_rate_mcs_effective': req['truth_rate_mcs'],
                })
            else:
                # アウトエージ
                results.append({
                    'timestamp': timestamp,
                    'vehicle_id': vehicle_id,
                    'selected_action_type': 'none',
                    'selected_bs_id': -1,
                    'selected_relay_id': -1,
                    'accepted': 0,
                    'opt_rate_used': 0.0,
                    'truth_rate_mcs_effective': 0.0,
                })

    return pd.DataFrame(results)


def greedy_assignment(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
) -> pd.DataFrame:
    """
    Greedy割当（rate_mcsベース）

    各車両がrate_mcsが最大のアクションを希望し、BS定員超過時は希望レート降順で採択

    Args:
        candidates_df: 候補DF
        bs_capacity: 各BSの容量

    Returns:
        割当結果DF
    """
    results = []

    for timestamp in sorted(candidates_df['timestamp'].unique()):
        df_t = candidates_df[candidates_df['timestamp'] == timestamp]
        vehicles_t = df_t['vehicle_id'].unique()

        # 各車両がrate_mcsが最大のアクションを希望
        requests = []
        for vehicle_id in vehicles_t:
            df_v = df_t[df_t['vehicle_id'] == vehicle_id]
            if len(df_v) > 0:
                # rate_mcsが最大のものを選択
                best = df_v.sort_values('rate_mcs', ascending=False).iloc[0]
                requests.append({
                    'vehicle_id': vehicle_id,
                    'bs_id': best['bs_id'],
                    'action_type': best['action_type'],
                    'relay_id': best['relay_id'],
                    'truth_rate_mcs': best['truth_rate_mcs'],
                    'rate_mcs': best['rate_mcs'],
                })

        # BS定員管理
        bs_assignments = {}
        for req in requests:
            bs_id = req['bs_id']
            if bs_id not in bs_assignments:
                bs_assignments[bs_id] = []
            bs_assignments[bs_id].append(req)

        # 各BSで定員超過時は希望レート降順で採択
        accepted_vehicles = set()
        for bs_id, reqs in bs_assignments.items():
            # 希望レート降順でソート
            reqs_sorted = sorted(reqs, key=lambda x: x['rate_mcs'], reverse=True)

            # トップbs_capacity個だけ採択
            for req in reqs_sorted[:bs_capacity]:
                accepted_vehicles.add(req['vehicle_id'])

        # 結果を生成
        for vehicle_id in vehicles_t:
            if vehicle_id in accepted_vehicles:
                # 採択された
                req = next(r for r in requests if r['vehicle_id'] == vehicle_id)
                results.append({
                    'timestamp': timestamp,
                    'vehicle_id': vehicle_id,
                    'selected_action_type': req['action_type'],
                    'selected_bs_id': req['bs_id'],
                    'selected_relay_id': req['relay_id'],
                    'accepted': 1,
                    'opt_rate_used': req['rate_mcs'],
                    'truth_rate_mcs_effective': req['truth_rate_mcs'],
                })
            else:
                # アウトエージ
                results.append({
                    'timestamp': timestamp,
                    'vehicle_id': vehicle_id,
                    'selected_action_type': 'none',
                    'selected_bs_id': -1,
                    'selected_relay_id': -1,
                    'accepted': 0,
                    'opt_rate_used': 0.0,
                    'truth_rate_mcs_effective': 0.0,
                })

    return pd.DataFrame(results)
