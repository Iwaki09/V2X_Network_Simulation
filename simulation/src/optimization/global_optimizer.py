#!/usr/bin/env python3
"""
グローバル最適化ソルバー

整数線形計画問題(ILP)を用いて、システム全体の総スループットを最大化する
集中制御型のリソース割り当てを計算する。
"""

import sys
import pandas as pd
import pulp
from pathlib import Path

# パラメータ設定
MAX_BS_CONNECTIONS = 10  # 基地局が同時に処理できる最大ユーザー数

# デフォルトのスループット列名
DEFAULT_THROUGHPUT_COL = 'theoretical_throughput_mbps'

# 許可されるスループット列
VALID_THROUGHPUT_COLS = ['theoretical_throughput_mbps', 'throughput_mbps_mcs']


def validate_throughput_column(df: pd.DataFrame, throughput_col: str) -> None:
    """
    スループット列の存在を検証し、不足時は分かりやすいエラーを出す

    Args:
        df: DataFrame
        throughput_col: スループット列名

    Raises:
        SystemExit: 列が存在しない場合
    """
    if throughput_col not in df.columns:
        print(f"\n❌ エラー: 指定されたスループット列 '{throughput_col}' が見つかりません。")
        print(f"\n利用可能な列:")
        for col in df.columns:
            print(f"  - {col}")
        print(f"\n有効なスループット列: {VALID_THROUGHPUT_COLS}")
        print(f"\nヒント: --rate-model both でスループット計算を再実行してください:")
        print(f"  python scripts/run_throughput.py --rate-model both")
        sys.exit(1)


def solve_global_optimization(
    input_csv: Path = None,
    output_csv: Path = None,
    output_dir: Path = None,
    throughput_col: str = DEFAULT_THROUGHPUT_COL
) -> pd.DataFrame:
    """
    グローバル最適化を実行し、結果を保存する

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_csv: 出力CSVファイルパス (global_optimization_results.csv)
        output_dir: 出力ディレクトリ（output_csvより優先度低い）
        throughput_col: 最適化に使用するスループット列名
            - 'theoretical_throughput_mbps': Shannon公式ベース（デフォルト）
            - 'throughput_mbps_mcs': MCSベース

    Returns:
        結果DataFrame
    """
    # パス設定
    if output_csv is None:
        if output_dir is not None:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_csv = output_dir / "global_optimization_results.csv"
        else:
            # デフォルト（後方互換性のため維持、ただし呼び出し元でoutput_dirを指定することを推奨）
            script_dir = Path(__file__).parent.parent.parent
            default_output_dir = script_dir / "output" / "scenarios" / "default" / "optimization"
            default_output_dir.mkdir(parents=True, exist_ok=True)
            output_csv = default_output_dir / "global_optimization_results.csv"

    print("=" * 60)
    print("グローバル最適化ソルバー")
    print("=" * 60)
    print(f"  スループット列: {throughput_col}")

    # データ読み込み
    print(f"\n[1] データ読み込み: {input_csv}")
    df = pd.read_csv(input_csv)

    # スループット列の検証
    validate_throughput_column(df, throughput_col)

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
            row[throughput_col] * link_vars[idx]
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
    results_df.to_csv(output_csv, index=False)
    print(f"\n[4] 出力ファイル: {output_csv}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("グローバル最適化完了")
    print("=" * 60)

    return results_df


def main():
    """メイン処理"""
    solve_global_optimization()


if __name__ == "__main__":
    main()
