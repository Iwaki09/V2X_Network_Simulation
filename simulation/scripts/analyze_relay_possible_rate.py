#!/usr/bin/env python3
"""
リレー可能率（relay-possible rate）分析スクリプト

V2Vリレーの可能性を評価する参考指標を算出します。
実際のリレー送信は実装せず、「リレー可能性」のみを集計します。

定義:
  時刻tで車両vが「リレー可能」と判定される条件：
  (1) vの直V2Iが"アウトエージ候補"である：throughput_v2i(v,t) < T_out
  (2) vの近傍に車両uが存在し、次を全て満たす：
      - throughput_v2v(v→u,t) >= T_v2v_min
      - throughput_v2i(u,t)    >= T_v2i_good
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

# 日本語フォント設定
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))


def load_network_results(csv_path: Path) -> pd.DataFrame:
    """
    ネットワーク結果CSVを読み込む

    Args:
        csv_path: theoretical_network_results.csvのパス

    Returns:
        DataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"✅ Loaded {len(df)} link records from {csv_path}")
    print(f"   - Timestamps: {df['timestamp'].nunique()}")
    print(f"   - V2I links: {len(df[df['link_type'] == 'V2I'])}")
    print(f"   - V2V links: {len(df[df['link_type'] == 'V2V'])}")
    return df


