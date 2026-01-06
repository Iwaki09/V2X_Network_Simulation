#!/usr/bin/env python3
"""
スループット計算実行スクリプト

レイトレーシング結果から理論的スループットを計算します。

使用方法:
    python scripts/run_throughput.py                    # デフォルト (shannon)
    python scripts/run_throughput.py --rate-model mcs   # MCSベース
    python scripts/run_throughput.py --rate-model both  # Shannon + MCS 比較
    python scripts/run_throughput.py --scenario corner_intersection  # シナリオ指定
"""

import sys
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.core.throughput import process_link_quality_data
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
        help='入力CSVファイルパス (デフォルト: シナリオ設定から取得)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='出力CSVファイルパス (デフォルト: シナリオ設定から取得)'
    )
    parser.add_argument(
        '--scenario',
        type=str,
        default='default',
        help='シナリオ名 (default, corner_intersection). デフォルト: default'
    )
    return parser.parse_args()


def main():
    """メイン処理"""
    args = parse_args()

    # シナリオ設定を取得
    scenario_config = get_scenario_config(args.scenario)

    # 入出力パス（引数優先、なければシナリオ設定から取得）
    input_csv = Path(args.input) if args.input else scenario_config.raytracing_output_path
    output_csv = Path(args.output) if args.output else scenario_config.throughput_output_path

    print(f"Scenario: {scenario_config.name}")
    print(f"Input: {input_csv}")
    print(f"Output: {output_csv}")

    # 出力ディレクトリを作成
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    process_link_quality_data(str(input_csv), str(output_csv), rate_model=args.rate_model)


if __name__ == "__main__":
    main()
