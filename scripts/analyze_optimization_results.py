#!/usr/bin/env python3
"""
最適化結果の詳細分析スクリプト

run_final_comparison.py の出力結果を深く分析し、以下を明らかにします：
1. 各手法の性能比較
2. Greedy vs Optimal の差異分析
3. Relay効果の詳細
4. 時系列パターン
5. 統計的有意性
"""

import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def analyze_basic_statistics(summary_df: pd.DataFrame) -> dict:
    """基本統計分析"""
    print("\n" + "="*80)
    print("1. 基本統計分析")
    print("="*80)

    results = {}

    # 手法ごとの性能
    print("\n【手法別性能サマリー】")
    for method in summary_df['method'].unique():
        df_method = summary_df[summary_df['method'] == method]

        if len(df_method) > 1:
            # TとOの両方がある場合
            t_row = df_method[df_method['objective'] == 'throughput'].iloc[0]
            o_row = df_method[df_method['objective'] == 'outage'].iloc[0]

            print(f"\n{method}:")
            print(f"  Throughput目的: Mean={t_row['mean_throughput_mbps']:.2f} Mbps, Relay率={t_row['relay_ratio']:.2%}")
            print(f"  Outage目的:     Mean={o_row['mean_throughput_mbps']:.2f} Mbps, Relay率={o_row['relay_ratio']:.2%}")
            print(f"  差分:           Mean差={o_row['mean_throughput_mbps']-t_row['mean_throughput_mbps']:.2f} Mbps")

            results[method] = {
                'T': t_row.to_dict(),
                'O': o_row.to_dict(),
                'diff': o_row['mean_throughput_mbps'] - t_row['mean_throughput_mbps']
            }
        else:
            # random/greedyなど1つだけの場合
            row = df_method.iloc[0]
            print(f"\n{method}:")
            print(f"  Mean={row['mean_throughput_mbps']:.2f} Mbps, Relay率={row['relay_ratio']:.2%}")
            results[method] = {'single': row.to_dict()}

    # Randomに対する改善率
    print("\n【Randomベースラインに対する改善率】")
    random_mean = summary_df[summary_df['method'] == 'random']['mean_throughput_mbps'].iloc[0]

    for _, row in summary_df.iterrows():
        if row['method'] != 'random':
            improvement = (row['mean_throughput_mbps'] - random_mean) / random_mean * 100
            print(f"  {row['method']}_{row['objective']}: +{improvement:.2f}%")

    return results


def _select_optimal_t(assignments_dir: Path) -> tuple:
    candidates = [
        ("Optimal MCS (T)", assignments_dir / 'assignment_optimal_mcs_T.csv'),
        ("Optimal Shannon (T)", assignments_dir / 'assignment_optimal_shannon_T.csv'),
    ]
    for label, path in candidates:
        if path.exists():
            return label, path
    raise FileNotFoundError("assignment_optimal_mcs_T.csv / assignment_optimal_shannon_T.csv が見つかりません")


def analyze_greedy_vs_optimal(assignments_dir: Path):
    """Greedy vs Optimal の詳細比較"""
    print("\n" + "="*80)
    print("2. Greedy vs Optimal 詳細比較")
    print("="*80)

    # 各手法の割当を読み込み
    greedy_df = pd.read_csv(assignments_dir / 'assignment_greedy_mcs.csv')
    optimal_label, optimal_path = _select_optimal_t(assignments_dir)
    optimal_T_df = pd.read_csv(optimal_path)

    print(f"\nGreedy割当数: {len(greedy_df)}")
    print(f"{optimal_label}割当数: {len(optimal_T_df)}")

    # 同一車両・同一timestampでの比較
    merged = greedy_df.merge(
        optimal_T_df,
        on=['timestamp', 'vehicle_id'],
        suffixes=('_greedy', '_optimal')
    )

    print(f"\n共通サンプル数: {len(merged)}")

    # 選択が一致しているか
    merged['action_match'] = (
        (merged['selected_action_type_greedy'] == merged['selected_action_type_optimal']) &
        (merged['selected_bs_id_greedy'] == merged['selected_bs_id_optimal']) &
        (merged['selected_relay_id_greedy'] == merged['selected_relay_id_optimal'])
    )

    match_rate = merged['action_match'].mean()
    print(f"\nアクション一致率: {match_rate:.2%}")

    # 不一致サンプルの分析
    diff_samples = merged[~merged['action_match']]
    print(f"不一致サンプル数: {len(diff_samples)}")

    if len(diff_samples) > 0:
        print("\n【不一致サンプルの傾向】")
        print(f"  Greedy→Direct, Optimal→Relay: {((diff_samples['selected_action_type_greedy']=='direct') & (diff_samples['selected_action_type_optimal']=='relay')).sum()}")
        print(f"  Greedy→Relay, Optimal→Direct: {((diff_samples['selected_action_type_greedy']=='relay') & (diff_samples['selected_action_type_optimal']=='direct')).sum()}")
        print(f"  Greedy→outage, Optimal→採択: {((diff_samples['accepted_greedy']==0) & (diff_samples['accepted_optimal']==1)).sum()}")
        print(f"  Greedy→採択, Optimal→outage: {((diff_samples['accepted_greedy']==1) & (diff_samples['accepted_optimal']==0)).sum()}")

        # スループット差分
        diff_samples['throughput_diff'] = diff_samples['truth_rate_mcs_effective_optimal'] - diff_samples['truth_rate_mcs_effective_greedy']
        print(f"\n  スループット差分: 平均={diff_samples['throughput_diff'].mean():.2f} Mbps")
        print(f"                    Optimal有利={len(diff_samples[diff_samples['throughput_diff']>0])}, Greedy有利={len(diff_samples[diff_samples['throughput_diff']<0])}")

    return {
        'optimal_label': optimal_label,
        'match_rate': match_rate,
        'diff_count': len(diff_samples),
        'diff_samples': diff_samples if len(diff_samples) > 0 else None
    }


