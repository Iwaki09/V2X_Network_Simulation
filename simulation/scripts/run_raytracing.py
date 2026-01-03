#!/usr/bin/env python3
"""
統合レイトレーシングシミュレーション実行スクリプト

SUMOのFCD出力を読み込み、SIONNA RTレイトレーシングシミュレーションを実行し、
リンク品質結果をCSVファイルに出力します。
"""

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
            'is_line_of_sight'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for lq in link_qualities:
            writer.writerow({
                'timestamp': lq.timestamp,
                'link_type': lq.link_type,
                'tx_id': lq.tx_id,
                'rx_id': lq.rx_id,
                'received_power': f"{lq.received_power_dbm:.2f}",
                'path_loss': f"{lq.path_loss_db:.2f}",
                'delay_spread': f"{lq.delay_spread_ns:.2f}",
                'is_line_of_sight': str(lq.is_line_of_sight)
            })


def main():
    """メイン実行関数"""
    print("=" * 80)
    print(" SUMO + SIONNA RT Integrated Simulation")
    print("=" * 80)

    # パス設定
    fcd_file = PROJECT_DIR / "output/data/fcd/fcd_output.xml"
    output_csv = PROJECT_DIR / "output/data/raytracing/link_quality_results.csv"

    # FCDファイルの存在確認
    if not fcd_file.exists():
        print(f"\n❌ Error: FCD file not found: {fcd_file}")
        print("Please run SUMO simulation first to generate FCD output.")
        sys.exit(1)

    # Step 1: FCDファイルをパース
    print(f"\n[Step 1] Parsing FCD file: {fcd_file}")
    try:
        timestep_data_list = parse_fcd_xml(str(fcd_file))
        print_summary(timestep_data_list)
    except Exception as e:
        print(f"\n❌ Error parsing FCD file: {e}")
        sys.exit(1)

    # Step 2: レイトレーシングシミュレータを初期化
    print("\n[Step 2] Initializing Ray Tracing Simulator")

    base_station = BaseStation(
        id="BS_1",
        position=[500.0, 150.0, 30.0],
        tx_power_dbm=30.0
    )

    building = Building(
        id="Building_1",
        center=[500.0, 50.0, 0.0],
        size=[20.0, 20.0, 100.0]
    )

    simulator = RayTracingSimulator(
        base_station=base_station,
        building=building,
        frequency_ghz=28.0
    )

    # Step 3: 各タイムステップでリンク品質を計算
    print(f"\n[Step 3] Computing link qualities for {len(timestep_data_list)} timesteps")
    print("This may take a while...")

    all_link_qualities = []
    progress_interval = max(1, len(timestep_data_list) // 10)

    for i, timestep_data in enumerate(timestep_data_list):
        # 進捗表示
        if i % progress_interval == 0:
            progress = (i / len(timestep_data_list)) * 100
            print(f"  Progress: {progress:.1f}% (timestep {i}/{len(timestep_data_list)})")

        # 車両位置を取得
        vehicle_positions = get_vehicle_positions(timestep_data)

        if not vehicle_positions:
            continue

        # リンク品質を計算
        link_qualities = simulator.calculate_link_quality(
            timestamp=timestep_data.timestamp,
            vehicle_positions=vehicle_positions
        )

        all_link_qualities.extend(link_qualities)

    print(f"  Progress: 100.0% (timestep {len(timestep_data_list)}/{len(timestep_data_list)})")
    print(f"✅ Computed {len(all_link_qualities)} link quality records")

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

    print("\n" + "=" * 80)
    print("✅ Simulation completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
