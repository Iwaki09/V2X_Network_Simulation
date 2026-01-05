#!/usr/bin/env python3
"""
スループット計算実行スクリプト

レイトレーシング結果から理論的スループットを計算します。

使用方法:
    python scripts/run_throughput.py                    # デフォルト (shannon)
    python scripts/run_throughput.py --rate-model mcs   # MCSベース
    python scripts/run_throughput.py --rate-model both  # Shannon + MCS 比較
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.core.throughput import process_link_quality_data


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description='レイトレーシング結果から理論的スループットを計算'
    )
    parser.add_argument(
        '--rate-model',
        type=str,
        choices=['shannon', 'mcs', 'both'],
        default='shannon',
        help='レートモデル: shannon (シャノン公式), mcs (離散レート), both (比較モード). デフォルト: shannon'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='入力CSVファイルパス (デフォルト: output/data/raytracing/link_quality_results.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='出力CSVファイルパス (デフォルト: output/data/throughput/theoretical_network_results.csv)'
    )
    return parser.parse_args()


def main():
    """メイン処理"""
    args = parse_args()

    # 入出力パス
    input_csv = Path(args.input) if args.input else PROJECT_DIR / 'output/data/raytracing/link_quality_results.csv'
    output_csv = Path(args.output) if args.output else PROJECT_DIR / 'output/data/throughput/theoretical_network_results.csv'

    # 出力ディレクトリを作成
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    process_link_quality_data(str(input_csv), str(output_csv), rate_model=args.rate_model)


if __name__ == "__main__":
    main()
