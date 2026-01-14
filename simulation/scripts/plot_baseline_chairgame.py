#!/usr/bin/env python3
"""
ベースライン手法（椅子取りゲーム）詳細可視化スクリプト

論文用の詳細な比較プロットを生成：
- Plot A: Outage Rate（棒グラフ）
- Plot B: Throughput CDF（0含む）
- Plot C: BS負荷分布（箱ひげ図）
- Plot D: Nearest距離 vs 品質（散布図）

使用方法:
    # 全プロット生成
    python scripts/plot_baseline_chairgame.py --scenario corner_intersection --baseline-dir output/scenarios/corner_intersection/baseline_chairgame --bs-capacity 10

    # 個別指定
    python scripts/plot_baseline_chairgame.py --theoretical-csv <path> --baseline-dir <path> --outdir <path>
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.visualization.baseline_plots import generate_all_baseline_plots
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
        description='ベースライン手法（椅子取りゲーム）詳細可視化',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 交差点シナリオで全プロット生成
  python scripts/plot_baseline_chairgame.py --scenario corner_intersection --baseline-dir output/scenarios/corner_intersection/baseline_chairgame --bs-capacity 10

  # 個別指定
  python scripts/plot_baseline_chairgame.py \\
    --theoretical-csv output/scenarios/corner_intersection/throughput/theoretical_network_results.csv \\
    --baseline-dir output/scenarios/corner_intersection/baseline_chairgame \\
    --fcd output/scenarios/corner_intersection/fcd/fcd_output.xml \\
    --outdir output/scenarios/corner_intersection/baseline_chairgame \\
    --bs-capacity 10
        """
    )

    # シナリオ指定（推奨）
    parser.add_argument(
        '--scenario',
        type=str,
        default=None,
        choices=['default', 'corner_intersection'],
        help='シナリオ名（指定すると他のパスを自動設定）'
    )

    # 個別指定（シナリオ指定がない場合に必要）
    parser.add_argument(
        '--theoretical-csv',
        type=str,
        default=None,
        help='theoretical_network_results.csv のパス'
    )
    parser.add_argument(
        '--baseline-dir',
        type=str,
        required=True,
        help='ベースライン結果ディレクトリ'
    )
    parser.add_argument(
        '--fcd',
        type=str,
        default=None,
        help='fcd_output.xml のパス（Plot D用）'
    )
    parser.add_argument(
        '--outdir',
        type=str,
        default=None,
        help='出力ディレクトリ（デフォルト: baseline-dirと同じ）'
    )

    # オプション
    parser.add_argument(
        '--eval-throughput-col',
        type=str,
        default='throughput_mbps_mcs',
        help='評価用スループット列名（デフォルト: throughput_mbps_mcs）'
    )
    parser.add_argument(
        '--bs-capacity',
        type=int,
        default=None,
        help='基地局定員（Plot Cの参照線用）'
    )
    parser.add_argument(
        '--xmax-mbps',
        type=float,
        default=None,
        help='CDF x軸の上限（Mbps）'
    )

    args = parser.parse_args()

    # シナリオ設定の取得
    if args.scenario:
        scenario_config = get_scenario_config(args.scenario)

        # パスを自動設定
        if args.theoretical_csv is None:
            args.theoretical_csv = str(scenario_config.throughput_output_path)
        if args.fcd is None:
            args.fcd = str(scenario_config.fcd_output_path)
    else:
        # シナリオ指定なしの場合、必須パスのチェック
        if args.theoretical_csv is None:
            parser.error("--theoretical-csv is required when --scenario is not specified")
        if args.fcd is None:
            parser.error("--fcd is required when --scenario is not specified")

        # ダミーのシナリオ設定を作成（座標変換なし）
        class DummyScenarioConfig:
            def transform_coordinates(self, x, y):
                return (x, y)
            base_station = type('obj', (object,), {'position': [0, 0, 0]})

        scenario_config = DummyScenarioConfig()

    # 出力ディレクトリの設定
    if args.outdir is None:
        args.outdir = args.baseline_dir

    print("\n" + "=" * 80)
    print("ベースライン詳細可視化")
    print("=" * 80)
    print(f"  シナリオ: {args.scenario if args.scenario else 'Not specified'}")
    print(f"  理論値CSV: {args.theoretical_csv}")
    print(f"  ベースラインディレクトリ: {args.baseline_dir}")
    print(f"  FCD: {args.fcd}")
    print(f"  出力ディレクトリ: {args.outdir}")
    print(f"  評価列: {args.eval_throughput_col}")
    print(f"  BS定員: {args.bs_capacity if args.bs_capacity else 'Not specified'}")
    print(f"  CDF x軸上限: {args.xmax_mbps if args.xmax_mbps else 'Auto'}")
    print("=" * 80 + "\n")

    # 全プロット生成
    try:
        generate_all_baseline_plots(
            baseline_dir=Path(args.baseline_dir),
            theoretical_csv=Path(args.theoretical_csv),
            fcd_path=Path(args.fcd),
            scenario_config=scenario_config,
            output_dir=Path(args.outdir),
            eval_throughput_col=args.eval_throughput_col,
            bs_capacity=args.bs_capacity,
            xmax_mbps=args.xmax_mbps
        )
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 80)
    print("完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
