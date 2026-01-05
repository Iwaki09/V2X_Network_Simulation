#!/usr/bin/env python3
"""
Shannon vs MCS スループットモデル分析スクリプト

theoretical_network_results.csv を読み込み、以下の分析・可視化を行う:

A) Shannon vs MCS 比較
   - 図1: スループットCDF（Shannon vs MCS）
   - 図2: 時系列総スループット（timestampごとの合計）

B) LOS/NLOS 別分析
   - 図3: LOS/NLOS 別CDF

C) prop_mode (D/K) 別分析
   - 図4: prop_mode別CDF

出力:
   - summary_shannon_vs_mcs.csv: 条件別の統計量
   - 各種PNG図

使用方法:
    python scripts/analyze_throughput_models.py
    python scripts/analyze_throughput_models.py --rmin-mbps 10
    python scripts/analyze_throughput_models.py --outdir results/analysis
"""

import sys
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

# 日本語フォント設定（なければ英語で表示）
plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 定数
SHANNON_COL = 'theoretical_throughput_mbps'
MCS_COL = 'throughput_mbps_mcs'
DEFAULT_RMIN_MBPS = 10.0


def validate_columns(df: pd.DataFrame) -> None:
    """必要な列が存在するか検証"""
    required_cols = [SHANNON_COL, MCS_COL, 'is_line_of_sight', 'prop_mode', 'timestamp']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f"\n❌ エラー: 必要な列が見つかりません: {missing}")
        print(f"\n利用可能な列:")
        for col in df.columns:
            print(f"  - {col}")
        print(f"\nヒント: --rate-model both でスループット計算を再実行してください:")
        print(f"  python scripts/run_throughput.py --rate-model both")
        sys.exit(1)


def plot_cdf(ax, data: np.ndarray, label: str, color: str, linestyle: str = '-'):
    """CDFをプロット"""
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    ax.plot(sorted_data, cdf, label=label, color=color, linestyle=linestyle, linewidth=2)


def calculate_statistics(data: pd.Series, rmin_mbps: float) -> dict:
    """統計量を計算"""
    return {
        'count': len(data),
        'mean': data.mean(),
        'median': data.median(),
        'std': data.std(),
        'min': data.min(),
        'max': data.max(),
        'p05': data.quantile(0.05),
        'p25': data.quantile(0.25),
        'p75': data.quantile(0.75),
        'p95': data.quantile(0.95),
        'outage_rate': (data < rmin_mbps).mean(),
    }


def generate_summary_csv(df: pd.DataFrame, output_path: Path, rmin_mbps: float) -> pd.DataFrame:
    """
    条件別の統計量を集計してCSVに出力
    """
    results = []

    # 条件リスト: (条件名, フィルタ関数)
    conditions = [
        ('All', lambda x: x),
        ('LOS', lambda x: x[x['is_line_of_sight'] == True]),
        ('NLOS', lambda x: x[x['is_line_of_sight'] == False]),
        ('prop_mode=D', lambda x: x[x['prop_mode'] == 'D']),
        ('prop_mode=K', lambda x: x[x['prop_mode'] == 'K']),
        ('LOS & prop_mode=D', lambda x: x[(x['is_line_of_sight'] == True) & (x['prop_mode'] == 'D')]),
        ('LOS & prop_mode=K', lambda x: x[(x['is_line_of_sight'] == True) & (x['prop_mode'] == 'K')]),
        ('NLOS & prop_mode=D', lambda x: x[(x['is_line_of_sight'] == False) & (x['prop_mode'] == 'D')]),
        ('NLOS & prop_mode=K', lambda x: x[(x['is_line_of_sight'] == False) & (x['prop_mode'] == 'K')]),
    ]

    for cond_name, filter_func in conditions:
        filtered_df = filter_func(df)
        if len(filtered_df) == 0:
            continue

        shannon_stats = calculate_statistics(filtered_df[SHANNON_COL], rmin_mbps)
        mcs_stats = calculate_statistics(filtered_df[MCS_COL], rmin_mbps)

        results.append({
            'condition': cond_name,
            'count': shannon_stats['count'],
            'mean_shannon_mbps': shannon_stats['mean'],
            'mean_mcs_mbps': mcs_stats['mean'],
            'median_shannon_mbps': shannon_stats['median'],
            'median_mcs_mbps': mcs_stats['median'],
            'p05_shannon_mbps': shannon_stats['p05'],
            'p05_mcs_mbps': mcs_stats['p05'],
            'p95_shannon_mbps': shannon_stats['p95'],
            'p95_mcs_mbps': mcs_stats['p95'],
            'outage_rate_shannon': shannon_stats['outage_rate'],
            'outage_rate_mcs': mcs_stats['outage_rate'],
            'mcs_shannon_ratio': mcs_stats['mean'] / shannon_stats['mean'] if shannon_stats['mean'] > 0 else 0,
        })

    summary_df = pd.DataFrame(results)
    summary_df.to_csv(output_path, index=False)
    print(f"✅ 集計CSV保存: {output_path}")
    return summary_df


