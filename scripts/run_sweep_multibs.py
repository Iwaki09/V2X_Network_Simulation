#!/usr/bin/env python3
"""
複数BS + C_b sweep 実験スクリプト

交差点シナリオを3基地局化し、基地局定員C_bを{10,15,20,30}でsweepして
提案手法の優位性（アウトエージ回避と下位性能）を示すための実験一式を実行します。

実行内容：
1. レイトレーシング（corner_intersection、3BS）
2. スループット計算
3. 各C_bについて4手法×2目的を実行
4. 追加可視化（BS負荷分布、負荷分散指標、C_b sweep図）
5. 自動チェック（複数BS検証、sweep完全性）
"""

import sys
import subprocess
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import json

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.optimization.candidates import generate_candidates
from src.optimization.optimizer import solve_optimization
from src.optimization.methods import random_assignment, greedy_assignment
from src.optimization.plotting import generate_all_plots, calculate_summary


def run_raytracing(scenario: str, output_base: Path, use_sionna: bool = True):
    """レイトレーシングを実行"""
    print("\n" + "=" * 80)
    print("レイトレーシング実行中...")
    print("=" * 80)

    cmd = [
        "python3", "simulation/scripts/run_raytracing.py",
        "--scenario", scenario,
        "--v2v-max-distance", "200.0"
    ]

    if use_sionna:
        cmd.append("--sionna-rt")

    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ レイトレーシング失敗: {result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("✅ レイトレーシング完了")

    # 出力ファイルパスを返す
    raytracing_output = project_root / f"simulation/output/scenarios/{scenario}/raytracing/link_quality_results.csv"
    return raytracing_output


def run_throughput(input_csv: Path, scenario: str):
    """スループット計算を実行"""
    print("\n" + "=" * 80)
    print("スループット計算実行中...")
    print("=" * 80)

    cmd = [
        "python3", "simulation/scripts/run_throughput.py",
        "--input", str(input_csv),
        "--scenario", scenario,
        "--rate-model", "mcs",
        "--enable-margin-estimate",
        "--margin-d-db", "6.5",
        "--margin-k-db", "6.5"
    ]

    result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ スループット計算失敗: {result.stderr}")
        sys.exit(1)

    print(result.stdout)
    print("✅ スループット計算完了")

    # 出力ファイルパスを返す
    throughput_output = project_root / f"simulation/output/scenarios/{scenario}/throughput/theoretical_network_results.csv"
    return throughput_output


def verify_multi_bs(theoretical_csv: Path) -> Dict:
    """複数BS化の検証（必須）"""
    print("\n" + "=" * 80)
    print("複数BS検証中...")
    print("=" * 80)

    df = pd.read_csv(theoretical_csv)

    # V2Iリンクのみ抽出
    df_v2i = df[df['link_type'] == 'V2I'].copy()

    # BSの識別（tx_idから）
    unique_bs = df_v2i['tx_id'].nunique()
    bs_counts = df_v2i['tx_id'].value_counts()

    # timestampごとのユニークBS数
    bs_per_timestamp = df_v2i.groupby('timestamp')['tx_id'].nunique()

    verification = {
        'unique_bs_count': unique_bs,
        'bs_link_counts': bs_counts.to_dict(),
        'min_bs_per_timestamp': bs_per_timestamp.min(),
        'mean_bs_per_timestamp': bs_per_timestamp.mean(),
        'max_bs_per_timestamp': bs_per_timestamp.max(),
    }

    print(f"  - ユニークBS数: {unique_bs}")
    print(f"  - BS別リンク数:")
    for bs_id, count in bs_counts.items():
        print(f"      {bs_id}: {count} links")
    print(f"  - timestampあたりBS数: min={verification['min_bs_per_timestamp']}, "
          f"mean={verification['mean_bs_per_timestamp']:.2f}, max={verification['max_bs_per_timestamp']}")

    # 検証判定
    if unique_bs < 2:
        print("  ⚠️  警告: ユニークBS数が1のままです。複数BS化が正しく機能していません。")
    else:
        print(f"  ✅ 検証OK: {unique_bs}個のBSが検出されました。")

    return verification


def run_optimization_for_cb(
    theoretical_csv: Path,
    cb_value: int,
    outdir: Path,
    neighbor_radius: float = 200.0,
    max_neighbors: int = 5,
    max_bs_candidates: int = 3,
    outage_threshold_mbps: float = 0.0,
    margin_d_db: float = 6.5,
    margin_k_db: float = 6.5,
    seed: int = 42,
    rolling_window: int = 0
) -> Dict:
    """指定されたC_bで最適化を実行"""

    print("\n" + "=" * 80)
    print(f"C_b={cb_value} の最適化実行中...")
    print("=" * 80)

    # 出力ディレクトリ作成
    outdir.mkdir(parents=True, exist_ok=True)
    plots_dir = outdir / 'plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: データ読み込み
    print("\n[1/7] データ読み込み中...")
    df_network = pd.read_csv(theoretical_csv)
    print(f"  - 読み込み完了: {len(df_network)} 行")

    # Step 2: 候補生成
    print("\n[2/7] 候補生成中...")
    candidates_df = generate_candidates(
        df_network=df_network,
        max_bs_candidates=max_bs_candidates,
        neighbor_radius_m=neighbor_radius,
        max_neighbors=max_neighbors,
        margin_d_db=margin_d_db,
        margin_k_db=margin_k_db,
        outage_threshold_mbps=outage_threshold_mbps,
    )
    print(f"  - 候補数: {len(candidates_df)}")
    print(f"  - Direct候補: {(candidates_df['action_type'] == 'direct').sum()}")
    print(f"  - Relay候補: {(candidates_df['action_type'] == 'relay').sum()}")

    # 候補統計（自動チェック用）
    candidate_stats = {
        'total_candidates': len(candidates_df),
        'direct_candidates': int((candidates_df['action_type'] == 'direct').sum()),
        'relay_candidates': int((candidates_df['action_type'] == 'relay').sum()),
    }

    # 候補を保存
    candidates_df.to_csv(outdir / 'candidates.csv', index=False)
    print(f"  - 候補を保存: {outdir / 'candidates.csv'}")

    # Step 3: 各手法を実行
    print("\n[3/7] 各手法を実行中...")

    all_results = {}
    all_assignments = []

    # 3-1. Random
    print("  - Random割当中...")
    result_random = random_assignment(candidates_df, cb_value, seed)
    result_random['method'] = 'random'
    result_random['objective'] = 'throughput'
    all_results['random'] = {'throughput': result_random.copy()}
    all_assignments.append(result_random)
    result_random.to_csv(outdir / 'assignment_random.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_random)['outage_rate']:.3f})")

    # 3-2. Greedy (MCS)
    print("  - Greedy (MCS) 割当中...")
    result_greedy = greedy_assignment(candidates_df, cb_value)
    result_greedy['method'] = 'greedy_mcs'
    result_greedy['objective'] = 'throughput'
    all_results['greedy_mcs'] = {'throughput': result_greedy.copy()}
    all_assignments.append(result_greedy)
    result_greedy.to_csv(outdir / 'assignment_greedy_mcs.csv', index=False)
    print(f"    ✓ 完了 (outage_rate={calculate_summary(result_greedy)['outage_rate']:.3f})")

    # 3-3. Optimal Shannon (Throughput)
    print("  - Optimal Shannon (Throughput) 最適化中...")
    result_opt_shannon_T = solve_optimization(
        candidates_df,
        cb_value,
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
        cb_value,
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
        cb_value,
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
        cb_value,
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
        summary['cb_value'] = cb_value
        summaries.append(summary)

    df_summary = pd.DataFrame(summaries)
    df_summary.to_csv(outdir / 'summary.csv', index=False)
    print(f"  - サマリーを保存: {outdir / 'summary.csv'}")

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
        'random': all_results['random']['throughput'],
        'greedy_mcs': all_results['greedy_mcs']['throughput'],
        'optimal_shannon_O': all_results['optimal_shannon']['outage'],
        'proposed_O': all_results['proposed_optimal_dkmcs']['outage'],
    }

    generate_all_plots(results_T, results_O, all_results, plots_dir, rolling_window)

    # Step 7: 完了
    print("\n[7/7] C_b={} の最適化完了!".format(cb_value))

    return {
        'cb_value': cb_value,
        'summary': df_summary,
        'candidate_stats': candidate_stats,
        'all_assignments': df_all_assignments,
    }


def generate_additional_plots(sweep_results: List[Dict], output_base: Path):
    """追加可視化（BS負荷分布、負荷分散指標、C_b sweep図）"""

    print("\n" + "=" * 80)
    print("追加可視化生成中...")
    print("=" * 80)

    # sweep_results から全サマリーを集約
    all_summaries = []
    for result in sweep_results:
        all_summaries.append(result['summary'])

    df_all_summary = pd.concat(all_summaries, ignore_index=True)

    # C_b sweep図を生成
    plot_cb_sweep_metrics(df_all_summary, output_base)

    print("✅ 追加可視化完了")


def plot_cb_sweep_metrics(df_summary: pd.DataFrame, output_base: Path):
    """C_b sweepのまとめ図を生成"""

    plots_dir = output_base / 'sweep_plots'
    plots_dir.mkdir(parents=True, exist_ok=True)

    # 目的別にデータを分割
    df_T = df_summary[df_summary['objective'] == 'throughput'].copy()
    df_O = df_summary[df_summary['objective'] == 'outage'].copy()

    methods = ['random', 'greedy_mcs', 'optimal_shannon', 'proposed_optimal_dkmcs']
    method_labels = {
        'random': 'Random',
        'greedy_mcs': 'Greedy (MCS)',
        'optimal_shannon': 'Optimal (Shannon)',
        'proposed_optimal_dkmcs': 'Proposed (D/K×MCS)',
    }

    # 1. Outage Rate vs C_b (Throughput目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_T[df_T['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['outage_rate'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('Outage Rate', fontsize=12)
    plt.title('Outage Rate vs C_b (Throughput Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'outage_rate_vs_Cb_T.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'outage_rate_vs_Cb_T.png'}")

    # 2. Outage Rate vs C_b (Outage目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_O[df_O['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['outage_rate'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('Outage Rate', fontsize=12)
    plt.title('Outage Rate vs C_b (Outage Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'outage_rate_vs_Cb_O.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'outage_rate_vs_Cb_O.png'}")

    # 3. P05 vs C_b (Throughput目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_T[df_T['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['p05'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('P05 Throughput [Mbps]', fontsize=12)
    plt.title('P05 Throughput vs C_b (Throughput Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'p05_vs_Cb_T.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'p05_vs_Cb_T.png'}")

    # 4. P05 vs C_b (Outage目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_O[df_O['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['p05'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('P05 Throughput [Mbps]', fontsize=12)
    plt.title('P05 Throughput vs C_b (Outage Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'p05_vs_Cb_O.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'p05_vs_Cb_O.png'}")

    # 5. Mean Throughput vs C_b (Throughput目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_T[df_T['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['mean_throughput_mbps'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('Mean Throughput [Mbps]', fontsize=12)
    plt.title('Mean Throughput vs C_b (Throughput Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'mean_vs_Cb_T.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'mean_vs_Cb_T.png'}")

    # 6. Mean Throughput vs C_b (Outage目的)
    plt.figure(figsize=(10, 6))
    for method in methods:
        df_method = df_O[df_O['method'] == method].sort_values('cb_value')
        plt.plot(df_method['cb_value'], df_method['mean_throughput_mbps'],
                marker='o', label=method_labels[method], linewidth=2)
    plt.xlabel('BS Capacity (C_b)', fontsize=12)
    plt.ylabel('Mean Throughput [Mbps]', fontsize=12)
    plt.title('Mean Throughput vs C_b (Outage Objective)', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / 'mean_vs_Cb_O.png', dpi=300)
    plt.close()
    print(f"  - 保存: {plots_dir / 'mean_vs_Cb_O.png'}")


def perform_automatic_checks(sweep_results: List[Dict], verification: Dict):
    """実験後の自動チェック（必須）"""

    print("\n" + "=" * 80)
    print("自動チェック実行中...")
    print("=" * 80)

    checks_passed = True

    # チェック1: ユニークBS数
    if verification['unique_bs_count'] < 2:
        print("  ❌ チェック失敗: ユニークBS数が1のままです")
        checks_passed = False
    else:
        print(f"  ✅ チェックOK: {verification['unique_bs_count']}個のBSが検出されました")

    # チェック2: C_b sweepの完全性
    cb_values_expected = {10, 15, 20, 30}
    cb_values_actual = {r['cb_value'] for r in sweep_results}

    if cb_values_actual != cb_values_expected:
        print(f"  ❌ チェック失敗: C_b sweep が不完全です（期待: {cb_values_expected}、実際: {cb_values_actual}）")
        checks_passed = False
    else:
        print(f"  ✅ チェックOK: C_b sweep が完全です（{cb_values_actual}）")

    # チェック3: 各C_bで結果ファイルが生成されているか
    for result in sweep_results:
        cb = result['cb_value']
        summary = result['summary']

        if summary.empty:
            print(f"  ❌ チェック失敗: C_b={cb} のサマリーが空です")
            checks_passed = False
        else:
            print(f"  ✅ チェックOK: C_b={cb} の結果が生成されています（{len(summary)}件）")

    # チェック4: GreedyとILPが完全同値かチェック（問題がある場合の補助ログ）
    print("\n  --- Greedy vs ILP 同値性チェック ---")
    for result in sweep_results:
        cb = result['cb_value']
        summary = result['summary']

        # Throughput目的のGreedyとOptimal Shannon
        greedy_summary = summary[(summary['method'] == 'greedy_mcs') & (summary['objective'] == 'throughput')]
        optimal_summary = summary[(summary['method'] == 'optimal_shannon') & (summary['objective'] == 'throughput')]

        if not greedy_summary.empty and not optimal_summary.empty:
            greedy_outage = greedy_summary['outage_rate'].iloc[0]
            optimal_outage = optimal_summary['outage_rate'].iloc[0]

            if abs(greedy_outage - optimal_outage) < 0.001:
                print(f"    [C_b={cb}] Greedy == Optimal (outage_rate: {greedy_outage:.4f})")
                print(f"      → 候補統計: Direct={result['candidate_stats']['direct_candidates']}, "
                      f"Relay={result['candidate_stats']['relay_candidates']}")
            else:
                print(f"    [C_b={cb}] Greedy != Optimal (Greedy: {greedy_outage:.4f}, Optimal: {optimal_outage:.4f})")

    print("\n" + "=" * 80)
    if checks_passed:
        print("✅ 全チェック通過!")
    else:
        print("⚠️  一部チェック失敗。上記の警告を確認してください。")
    print("=" * 80)

    return checks_passed


def main():
    parser = argparse.ArgumentParser(
        description='複数BS + C_b sweep 実験',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 scripts/run_sweep_multibs.py --outdir simulation/output/multibs_3

実行内容:
  1. レイトレーシング（corner_intersection、3BS）
  2. スループット計算
  3. C_b ∈ {10,15,20,30} で最適化実行
  4. 追加可視化（BS負荷分布、C_b sweep図）
  5. 自動チェック
        """
    )

    parser.add_argument('--outdir', type=str, required=True,
                        help='出力ベースディレクトリ（例: simulation/output/multibs_3）')
    parser.add_argument('--scenario', type=str, default='corner_intersection',
                        help='シナリオ名（デフォルト: corner_intersection）')
    parser.add_argument('--cb-values', type=int, nargs='+', default=[10, 15, 20, 30],
                        help='C_bのsweep値リスト（デフォルト: 10 15 20 30）')
    parser.add_argument('--skip-raytracing', action='store_true',
                        help='レイトレーシングをスキップ（既存結果を使用）')
    parser.add_argument('--skip-throughput', action='store_true',
                        help='スループット計算をスキップ（既存結果を使用）')
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
    parser.add_argument('--use-sionna', action='store_true',
                        help='Sionna RTを使用（マルチパス、D/K判定に必要）')

    args = parser.parse_args()

    output_base = Path(args.outdir)
    output_base.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("複数BS + C_b Sweep 実験")
    print("=" * 80)
    print(f"シナリオ: {args.scenario}")
    print(f"出力ディレクトリ: {args.outdir}")
    print(f"C_b sweep値: {args.cb_values}")
    print("=" * 80)

    # Step 1: レイトレーシング（一度だけ）
    theoretical_csv = project_root / f"simulation/output/scenarios/{args.scenario}/throughput/theoretical_network_results.csv"

    if not args.skip_raytracing:
        raytracing_csv = run_raytracing(args.scenario, output_base, args.use_sionna)
    else:
        print("\n⏩ レイトレーシングをスキップ（既存結果を使用）")
        raytracing_csv = project_root / f"simulation/output/scenarios/{args.scenario}/raytracing/link_quality_results.csv"

    # Step 2: スループット計算（一度だけ）
    if not args.skip_throughput:
        theoretical_csv = run_throughput(raytracing_csv, args.scenario)
    else:
        print("\n⏩ スループット計算をスキップ（既存結果を使用）")

    # Step 3: 複数BS検証
    verification = verify_multi_bs(theoretical_csv)

    # 検証結果を保存
    verification_file = output_base / 'verification.json'
    with open(verification_file, 'w') as f:
        json.dump(verification, f, indent=2)
    print(f"\n  - 検証結果を保存: {verification_file}")

    # Step 4: C_b sweep
    sweep_results = []

    for cb_value in args.cb_values:
        cb_outdir = output_base / f'Cb_{cb_value}'

        result = run_optimization_for_cb(
            theoretical_csv=theoretical_csv,
            cb_value=cb_value,
            outdir=cb_outdir,
            neighbor_radius=args.neighbor_radius,
            max_neighbors=args.max_neighbors,
            max_bs_candidates=args.max_bs_candidates,
            outage_threshold_mbps=args.outage_threshold_mbps,
            margin_d_db=args.margin_d_db,
            margin_k_db=args.margin_k_db,
            seed=args.seed,
            rolling_window=args.rolling_window
        )

        sweep_results.append(result)

    # Step 5: 追加可視化
    generate_additional_plots(sweep_results, output_base)

    # Step 6: 自動チェック
    checks_passed = perform_automatic_checks(sweep_results, verification)

    # Step 7: 完了
    print("\n" + "=" * 80)
    print("実験完了!")
    print("=" * 80)
    print(f"すべての結果が {args.outdir} に保存されました。")
    print("\n各C_bの結果:")
    for cb_value in args.cb_values:
        print(f"  - C_b={cb_value}: {output_base / f'Cb_{cb_value}'}")
    print(f"\nSweep プロット: {output_base / 'sweep_plots'}")
    print("=" * 80)

    if not checks_passed:
        print("\n⚠️  一部のチェックが失敗しました。上記のログを確認してください。")
        sys.exit(1)


if __name__ == '__main__':
    main()
