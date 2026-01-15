"""
最適化ソルバーモジュール

V2X通信の割当最適化問題を解きます。
- Obj-T: スループット最大化
- Obj-O: アウトエージ最小化（救済数最大＋スループット最大）
"""

import pandas as pd
import numpy as np
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatus, PULP_CBC_CMD
from typing import Dict, Tuple, List


def solve_optimization(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
    rate_col: str,
    objective: str = "throughput",
    verbose: bool = False,
    progress_log: bool = True,
) -> pd.DataFrame:
    """
    最適化問題を解く

    Args:
        candidates_df: 候補DF
        bs_capacity: 各BSの容量
        rate_col: 最適化に使用するレート列（rate_shannon, rate_mcs, rate_dkmcs）
        objective: "throughput" (Obj-T) or "outage" (Obj-O)
        verbose: 詳細出力（ソルバーの詳細ログ）
        progress_log: 進捗ログの表示

    Returns:
        割当結果DF (timestamp, vehicle_id, selected_action_type, selected_bs_id,
                    selected_relay_id, accepted, opt_rate_used, truth_rate_mcs_effective)
    """
    if objective == "throughput":
        return _solve_throughput_max(candidates_df, bs_capacity, rate_col, verbose, progress_log)
    elif objective == "outage":
        return _solve_outage_min(candidates_df, bs_capacity, rate_col, verbose, progress_log)
    else:
        raise ValueError(f"Unknown objective: {objective}")


