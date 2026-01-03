#!/usr/bin/env python3
"""
分散型制御シミュレータ

従来の「分散型・局所最適」な制御をシミュレートする。
各車両は他車の状況を考慮せず、自身にとって最強のV2Iリンクを1つだけ選択する。
"""

import pandas as pd
from pathlib import Path


def load_network_results(csv_path: Path) -> pd.DataFrame:
    """
    ネットワーク結果CSVを読み込む

    Args:
        csv_path: CSVファイルのパス

    Returns:
        読み込んだDataFrame
    """
    df = pd.read_csv(csv_path)
    print(f"読み込んだデータ: {len(df)} 行")
    print(f"列: {df.columns.tolist()}")
    return df


def filter_v2i_links(df: pd.DataFrame) -> pd.DataFrame:
    """
    V2Iリンクのみを抽出

    Args:
        df: 全リンクのDataFrame

    Returns:
        V2IリンクのみのDataFrame
    """
    v2i_df = df[df['link_type'] == 'V2I'].copy()
    print(f"V2Iリンク数: {len(v2i_df)} 行")
    return v2i_df


def select_best_v2i_per_vehicle(v2i_df: pd.DataFrame) -> pd.DataFrame:
    """
    各車両が自身にとって最強のV2Iリンクを1つ選択（分散型・局所最適）

    将来的に複数基地局（BS_1, BS_2...）が存在するシナリオに対応するため、
    各時刻の各車両は、複数のV2I候補の中から最大スループットのリンクを選択する。

    Args:
        v2i_df: V2IリンクのみのDataFrame

    Returns:
        各車両が選択した最強V2IリンクのみのDataFrame
    """
    # timestamp と rx_id (車両ID) でグループ化し、各グループで最大スループットの行を選択
    idx_max = v2i_df.groupby(['timestamp', 'rx_id'])['theoretical_throughput_mbps'].idxmax()
    best_links_df = v2i_df.loc[idx_max].copy()

    print(f"選択された最強V2Iリンク数: {len(best_links_df)} 行")
    print(f"ユニークな車両数: {best_links_df['rx_id'].nunique()}")
    print(f"タイムステップ数: {best_links_df['timestamp'].nunique()}")

    return best_links_df


def calculate_total_throughput_per_timestamp(best_links_df: pd.DataFrame) -> pd.DataFrame:
    """
    各タイムスタンプでのV2I総スループットを計算

    Args:
        best_links_df: 各車両が選択した最強V2IリンクのDataFrame

    Returns:
        timestamp と total_v2i_throughput_mbps の2列を持つDataFrame
    """
    result_df = best_links_df.groupby('timestamp')['theoretical_throughput_mbps'].sum().reset_index()
    result_df.columns = ['timestamp', 'total_v2i_throughput_mbps']

    print(f"計算結果: {len(result_df)} タイムステップ")
    print(f"V2I総スループット範囲: {result_df['total_v2i_throughput_mbps'].min():.2f} - {result_df['total_v2i_throughput_mbps'].max():.2f} Mbps")

    return result_df


def save_baseline_results(result_df: pd.DataFrame, output_path: Path) -> None:
    """
    ベースライン結果をCSVファイルに保存

    Args:
        result_df: 結果DataFrame
        output_path: 出力ファイルパス
    """
    result_df.to_csv(output_path, index=False)
    print(f"結果を保存しました: {output_path}")


def simulate_distributed_control(input_csv: Path = None, output_csv: Path = None) -> pd.DataFrame:
    """
    分散型制御シミュレーションを実行

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_csv: 出力CSVファイルパス (baseline_distributed_results.csv)

    Returns:
        結果DataFrame
    """
    # パス設定
    script_dir = Path(__file__).parent.parent.parent
    if input_csv is None:
        input_csv = script_dir / "output" / "throughput" / "theoretical_network_results.csv"
    if output_csv is None:
        output_dir = script_dir / "output" / "baseline"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_csv = output_dir / "baseline_distributed_results.csv"

    print("=" * 60)
    print("分散型制御シミュレータ")
    print("=" * 60)

    # 1. データ読み込み
    print("\n[1] データ読み込み")
    df = load_network_results(input_csv)

    # 2. V2Iリンクのみ抽出
    print("\n[2] V2Iリンク抽出")
    v2i_df = filter_v2i_links(df)

    # 3. 各車両が最強V2Iリンクを選択（分散型・局所最適）
    print("\n[3] 各車両が最強V2Iリンクを選択")
    best_links_df = select_best_v2i_per_vehicle(v2i_df)

    # 4. タイムスタンプごとのV2I総スループット計算
    print("\n[4] V2I総スループット計算")
    result_df = calculate_total_throughput_per_timestamp(best_links_df)

    # 5. 結果保存
    print("\n[5] 結果保存")
    save_baseline_results(result_df, output_csv)

    print("\n" + "=" * 60)
    print("完了")
    print("=" * 60)

    return result_df


def main():
    """メイン処理"""
    simulate_distributed_control()


if __name__ == "__main__":
    main()
