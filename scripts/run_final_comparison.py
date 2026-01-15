#!/usr/bin/env python3
"""
V2X割当最適化の最終比較実行スクリプト

4つの手法（random、greedy_mcs、optimal_shannon、proposed_optimal_dkmcs）と
2つの目的（throughput、outage）を比較評価します。
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.optimization.candidates import generate_candidates, get_rate_column
from src.optimization.optimizer import solve_optimization
from src.optimization.methods import random_assignment, greedy_assignment
from src.optimization.plotting import generate_all_plots, calculate_summary


def main():
    parser = argparse.ArgumentParser(description='V2X割当最適化の最終比較実行')
    parser.add_argument('--input-theoretical', type=str, required=True,
                        help='入力CSVファイル（theoretical_network_results.csv）')
    parser.add_argument('--outdir', type=str, required=True,
                        help='出力ディレクトリ')
    parser.add_argument('--bs-capacity', type=int, default=5,
                        help='各BSの容量（デフォルト: 5）')
    parser.add_argument('--neighbor-radius', type=float, default=200.0,
                        help='近傍車の最大距離（デフォルト: 200.0）')
    parser.add_argument('--max-neighbors', type=int, default=5,
                        help='各車両あたりの最大近傍車数（デフォルト: 5）')
    parser.add_argument('--max-bs-candidates', type=int, default=3,
                        help='各車両あたりの最大BS候補数（デフォルト: 3）')
    parser.add_argument('--outage-threshold-mbps', type=float, default=0.0,
                        help='アウトエージ閾値（デフォルト: 0.0）')
    parser.add_argument('--margin-d-db', type=float, default=6.5,
                        help='LOS系（D）のマージン（デフォルト: 6.5）')
    parser.add_argument('--margin-k-db', type=float, default=6.5,
                        help='NLOS系（K）のマージン（デフォルト: 6.5）')
    parser.add_argument('--seed', type=int, default=42,
                        help='乱数シード（デフォルト: 42）')
    parser.add_argument('--rolling-window', type=int, default=0,
                        help='時系列プロットの移動平均ウィンドウ（デフォルト: 0=無効）')

    args = parser.parse_args()

    # 出力ディレクトリ作成
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    plots_dir = outdir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("V2X割当最適化 最終比較実行")
    print("=" * 60)
    print(f"入力ファイル: {args.input_theoretical}")
    print(f"出力ディレクトリ: {args.outdir}")
    print(f"BS容量: {args.bs_capacity}")
    print(f"近傍車距離: {args.neighbor_radius}m")
    print(f"最大近傍車数: {args.max_neighbors}")
    print(f"最大BS候補数: {args.max_bs_candidates}")
    print(f"アウトエージ閾値: {args.outage_threshold_mbps} Mbps")
    print(f"マージン D/K: {args.margin_d_db}/{args.margin_k_db} dB")
    print(f"乱数シード: {args.seed}")
    print("=" * 60)

    # Step 1: データ読み込み
    print("\n[1/7] データ読み込み中...")
    df_network = pd.read_csv(args.input_theoretical)
    print(f"  - 読み込み完了: {len(df_network)} 行")

    # Step 2: 候補生成
    print("\n[2/7] 候補生成中...")
    candidates_df = generate_candidates(
        df_network=df_network,
        max_bs_candidates=args.max_bs_candidates,
        neighbor_radius_m=args.neighbor_radius,
        max_neighbors=args.max_neighbors,
        margin_d_db=args.margin_d_db,
        margin_k_db=args.margin_k_db,
        outage_threshold_mbps=args.outage_threshold_mbps,
    )
    print(f"  - 候補数: {len(candidates_df)}")
    print(f"  - Direct候補: {(candidates_df['action_type'] == 'direct').sum()}")
    print(f"  - Relay候補: {(candidates_df['action_type'] == 'relay').sum()}")

    # 候補を保存
    candidates_df.to_csv(outdir / 'candidates.csv', index=False)
    print(f"  - 候補を保存: {outdir / 'candidates.csv'}")

    # Step 3: 各手法を実行
    print("\n[3/7] 各手法を実行中...")

    all_results = {}
    all_assignments = []

    # 3-1. Random
    print("  - Random割当中...")
    result_random = random_assignment(candidates_df, args.bs_capacity, args.seed)
    result_random['method'] = 'random'
    result_random['objective'] = 'throughput'  # Randomは目的によらず同じ
    all_results['random'] = {'throughput': result_random.copy()}
    all_assignments.append(result_random)
    result_random.to_csv(outdir / 'assignment_random.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_random)['outage_rate']:.3f})")

    # 3-2. Greedy (MCS)
    print("  - Greedy (MCS) 割当中...")
    result_greedy = greedy_assignment(candidates_df, args.bs_capacity)
    result_greedy['method'] = 'greedy_mcs'
    result_greedy['objective'] = 'throughput'  # Greedyは目的によらず同じ
    all_results['greedy_mcs'] = {'throughput': result_greedy.copy()}
    all_assignments.append(result_greedy)
    result_greedy.to_csv(outdir / 'assignment_greedy_mcs.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_greedy)['outage_rate']:.3f})")

    # 3-3. Optimal Shannon (Throughput)
    print("  - Optimal Shannon (Throughput) 最適化中...")
    result_opt_shannon_T = solve_optimization(
        candidates_df,
        args.bs_capacity,
        rate_col='rate_shannon',
        objective='throughput',
        verbose=False,
    )
    result_opt_shannon_T['method'] = 'optimal_shannon'
    result_opt_shannon_T['objective'] = 'throughput'
    if 'optimal_shannon' not in all_results:
        all_results['optimal_shannon'] = {}
    all_results['optimal_shannon']['throughput'] = result_opt_shannon_T.copy()
    all_assignments.append(result_opt_shannon_T)
    result_opt_shannon_T.to_csv(outdir / 'assignment_optimal_shannon_T.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_opt_shannon_T)['outage_rate']:.3f})")

    # 3-4. Optimal Shannon (Outage)
    print("  - Optimal Shannon (Outage) 最適化中...")
    result_opt_shannon_O = solve_optimization(
        candidates_df,
        args.bs_capacity,
        rate_col='rate_shannon',
        objective='outage',
        verbose=False,
    )
    result_opt_shannon_O['method'] = 'optimal_shannon'
    result_opt_shannon_O['objective'] = 'outage'
    all_results['optimal_shannon']['outage'] = result_opt_shannon_O.copy()
    all_assignments.append(result_opt_shannon_O)
    result_opt_shannon_O.to_csv(outdir / 'assignment_optimal_shannon_O.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_opt_shannon_O)['outage_rate']:.3f})")

    # 3-5. Proposed Optimal (D/K×MCS+margin) (Throughput)
    print("  - Proposed Optimal (D/K×MCS+margin) (Throughput) 最適化中...")
    result_proposed_T = solve_optimization(
        candidates_df,
        args.bs_capacity,
        rate_col='rate_dkmcs',
        objective='throughput',
        verbose=False,
    )
    result_proposed_T['method'] = 'proposed_optimal_dkmcs'
    result_proposed_T['objective'] = 'throughput'
    if 'proposed_optimal_dkmcs' not in all_results:
        all_results['proposed_optimal_dkmcs'] = {}
    all_results['proposed_optimal_dkmcs']['throughput'] = result_proposed_T.copy()
    all_assignments.append(result_proposed_T)
    result_proposed_T.to_csv(outdir / 'assignment_proposed_optimal_dkmcs_T.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_proposed_T)['outage_rate']:.3f})")

    # 3-6. Proposed Optimal (D/K×MCS+margin) (Outage)
    print("  - Proposed Optimal (D/K×MCS+margin) (Outage) 最適化中...")
    result_proposed_O = solve_optimization(
        candidates_df,
        args.bs_capacity,
        rate_col='rate_dkmcs',
        objective='outage',
        verbose=False,
    )
    result_proposed_O['method'] = 'proposed_optimal_dkmcs'
    result_proposed_O['objective'] = 'outage'
    all_results['proposed_optimal_dkmcs']['outage'] = result_proposed_O.copy()
    all_assignments.append(result_proposed_O)
    result_proposed_O.to_csv(outdir / 'assignment_proposed_optimal_dkmcs_O.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_proposed_O)['outage_rate']:.3f})")

    # Step 4: 全結果を統合して保存
    print("\n[4/7] 全結果を統合中...")
    df_all_assignments = pd.concat(all_assignments, ignore_index=True)
    df_all_assignments.to_csv(outdir / 'all_assignments.csv', index=False)
    print(f"  - 統合結果を保存: {outdir / 'all_assignments.csv'}")

    # Step 5: サマリー生成
    print("\n[5/7] サマリー生成中...")
    summaries = []
    for assignments_df in all_assignments:
        method = assignments_df['method'].iloc[0]
        objective = assignments_df['objective'].iloc[0]
        summary = calculate_summary(assignments_df)
        summary['method'] = method
        summary['objective'] = objective
        summaries.append(summary)

    df_summary = pd.DataFrame(summaries)
    df_summary.to_csv(outdir / 'summary.csv', index=False)
    print(f"  - サマリーを保存: {outdir / 'summary.csv'}")
    print("\n" + "=" * 60)
    print("サマリー:")
    print(df_summary.to_string(index=False))
    print("=" * 60)

    # Step 6: プロット生成
    print("\n[6/7] プロット生成中...")

    # Throughput目的セット（4手法）
    results_T = {
        'random': all_results['random']['throughput'],
        'greedy_mcs': all_results['greedy_mcs']['throughput'],
        'optimal_shannon_T': all_results['optimal_shannon']['throughput'],
        'proposed_T': all_results['proposed_optimal_dkmcs']['throughput'],
    }

    # Outage目的セット（4手法）
    results_O = {
        'random': all_results['random']['throughput'],  # Randomは同じ
        'greedy_mcs': all_results['greedy_mcs']['throughput'],  # Greedyも同じ
        'optimal_shannon_O': all_results['optimal_shannon']['outage'],
        'proposed_O': all_results['proposed_optimal_dkmcs']['outage'],
    }

    generate_all_plots(results_T, results_O, all_results, plots_dir, args.rolling_window)

    # Step 7: 完了
    print("\n[7/7] 完了!")
    print("=" * 60)
    print(f"すべての結果が {args.outdir} に保存されました。")
    print(f"プロットは {plots_dir} に保存されました。")
    print("=" * 60)


if __name__ == '__main__':
    main()