def plot_shannon_vs_mcs_cdf(df: pd.DataFrame, output_path: Path) -> None:
    """
    図1: Shannon vs MCS のCDF比較
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    plot_cdf(ax, df[SHANNON_COL].values, 'Shannon', 'blue', '-')
    plot_cdf(ax, df[MCS_COL].values, 'MCS', 'red', '--')

    ax.set_xlabel('Throughput (Mbps)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('Throughput CDF: Shannon vs MCS', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ 図1保存: {output_path}")


def plot_timeseries_throughput(df: pd.DataFrame, output_path: Path) -> None:
    """
    図2: 時系列総スループット（timestampごとの全リンク合計）
    """
    # timestampごとに合計
    ts_shannon = df.groupby('timestamp')[SHANNON_COL].sum()
    ts_mcs = df.groupby('timestamp')[MCS_COL].sum()

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(ts_shannon.index, ts_shannon.values, label='Shannon (sum)', color='blue', linewidth=1.5)
    ax.plot(ts_mcs.index, ts_mcs.values, label='MCS (sum)', color='red', linewidth=1.5, linestyle='--')

    ax.set_xlabel('Timestamp (s)', fontsize=12)
    ax.set_ylabel('Total Throughput (Mbps)', fontsize=12)
    ax.set_title('Time Series: Total Throughput (Sum of All Links)', fontsize=14)
    ax.legend(loc='upper right', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ 図2保存: {output_path}")


def plot_los_nlos_cdf(df: pd.DataFrame, output_path: Path) -> None:
    """
    図3: LOS/NLOS 別CDF（Shannon vs MCS）
    """
    los_df = df[df['is_line_of_sight'] == True]
    nlos_df = df[df['is_line_of_sight'] == False]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # LOS
    ax = axes[0]
    if len(los_df) > 0:
        plot_cdf(ax, los_df[SHANNON_COL].values, 'Shannon', 'blue', '-')
        plot_cdf(ax, los_df[MCS_COL].values, 'MCS', 'red', '--')
    ax.set_xlabel('Throughput (Mbps)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title(f'LOS Links (n={len(los_df)})', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    # NLOS
    ax = axes[1]
    if len(nlos_df) > 0:
        plot_cdf(ax, nlos_df[SHANNON_COL].values, 'Shannon', 'blue', '-')
        plot_cdf(ax, nlos_df[MCS_COL].values, 'MCS', 'red', '--')
    ax.set_xlabel('Throughput (Mbps)', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title(f'NLOS Links (n={len(nlos_df)})', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ 図3保存: {output_path}")


def plot_prop_mode_cdf(df: pd.DataFrame, output_path: Path) -> None:
    """
    図4: prop_mode (D/K) 別CDF（MCSベース）
    """
    d_df = df[df['prop_mode'] == 'D']
    k_df = df[df['prop_mode'] == 'K']

    fig, ax = plt.subplots(figsize=(10, 6))

    if len(d_df) > 0:
        plot_cdf(ax, d_df[MCS_COL].values, f'prop_mode=D (n={len(d_df)})', 'green', '-')
    if len(k_df) > 0:
        plot_cdf(ax, k_df[MCS_COL].values, f'prop_mode=K (n={len(k_df)})', 'orange', '--')

    ax.set_xlabel('Throughput (Mbps) [MCS-based]', fontsize=12)
    ax.set_ylabel('CDF', fontsize=12)
    ax.set_title('Throughput CDF by Propagation Mode (D vs K)', fontsize=14)
    ax.legend(loc='lower right', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(left=0)
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"✅ 図4保存: {output_path}")


def print_summary(summary_df: pd.DataFrame, rmin_mbps: float) -> None:
    """集計結果をコンソールに表示"""
    print("\n" + "=" * 70)
    print(f"Shannon vs MCS 比較サマリー (Rmin={rmin_mbps} Mbps)")
    print("=" * 70)

    for _, row in summary_df.iterrows():
        print(f"\n【{row['condition']}】 (n={row['count']})")
        print(f"  平均スループット:")
        print(f"    Shannon: {row['mean_shannon_mbps']:.2f} Mbps")
        print(f"    MCS:     {row['mean_mcs_mbps']:.2f} Mbps")
        print(f"    MCS/Shannon比: {row['mcs_shannon_ratio']*100:.1f}%")
        print(f"  5%タイル:")
        print(f"    Shannon: {row['p05_shannon_mbps']:.2f} Mbps")
        print(f"    MCS:     {row['p05_mcs_mbps']:.2f} Mbps")
        print(f"  アウテージ率 (<{rmin_mbps} Mbps):")
        print(f"    Shannon: {row['outage_rate_shannon']*100:.2f}%")
        print(f"    MCS:     {row['outage_rate_mcs']*100:.2f}%")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='Shannon vs MCS スループットモデル分析',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='入力CSVファイルパス (デフォルト: output/data/throughput/theoretical_network_results.csv)'
    )
    parser.add_argument(
        '--outdir',
        type=str,
        default=None,
        help='出力ディレクトリ (デフォルト: output/analysis)'
    )
    parser.add_argument(
        '--rmin-mbps',
        type=float,
        default=DEFAULT_RMIN_MBPS,
        help=f'アウテージ判定閾値 (Mbps). デフォルト: {DEFAULT_RMIN_MBPS}'
    )
    args = parser.parse_args()

    # パス設定
    input_csv = Path(args.input) if args.input else PROJECT_DIR / 'output' / 'data' / 'throughput' / 'theoretical_network_results.csv'
    output_dir = Path(args.outdir) if args.outdir else PROJECT_DIR / 'output' / 'analysis'
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Shannon vs MCS スループットモデル分析")
    print("=" * 70)
    print(f"  入力ファイル: {input_csv}")
    print(f"  出力ディレクトリ: {output_dir}")
    print(f"  アウテージ閾値 (Rmin): {args.rmin_mbps} Mbps")

    # データ読み込み
    print("\n[1] データ読み込み")
    if not input_csv.exists():
        print(f"❌ エラー: 入力ファイルが見つかりません: {input_csv}")
        sys.exit(1)

    df = pd.read_csv(input_csv)
    print(f"  読み込み完了: {len(df)} レコード")

    # 列検証
    validate_columns(df)

    # 基本統計
    print(f"\n[2] 基本情報")
    print(f"  V2Iリンク数: {len(df[df['link_type'] == 'V2I'])}")
    print(f"  V2Vリンク数: {len(df[df['link_type'] == 'V2V'])}")
    print(f"  LOSリンク数: {len(df[df['is_line_of_sight'] == True])}")
    print(f"  NLOSリンク数: {len(df[df['is_line_of_sight'] == False])}")
    print(f"  prop_mode=D: {len(df[df['prop_mode'] == 'D'])}")
    print(f"  prop_mode=K: {len(df[df['prop_mode'] == 'K'])}")

    # 集計CSV生成
    print("\n[3] 集計CSV生成")
    summary_df = generate_summary_csv(
        df,
        output_dir / 'summary_shannon_vs_mcs.csv',
        args.rmin_mbps
    )

    # 図の生成
    print("\n[4] 図の生成")

    # 図1: Shannon vs MCS CDF
    plot_shannon_vs_mcs_cdf(df, output_dir / 'fig1_cdf_shannon_vs_mcs.png')

    # 図2: 時系列総スループット
    plot_timeseries_throughput(df, output_dir / 'fig2_timeseries_throughput.png')

    # 図3: LOS/NLOS別CDF
    plot_los_nlos_cdf(df, output_dir / 'fig3_cdf_los_nlos.png')

    # 図4: prop_mode別CDF
    plot_prop_mode_cdf(df, output_dir / 'fig4_cdf_prop_mode.png')

    # サマリー表示
    print_summary(summary_df, args.rmin_mbps)

    print("\n" + "=" * 70)
    print("✅ 分析完了")
    print("=" * 70)
    print(f"\n生成ファイル:")
    print(f"  - {output_dir / 'summary_shannon_vs_mcs.csv'}")
    print(f"  - {output_dir / 'fig1_cdf_shannon_vs_mcs.png'}")
    print(f"  - {output_dir / 'fig2_timeseries_throughput.png'}")
    print(f"  - {output_dir / 'fig3_cdf_los_nlos.png'}")
    print(f"  - {output_dir / 'fig4_cdf_prop_mode.png'}")


if __name__ == "__main__":
    main()
