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

    # シナリオ指定
    python scripts/run_optimization.py --scenario corner_intersection
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
from src.scenarios.default import DefaultScenarioConfig
from src.scenarios.corner_intersection import CornerIntersectionConfig


def get_scenario_config(scenario_name: str):
    """シナリオ名に基づいて設定を取得"""
    if scenario_name == "default":
        return DefaultScenarioConfig()
    elif scenario_name == "corner_intersection":
        return CornerIntersectionConfig()
    else:
        raise ValueError(f"Unknown scenario: {scenario_name}")


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

  # 交差点シナリオで実行
  python scripts/run_optimization.py --scenario corner_intersection
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
        help='入力CSVファイルパス (デフォルト: シナリオ設定から取得)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        default='default',
        help='シナリオ名 (default, corner_intersection). デフォルト: default'
    )
    args = parser.parse_args()

    # どちらも指定されていない場合は両方実行
    run_distributed = args.distributed or not (args.distributed or args.global_opt)
    run_global = args.global_opt or not (args.distributed or args.global_opt)

    # シナリオ設定を取得
    scenario_config = get_scenario_config(args.scenario)

    # 入力ファイルパス（引数優先、なければシナリオ設定から取得）
    input_csv = Path(args.input) if args.input else scenario_config.throughput_output_path

    print(f"\nScenario: {scenario_config.name}")
    print(f"Input: {input_csv}")
    print(f"使用するスループット列: {args.throughput_col}")

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

    print("\n  最適化処理完了")


if __name__ == "__main__":
    main()
