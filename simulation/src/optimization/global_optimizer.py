#!/usr/bin/env python3
"""
グローバル最適化ソルバー

整数線形計画問題(ILP)を用いて、システム全体の総スループットを最大化する
集中制御型のリソース割り当てを計算する。
"""

import sys
import time
import pandas as pd
import pulp
from pathlib import Path

# パラメータ設定
MAX_BS_CONNECTIONS = 10  # 基地局が同時に処理できる最大ユーザー数

# デフォルトのスループット列名
DEFAULT_THROUGHPUT_COL = 'theoretical_throughput_mbps'

# 許可されるスループット列
VALID_THROUGHPUT_COLS = [
    'theoretical_throughput_mbps',
    'throughput_mbps_mcs',
    'throughput_mbps_mcs_est'  # 推定列（Mode-aware Margin適用後）
]

def get_rss_mb():
    """現在のプロセス最大RSSをMB単位で返す（取得不可ならNone）"""
    try:
        import resource
    except ImportError:
        return None

    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOSはbytes、LinuxはKB
    if sys.platform == "darwin":
        return rss / (1024 * 1024)
    return rss / 1024


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
    throughput_col: str = DEFAULT_THROUGHPUT_COL,
    eval_throughput_col: str = None,
    outage_threshold_mbps: float = 50.0,
    memory_log_interval: int = 10,
    log_per_timestamp: bool = True,
    time_limit_sec: float = None
) -> pd.DataFrame:
    """
    グローバル最適化を実行し、結果を保存する

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_csv: 出力CSVファイルパス (global_optimization_results.csv)
        output_dir: 出力ディレクトリ（output_csvより優先度低い）
        throughput_col: 最適化（選択）に使用するスループット列名
            - 'theoretical_throughput_mbps': Shannon公式ベース（デフォルト）
            - 'throughput_mbps_mcs': MCSベース
            - 'throughput_mbps_mcs_est': 推定列（Mode-aware Margin適用後）
        eval_throughput_col: 評価に使用するスループット列名（Noneの場合はthroughput_colと同じ）
        outage_threshold_mbps: アウトエージ判定しきい値 [Mbps]（評価列に対して適用）

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

    # 評価列の決定
    if eval_throughput_col is None:
        eval_throughput_col = throughput_col

    print("=" * 60)
    print("グローバル最適化ソルバー")
    print("=" * 60)
    print(f"  最適化入力列 (opt):  {throughput_col}")
    print(f"  評価列 (eval):       {eval_throughput_col}")
    print(f"  アウトエージしきい値: {outage_threshold_mbps} Mbps")
    if memory_log_interval:
        print(f"  メモリログ: {memory_log_interval} タイムスタンプ毎 (RSS max)")
    if log_per_timestamp:
        print("  タイムスタンプ毎ログ: 有効")
    if time_limit_sec:
        print(f"  タイムリミット: {time_limit_sec} 秒/タイムスタンプ")

    # データ読み込み
    print(f"\n[1] データ読み込み: {input_csv}")
    df_head = pd.read_csv(input_csv, nrows=0)

    # スループット列の検証（usecolsの事前確認）
    validate_throughput_column(df_head, throughput_col)
    if eval_throughput_col != throughput_col:
        validate_throughput_column(df_head, eval_throughput_col)

    required_cols = {
        'timestamp',
        'link_type',
        'tx_id',
        'rx_id',
        throughput_col,
        eval_throughput_col
    }
    df = pd.read_csv(input_csv, usecols=sorted(required_cols))

    print(f"  - 総レコード数: {len(df)}")
    print(f"  - タイムスタンプ範囲: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
    print(f"  - リンクタイプ: {df['link_type'].unique()}")

    # タイムスタンプごとに最適化を実行
    results = []
    selected_eval_throughputs = []  # 選択リンクのeval列のみ保持
    timestamps = sorted(df['timestamp'].unique())

    print(f"\n[2] 最適化実行（{len(timestamps)} タイムスタンプ）")
    print(f"  - 制約条件:")
    print(f"    * 各車両: 最大1リンク（送受信いずれか）")
    print(f"    * 基地局BS_1: 最大{MAX_BS_CONNECTIONS}リンク（送信のみ）")

    for i, timestamp in enumerate(timestamps):
        start_time = time.perf_counter()
        if log_per_timestamp:
            print(f"  [t={timestamp}] 開始 ({i+1}/{len(timestamps)})")
        # 当該タイムスタンプのデータを抽出
        df_t = df[df['timestamp'] == timestamp]

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
        solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=time_limit_sec) if time_limit_sec else pulp.PULP_CBC_CMD(msg=0)
        problem.solve(solver)

        # 結果を取得
        status = pulp.LpStatus[problem.status]
        if status in {'Optimal', 'Not Solved'}:
            optimized_throughput = pulp.value(problem.objective)
            if optimized_throughput is None:
                optimized_throughput = 0.0

            # 選択されたリンクを保存（eval列での評価用）
            for idx, row in df_t.iterrows():
                if link_vars[idx].varValue == 1:
                    selected_eval_throughputs.append(row[eval_throughput_col])
        else:
            optimized_throughput = 0.0
            print(f"  [警告] t={timestamp}: 解が取得できませんでした (status={status})")

        results.append({
            'timestamp': timestamp,
            'optimized_total_throughput_mbps': optimized_throughput,
            'solve_status': status
        })

        elapsed = time.perf_counter() - start_time
        if log_per_timestamp:
            print(f"  [t={timestamp}] 完了 status={status} time={elapsed:.2f}s")

        # 進捗表示
        if (i + 1) % 10 == 0 or (i + 1) == len(timestamps):
            print(f"  - 進捗: {i+1}/{len(timestamps)} ({100*(i+1)/len(timestamps):.1f}%)")
        if memory_log_interval and ((i + 1) % memory_log_interval == 0 or (i + 1) == len(timestamps)):
            rss_mb = get_rss_mb()
            if rss_mb is not None:
                print(f"    RSS(max): {rss_mb:.1f} MB")

    # 結果をDataFrameに変換
    results_df = pd.DataFrame(results)

    # 統計情報を表示
    print(f"\n[3] 最適化結果（opt列）")
    print(f"  - 平均スループット: {results_df['optimized_total_throughput_mbps'].mean():.2f} Mbps")
    print(f"  - 最大スループット: {results_df['optimized_total_throughput_mbps'].max():.2f} Mbps")
    print(f"  - 最小スループット: {results_df['optimized_total_throughput_mbps'].min():.2f} Mbps")

    # 評価指標の計算（eval列）
    print(f"\n[4] 評価指標の計算（eval列）")
    if eval_throughput_col != throughput_col:
        print(f"  評価列 '{eval_throughput_col}' を使用して評価指標を計算")

    if len(selected_eval_throughputs) > 0:
        # 選択されたリンクのeval列スループット
        eval_throughputs = pd.Series(selected_eval_throughputs)

        # アウトエージ率（eval列で判定）
        outage_count = int((eval_throughputs < outage_threshold_mbps).sum())
        outage_rate = outage_count / len(eval_throughputs) if len(eval_throughputs) > 0 else 0.0

        # P05（下位5%）
        p05_eval = float(pd.Series(eval_throughputs).quantile(0.05))

        # 平均
        mean_eval = float(pd.Series(eval_throughputs).mean())

        print(f"  評価結果:")
        print(f"    - アウトエージ率 (< {outage_threshold_mbps} Mbps): {outage_rate*100:.2f}% ({outage_count}/{len(eval_throughputs)})")
        print(f"    - P05 (下位5%):       {p05_eval:.2f} Mbps")
        print(f"    - 平均スループット:    {mean_eval:.2f} Mbps")

        # 結果に評価指標を追加
        summary_stats = {
            'outage_threshold_mbps': outage_threshold_mbps,
            'outage_rate_eval': outage_rate,
            'outage_count_eval': outage_count,
            'total_links_eval': len(eval_throughputs),
            'p05_eval_mbps': p05_eval,
            'mean_eval_mbps': mean_eval,
            'opt_col': throughput_col,
            'eval_col': eval_throughput_col
        }

        # サマリーをCSVファイルに保存（別ファイル）
        summary_output_csv = output_csv.parent / output_csv.name.replace('.csv', '_summary.csv')
        summary_df = pd.DataFrame([summary_stats])
        summary_df.to_csv(summary_output_csv, index=False)
        print(f"  評価サマリー保存: {summary_output_csv}")
    else:
        print(f"  警告: 選択されたリンクがありません")

    # CSV保存
    results_df.to_csv(output_csv, index=False)
    print(f"\n[5] 出力ファイル: {output_csv}")
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
