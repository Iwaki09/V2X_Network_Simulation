#!/usr/bin/env python3
"""
可視化実行スクリプト

リンク可視化フレーム生成とグラフ生成を実行します。

使用方法:
    python scripts/run_visualization.py              # デフォルトシナリオですべて実行
    python scripts/run_visualization.py --scenario corner_intersection  # 交差点シナリオ
    python scripts/run_visualization.py --frames     # フレーム生成のみ
    python scripts/run_visualization.py --network    # ネットワークサマリーのみ
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
    parser.add_argument('--scenario', '-s', type=str, default='default',
                        help='シナリオ名 (default, corner_intersection). デフォルト: default')
    args = parser.parse_args()

    # シナリオ設定を取得
    scenario_config = get_scenario_config(args.scenario)

    print(f"\nScenario: {scenario_config.name}")

    # 何も指定されていない場合はすべて実行
    run_all = args.all or not (args.frames or args.network or args.baseline or args.final)

    # パス設定
    fcd_file = str(scenario_config.fcd_output_path)
    csv_file = str(scenario_config.raytracing_output_path)
    throughput_csv = str(scenario_config.throughput_output_path)
    optimization_dir = scenario_config.optimization_output_dir
    figures_dir = scenario_config.figures_output_dir
    frames_dir = figures_dir / "frames"

    if args.frames or run_all:
        print("\n" + "=" * 60)
        print("リンク可視化フレームを生成")
        print("=" * 60)
        run_visualization(
            fcd_file=fcd_file,
            csv_file=csv_file,
            output_dir=str(frames_dir)
        )

    if args.network or run_all:
        print("\n" + "=" * 60)
        print("ネットワーク性能サマリーグラフを生成")
        print("=" * 60)
        plot_network_summary(
            input_csv=throughput_csv,
            output_dir=str(figures_dir)
        )

    if args.baseline or run_all:
        print("\n" + "=" * 60)
        print("ベースライン比較グラフを生成")
        print("=" * 60)
        plot_baseline_comparison(
            theoretical_csv=throughput_csv,
            baseline_csv=str(optimization_dir / "baseline_distributed_results.csv"),
            output_dir=str(figures_dir)
        )

    if args.final or run_all:
        print("\n" + "=" * 60)
        print("最終性能比較グラフを生成")
        print("=" * 60)
        plot_final_comparison(
            baseline_csv=str(optimization_dir / "baseline_distributed_results.csv"),
            optimization_csv=str(optimization_dir / "global_optimization_results.csv"),
            output_dir=str(figures_dir)
        )

    print("\n✅ 可視化処理完了")


if __name__ == "__main__":
    main()