def analyze_relay_possible_rate(
    df: pd.DataFrame,
    throughput_col: str = "throughput_mbps_mcs",
    t_out: float = 50.0,
    t_v2v_min: float = 50.0,
    t_v2i_good: float = 100.0,
    v2v_radius_m: float = 100.0
) -> dict:
    """
    リレー可能率を分析

    Args:
        df: ネットワーク結果DataFrame
        throughput_col: 使用するスループット列名
        t_out: アウトエージ候補閾値 [Mbps]
        t_v2v_min: V2Vリンク成立閾値 [Mbps]
        t_v2i_good: 中継車のV2Iが十分な閾値 [Mbps]
        v2v_radius_m: V2V近傍距離閾値 [m]（未使用：既にRTで絞り込み済み）

    Returns:
        集計結果の辞書
    """
    # スループット列の存在確認
    if throughput_col not in df.columns:
        raise ValueError(
            f"Throughput column '{throughput_col}' not found. "
            f"Available columns: {df.columns.tolist()}"
        )

    print(f"\n{'='*60}")
    print("Relay Possible Rate Analysis")
    print(f"{'='*60}")
    print(f"Parameters:")
    print(f"  - Throughput column: {throughput_col}")
    print(f"  - T_out (outage candidate): {t_out} Mbps")
    print(f"  - T_v2v_min (V2V成立): {t_v2v_min} Mbps")
    print(f"  - T_v2i_good (中継車V2I): {t_v2i_good} Mbps")
    print(f"  - V2V radius: {v2v_radius_m} m (already filtered in RT)")

    # V2IとV2Vに分割
    v2i_df = df[df['link_type'] == 'V2I'].copy()
    v2v_df = df[df['link_type'] == 'V2V'].copy()

    print(f"\nData overview:")
    print(f"  - V2I links: {len(v2i_df)}")
    print(f"  - V2V links: {len(v2v_df)}")

    # 各timestampで処理
    timestamps = sorted(df['timestamp'].unique())
    print(f"  - Analyzing {len(timestamps)} timestamps...")

    # 集計用リスト
    results_per_vehicle_time = []

    for ts in timestamps:
        v2i_ts = v2i_df[v2i_df['timestamp'] == ts]
        v2v_ts = v2v_df[v2v_df['timestamp'] == ts]

        # 各車両の直V2I throughput（最大値を採用：複数BSの場合）
        v2i_dict = v2i_ts.groupby('rx_id')[throughput_col].max().to_dict()

        # 車両リスト
        vehicles = list(v2i_dict.keys())

        for veh_id in vehicles:
            v2i_throughput = v2i_dict.get(veh_id, 0.0)

            # (1) アウトエージ候補判定
            is_outage_candidate = v2i_throughput < t_out

            # (2) リレー可能判定
            # vが送信側（tx_id）のV2Vリンクを取得
            v2v_from_v = v2v_ts[v2v_ts['tx_id'] == veh_id]

            # 近傍車両（rx_id）のV2I throughputを確認
            relay_possible = False
            num_neighbors = len(v2v_from_v)
            num_good_neighbors = 0

            for _, v2v_link in v2v_from_v.iterrows():
                u_id = v2v_link['rx_id']
                v2v_throughput = v2v_link[throughput_col]
                u_v2i_throughput = v2i_dict.get(u_id, 0.0)

                # V2VリンクとuのV2Iが十分か
                if v2v_throughput >= t_v2v_min and u_v2i_throughput >= t_v2i_good:
                    num_good_neighbors += 1
                    relay_possible = True

            results_per_vehicle_time.append({
                'timestamp': ts,
                'vehicle_id': veh_id,
                'v2i_throughput': v2i_throughput,
                'is_outage_candidate': is_outage_candidate,
                'relay_possible': relay_possible,
                'num_neighbors': num_neighbors,
                'num_good_neighbors': num_good_neighbors
            })

    # DataFrameに変換
    results_df = pd.DataFrame(results_per_vehicle_time)

    # 集計
    total_samples = len(results_df)
    outage_candidates = results_df[results_df['is_outage_candidate']]
    num_outage_candidates = len(outage_candidates)

    outage_and_relay_possible = results_df[
        results_df['is_outage_candidate'] & results_df['relay_possible']
    ]
    num_outage_and_relay_possible = len(outage_and_relay_possible)

    # 指標計算
    outage_candidate_rate = num_outage_candidates / total_samples if total_samples > 0 else 0.0
    relay_possible_rate_vehicle = num_outage_and_relay_possible / total_samples if total_samples > 0 else 0.0
    conditional_relay_possible_rate = (
        num_outage_and_relay_possible / num_outage_candidates if num_outage_candidates > 0 else 0.0
    )

    # 近傍車両数の平均
    avg_neighbors = results_df['num_neighbors'].mean()
    avg_neighbors_with_at_least_one = (results_df['num_neighbors'] >= 1).mean()

    # 交差点中心周辺の同時車両数（timestampごと）
    # ※ FCDから計算するのが理想だが、ここでは車両数でカウント
    vehicles_per_timestamp = results_df.groupby('timestamp')['vehicle_id'].nunique()
    avg_vehicles_per_timestamp = vehicles_per_timestamp.mean()

    # 結果をまとめる
    summary = {
        'total_samples': total_samples,
        'num_outage_candidates': num_outage_candidates,
        'num_outage_and_relay_possible': num_outage_and_relay_possible,
        'outage_candidate_rate': outage_candidate_rate,
        'relay_possible_rate_vehicle': relay_possible_rate_vehicle,
        'conditional_relay_possible_rate': conditional_relay_possible_rate,
        'avg_neighbors_within_R': avg_neighbors,
        'rate_vehicles_with_neighbors': avg_neighbors_with_at_least_one,
        'avg_vehicles_per_timestamp': avg_vehicles_per_timestamp
    }

    return summary, results_df


def print_summary(summary: dict):
    """集計結果を標準出力に表示"""
    print(f"\n{'='*60}")
    print("Summary Statistics")
    print(f"{'='*60}")
    print(f"Total vehicle-time samples: {summary['total_samples']}")
    print(f"Average vehicles per timestamp: {summary['avg_vehicles_per_timestamp']:.2f}")
    print(f"\nOutage Candidates:")
    print(f"  - Count: {summary['num_outage_candidates']}")
    print(f"  - Rate: {summary['outage_candidate_rate']*100:.2f}%")
    print(f"\nRelay Possible:")
    print(f"  - Count (outage & relay possible): {summary['num_outage_and_relay_possible']}")
    print(f"  - Relay possible rate (vehicle): {summary['relay_possible_rate_vehicle']*100:.2f}%")
    print(f"  - Conditional relay possible rate: {summary['conditional_relay_possible_rate']*100:.2f}%")
    print(f"\nNeighbors:")
    print(f"  - Average neighbors within R: {summary['avg_neighbors_within_R']:.2f}")
    print(f"  - Rate of vehicles with >=1 neighbors: {summary['rate_vehicles_with_neighbors']*100:.2f}%")
    print(f"{'='*60}")


