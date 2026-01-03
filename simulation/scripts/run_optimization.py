#!/usr/bin/env python3
"""
最適化実行スクリプト

分散型制御シミュレーションとグローバル最適化を実行します。
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.optimization.distributed import simulate_distributed_control
from src.optimization.global_optimizer import solve_global_optimization


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='最適化シミュレーションを実行')
    parser.add_argument('--distributed', '-d', action='store_true',
                        help='分散型制御シミュレーションのみ実行')
    parser.add_argument('--global', '-g', dest='global_opt', action='store_true',
                        help='グローバル最適化のみ実行')
    args = parser.parse_args()

    # どちらも指定されていない場合は両方実行
    run_distributed = args.distributed or not (args.distributed or args.global_opt)
    run_global = args.global_opt or not (args.distributed or args.global_opt)

    if run_distributed:
        print("\n" + "=" * 60)
        print("分散型制御シミュレーションを実行")
        print("=" * 60)
        simulate_distributed_control()

    if run_global:
        print("\n" + "=" * 60)
        print("グローバル最適化を実行")
        print("=" * 60)
        solve_global_optimization()

    print("\n✅ 最適化処理完了")


if __name__ == "__main__":
    main()
