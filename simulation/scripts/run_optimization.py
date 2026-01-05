#!/usr/bin/env python3
"""
最適化実行スクリプト

分散型制御シミュレーションとグローバル最適化を実行します。

使用方法:
    # デフォルト（Shannon公式ベース）
    python scripts/run_optimization.py

    # MCSベースで最適化
    python scripts/run_optimization.py --throughput-col throughput_mbps_mcs

    # 分散型のみ
    python scripts/run_optimization.py --distributed

    # グローバル最適化のみ
    python scripts/run_optimization.py --global
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.optimization.distributed import (
    simulate_distributed_control,
    DEFAULT_THROUGHPUT_COL,
    VALID_THROUGHPUT_COLS,
)
from src.optimization.global_optimizer import solve_global_optimization


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='最適化シミュレーションを実行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # デフォルト（Shannon公式ベース）で両方実行
  python scripts/run_optimization.py

  # MCSベースで最適化
  python scripts/run_optimization.py --throughput-col throughput_mbps_mcs

  # Shannon vs MCS を比較する場合は、それぞれ実行して結果を比較
  python scripts/run_optimization.py --throughput-col theoretical_throughput_mbps
  python scripts/run_optimization.py --throughput-col throughput_mbps_mcs
        """
    )
    parser.add_argument('--distributed', '-d', action='store_true',
                        help='分散型制御シミュレーションのみ実行')
    parser.add_argument('--global', '-g', dest='global_opt', action='store_true',
                        help='グローバル最適化のみ実行')
    parser.add_argument(
        '--throughput-col', '-t',
        type=str,
        choices=VALID_THROUGHPUT_COLS,
        default=DEFAULT_THROUGHPUT_COL,
        help=f'最適化に使用するスループット列 (デフォルト: {DEFAULT_THROUGHPUT_COL})'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='入力CSVファイルパス (デフォルト: output/data/throughput/theoretical_network_results.csv)'
    )
    args = parser.parse_args()

    # どちらも指定されていない場合は両方実行
    run_distributed = args.distributed or not (args.distributed or args.global_opt)
    run_global = args.global_opt or not (args.distributed or args.global_opt)

    # 入力ファイルパス
    input_csv = Path(args.input) if args.input else None

    print(f"\n使用するスループット列: {args.throughput_col}")

    if run_distributed:
        print("\n" + "=" * 60)
        print("分散型制御シミュレーションを実行")
        print("=" * 60)
        simulate_distributed_control(
            input_csv=input_csv,
            throughput_col=args.throughput_col
        )

    if run_global:
        print("\n" + "=" * 60)
        print("グローバル最適化を実行")
        print("=" * 60)
        solve_global_optimization(
            input_csv=input_csv,
            throughput_col=args.throughput_col
        )

    print("\n✅ 最適化処理完了")


if __name__ == "__main__":
    main()
