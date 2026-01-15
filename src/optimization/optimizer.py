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
) -> pd.DataFrame:
    """
    最適化問題を解く

    Args:
        candidates_df: 候補DF
        bs_capacity: 各BSの容量
        rate_col: 最適化に使用するレート列（rate_shannon, rate_mcs, rate_dkmcs）
        objective: "throughput" (Obj-T) or "outage" (Obj-O)
        verbose: 詳細出力

    Returns:
        割当結果DF (timestamp, vehicle_id, selected_action_type, selected_bs_id,
                    selected_relay_id, accepted, opt_rate_used, truth_rate_mcs_effective)
    """
    if objective == "throughput":
        return _solve_throughput_max(candidates_df, bs_capacity, rate_col, verbose)
    elif objective == "outage":
        return _solve_outage_min(candidates_df, bs_capacity, rate_col, verbose)
    else:
        raise ValueError(f"Unknown objective: {objective}")


def _solve_throughput_max(
    candidates_df: pd.DataFrame,
    bs_capacity: int,
    rate_col: str,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Obj-T: スループット最大化

    maximize Σ_{v,a} x_{v,a} * R(v,a)
    subject to:
        - Σ_a x_{v,a} <= 1  (各車両は最大1アクション)
        - Σ_{v,a uses b} x_{v,a} <= C_b  (BS容量制約)
        - x_{v,a} ∈ {0,1}
    """
    prob = LpProblem("V2X_Throughput_Maximization", LpMaximize)

    # 変数定義
    candidates = candidates_df.to_dict('records')
    x_vars = {}
    for idx, cand in enumerate(candidates):
        x_vars[idx] = LpVariable(f"x_{idx}", cat='Binary')

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

    # 制約2: BS容量制約
    bs_usage = {}
    for idx, cand in enumerate(candidates):
        key = (cand['timestamp'], cand['bs_id'])
        if key not in bs_usage:
            bs_usage[key] = []
        bs_usage[key].append(idx)

    for key, indices in bs_usage.items():
        prob += lpSum([x_vars[idx] for idx in indices]) <= bs_capacity, f"BS_{key[0]}_{key[1]}"

    # 求解
    solver = PULP_CBC_CMD(msg=verbose)
    prob.solve(solver)

    if verbose:
        print(f"Status: {LpStatus[prob.status]}")
        print(f"Objective: {prob.objective.value()}")

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
) -> pd.DataFrame:
    """
    Obj-O: アウトエージ最小化（2段階最適化）

    第1段: maximize Σ_v y_v (救済数最大)
    第2段: Y*を固定して maximize Σ x*R (スループット最大)
    """
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

    # 制約3: BS容量制約
    bs_usage = {}
    for idx, cand in enumerate(candidates):
        key = (cand['timestamp'], cand['bs_id'])
        if key not in bs_usage:
            bs_usage[key] = []
        bs_usage[key].append(idx)

    for key, indices in bs_usage.items():
        prob1 += lpSum([x_vars[idx] for idx in indices]) <= bs_capacity, f"BS_{key[0]}_{key[1]}"

    # 第1段求解
    solver = PULP_CBC_CMD(msg=verbose)
    prob1.solve(solver)

    if verbose:
        print(f"[Stage 1] Status: {LpStatus[prob1.status]}")
        print(f"[Stage 1] Rescued vehicles: {prob1.objective.value()}")

    rescued_count = int(round(prob1.objective.value()))

    # === 第2段: 救済数を固定してスループット最大化 ===
    prob2 = LpProblem("V2X_Throughput_Given_Rescue", LpMaximize)

    # 新しい変数を定義
    x_vars2 = {}
    y_vars2 = {}

    for v_key in vehicles_all:
        y_vars2[v_key] = LpVariable(f"y2_{v_key[0]}_{v_key[1]}", cat='Binary')

    for idx, cand in enumerate(candidates):
        x_vars2[idx] = LpVariable(f"x2_{idx}", cat='Binary')

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

    # 制約4: BS容量制約
    for key, indices in bs_usage.items():
        prob2 += lpSum([x_vars2[idx] for idx in indices]) <= bs_capacity, f"BS_{key[0]}_{key[1]}"

    # 第2段求解
    prob2.solve(solver)

    if verbose:
        print(f"[Stage 2] Status: {LpStatus[prob2.status]}")
        print(f"[Stage 2] Throughput: {prob2.objective.value()}")

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
