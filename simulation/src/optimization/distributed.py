#!/usr/bin/env python3
"""
分散型制御シミュレータ

従来の「分散型・局所最適」な制御をシミュレートする。
各車両は他車の状況を考慮せず、自身にとって最強のV2Iリンクを1つだけ選択する。
"""

import sys
import pandas as pd
from pathlib import Path

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


def select_best_v2i_per_vehicle(
    v2i_df: pd.DataFrame,
    throughput_col: str = DEFAULT_THROUGHPUT_COL
) -> pd.DataFrame:
    """
    各車両が自身にとって最強のV2Iリンクを1つ選択（分散型・局所最適）

    将来的に複数基地局（BS_1, BS_2...）が存在するシナリオに対応するため、
    各時刻の各車両は、複数のV2I候補の中から最大スループットのリンクを選択する。

    Args:
        v2i_df: V2IリンクのみのDataFrame
        throughput_col: スループット列名

    Returns:
        各車両が選択した最強V2IリンクのみのDataFrame
    """
    # timestamp と rx_id (車両ID) でグループ化し、各グループで最大スループットの行を選択
    idx_max = v2i_df.groupby(['timestamp', 'rx_id'])[throughput_col].idxmax()
    best_links_df = v2i_df.loc[idx_max].copy()

    print(f"選択された最強V2Iリンク数: {len(best_links_df)} 行")
    print(f"ユニークな車両数: {best_links_df['rx_id'].nunique()}")
    print(f"タイムステップ数: {best_links_df['timestamp'].nunique()}")

    return best_links_df


def calculate_total_throughput_per_timestamp(
    best_links_df: pd.DataFrame,
    throughput_col: str = DEFAULT_THROUGHPUT_COL
) -> pd.DataFrame:
    """
    各タイムスタンプでのV2I総スループットを計算

    Args:
        best_links_df: 各車両が選択した最強V2IリンクのDataFrame
        throughput_col: スループット列名

    Returns:
        timestamp と total_v2i_throughput_mbps の2列を持つDataFrame
    """
    result_df = best_links_df.groupby('timestamp')[throughput_col].sum().reset_index()
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


def simulate_distributed_control(
    input_csv: Path = None,
    output_csv: Path = None,
    output_dir: Path = None,
    throughput_col: str = DEFAULT_THROUGHPUT_COL
) -> pd.DataFrame:
    """
    分散型制御シミュレーションを実行

    Args:
        input_csv: 入力CSVファイルパス (theoretical_network_results.csv)
        output_csv: 出力CSVファイルパス (baseline_distributed_results.csv)
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
            output_csv = output_dir / "baseline_distributed_results.csv"
        else:
            # デフォルト（後方互換性のため維持、ただし呼び出し元でoutput_dirを指定することを推奨）
            script_dir = Path(__file__).parent.parent.parent
            default_output_dir = script_dir / "output" / "scenarios" / "default" / "optimization"
            default_output_dir.mkdir(parents=True, exist_ok=True)
            output_csv = default_output_dir / "baseline_distributed_results.csv"

    print("=" * 60)
    print("分散型制御シミュレータ")
    print("=" * 60)
    print(f"  スループット列: {throughput_col}")

    # 1. データ読み込み
    print("\n[1] データ読み込み")
    df = load_network_results(input_csv)

    # スループット列の検証
    validate_throughput_column(df, throughput_col)

    # 2. V2Iリンクのみ抽出
    print("\n[2] V2Iリンク抽出")
    v2i_df = filter_v2i_links(df)

    # 3. 各車両が最強V2Iリンクを選択（分散型・局所最適）
    print("\n[3] 各車両が最強V2Iリンクを選択")
    best_links_df = select_best_v2i_per_vehicle(v2i_df, throughput_col=throughput_col)

    # 4. タイムスタンプごとのV2I総スループット計算
    print("\n[4] V2I総スループット計算")
    result_df = calculate_total_throughput_per_timestamp(best_links_df, throughput_col=throughput_col)

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
