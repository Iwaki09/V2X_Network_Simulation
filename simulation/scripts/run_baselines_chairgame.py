#!/usr/bin/env python3
"""
ベースライン手法（椅子取りゲーム）実行スクリプト

3種類のベースライン手法を実行：
1. Max-SNR (Greedy): 各車両が最大SNRのBSを希望
2. Nearest-BS (Distance): 各車両が最近接BSを希望
3. Random: 各車両がランダムにBSを希望

使用方法:
    # 交差点シナリオでMax-SNRベースラインを実行（BS定員=10）
    python scripts/run_baselines_chairgame.py --scenario corner_intersection --baseline max_snr --bs-capacity 10

    # 全ベースラインを実行
    python scripts/run_baselines_chairgame.py --scenario corner_intersection --baseline all --bs-capacity 10

    # Randomベースラインに乱数シードを指定
    python scripts/run_baselines_chairgame.py --scenario corner_intersection --baseline random --bs-capacity 10 --seed 42

    # 評価列を指定
    python scripts/run_baselines_chairgame.py --scenario corner_intersection --baseline all --bs-capacity 10 --eval-throughput-col throughput_mbps_mcs
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.optimization.baselines_chairgame import (
    run_baseline_chairgame,
    BaselineConfig
)
from src.scenarios.default import DefaultScenarioConfig
from src.scenarios.corner_intersection import CornerIntersectionConfig
from src.visualization.plots import (
    plot_baselines_chairgame_comparison,
    plot_all_baselines_vs_theoretical,
    plot_all_methods_comparison
)
from src.visualization.baseline_plots import generate_all_baseline_plots


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
        description='ベースライン手法（椅子取りゲーム）を実行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # Max-SNRベースラインを実行
  python scripts/run_baselines_chairgame.py --baseline max_snr --bs-capacity 10

  # 全ベースラインを実行
  python scripts/run_baselines_chairgame.py --baseline all --bs-capacity 10

  # 交差点シナリオで実行
  python scripts/run_baselines_chairgame.py --scenario corner_intersection --baseline all --bs-capacity 10

  # 評価列を指定（MCSベース）
  python scripts/run_baselines_chairgame.py --baseline all --bs-capacity 10 --eval-throughput-col throughput_mbps_mcs

ベースライン手法:
  max_snr:  各車両が最大SNRのBSを希望（Greedy）
  nearest:  各車両が最近接BSを希望（Distance-based）
  random:   各車両がランダムにBSを希望（Lower Bound）
  all:      上記3つすべてを実行
        """
    )

    # 必須引数
    parser.add_argument(
        '--baseline',
        type=str,
        required=True,
        choices=['max_snr', 'nearest', 'random', 'all'],
        help='ベースライン手法を選択'
    )
    parser.add_argument(
        '--bs-capacity',
        type=int,
        required=True,
        help='基地局定員（全BS共通）'
    )

    # オプション引数
    parser.add_argument(
        '--scenario',
        type=str,
        default='default',
        choices=['default', 'corner_intersection'],
        help='シナリオ名（デフォルト: default）'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='入力CSVファイルパス（デフォルト: シナリオ設定から取得）'
    )
    parser.add_argument(
        '--outdir',
        type=str,
        default=None,
        help='出力ディレクトリ（デフォルト: output/scenarios/{scenario}/baseline_chairgame/）'
    )
    parser.add_argument(
        '--eval-throughput-col',
        type=str,
        default='throughput_mbps_mcs',
        help='評価に使用するスループット列（デフォルト: throughput_mbps_mcs）'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='乱数シード（Randomベースライン用、デフォルト: 42）'
    )

    args = parser.parse_args()

    # シナリオ設定を取得
    scenario_config = get_scenario_config(args.scenario)

    # 入力ファイルパス
    input_csv = Path(args.input) if args.input else scenario_config.throughput_output_path

    # 出力ディレクトリ
    if args.outdir:
        output_dir = Path(args.outdir)
    else:
        output_dir = scenario_config.optimization_output_dir.parent / "baseline_chairgame"

    # FCD パス（Nearest用）
    fcd_path = scenario_config.fcd_output_path

    print("\n" + "=" * 80)
    print("ベースライン手法: 椅子取りゲーム")
    print("=" * 80)
    print(f"  シナリオ: {scenario_config.name}")
    print(f"  入力CSV: {input_csv}")
    print(f"  FCD: {fcd_path}")
    print(f"  出力ディレクトリ: {output_dir}")
    print(f"  BS定員: {args.bs_capacity}")
    print(f"  評価列: {args.eval_throughput_col}")
    print(f"  乱数シード: {args.seed}")
    print("=" * 80 + "\n")

    # 実行するベースラインのリスト
    if args.baseline == 'all':
        baselines = ['max_snr', 'nearest', 'random']
    else:
        baselines = [args.baseline]

    # 各ベースラインを実行
    all_results = {}
    for baseline_name in baselines:
        # ベースライン設定
        config = BaselineConfig(
            baseline_name=baseline_name,
            bs_capacity=args.bs_capacity,
            seed=args.seed if baseline_name == 'random' else None
        )

        # 実行
        assignment_df, metrics = run_baseline_chairgame(
            input_csv=input_csv,
            fcd_path=fcd_path,
            scenario_config=scenario_config,
            config=config,
            throughput_col=args.eval_throughput_col,
            output_dir=output_dir
        )

        all_results[baseline_name] = metrics

    # 全ベースラインの比較サマリー
    if len(baselines) > 1:
        print("\n" + "=" * 80)
        print("ベースライン比較サマリー")
        print("=" * 80)

        # 表形式で表示
        import pandas as pd
        summary_rows = []
        for baseline_name, metrics in all_results.items():
            summary_rows.append({
                'Baseline': baseline_name.upper(),
                'Outage Rate (%)': f"{metrics['outage_rate'] * 100:.2f}",
                'Mean Throughput (Mbps)': f"{metrics['mean_throughput_mbps']:.2f}",
                'P05 Throughput (Mbps)': f"{metrics['p05_throughput_mbps']:.2f}",
                'BS Load (mean)': f"{metrics['bs_load_mean']:.1f}",
                'BS Load (max)': metrics['bs_load_max']
            })

        summary_df = pd.DataFrame(summary_rows)
        print(summary_df.to_string(index=False))

        # 比較サマリーをCSVに保存
        comparison_csv = output_dir / "baseline_comparison_summary.csv"
        summary_df.to_csv(comparison_csv, index=False)
        print(f"\n[Output] 比較サマリー: {comparison_csv}")

        # サマリー比較グラフを生成
        print("\n" + "=" * 80)
        print("サマリー比較グラフ生成")
        print("=" * 80)
        try:
            plot_baselines_chairgame_comparison(
                baseline_dir=str(output_dir),
                bs_capacity=args.bs_capacity
            )
        except Exception as e:
            print(f"⚠️  警告: サマリーグラフ生成に失敗しました: {e}")

        # 詳細比較プロットを生成
        print("\n" + "=" * 80)
        print("詳細比較プロット生成")
        print("=" * 80)
        try:
            generate_all_baseline_plots(
                baseline_dir=output_dir,
                theoretical_csv=input_csv,
                fcd_path=fcd_path,
                scenario_config=scenario_config,
                output_dir=output_dir,
                eval_throughput_col=args.eval_throughput_col,
                bs_capacity=args.bs_capacity,
                xmax_mbps=None  # Auto
            )
        except Exception as e:
            print(f"⚠️  警告: 詳細プロット生成に失敗しました: {e}")
            import traceback
            traceback.print_exc()

        # figures/ ディレクトリに統合プロットを生成
        print("\n" + "=" * 80)
        print("figures/ ディレクトリに統合プロット生成")
        print("=" * 80)

        figures_dir = scenario_config.figures_output_dir
        figures_dir.mkdir(parents=True, exist_ok=True)

        # 既存の distributed ベースライン結果があるか確認
        distributed_csv = scenario_config.optimization_output_dir / "baseline_distributed_results.csv"
        optimization_csv = scenario_config.optimization_output_dir / "global_optimization_results.csv"

        # Plot 1: All Baselines vs Theoretical Maximum
        try:
            if distributed_csv.exists():
                plot_all_baselines_vs_theoretical(
                    theoretical_csv=str(input_csv),
                    baseline_distributed_csv=str(distributed_csv),
                    baseline_chairgame_dir=str(output_dir),
                    output_png=str(figures_dir / "all_baselines_vs_theoretical.png"),
                    eval_throughput_col=args.eval_throughput_col
                )
            else:
                print(f"  ⚠️ スキップ: {distributed_csv} が見つかりません")
        except Exception as e:
            print(f"  ⚠️ 警告: All Baselines vs Theoretical プロット生成失敗: {e}")

        # Plot 2: Proposed vs All Baselines
        try:
            if distributed_csv.exists() and optimization_csv.exists():
                plot_all_methods_comparison(
                    theoretical_csv=str(input_csv),
                    baseline_distributed_csv=str(distributed_csv),
                    baseline_chairgame_dir=str(output_dir),
                    optimization_csv=str(optimization_csv),
                    output_png=str(figures_dir / "all_methods_comparison.png"),
                    eval_throughput_col=args.eval_throughput_col
                )
            else:
                missing = []
                if not distributed_csv.exists():
                    missing.append("distributed")
                if not optimization_csv.exists():
                    missing.append("optimization")
                print(f"  ⚠️ スキップ: {', '.join(missing)} 結果が見つかりません")
        except Exception as e:
            print(f"  ⚠️ 警告: All Methods Comparison プロット生成失敗: {e}")

    print("\n" + "=" * 80)
    print("完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