def _solve_throughput_max(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
    rate_col: str,
    verbose: bool = False,
    progress_log: bool = True,
) -> pd.DataFrame:
    """
    Obj-T: スループット最大化

    maximize Σ_{v,a} x_{v,a} * R(v,a)
    subject to:
        - Σ_a x_{v,a} <= 1  (各車両は最大1アクション)
        - BS容量制約（Direct接続車両 + BS接続リレー車 <= C_b）
        - x_{v,a} ∈ {0,1}
    """
    if progress_log:
        print(f"    - 変数定義中...")
        print(f"      候補数: {len(candidates_df)}")
        print(f"      タイムスタンプ数: {candidates_df['timestamp'].nunique()}")
        print(f"      車両数: {candidates_df['vehicle_id'].nunique()}")

    prob = LpProblem("V2X_Throughput_Maximization", LpMaximize)

    # 変数定義
    candidates = candidates_df.to_dict('records')
    x_vars = {}
    for idx, cand in enumerate(candidates):
        x_vars[idx] = LpVariable(f"x_{idx}", cat='Binary')

    # リレー車がBSに接続しているかを表す補助変数
    # z[(timestamp, relay_id, bs_id)] = 1 if relay車がBSに接続
    z_vars = {}
    relay_bs_connections = set()
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'relay':
            key = (cand['timestamp'], cand['relay_id'], cand['bs_id'])
            relay_bs_connections.add(key)

    for key in relay_bs_connections:
        z_vars[key] = LpVariable(f"z_{key[0]}_{key[1]}_{key[2]}", cat='Binary')

    # 目的関数: maximize Σ x * R
    prob += lpSum([x_vars[idx] * cand[rate_col] for idx, cand in enumerate(candidates)])

    # 制約1: 各車両は最大1アクション
    vehicles_by_timestamp = {}
    for idx, cand in enumerate(candidates):
        key = (cand['timestamp'], cand['vehicle_id'])
        if key not in vehicles_by_timestamp:
            vehicles_by_timestamp[key] = []
        vehicles_by_timestamp[key].append(idx)

    for key, indices in vehicles_by_timestamp.items():
        prob += lpSum([x_vars[idx] for idx in indices]) <= 1, f"Vehicle_{key[0]}_{key[1]}"

    # 制約2: Relayアクションが選ばれた場合、対応するリレー車-BS接続を有効化
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'relay':
            key = (cand['timestamp'], cand['relay_id'], cand['bs_id'])
            prob += x_vars[idx] <= z_vars[key], f"RelayActive_{idx}"

    # 制約3: BS容量制約
    # Direct接続の車両数 + リレー車のBS接続数 <= bs_capacity
    bs_usage_by_timestamp = {}
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'direct':
            key = (cand['timestamp'], cand['bs_id'])
            if key not in bs_usage_by_timestamp:
                bs_usage_by_timestamp[key] = {'direct': [], 'relay_vars': []}
            bs_usage_by_timestamp[key]['direct'].append(idx)

    for relay_key in relay_bs_connections:
        timestamp, relay_id, bs_id = relay_key
        key = (timestamp, bs_id)
        if key not in bs_usage_by_timestamp:
            bs_usage_by_timestamp[key] = {'direct': [], 'relay_vars': []}
        bs_usage_by_timestamp[key]['relay_vars'].append(relay_key)

    for key, usage in bs_usage_by_timestamp.items():
        direct_connections = [x_vars[idx] for idx in usage['direct']]
        relay_connections = [z_vars[rkey] for rkey in usage['relay_vars']]
        prob += lpSum(direct_connections + relay_connections) <= bs_capacity, f"BS_{key[0]}_{key[1]}"

    if progress_log:
        print(f"    - 最適化問題を構築完了")
        print(f"      変数数: {len(x_vars) + len(z_vars)}")
        print(f"      制約数: {len(prob.constraints)}")
        print(f"    - ソルバー実行中...")

    # 求解
    solver = PULP_CBC_CMD(msg=verbose)
    prob.solve(solver)

    if progress_log or verbose:
        print(f"    - ソルバー完了: {LpStatus[prob.status]}")
        if prob.objective.value() is not None:
            print(f"      目的関数値: {prob.objective.value():.2f}")

    # 結果を抽出
    results = []
    for timestamp in candidates_df['timestamp'].unique():
        df_t = candidates_df[candidates_df['timestamp'] == timestamp]
        vehicles_t = df_t['vehicle_id'].unique()

        for vehicle_id in vehicles_t:
            df_v = df_t[df_t['vehicle_id'] == vehicle_id]

            # この車両のどのアクションが選ばれたかチェック
            selected = False
            for idx in df_v.index:
                row_idx = candidates_df.index.get_loc(idx)
                if x_vars[row_idx].varValue and x_vars[row_idx].varValue > 0.5:
                    cand = candidates[row_idx]
                    results.append({
                        'timestamp': timestamp,
                        'vehicle_id': vehicle_id,
                        'selected_action_type': cand['action_type'],
                        'selected_bs_id': cand['bs_id'],
                        'selected_relay_id': cand['relay_id'],
                        'accepted': 1,
                        'opt_rate_used': cand[rate_col],
                        'truth_rate_mcs_effective': cand['truth_rate_mcs'],
                    })
                    selected = True
                    break

            if not selected:
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


