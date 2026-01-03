#!/usr/bin/env python3
"""
可視化実行スクリプト

リンク可視化フレーム生成とグラフ生成を実行します。
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.visualization.link_visualizer import run_visualization
from src.visualization.plots import (
    plot_network_summary,
    plot_baseline_comparison,
    plot_final_comparison
)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='可視化を実行')
    parser.add_argument('--frames', '-f', action='store_true',
                        help='リンク可視化フレームを生成')
    parser.add_argument('--network', '-n', action='store_true',
                        help='ネットワーク性能サマリーグラフを生成')
    parser.add_argument('--baseline', '-b', action='store_true',
                        help='ベースライン比較グラフを生成')
    parser.add_argument('--final', '-F', action='store_true',
                        help='最終性能比較グラフを生成')
    parser.add_argument('--all', '-a', action='store_true',
                        help='すべての可視化を実行')
    args = parser.parse_args()

    # 何も指定されていない場合はすべて実行
    run_all = args.all or not (args.frames or args.network or args.baseline or args.final)

    if args.frames or run_all:
        print("\n" + "=" * 60)
        print("リンク可視化フレームを生成")
        print("=" * 60)
        run_visualization()

    if args.network or run_all:
        print("\n" + "=" * 60)
        print("ネットワーク性能サマリーグラフを生成")
        print("=" * 60)
        plot_network_summary()

    if args.baseline or run_all:
        print("\n" + "=" * 60)
        print("ベースライン比較グラフを生成")
        print("=" * 60)
        plot_baseline_comparison()

    if args.final or run_all:
        print("\n" + "=" * 60)
        print("最終性能比較グラフを生成")
        print("=" * 60)
        plot_final_comparison()

    print("\n✅ 可視化処理完了")


if __name__ == "__main__":
    main()
