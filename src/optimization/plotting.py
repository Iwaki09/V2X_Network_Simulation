"""
プロット生成モジュール

論文用の比較プロットを生成します。
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List


# プロットスタイル設定
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def calculate_summary(assignments_df: pd.DataFrame) -> Dict:
    """
    割当結果のサマリーを計算

    Args:
        assignments_df: 割当結果DF

    Returns:
        サマリー辞書
    """
    total_samples = len(assignments_df)
    outage_count = (assignments_df['accepted'] == 0).sum()
    outage_rate = outage_count / total_samples if total_samples > 0 else 0.0

    throughput_values = assignments_df['truth_rate_mcs_effective'].values
    mean_throughput = np.mean(throughput_values)
    p05 = np.percentile(throughput_values, 5)
    p50 = np.percentile(throughput_values, 50)
    p95 = np.percentile(throughput_values, 95)

    relay_count = (assignments_df['selected_action_type'] == 'relay').sum()
    direct_count = (assignments_df['selected_action_type'] == 'direct').sum()
    accepted_count = relay_count + direct_count
    relay_ratio = relay_count / accepted_count if accepted_count > 0 else 0.0

    # BS負荷
    bs_loads = []
    for timestamp in assignments_df['timestamp'].unique():
        df_t = assignments_df[assignments_df['timestamp'] == timestamp]
        df_accepted = df_t[df_t['accepted'] == 1]
        if len(df_accepted) > 0:
            bs_counts = df_accepted.groupby('selected_bs_id').size()
            bs_loads.extend(bs_counts.values)

    bs_load_mean = np.mean(bs_loads) if len(bs_loads) > 0 else 0.0
    bs_load_max = np.max(bs_loads) if len(bs_loads) > 0 else 0.0

    return {
        'total_samples': total_samples,
        'outage_rate': outage_rate,
        'mean_throughput_mbps': mean_throughput,
        'p05': p05,
        'p50': p50,
        'p95': p95,
        'relay_ratio': relay_ratio,
        'bs_load_mean': bs_load_mean,
        'bs_load_max': bs_load_max,
    }


def plot_outage_rate_bar(results_dict: Dict[str, pd.DataFrame], outdir: Path, suffix: str = "T"):
    """
    アウトエージ率の棒グラフ

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
    """
    methods = []
    outage_rates = []

    for method, df in results_dict.items():
        summary = calculate_summary(df)
        methods.append(method)
        outage_rates.append(summary['outage_rate'])

    plt.figure(figsize=(10, 6))
    plt.bar(methods, outage_rates)
    plt.xlabel('Method')
    plt.ylabel('Outage Rate')
    plt.title(f'Outage Rate Comparison (Objective: {suffix})')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(outdir / f'outage_rate_bar_{suffix}.png', dpi=300)
    plt.close()


def plot_throughput_cdf(results_dict: Dict[str, pd.DataFrame], outdir: Path, suffix: str = "T"):
    """
    スループットCDF（0を含む）

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
    """
    plt.figure(figsize=(10, 6))

    for method, df in results_dict.items():
        throughput_values = df['truth_rate_mcs_effective'].values
        sorted_values = np.sort(throughput_values)
        cdf = np.arange(1, len(sorted_values) + 1) / len(sorted_values)
        plt.plot(sorted_values, cdf, label=method, linewidth=2)

    plt.xlabel('Throughput (Mbps)')
    plt.ylabel('CDF')
    plt.title(f'Throughput CDF (Objective: {suffix})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outdir / f'throughput_cdf_{suffix}.png', dpi=300)
    plt.close()


def plot_p05_mean(results_dict: Dict[str, pd.DataFrame], outdir: Path, suffix: str = "T"):
    """
    P05とMeanの比較プロット

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
    """
    methods = []
    p05_values = []
    mean_values = []

    for method, df in results_dict.items():
        summary = calculate_summary(df)
        methods.append(method)
        p05_values.append(summary['p05'])
        mean_values.append(summary['mean_throughput_mbps'])

    x = np.arange(len(methods))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, p05_values, width, label='P05')
    plt.bar(x + width/2, mean_values, width, label='Mean')
    plt.xlabel('Method')
    plt.ylabel('Throughput (Mbps)')
    plt.title(f'P05 and Mean Throughput (Objective: {suffix})')
    plt.xticks(x, methods, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / f'p05_mean_{suffix}.png', dpi=300)
    plt.close()


def plot_relay_ratio(results_dict: Dict[str, pd.DataFrame], outdir: Path, suffix: str = "T"):
    """
    リレー率の棒グラフ

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
    """
    methods = []
    relay_ratios = []

    for method, df in results_dict.items():
        summary = calculate_summary(df)
        methods.append(method)
        relay_ratios.append(summary['relay_ratio'])

    plt.figure(figsize=(10, 6))
    plt.bar(methods, relay_ratios)
    plt.xlabel('Method')
    plt.ylabel('Relay Ratio')
    plt.title(f'Relay Ratio (Objective: {suffix})')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(outdir / f'relay_ratio_{suffix}.png', dpi=300)
    plt.close()


def plot_bs_load(results_dict: Dict[str, pd.DataFrame], outdir: Path, suffix: str = "T"):
    """
    BS負荷の比較プロット

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
    """
    methods = []
    bs_load_means = []
    bs_load_maxs = []

    for method, df in results_dict.items():
        summary = calculate_summary(df)
        methods.append(method)
        bs_load_means.append(summary['bs_load_mean'])
        bs_load_maxs.append(summary['bs_load_max'])

    x = np.arange(len(methods))
    width = 0.35

    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, bs_load_means, width, label='Mean Load')
    plt.bar(x + width/2, bs_load_maxs, width, label='Max Load')
    plt.xlabel('Method')
    plt.ylabel('BS Load')
    plt.title(f'BS Load Comparison (Objective: {suffix})')
    plt.xticks(x, methods, rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / f'bs_load_{suffix}.png', dpi=300)
    plt.close()


def plot_throughput_timeseries(
    results_dict: Dict[str, pd.DataFrame],
    outdir: Path,
    suffix: str = "T",
    metric: str = "mean",
    rolling_window: int = 0,
):
    """
    時系列スループットプロット

    Args:
        results_dict: {method_name: assignments_df}
        outdir: 出力ディレクトリ
        suffix: "T" or "O"
        metric: "mean" or "p05"
        rolling_window: 移動平均ウィンドウサイズ（0なら無効）
    """
    plt.figure(figsize=(12, 6))

    for method, df in results_dict.items():
        timestamps = sorted(df['timestamp'].unique())
        values = []

        for t in timestamps:
            df_t = df[df['timestamp'] == t]
            throughput_values = df_t['truth_rate_mcs_effective'].values

            if metric == "mean":
                values.append(np.mean(throughput_values))
            elif metric == "p05":
                values.append(np.percentile(throughput_values, 5))

        values = np.array(values)

        # 移動平均適用
        if rolling_window > 0 and len(values) > rolling_window:
            values = pd.Series(values).rolling(window=rolling_window, center=True).mean().values

        plt.plot(timestamps, values, label=method, linewidth=2)

    plt.xlabel('Timestamp')
    plt.ylabel(f'Throughput {metric.upper()} (Mbps)')
    plt.title(f'Throughput {metric.upper()} Time Series (Objective: {suffix})')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outdir / f'throughput_timeseries_{metric}_{suffix}.png', dpi=300)
    plt.close()


def plot_tradeoff_frontier(all_results: Dict[str, Dict[str, pd.DataFrame]], outdir: Path):
    """
    トレードオフフロンティア（outage_rate vs mean_throughput）

    Args:
        all_results: {method: {objective: assignments_df}}
        outdir: 出力ディレクトリ
    """
    plt.figure(figsize=(10, 8))

    # 各手法×目的の組み合わせをプロット
    for method, objectives in all_results.items():
        for objective, df in objectives.items():
            summary = calculate_summary(df)
            label = f"{method}_{objective}"
            plt.scatter(summary['outage_rate'], summary['mean_throughput_mbps'],
                       s=100, label=label, alpha=0.7)

    plt.xlabel('Outage Rate')
    plt.ylabel('Mean Throughput (Mbps)')
    plt.title('Tradeoff Frontier: Outage Rate vs Mean Throughput')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(outdir / 'tradeoff_frontier.png', dpi=300, bbox_inches='tight')
    plt.close()


def generate_all_plots(
    results_T: Dict[str, pd.DataFrame],
    results_O: Dict[str, pd.DataFrame],
    all_results: Dict[str, Dict[str, pd.DataFrame]],
    outdir: Path,
    rolling_window: int = 0,
):
    """
    すべてのプロットを生成

    Args:
        results_T: Throughput目的の結果 {method: assignments_df}
        results_O: Outage目的の結果 {method: assignments_df}
        all_results: 全結果 {method: {objective: assignments_df}}
        outdir: 出力ディレクトリ
        rolling_window: 時系列の移動平均ウィンドウ
    """
    outdir.mkdir(parents=True, exist_ok=True)

    print("Generating plots for Throughput objective...")
    plot_outage_rate_bar(results_T, outdir, "T")
    plot_throughput_cdf(results_T, outdir, "T")
    plot_p05_mean(results_T, outdir, "T")
    plot_relay_ratio(results_T, outdir, "T")
    plot_bs_load(results_T, outdir, "T")
    plot_throughput_timeseries(results_T, outdir, "T", "mean", rolling_window)
    plot_throughput_timeseries(results_T, outdir, "T", "p05", rolling_window)

    print("Generating plots for Outage objective...")
    plot_outage_rate_bar(results_O, outdir, "O")
    plot_throughput_cdf(results_O, outdir, "O")
    plot_p05_mean(results_O, outdir, "O")
    plot_relay_ratio(results_O, outdir, "O")
    plot_bs_load(results_O, outdir, "O")
    plot_throughput_timeseries(results_O, outdir, "O", "mean", rolling_window)
    plot_throughput_timeseries(results_O, outdir, "O", "p05", rolling_window)

    print("Generating tradeoff frontier plot...")
    plot_tradeoff_frontier(all_results, outdir)

    print(f"All plots saved to {outdir}")
