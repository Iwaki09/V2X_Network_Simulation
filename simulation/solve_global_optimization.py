#!/usr/bin/env python3
"""
グローバル最適化ソルバー

整数線形計画問題(ILP)を用いて、システム全体の総スループットを最大化する
集中制御型のリソース割り当てを計算する。
"""

import pandas as pd
import pulp
from pathlib import Path

# パラメータ設定
MAX_BS_CONNECTIONS = 10  # 基地局が同時に処理できる最大ユーザー数

# ファイルパス
INPUT_FILE = Path(__file__).parent / "output" / "throughput" / "theoretical_network_results.csv"
OUTPUT_FILE = Path(__file__).parent / "global_optimization_results.csv"


def solve_global_optimization():
    """
    グローバル最適化を実行し、結果を保存する
    """
    print("=" * 60)
    print("グローバル最適化ソルバー")
    print("=" * 60)

    # データ読み込み
    print(f"\n[1] データ読み込み: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"  - 総レコード数: {len(df)}")
    print(f"  - タイムスタンプ範囲: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    print(f"  - リンクタイプ: {df['link_type'].unique()}")

    # タイムスタンプごとに最適化を実行
    results = []
    timestamps = sorted(df['timestamp'].unique())

    print(f"\n[2] 最適化実行（{len(timestamps)} タイムスタンプ）")
    print(f"  - 制約条件:")
    print(f"    * 各車両: 最大1リンク（送受信いずれか）")
    print(f"    * 基地局BS_1: 最大{MAX_BS_CONNECTIONS}リンク（送信のみ）")

    for i, timestamp in enumerate(timestamps):
        # 当該タイムスタンプのデータを抽出
        df_t = df[df['timestamp'] == timestamp].copy()

        # 最適化問題の定義
        problem = pulp.LpProblem(f"GlobalOpt_t{timestamp}", pulp.LpMaximize)

        # 決定変数: 各リンクがアクティブかどうか (0 or 1)
        link_vars = {}
        for idx, row in df_t.iterrows():
            var_name = f"link_{row['link_type']}_{row['tx_id']}_{row['rx_id']}"
            link_vars[idx] = pulp.LpVariable(var_name, cat='Binary')

        # 目的関数: スループットの総和を最大化
        objective = pulp.lpSum([
            row['theoretical_throughput_mbps'] * link_vars[idx]
            for idx, row in df_t.iterrows()
        ])
        problem += objective

        # 制約条件1: 車両の制約（各車両は最大1リンク）
        # 車両IDを抽出（BS_1以外のtx_id, rx_id）
        vehicle_ids = set()
        for _, row in df_t.iterrows():
            if row['tx_id'] != 'BS_1':
                vehicle_ids.add(row['tx_id'])
            if row['rx_id'] != 'BS_1':
                vehicle_ids.add(row['rx_id'])

        for vehicle_id in vehicle_ids:
            # この車両が関わる全リンク（送信または受信）
            related_links = []
            for idx, row in df_t.iterrows():
                if row['tx_id'] == vehicle_id or row['rx_id'] == vehicle_id:
                    related_links.append(link_vars[idx])

            if related_links:
                problem += (
                    pulp.lpSum(related_links) <= 1,
                    f"vehicle_constraint_{vehicle_id}"
                )

        # 制約条件2: 基地局の制約（BS_1は最大MAX_BS_CONNECTIONS個のリンク）
        bs_links = []
        for idx, row in df_t.iterrows():
            if row['tx_id'] == 'BS_1':
                bs_links.append(link_vars[idx])

        if bs_links:
            problem += (
                pulp.lpSum(bs_links) <= MAX_BS_CONNECTIONS,
                "bs_constraint"
            )

        # 問題を解く
        problem.solve(pulp.PULP_CBC_CMD(msg=0))  # msg=0でログ非表示

        # 結果を取得
        status = pulp.LpStatus[problem.status]
        if status == 'Optimal':
            optimized_throughput = pulp.value(problem.objective)
        else:
            optimized_throughput = 0.0
            print(f"  [警告] t={timestamp}: 最適解が見つかりませんでした (status={status})")

        results.append({
            'timestamp': timestamp,
            'optimized_total_throughput_mbps': optimized_throughput
        })

        # 進捗表示
        if (i + 1) % 10 == 0 or (i + 1) == len(timestamps):
            print(f"  - 進捗: {i+1}/{len(timestamps)} ({100*(i+1)/len(timestamps):.1f}%)")

    # 結果をDataFrameに変換
    results_df = pd.DataFrame(results)

    # 統計情報を表示
    print(f"\n[3] 最適化結果")
    print(f"  - 平均スループット: {results_df['optimized_total_throughput_mbps'].mean():.2f} Mbps")
    print(f"  - 最大スループット: {results_df['optimized_total_throughput_mbps'].max():.2f} Mbps")
    print(f"  - 最小スループット: {results_df['optimized_total_throughput_mbps'].min():.2f} Mbps")

    # CSV保存
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[4] 出力ファイル: {OUTPUT_FILE}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("グローバル最適化完了")
    print("=" * 60)


if __name__ == "__main__":
    solve_global_optimization()
