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
    Relay接続の場合、リレー車のBS接続を正しくカウント

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

        # BS容量管理：Direct接続車両 + リレー車のBS接続をカウント
        bs_usage = {}  # {bs_id: {'direct': [...], 'relay_vehicles': {relay_id: [...]}}}
        for req in requests:
            bs_id = req['bs_id']
            if bs_id not in bs_usage:
                bs_usage[bs_id] = {'direct': [], 'relay_vehicles': {}}

            if req['action_type'] == 'direct':
                bs_usage[bs_id]['direct'].append(req)
            elif req['action_type'] == 'relay':
                relay_id = req['relay_id']
                if relay_id not in bs_usage[bs_id]['relay_vehicles']:
                    bs_usage[bs_id]['relay_vehicles'][relay_id] = []
                bs_usage[bs_id]['relay_vehicles'][relay_id].append(req)

        # 各BSで定員超過時はランダムに採択
        accepted_vehicles = set()
        for bs_id, usage in bs_usage.items():
            direct_reqs = usage['direct']
            relay_groups = usage['relay_vehicles']

            # 候補リスト作成：Direct車両 + リレー車グループ
            candidates_for_bs = []
            for req in direct_reqs:
                candidates_for_bs.append(('direct', req))
            for relay_id, relay_reqs in relay_groups.items():
                candidates_for_bs.append(('relay_group', relay_id, relay_reqs))

            # 現在のBS使用数
            current_usage = len(direct_reqs) + len(relay_groups)

            if current_usage <= bs_capacity:
                # 全員採択
                for req in direct_reqs:
                    accepted_vehicles.add(req['vehicle_id'])
                for relay_reqs in relay_groups.values():
                    for req in relay_reqs:
                        accepted_vehicles.add(req['vehicle_id'])
            else:
                # ランダムにbs_capacity個だけ採択
                np.random.shuffle(candidates_for_bs)
                selected_count = 0
                for item in candidates_for_bs:
                    if selected_count >= bs_capacity:
                        break
                    if item[0] == 'direct':
                        accepted_vehicles.add(item[1]['vehicle_id'])
                        selected_count += 1
                    elif item[0] == 'relay_group':
                        relay_id, relay_reqs = item[1], item[2]
                        for req in relay_reqs:
                            accepted_vehicles.add(req['vehicle_id'])
                        selected_count += 1

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
    Greedy割当（rate_mcsベース、全体ソート）

    候補全体をrate_mcs降順で見て、制約を満たす限り採択する
    Relay接続の場合、リレー車のBS接続を正しくカウント

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

        # 候補全体をrate_mcs降順で並べて採択
        df_sorted = df_t.sort_values('rate_mcs', ascending=False)
        accepted_by_vehicle = {}
        bs_usage = {}  # {bs_id: {'direct': int, 'relay_groups': set(relay_id)}}

        for _, cand in df_sorted.iterrows():
            vehicle_id = cand['vehicle_id']
            if vehicle_id in accepted_by_vehicle:
                continue

            bs_id = cand['bs_id']
            if bs_id not in bs_usage:
                bs_usage[bs_id] = {'direct': 0, 'relay_groups': set()}

            usage = bs_usage[bs_id]
            current_usage = usage['direct'] + len(usage['relay_groups'])

            if cand['action_type'] == 'direct':
                if current_usage >= bs_capacity:
                    continue
                usage['direct'] += 1
                accepted_by_vehicle[vehicle_id] = cand
            elif cand['action_type'] == 'relay':
                relay_id = cand['relay_id']
                if relay_id in usage['relay_groups']:
                    # 既にrelayグループが有効ならBS容量を消費しない
                    accepted_by_vehicle[vehicle_id] = cand
                else:
                    if current_usage >= bs_capacity:
                        continue
                    usage['relay_groups'].add(relay_id)
                    accepted_by_vehicle[vehicle_id] = cand

        # 結果を生成
        for vehicle_id in vehicles_t:
            if vehicle_id in accepted_by_vehicle:
                # 採択された
                req = accepted_by_vehicle[vehicle_id]
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