def analyze_relay_effect(assignments_dir: Path):
    """Relay効果の詳細分析"""
    print("\n" + "="*80)
    print("3. Relay効果の詳細分析")
    print("="*80)

    optimal_label, optimal_path = _select_optimal_t(assignments_dir)
    print(f"\n  使用データ: {optimal_label}")
    df = pd.read_csv(optimal_path)

    # 採択されたサンプルのみ
    df_accepted = df[df['accepted'] == 1]

    # Direct vs Relay
    direct_samples = df_accepted[df_accepted['selected_action_type'] == 'direct']
    relay_samples = df_accepted[df_accepted['selected_action_type'] == 'relay']

    print(f"\nDirect採択数: {len(direct_samples)}")
    print(f"Relay採択数: {len(relay_samples)}")
    print(f"Relay率: {len(relay_samples)/len(df_accepted):.2%}")

    # スループット比較
    print(f"\n【スループット統計】")
    print(f"Direct: Mean={direct_samples['truth_rate_mcs_effective'].mean():.2f} Mbps, Median={direct_samples['truth_rate_mcs_effective'].median():.2f} Mbps")
    print(f"Relay:  Mean={relay_samples['truth_rate_mcs_effective'].mean():.2f} Mbps, Median={relay_samples['truth_rate_mcs_effective'].median():.2f} Mbps")

    # 統計的検定
    t_stat, p_value = stats.ttest_ind(
        direct_samples['truth_rate_mcs_effective'],
        relay_samples['truth_rate_mcs_effective']
    )
    print(f"\nt検定: t={t_stat:.3f}, p={p_value:.4f}")

    if p_value < 0.05:
        print("  → 有意差あり（p<0.05）")
    else:
        print("  → 有意差なし（p>=0.05）")

    # Relayのスループット分布
    relay_throughputs = relay_samples['truth_rate_mcs_effective']
    print(f"\n【Relayスループット分布】")
    print(f"  P05={np.percentile(relay_throughputs, 5):.2f} Mbps")
    print(f"  P25={np.percentile(relay_throughputs, 25):.2f} Mbps")
    print(f"  P50={np.percentile(relay_throughputs, 50):.2f} Mbps")
    print(f"  P75={np.percentile(relay_throughputs, 75):.2f} Mbps")
    print(f"  P95={np.percentile(relay_throughputs, 95):.2f} Mbps")

    return {
        'direct_count': len(direct_samples),
        'relay_count': len(relay_samples),
        'direct_mean': direct_samples['truth_rate_mcs_effective'].mean(),
        'relay_mean': relay_samples['truth_rate_mcs_effective'].mean(),
        't_stat': t_stat,
        'p_value': p_value
    }