def save_summary_csv(summary: dict, output_path: Path):
    """集計結果をCSVに保存"""
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv(output_path, index=False)
    print(f"✅ Saved summary to {output_path}")


def save_timeseries_csv(results_df: pd.DataFrame, output_path: Path):
    """時系列データをCSVに保存（任意）"""
    # timestampごとの集計
    ts_summary = results_df.groupby('timestamp').agg({
        'vehicle_id': 'count',
        'is_outage_candidate': 'sum',
        'relay_possible': 'sum',
        'num_neighbors': 'mean'
    }).reset_index()

    ts_summary.columns = [
        'timestamp',
        'num_vehicles',
        'num_outage_candidates',
        'num_relay_possible',
        'avg_neighbors'
    ]

    ts_summary['relay_possible_rate'] = (
        ts_summary['num_relay_possible'] / ts_summary['num_vehicles']
    )

    ts_summary.to_csv(output_path, index=False)
    print(f"✅ Saved time-series data to {output_path}")


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="リレー可能率（relay-possible rate）分析スクリプト"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="output/scenarios/corner_intersection/throughput/theoretical_network_results.csv",
        help="入力CSV（theoretical_network_results.csv）のパス"
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="output/scenarios/corner_intersection/analysis",
        help="出力ディレクトリ"
    )
    parser.add_argument(
        "--throughput-col",
        type=str,
        default="throughput_mbps_mcs",
        help="使用するスループット列名（デフォルト: throughput_mbps_mcs）"
    )
    parser.add_argument(
        "--t-out",
        type=float,
        default=50.0,
        help="アウトエージ候補閾値 [Mbps]（デフォルト: 50）"
    )
    parser.add_argument(
        "--t-v2v-min",
        type=float,
        default=50.0,
        help="V2Vリンク成立閾値 [Mbps]（デフォルト: 50）"
    )
    parser.add_argument(
        "--t-v2i-good",
        type=float,
        default=100.0,
        help="中継車のV2Iが十分な閾値 [Mbps]（デフォルト: 100）"
    )
    parser.add_argument(
        "--v2v-radius-m",
        type=float,
        default=100.0,
        help="V2V近傍距離閾値 [m]（デフォルト: 100、既にRTで絞り込み済み）"
    )
    return parser.parse_args()


def main():
    """メイン関数"""
    args = parse_args()

    print("=" * 80)
    print(" Relay Possible Rate Analysis")
    print("=" * 80)

    # パス設定
    input_csv = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # 入力ファイルの存在確認
    if not input_csv.exists():
        print(f"❌ Error: Input file not found: {input_csv}")
        print("   Please run the simulation pipeline first:")
        print("   ./run_simulation.sh --scenario corner_intersection --all")
        sys.exit(1)

    # データ読み込み
    df = load_network_results(input_csv)

    # 分析実行
    summary, results_df = analyze_relay_possible_rate(
        df=df,
        throughput_col=args.throughput_col,
        t_out=args.t_out,
        t_v2v_min=args.t_v2v_min,
        t_v2i_good=args.t_v2i_good,
        v2v_radius_m=args.v2v_radius_m
    )

    # 結果表示
    print_summary(summary)

    # CSV保存
    summary_csv = outdir / "relay_possible_rate_summary.csv"
    save_summary_csv(summary, summary_csv)

    # 時系列データ保存（任意）
    timeseries_csv = outdir / "relay_possible_rate_by_time.csv"
    save_timeseries_csv(results_df, timeseries_csv)

    print(f"\n✅ Analysis complete!")
    print(f"   Output directory: {outdir}")


if __name__ == "__main__":
    main()
