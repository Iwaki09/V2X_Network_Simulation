"""
ネットワーク性能サマリー可視化スクリプト

theoretical_network_results.csv から、時系列での総スループットを可視化します。
各タイムステップにおける全リンク（V2I + V2V）のスループット合計値をプロットします。
"""

import pandas as pd
import matplotlib.pyplot as plt


def plot_total_throughput_over_time(input_csv: str, output_png: str):
    """
    時系列での総スループットをプロット

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_png: 出力PNGファイルパス (network_performance_summary.png)
    """
    print("=" * 70)
    print("ネットワーク性能サマリー可視化")
    print("=" * 70)
    print()
    print(f"入力ファイル: {input_csv}")
    print()

    # CSVファイルを読み込む
    df = pd.read_csv(input_csv)
    print(f"✅ データ読み込み完了: {len(df)} レコード")
    print()

    # タイムスタンプごとにグループ化してスループット合計を計算
    print("【計算中】タイムスタンプごとのスループット合計を計算...")
    throughput_summary = df.groupby('timestamp')['theoretical_throughput_mbps'].sum().reset_index()
    throughput_summary.rename(columns={'theoretical_throughput_mbps': 'total_throughput_mbps'}, inplace=True)

    print(f"✅ 計算完了: {len(throughput_summary)} タイムステップ")
    print()

    # 統計情報を表示
    print("【統計情報】")
    print(f"  総スループット (Mbps):")
    print(f"    - 平均: {throughput_summary['total_throughput_mbps'].mean():.2f} Mbps")
    print(f"    - 最小: {throughput_summary['total_throughput_mbps'].min():.2f} Mbps")
    print(f"    - 最大: {throughput_summary['total_throughput_mbps'].max():.2f} Mbps")
    print()

    # グラフの作成
    print("【可視化中】グラフを生成...")
    fig, ax = plt.subplots(figsize=(12, 6))

    # 折れ線グラフをプロット
    ax.plot(throughput_summary['timestamp'],
            throughput_summary['total_throughput_mbps'],
            linewidth=2, color='steelblue', marker='o', markersize=3)

    # グラフの装飾
    ax.set_xlabel('Time [s]', fontsize=12)
    ax.set_ylabel('Total Theoretical Throughput [Mbps]', fontsize=12)
    ax.set_title('Network Performance Summary (V2I + V2V)', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')

    # 平均値のラインを追加（破線）
    mean_throughput = throughput_summary['total_throughput_mbps'].mean()
    ax.axhline(y=mean_throughput, color='red', linestyle='--', linewidth=1.5,
               label=f'Average: {mean_throughput:.2f} Mbps')

    # 凡例を表示
    ax.legend(loc='upper right', fontsize=10)

    # レイアウトの調整
    plt.tight_layout()

    # PNGファイルとして保存
    plt.savefig(output_png, dpi=150)
    print(f"✅ グラフ保存完了: {output_png}")
    print()
    print("=" * 70)

    plt.close(fig)


def main():
    """メイン処理"""
    input_csv = 'output/throughput/theoretical_network_results.csv'
    output_png = 'output/visualizations/network_performance_summary.png'

    plot_total_throughput_over_time(input_csv, output_png)


if __name__ == "__main__":
    main()