def _solve_outage_min(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
    rate_col: str,
    verbose: bool = False,
    progress_log: bool = True,
) -> pd.DataFrame:
    """
    Obj-O: アウトエージ最小化（2段階最適化）

    第1段: maximize Σ_v y_v (救済数最大)
    第2段: Y*を固定して maximize Σ x*R (スループット最大)
    """
    if progress_log:
        print(f"    - [第1段] 救済数最大化の変数定義中...")
        print(f"      候補数: {len(candidates_df)}")
        print(f"      タイムスタンプ数: {candidates_df['timestamp'].nunique()}")
        print(f"      車両数: {candidates_df['vehicle_id'].nunique()}")

    # === 第1段: 救済数最大化 ===
    prob1 = LpProblem("V2X_Rescue_Maximization", LpMaximize)

    candidates = candidates_df.to_dict('records')
    x_vars = {}
    y_vars = {}

    # 車両ごとのy変数
    vehicles_all = set()
    for cand in candidates:
        vehicles_all.add((cand['timestamp'], cand['vehicle_id']))

    for v_key in vehicles_all:
        y_vars[v_key] = LpVariable(f"y_{v_key[0]}_{v_key[1]}", cat='Binary')

    # x変数
    for idx, cand in enumerate(candidates):
        x_vars[idx] = LpVariable(f"x_{idx}", cat='Binary')

    # リレー車がBSに接続しているかを表す補助変数
    z_vars = {}
    relay_bs_connections = set()
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'relay':
            key = (cand['timestamp'], cand['relay_id'], cand['bs_id'])
            relay_bs_connections.add(key)

    for key in relay_bs_connections:
        z_vars[key] = LpVariable(f"z_{key[0]}_{key[1]}_{key[2]}", cat='Binary')

    # 目的関数: maximize Σ y_v
    prob1 += lpSum([y_vars[v_key] for v_key in vehicles_all])

    # 制約1: y_v <= Σ_a x_{v,a}
    vehicles_by_timestamp = {}
    for idx, cand in enumerate(candidates):
        key = (cand['timestamp'], cand['vehicle_id'])
        if key not in vehicles_by_timestamp:
            vehicles_by_timestamp[key] = []
        vehicles_by_timestamp[key].append(idx)

    for key, indices in vehicles_by_timestamp.items():
        prob1 += y_vars[key] <= lpSum([x_vars[idx] for idx in indices]), f"Y_Vehicle_{key[0]}_{key[1]}"

    # 制約2: 各車両は最大1アクション
    for key, indices in vehicles_by_timestamp.items():
        prob1 += lpSum([x_vars[idx] for idx in indices]) <= 1, f"Vehicle_{key[0]}_{key[1]}"

    # 制約3: Relayアクションが選ばれた場合、対応するリレー車-BS接続を有効化
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'relay':
            key = (cand['timestamp'], cand['relay_id'], cand['bs_id'])
            prob1 += x_vars[idx] <= z_vars[key], f"RelayActive_{idx}"

    # 制約4: BS容量制約（Direct接続車両 + BS接続リレー車 <= C_b）
    bs_usage_by_timestamp = {}
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'direct':
            key = (cand['timestamp'], cand['bs_id'])
            if key not in bs_usage_by_timestamp:
                bs_usage_by_timestamp[key] = {'direct': [], 'relay_vars': []}
            bs_usage_by_timestamp[key]['direct'].append(idx)

    for relay_key in relay_bs_connections:
        timestamp, relay_id, bs_id = relay_key
        key = (timestamp, bs_id)
        if key not in bs_usage_by_timestamp:
            bs_usage_by_timestamp[key] = {'direct': [], 'relay_vars': []}
        bs_usage_by_timestamp[key]['relay_vars'].append(relay_key)

    for key, usage in bs_usage_by_timestamp.items():
        direct_connections = [x_vars[idx] for idx in usage['direct']]
        relay_connections = [z_vars[rkey] for rkey in usage['relay_vars']]
        prob1 += lpSum(direct_connections + relay_connections) <= bs_capacity, f"BS_{key[0]}_{key[1]}"

    if progress_log:
        print(f"    - [第1段] 最適化問題を構築完了")
        print(f"      変数数: {len(x_vars) + len(y_vars) + len(z_vars)}")
        print(f"      制約数: {len(prob1.constraints)}")
        print(f"    - [第1段] ソルバー実行中...")

    # 第1段求解
    solver = PULP_CBC_CMD(msg=verbose)
    prob1.solve(solver)

    rescued_count = int(round(prob1.objective.value())) if prob1.objective.value() else 0

    if progress_log or verbose:
        print(f"    - [第1段] ソルバー完了: {LpStatus[prob1.status]}")
        print(f"      救済車両数: {rescued_count}")

    # === 第2段: 救済数を固定してスループット最大化 ===
    prob2 = LpProblem("V2X_Throughput_Given_Rescue", LpMaximize)

    # 新しい変数を定義
    x_vars2 = {}
    y_vars2 = {}
    z_vars2 = {}

    for v_key in vehicles_all:
        y_vars2[v_key] = LpVariable(f"y2_{v_key[0]}_{v_key[1]}", cat='Binary')

    for idx, cand in enumerate(candidates):
        x_vars2[idx] = LpVariable(f"x2_{idx}", cat='Binary')

    for key in relay_bs_connections:
        z_vars2[key] = LpVariable(f"z2_{key[0]}_{key[1]}_{key[2]}", cat='Binary')

    # 目的関数: maximize Σ x * R
    prob2 += lpSum([x_vars2[idx] * cand[rate_col] for idx, cand in enumerate(candidates)])

    # 制約1: Σ y_v = rescued_count (第1段の結果を固定)
    prob2 += lpSum([y_vars2[v_key] for v_key in vehicles_all]) == rescued_count, "FixedRescueCount"

    # 制約2: y_v <= Σ_a x_{v,a}
    for key, indices in vehicles_by_timestamp.items():
        prob2 += y_vars2[key] <= lpSum([x_vars2[idx] for idx in indices]), f"Y_Vehicle_{key[0]}_{key[1]}"

    # 制約3: 各車両は最大1アクション
    for key, indices in vehicles_by_timestamp.items():
        prob2 += lpSum([x_vars2[idx] for idx in indices]) <= 1, f"Vehicle_{key[0]}_{key[1]}"

    # 制約4: Relayアクションが選ばれた場合、対応するリレー車-BS接続を有効化
    for idx, cand in enumerate(candidates):
        if cand['action_type'] == 'relay':
            key = (cand['timestamp'], cand['relay_id'], cand['bs_id'])
            prob2 += x_vars2[idx] <= z_vars2[key], f"RelayActive2_{idx}"

    # 制約5: BS容量制約（Direct接続車両 + BS接続リレー車 <= C_b）
    for key, usage in bs_usage_by_timestamp.items():
        direct_connections = [x_vars2[idx] for idx in usage['direct']]
        relay_connections = [z_vars2[rkey] for rkey in usage['relay_vars']]
        prob2 += lpSum(direct_connections + relay_connections) <= bs_capacity, f"BS2_{key[0]}_{key[1]}"

    if progress_log:
        print(f"    - [第2段] スループット最大化の問題構築完了")
        print(f"      変数数: {len(x_vars2) + len(y_vars2) + len(z_vars2)}")
        print(f"      制約数: {len(prob2.constraints)}")
        print(f"    - [第2段] ソルバー実行中...")

    # 第2段求解
    prob2.solve(solver)

    if progress_log or verbose:
        print(f"    - [第2段] ソルバー完了: {LpStatus[prob2.status]}")
        if prob2.objective.value() is not None:
            print(f"      目的関数値: {prob2.objective.value():.2f}")

    # 結果を抽出
    results = []
    for timestamp in candidates_df['timestamp'].unique():
        df_t = candidates_df[candidates_df['timestamp'] == timestamp]
        vehicles_t = df_t['vehicle_id'].unique()

        for vehicle_id in vehicles_t:
            df_v = df_t[df_t['vehicle_id'] == vehicle_id]

            # この車両のどのアクションが選ばれたかチェック
            selected = False
            for idx in df_v.index:
                row_idx = candidates_df.index.get_loc(idx)
                if x_vars2[row_idx].varValue and x_vars2[row_idx].varValue > 0.5:
                    cand = candidates[row_idx]
                    results.append({
                        'timestamp': timestamp,
                        'vehicle_id': vehicle_id,
                        'selected_action_type': cand['action_type'],
                        'selected_bs_id': cand['bs_id'],
                        'selected_relay_id': cand['relay_id'],
                        'accepted': 1,
                        'opt_rate_used': cand[rate_col],
                        'truth_rate_mcs_effective': cand['truth_rate_mcs'],
                    })
                    selected = True
                    break

            if not selected:
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