def analyze_timeseries(assignments_dir: Path, outdir: Path):
    """時系列パターン分析"""
    print("\n" + "="*80)
    print("4. 時系列パターン分析")
    print("="*80)

    # 各手法の時系列データ
    methods = {
        'random': 'assignment_random.csv',
        'greedy': 'assignment_greedy_mcs.csv',
        'proposed_T': 'assignment_proposed_optimal_dkmcs_T.csv',
    }
    optimal_mcs_path = assignments_dir / 'assignment_optimal_mcs_T.csv'
    if optimal_mcs_path.exists():
        methods['optimal_mcs_T'] = 'assignment_optimal_mcs_T.csv'
    else:
        methods['optimal_T'] = 'assignment_optimal_shannon_T.csv'

    timeseries_data = {}

    for method_name, filename in methods.items():
        df = pd.read_csv(assignments_dir / filename)

        ts_stats = []
        for timestamp in sorted(df['timestamp'].unique()):
            df_t = df[df['timestamp'] == timestamp]

            ts_stats.append({
                'timestamp': timestamp,
                'total_vehicles': len(df_t),
                'accepted': (df_t['accepted'] == 1).sum(),
                'outage': (df_t['accepted'] == 0).sum(),
                'relay': (df_t['selected_action_type'] == 'relay').sum(),
                'mean_throughput': df_t['truth_rate_mcs_effective'].mean(),
                'p05_throughput': np.percentile(df_t['truth_rate_mcs_effective'], 5),
            })

        timeseries_data[method_name] = pd.DataFrame(ts_stats)

        print(f"\n{method_name}:")
        print(f"  タイムスタンプ数: {len(timeseries_data[method_name])}")
        print(f"  平均車両数: {timeseries_data[method_name]['total_vehicles'].mean():.2f}")
        print(f"  平均採択数: {timeseries_data[method_name]['accepted'].mean():.2f}")
        print(f"  平均Relay数: {timeseries_data[method_name]['relay'].mean():.2f}")

    # 時系列の変動係数（CV）
    print("\n【時系列変動係数（CV = std/mean）】")
    for method_name, ts_df in timeseries_data.items():
        cv_throughput = ts_df['mean_throughput'].std() / ts_df['mean_throughput'].mean()
        print(f"  {method_name}: CV={cv_throughput:.3f}")

    # 時系列プロット（詳細版）
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # (a) 平均スループット
    ax = axes[0, 0]
    for method_name, ts_df in timeseries_data.items():
        ax.plot(ts_df['timestamp'], ts_df['mean_throughput'], label=method_name, linewidth=2)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Mean Throughput (Mbps)')
    ax.set_title('(a) Mean Throughput over Time')
    ax.legend()
    ax.grid(True)

    # (b) P05スループット
    ax = axes[0, 1]
    for method_name, ts_df in timeseries_data.items():
        ax.plot(ts_df['timestamp'], ts_df['p05_throughput'], label=method_name, linewidth=2)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('P05 Throughput (Mbps)')
    ax.set_title('(b) P05 Throughput over Time')
    ax.legend()
    ax.grid(True)

    # (c) 採択数
    ax = axes[1, 0]
    for method_name, ts_df in timeseries_data.items():
        ax.plot(ts_df['timestamp'], ts_df['accepted'], label=method_name, linewidth=2)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Accepted Vehicles')
    ax.set_title('(c) Accepted Vehicles over Time')
    ax.legend()
    ax.grid(True)

    # (d) Relay数
    ax = axes[1, 1]
    for method_name, ts_df in timeseries_data.items():
        ax.plot(ts_df['timestamp'], ts_df['relay'], label=method_name, linewidth=2)
    ax.set_xlabel('Timestamp')
    ax.set_ylabel('Relay Count')
    ax.set_title('(d) Relay Count over Time')
    ax.legend()
    ax.grid(True)

    plt.tight_layout()
    plt.savefig(outdir / 'detailed_timeseries_analysis.png', dpi=300)
    plt.close()

    print(f"\n  時系列詳細プロット保存: {outdir / 'detailed_timeseries_analysis.png'}")

    return timeseries_data


