#!/usr/bin/env python3
"""
統合レイトレーシングシミュレーション実行スクリプト

SUMOのFCD出力を読み込み、SIONNA RTレイトレーシングシミュレーションを実行し、
リンク品質結果をCSVファイルに出力します。

オプション:
  --sionna-rt: Sionna RTによる本格的なレイトレーシング（マルチパス対応）を使用
               指定しない場合は簡易パスロスモデル（単一パス）を使用
  --scenario: シナリオ名（default, corner_intersection）
"""

import argparse
import csv
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.parsers.fcd_parser import parse_fcd_xml, print_summary, get_vehicle_positions
from src.core.raytracing import (
    RayTracingSimulator,
    BaseStation,
    Building,
    LinkQuality
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


def save_link_quality_csv(link_qualities: list, output_path: str):
    """
    リンク品質結果をCSVファイルに保存

    Args:
        link_qualities: リンク品質のリスト
        output_path: 出力CSVファイルのパス
    """
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'timestamp',
            'link_type',
            'tx_id',
            'rx_id',
            'received_power',
            'path_loss',
            'delay_spread',
            'is_line_of_sight',
            # Propagation-Mode Switch (D/K) 関連列
            'num_paths',
            'p_tot_watts',
            'p_max_watts',
            'dominance',
            'k_factor',
            'k_factor_db',
            'prop_mode'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for lq in link_qualities:
            # k_factor と k_factor_db は inf の可能性があるため文字列変換
            k_factor_str = "inf" if lq.k_factor == float("inf") else f"{lq.k_factor:.6f}"
            k_factor_db_str = "inf" if lq.k_factor_db == float("inf") else f"{lq.k_factor_db:.2f}"

            writer.writerow({
                'timestamp': lq.timestamp,
                'link_type': lq.link_type,
                'tx_id': lq.tx_id,
                'rx_id': lq.rx_id,
                'received_power': f"{lq.received_power_dbm:.2f}",
                'path_loss': f"{lq.path_loss_db:.2f}",
                'delay_spread': f"{lq.delay_spread_ns:.2f}",
                'is_line_of_sight': str(lq.is_line_of_sight),
                # D/K 関連
                'num_paths': lq.num_paths,
                'p_tot_watts': f"{lq.p_tot_watts:.12e}",
                'p_max_watts': f"{lq.p_max_watts:.12e}",
                'dominance': f"{lq.dominance:.6f}",
                'k_factor': k_factor_str,
                'k_factor_db': k_factor_db_str,
                'prop_mode': lq.prop_mode
            })


def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(
        description="SUMO + SIONNA RT統合レイトレーシングシミュレーション"
    )
    parser.add_argument(
        "--sionna-rt",
        action="store_true",
        help="Sionna RTによるマルチパス計算を有効化（デフォルト: 簡易モデル）"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="レイトレーシングの最大反射回数（デフォルト: 3）"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=1000000,
        help="レイトレーシングのサンプル数（デフォルト: 1000000）"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="default",
        help="シナリオ名（default, corner_intersection）"
    )
    return parser.parse_args()


def main():
    """メイン実行関数"""
    args = parse_args()

    # シナリオ設定を取得
    scenario_config = get_scenario_config(args.scenario)

    print("=" * 80)
    print(" SUMO + SIONNA RT Integrated Simulation")
    print("=" * 80)
    print(f"  Scenario: {scenario_config.name}")
    print(f"  Description: {scenario_config.description}")
    print(f"  Mode: {'Sionna RT (multi-path)' if args.sionna_rt else 'Simple model (single-path)'}")

    # パス設定（シナリオから取得）
    fcd_file = scenario_config.fcd_output_path
    output_csv = scenario_config.raytracing_output_path

    # FCDファイルの存在確認
    if not fcd_file.exists():
        print(f"\n Error: FCD file not found: {fcd_file}")
        print("Please run SUMO simulation first to generate FCD output.")
        sys.exit(1)

    # Step 1: FCDファイルをパース
    print(f"\n[Step 1] Parsing FCD file: {fcd_file}")
    try:
        timestep_data_list = parse_fcd_xml(str(fcd_file))
        print_summary(timestep_data_list)
    except Exception as e:
        print(f"\n Error parsing FCD file: {e}")
        sys.exit(1)

    # Step 2: レイトレーシングシミュレータを初期化
    print("\n[Step 2] Initializing Ray Tracing Simulator")

    # シナリオ設定から基地局と建物を取得
    base_station = scenario_config.base_station
    buildings = scenario_config.buildings

    simulator = RayTracingSimulator(
        base_station=base_station,
        buildings=buildings,
        frequency_ghz=scenario_config.frequency_ghz,
        v2v_tx_power_dbm=scenario_config.v2v_tx_power_dbm,
        use_sionna_rt=args.sionna_rt,
        max_depth=args.max_depth,
        num_samples=args.num_samples
    )

    # Step 3: 各タイムステップでリンク品質を計算
    print(f"\n[Step 3] Computing link qualities for {len(timestep_data_list)} timesteps")
    print(f"  Coordinate offset: ({scenario_config.coord_offset_x}, {scenario_config.coord_offset_y})")
    print("This may take a while...")

    all_link_qualities = []
    progress_interval = max(1, len(timestep_data_list) // 10)

    for i, timestep_data in enumerate(timestep_data_list):
        # 進捗表示
        if i % progress_interval == 0:
            progress = (i / len(timestep_data_list)) * 100
            print(f"  Progress: {progress:.1f}% (timestep {i}/{len(timestep_data_list)})")

        # 車両位置を取得
        raw_positions = get_vehicle_positions(timestep_data)

        if not raw_positions:
            continue

        # 座標変換を適用（シナリオのオフセット）
        vehicle_positions = {}
        for vid, pos in raw_positions.items():
            new_x, new_y = scenario_config.transform_coordinates(pos[0], pos[1])
            vehicle_positions[vid] = [new_x, new_y, pos[2]]

        # リンク品質を計算
        link_qualities = simulator.calculate_link_quality(
            timestamp=timestep_data.timestamp,
            vehicle_positions=vehicle_positions
        )

        all_link_qualities.extend(link_qualities)

    print(f"  Progress: 100.0% (timestep {len(timestep_data_list)}/{len(timestep_data_list)})")
    print(f"  Computed {len(all_link_qualities)} link quality records")

    # Step 4: 結果をCSVに保存
    print(f"\n[Step 4] Saving results to: {output_csv}")
    try:
        save_link_quality_csv(all_link_qualities, str(output_csv))
        print(f"✅ Results saved successfully!")
    except Exception as e:
        print(f"\n❌ Error saving CSV file: {e}")
        sys.exit(1)

    # Step 5: サマリー表示
    print("\n" + "=" * 80)
    print(" Simulation Summary")
    print("=" * 80)
    print(f"  Total timesteps processed: {len(timestep_data_list)}")
    print(f"  Total link quality records: {len(all_link_qualities)}")
    print(f"  Output CSV: {output_csv}")

    # サンプル結果を表示
    if all_link_qualities:
        print("\n  Sample results (first 5 records):")
        for lq in all_link_qualities[:5]:
            los_str = "LOS" if lq.is_line_of_sight else "NLOS"
            print(f"    t={lq.timestamp:.1f}s, {lq.link_type}: {lq.tx_id} -> {lq.rx_id}: "
                  f"Rx={lq.received_power_dbm:.2f}dBm, PL={lq.path_loss_db:.2f}dB ({los_str})")

        # V2I/V2Vリンク数の統計
        v2i_count = sum(1 for lq in all_link_qualities if lq.link_type == "V2I")
        v2v_count = sum(1 for lq in all_link_qualities if lq.link_type == "V2V")
        print(f"\n  Link statistics:")
        print(f"    V2I links: {v2i_count}")
        print(f"    V2V links: {v2v_count}")

        # LOS/NLOS統計（検証ログ）
        los_count = sum(1 for lq in all_link_qualities if lq.is_line_of_sight)
        nlos_count = sum(1 for lq in all_link_qualities if not lq.is_line_of_sight)
        total_links = len(all_link_qualities)
        nlos_ratio = (nlos_count / total_links * 100) if total_links > 0 else 0

        print(f"\n  LOS/NLOS statistics:")
        print(f"    LOS links: {los_count}")
        print(f"    NLOS links: {nlos_count}")
        print(f"    NLOS ratio: {nlos_ratio:.1f}%")

        # prop_mode統計（D/K）
        prop_d_count = sum(1 for lq in all_link_qualities if lq.prop_mode == "D")
        prop_k_count = sum(1 for lq in all_link_qualities if lq.prop_mode == "K")

        print(f"\n  Propagation mode statistics:")
        print(f"    prop_mode=D: {prop_d_count}")
        print(f"    prop_mode=K: {prop_k_count}")

        # 合格条件のチェック
        print(f"\n  Validation check:")
        if nlos_ratio >= 5.0:
            print(f"    [PASS] NLOS ratio >= 5% ({nlos_ratio:.1f}%)")
        else:
            print(f"    [WARN] NLOS ratio < 5% ({nlos_ratio:.1f}%) - consider adjusting building layout")

        if prop_k_count >= 100:
            print(f"    [PASS] prop_mode=K count >= 100 ({prop_k_count})")
        else:
            print(f"    [WARN] prop_mode=K count < 100 ({prop_k_count}) - increase multipath scenarios")

    print("\n" + "=" * 80)
    print("  Simulation completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
