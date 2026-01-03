"""
FCD (Floating Car Data) XMLパーサー

SUMOが生成したFCD XMLファイルをパースし、
各タイムステップにおける車両の位置情報を抽出します。
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class VehicleState:
    """車両の状態を表すデータクラス"""
    vehicle_id: str
    x: float  # X座標 [m]
    y: float  # Y座標 [m]
    z: float  # Z座標 [m]（アンテナ高さ）
    speed: float  # 速度 [m/s]
    angle: float  # 進行方向 [度]


@dataclass
class TimestepData:
    """タイムステップごとのデータ"""
    timestamp: float  # タイムステップ [秒]
    vehicles: List[VehicleState]


def parse_fcd_xml(filepath: str, antenna_height: float = 1.5) -> List[TimestepData]:
    """
    FCD XMLファイルをパースし、各タイムステップの車両情報を抽出

    Args:
        filepath: FCD XMLファイルのパス
        antenna_height: 車両アンテナの高さ（Z座標） [m]

    Returns:
        タイムステップごとの車両情報のリスト
    """
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
    except Exception as e:
        raise RuntimeError(f"Failed to parse FCD XML file: {filepath}") from e

    timestep_data_list = []

    # 各タイムステップを処理
    for timestep_elem in root.findall('timestep'):
        timestamp = float(timestep_elem.get('time'))
        vehicles = []

        # 各車両を処理
        for vehicle_elem in timestep_elem.findall('vehicle'):
            vehicle_id = vehicle_elem.get('id')
            x = float(vehicle_elem.get('x'))
            y = float(vehicle_elem.get('y'))
            speed = float(vehicle_elem.get('speed'))
            angle = float(vehicle_elem.get('angle'))

            # 車両状態を作成（Z座標はアンテナ高さ）
            vehicle_state = VehicleState(
                vehicle_id=vehicle_id,
                x=x,
                y=y,
                z=antenna_height,
                speed=speed,
                angle=angle
            )
            vehicles.append(vehicle_state)

        # タイムステップデータを作成
        timestep_data = TimestepData(
            timestamp=timestamp,
            vehicles=vehicles
        )
        timestep_data_list.append(timestep_data)

    return timestep_data_list


def get_vehicle_positions(timestep_data: TimestepData) -> Dict[str, List[float]]:
    """
    タイムステップデータから車両IDと3次元座標のマッピングを取得

    Args:
        timestep_data: タイムステップデータ

    Returns:
        車両IDをキー、3次元座標[x, y, z]を値とする辞書
    """
    positions = {}
    for vehicle in timestep_data.vehicles:
        positions[vehicle.vehicle_id] = [vehicle.x, vehicle.y, vehicle.z]
    return positions


def print_summary(timestep_data_list: List[TimestepData]):
    """
    パース結果のサマリーを表示

    Args:
        timestep_data_list: タイムステップデータのリスト
    """
    if not timestep_data_list:
        print("No data available")
        return

    num_timesteps = len(timestep_data_list)
    first_time = timestep_data_list[0].timestamp
    last_time = timestep_data_list[-1].timestamp

    # 全タイムステップの車両IDを収集
    all_vehicle_ids = set()
    for timestep_data in timestep_data_list:
        for vehicle in timestep_data.vehicles:
            all_vehicle_ids.add(vehicle.vehicle_id)

    num_vehicles = len(all_vehicle_ids)

    print("=" * 60)
    print("FCD Parsing Summary")
    print("=" * 60)
    print(f"Number of timesteps: {num_timesteps}")
    print(f"Time range: {first_time:.1f}s - {last_time:.1f}s")
    print(f"Total unique vehicles: {num_vehicles}")
    print(f"Vehicle IDs: {sorted(all_vehicle_ids)[:10]}..." if num_vehicles > 10 else f"Vehicle IDs: {sorted(all_vehicle_ids)}")
    print("=" * 60)


if __name__ == "__main__":
    """パーサーの単体テスト"""
    import sys
    from pathlib import Path

    # スクリプトディレクトリを基準にパスを解決
    script_dir = Path(__file__).parent.parent.parent
    fcd_file = sys.argv[1] if len(sys.argv) > 1 else str(script_dir / "output/fcd/fcd_output.xml")

    print(f"Parsing FCD file: {fcd_file}")

    try:
        # FCDファイルをパース
        timestep_data_list = parse_fcd_xml(fcd_file)

        # サマリーを表示
        print_summary(timestep_data_list)

        # 最初のいくつかのタイムステップを詳細表示
        print("\nFirst 3 timesteps (detailed):")
        for timestep_data in timestep_data_list[:3]:
            print(f"\n  Time: {timestep_data.timestamp:.1f}s")
            print(f"  Vehicles: {len(timestep_data.vehicles)}")
            for vehicle in timestep_data.vehicles[:5]:  # 最初の5台のみ表示
                print(f"    - {vehicle.vehicle_id}: ({vehicle.x:.2f}, {vehicle.y:.2f}, {vehicle.z:.2f}) @ {vehicle.speed:.2f} m/s")

        print("\n✅ FCD parsing test completed successfully!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
