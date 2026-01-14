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
from src.core.beamforming import BeamformingConfig
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

    # Mode-aware Fading Margin オプション
    parser.add_argument(
        '--enable-margin-estimate',
        action='store_true',
        help='推定列生成を有効化（Mode-aware Fading Margin適用）'
    )
    parser.add_argument(
        '--margin-p',
        type=float,
        default=0.10,
        help='Dモード用の目標信頼性（下位p分位）. デフォルト: 0.10'
    )
    parser.add_argument(
        '--margin-k-db',
        type=float,
        default=3.0,
        help='Kモード用の固定マージン [dB]. デフォルト: 3.0'
    )
    parser.add_argument(
        '--margin-d-db',
        type=float,
        default=None,
        help='Dモード用マージンを手動指定 [dB] (指定しない場合はmargin-pから計算)'
    )

    # Beamforming オプション
    parser.add_argument(
        '--disable-beamforming',
        action='store_false',
        dest='enable_beamforming',
        help='ビームフォーミング計算を無効化（デフォルト: 有効）'
    )
    parser.add_argument(
        '--bf-tx-power-db',
        type=float,
        default=40.0,
        help='BF用Tx電力 (PA出力) [dBm]. デフォルト: 40'
    )
    parser.add_argument(
        '--bf-feeder-loss-db',
        type=float,
        default=3.0,
        help='フィーダ損失 [dB]. デフォルト: 3'
    )
    parser.add_argument(
        '--bs-array-rows',
        type=int,
        default=16,
        help='BSアンテナ配列 行数 (デフォルト: 16)'
    )
    parser.add_argument(
        '--bs-array-cols',
        type=int,
        default=16,
        help='BSアンテナ配列 列数 (デフォルト: 16)'
    )
    parser.add_argument(
        '--ue-array',
        type=str,
        choices=['ula', 'upa'],
        default='ula',
        help='UE配列形状 (ula=1x10, upa=2x5). デフォルト: ula'
    )
    parser.add_argument(
        '--ue-array-rows',
        type=int,
        default=None,
        help='UE配列 行数 (未指定なら --ue-array に従う)'
    )
    parser.add_argument(
        '--ue-array-cols',
        type=int,
        default=None,
        help='UE配列 列数 (未指定なら --ue-array に従う)'
    )
    parser.add_argument(
        '--element-spacing-lambda',
        type=float,
        default=0.5,
        help='素子間隔 [lambda]. デフォルト: 0.5'
    )
    parser.add_argument(
        '--bs-element-gain-db',
        type=float,
        default=8.0,
        help='BS素子最大利得 [dBi]. デフォルト: 8'
    )
    parser.add_argument(
        '--ue-element-gain-db',
        type=float,
        default=0.0,
        help='UE素子利得 [dBi]. デフォルト: 0'
    )
    parser.add_argument(
        '--theta-3db',
        type=float,
        default=65.0,
        help='3GPP素子パターン θ_3dB [deg]. デフォルト: 65'
    )
    parser.add_argument(
        '--phi-3db',
        type=float,
        default=65.0,
        help='3GPP素子パターン φ_3dB [deg]. デフォルト: 65'
    )
    parser.add_argument(
        '--sla-v',
        type=float,
        default=30.0,
        help='3GPP素子パターン SLA_V [dB]. デフォルト: 30'
    )
    parser.add_argument(
        '--a-m',
        type=float,
        default=30.0,
        help='3GPP素子パターン A_m [dB]. デフォルト: 30'
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

    beamforming_config = None
    if args.enable_beamforming:
        if args.ue_array_rows is None or args.ue_array_cols is None:
            if args.ue_array == 'ula':
                ue_rows, ue_cols = 1, 10
            else:
                ue_rows, ue_cols = 2, 5
        else:
            ue_rows, ue_cols = args.ue_array_rows, args.ue_array_cols

        beamforming_config = BeamformingConfig(
            bs_num_rows=args.bs_array_rows,
            bs_num_cols=args.bs_array_cols,
            ue_num_rows=ue_rows,
            ue_num_cols=ue_cols,
            element_spacing_lambda=args.element_spacing_lambda,
            bs_element_gain_db=args.bs_element_gain_db,
            ue_element_gain_db=args.ue_element_gain_db,
            tx_power_dbm=args.bf_tx_power_db,
            feeder_loss_db=args.bf_feeder_loss_db,
            theta_3db=args.theta_3db,
            phi_3db=args.phi_3db,
            sla_v=args.sla_v,
            a_m=args.a_m,
            rt_tx_power_dbm=scenario_config.base_station.tx_power_dbm
        )

    process_link_quality_data(
        str(input_csv),
        str(output_csv),
        rate_model=args.rate_model,
        enable_margin_estimate=args.enable_margin_estimate,
        margin_p=args.margin_p,
        margin_k_db=args.margin_k_db,
        margin_d_db_override=args.margin_d_db,
        enable_beamforming=args.enable_beamforming,
        beamforming_config=beamforming_config
    )


if __name__ == "__main__":
    main()