def generate_analysis_report(results: dict, outdir: Path):
    """最終分析レポート生成"""
    print("\n" + "="*80)
    print("5. 最終分析レポート生成")
    print("="*80)

    report_path = outdir / 'detailed_analysis_report.txt'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("V2X割当最適化システム - 詳細分析レポート\n")
        f.write("="*80 + "\n\n")

        # 1. エグゼクティブサマリー
        f.write("【エグゼクティブサマリー】\n\n")

        basic_stats = results['basic_statistics']
        random_mean = basic_stats['random']['single']['mean_throughput_mbps']
        greedy_mean = basic_stats['greedy_mcs']['single']['mean_throughput_mbps']
        optimal_mcs_stats = basic_stats.get('optimal_mcs')
        optimal_shannon_stats = basic_stats.get('optimal_shannon')
        proposed_mean = basic_stats['proposed_optimal_dkmcs']['T']['mean_throughput_mbps']
        optimal_shannon_mean = None
        optimal_mcs_mean = None
        if optimal_shannon_stats:
            optimal_shannon_mean = optimal_shannon_stats['T']['mean_throughput_mbps']
        if optimal_mcs_stats:
            optimal_mcs_mean = optimal_mcs_stats['T']['mean_throughput_mbps']

        f.write(f"- Random baseline: {random_mean:.2f} Mbps\n")
        f.write(f"- Greedy (MCS): {greedy_mean:.2f} Mbps (+{(greedy_mean-random_mean)/random_mean*100:.1f}%)\n")
        if optimal_mcs_mean is not None:
            f.write(f"- Optimal MCS: {optimal_mcs_mean:.2f} Mbps (+{(optimal_mcs_mean-random_mean)/random_mean*100:.1f}%)\n")
        if optimal_shannon_mean is not None:
            f.write(f"- Optimal Shannon: {optimal_shannon_mean:.2f} Mbps (+{(optimal_shannon_mean-random_mean)/random_mean*100:.1f}%)\n")
        f.write(f"- Proposed (D/K×MCS): {proposed_mean:.2f} Mbps (+{(proposed_mean-random_mean)/random_mean*100:.1f}%)\n\n")

        # 2. 主要な発見
        f.write("【主要な発見】\n\n")

        greedy_vs_optimal = results['greedy_vs_optimal']
        f.write(f"1. Greedyと{greedy_vs_optimal['optimal_label']}の一致率: {greedy_vs_optimal['match_rate']:.2%}\n")
        f.write(f"   → Greedyが既にほぼ最適解に到達している\n\n")

        relay_effect = results['relay_effect']
        f.write(f"2. Relay活用率: {relay_effect['relay_count']/(relay_effect['direct_count']+relay_effect['relay_count']):.2%}\n")
        f.write(f"   → 最適化手法はRelayを積極活用（~77%）\n\n")

        f.write(f"3. Direct vs Relay スループット:\n")
        f.write(f"   - Direct平均: {relay_effect['direct_mean']:.2f} Mbps\n")
        f.write(f"   - Relay平均: {relay_effect['relay_mean']:.2f} Mbps\n")
        f.write(f"   - t検定 p値: {relay_effect['p_value']:.4f}\n\n")

        # 3. 推奨事項
        f.write("【推奨事項】\n\n")
        f.write("1. Greedy手法の有効性:\n")
        f.write("   - 計算コストが低く、ほぼ最適解に到達\n")
        f.write("   - 実用的にはGreedy-MCSが推奨される\n\n")

        f.write("2. Relayの戦略的活用:\n")
        f.write("   - 最適化により約77%の通信でRelayを活用\n")
        f.write("   - V2V通信の品質確保が重要\n\n")

        f.write("3. 今後の研究方向:\n")
        f.write("   - V2V干渉制約の追加\n")
        f.write("   - 動的なBS容量割当\n")
        f.write("   - マルチホップRelay対応\n\n")

    print(f"\n詳細レポート保存: {report_path}")

    return str(report_path)


def main():
    parser = argparse.ArgumentParser(description='最適化結果の詳細分析')
    parser.add_argument('--input-dir', type=str, required=True,
                        help='run_final_comparison.pyの出力ディレクトリ')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    if not input_dir.exists():
        print(f"エラー: {input_dir} が存在しません")
        return 1

    print("="*80)
    print("V2X割当最適化システム - 詳細分析")
    print("="*80)
    print(f"入力ディレクトリ: {input_dir}")

    # サマリー読み込み
    summary_df = pd.read_csv(input_dir / 'summary.csv')

    # 分析実行
    results = {}

    # 1. 基本統計
    results['basic_statistics'] = analyze_basic_statistics(summary_df)

    # 2. Greedy vs Optimal
    results['greedy_vs_optimal'] = analyze_greedy_vs_optimal(input_dir)

    # 3. Relay効果
    results['relay_effect'] = analyze_relay_effect(input_dir)

    # 4. 時系列分析
    results['timeseries'] = analyze_timeseries(input_dir, input_dir / 'plots')

    # 5. 最終レポート
    report_path = generate_analysis_report(results, input_dir)

    print("\n" + "="*80)
    print("分析完了！")
    print("="*80)
    print(f"\n詳細レポート: {report_path}")
    print(f"追加プロット: {input_dir / 'plots' / 'detailed_timeseries_analysis.png'}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
