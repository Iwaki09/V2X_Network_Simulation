#!/usr/bin/env python3
"""
交差点シナリオ用FCD（Floating Car Data）生成スクリプト

SUMOを使わずに、Pythonで直接FCDデータを生成します。
交差点（十字路）を通過する車両の軌跡をシミュレートします。

座標系:
- SUMOネットワーク: 交差点中心が (200, 200)
- 道路: x方向 0-400m, y方向 0-400m
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from dataclasses import dataclass
from typing import List, Tuple
import math
from pathlib import Path


@dataclass
class Vehicle:
    """車両の状態"""
    id: str
    route: str
    speed: float  # m/s
    depart_time: float  # 出発時刻
    start_pos: Tuple[float, float]  # 開始位置
    end_pos: Tuple[float, float]  # 終了位置
    waypoints: List[Tuple[float, float]] = None  # 経由点（左折等）


def create_vehicles() -> List[Vehicle]:
    """
    車両リストを作成

    目標: 交差点中心(0,0)の周辺半径R=150m内で、時刻平均の同時車両数が平均10台以上
    方針: プラトーン投入方式で短間隔（0.5〜1.5s）で車両を投入し、交差点周辺に車を"溜める"
    """
    vehicles = []

    # ルート定義（SUMOネットワーク座標系: 交差点中心=200,200）
    # 道路幅を考慮してy座標を少しずらす
    # 速度を遅くして交差点周辺に長く滞在させる（8〜11 m/s）

    # プラトーン投入パラメータ
    platoon_interval = 0.8  # プラトーン内車両間隔 [秒]
    platoon_size = 20  # 各ルートのプラトーンサイズ（車両数）
    speed_variation = 0.3  # 速度のバリエーション

    # Route A: West→East（直進）y=198.4（南側車線）
    for i in range(platoon_size):
        vehicles.append(Vehicle(
            id=f"we_{i}", route="west_east",
            speed=9.0 + (i % 4) * speed_variation,
            depart_time=i * platoon_interval,
            start_pos=(7.2, 198.4), end_pos=(392.8, 198.4)
        ))

    # Route B: South→North（直進）x=201.6（東側車線）
    for i in range(platoon_size):
        vehicles.append(Vehicle(
            id=f"sn_{i}", route="south_north",
            speed=9.5 + (i % 4) * speed_variation,
            depart_time=0.3 + i * platoon_interval,
            start_pos=(201.6, 7.2), end_pos=(201.6, 392.8)
        ))

    # Route C: East→West（直進）y=201.6（北側車線）
    for i in range(platoon_size):
        vehicles.append(Vehicle(
            id=f"ew_{i}", route="east_west",
            speed=9.0 + (i % 4) * speed_variation,
            depart_time=0.6 + i * platoon_interval,
            start_pos=(392.8, 201.6), end_pos=(7.2, 201.6)
        ))

    # Route D: North→South（直進）x=198.4（西側車線）
    for i in range(platoon_size):
        vehicles.append(Vehicle(
            id=f"ns_{i}", route="north_south",
            speed=9.5 + (i % 4) * speed_variation,
            depart_time=0.9 + i * platoon_interval,
            start_pos=(198.4, 392.8), end_pos=(198.4, 7.2)
        ))

    # Route E: West→North（左折）- 交差点内で滞留
    for i in range(platoon_size // 2):  # 左折は少なめ
        vehicles.append(Vehicle(
            id=f"wn_{i}", route="west_north",
            speed=8.0 + (i % 3) * speed_variation,
            depart_time=1.2 + i * platoon_interval * 1.5,
            start_pos=(7.2, 198.4), end_pos=(201.6, 392.8),
            waypoints=[(200.0, 200.0)]  # 交差点中心で曲がる
        ))

    # Route F: South→East（左折）- 交差点内で滞留
    for i in range(platoon_size // 2):  # 左折は少なめ
        vehicles.append(Vehicle(
            id=f"se_{i}", route="south_east",
            speed=8.0 + (i % 3) * speed_variation,
            depart_time=1.5 + i * platoon_interval * 1.5,
            start_pos=(201.6, 7.2), end_pos=(392.8, 198.4),
            waypoints=[(200.0, 200.0)]
        ))

    return vehicles


def interpolate_position(
    vehicle: Vehicle,
    current_time: float
) -> Tuple[float, float, float, float]:
    """
    車両の現在位置を補間計算

    Returns:
        (x, y, angle, speed) または None（走行前/後）
    """
    if current_time < vehicle.depart_time:
        return None

    elapsed = current_time - vehicle.depart_time
    speed = vehicle.speed

    if vehicle.waypoints:
        # 経由点がある場合（左折等）
        points = [vehicle.start_pos] + vehicle.waypoints + [vehicle.end_pos]
        total_distance = 0
        segments = []

        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            seg_dist = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            segments.append((p1, p2, seg_dist))
            total_distance += seg_dist

        traveled = elapsed * speed
        if traveled > total_distance:
            return None  # 到着済み

        # どのセグメントにいるか
        cumulative = 0
        for p1, p2, seg_dist in segments:
            if cumulative + seg_dist >= traveled:
                # このセグメント内
                seg_traveled = traveled - cumulative
                ratio = seg_traveled / seg_dist if seg_dist > 0 else 0
                x = p1[0] + (p2[0] - p1[0]) * ratio
                y = p1[1] + (p2[1] - p1[1]) * ratio
                angle = math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
                return (x, y, angle, speed)
            cumulative += seg_dist

        return None
    else:
        # 直線移動
        dx = vehicle.end_pos[0] - vehicle.start_pos[0]
        dy = vehicle.end_pos[1] - vehicle.start_pos[1]
        total_distance = math.sqrt(dx**2 + dy**2)

        traveled = elapsed * speed
        if traveled > total_distance:
            return None  # 到着済み

        ratio = traveled / total_distance
        x = vehicle.start_pos[0] + dx * ratio
        y = vehicle.start_pos[1] + dy * ratio
        angle = math.degrees(math.atan2(dy, dx))

        return (x, y, angle, speed)


def generate_fcd_xml(vehicles: List[Vehicle], output_path: str, duration: float = 100.0, step: float = 1.0):
    """
    FCD XMLファイルを生成

    Args:
        vehicles: 車両リスト
        output_path: 出力ファイルパス
        duration: シミュレーション時間 [秒]
        step: タイムステップ [秒]
    """
    root = ET.Element("fcd-export")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    root.set("xsi:noNamespaceSchemaLocation", "http://sumo.dlr.de/xsd/fcd_file.xsd")

    current_time = 0.0
    while current_time <= duration:
        timestep = ET.SubElement(root, "timestep")
        timestep.set("time", f"{current_time:.2f}")

        for vehicle in vehicles:
            pos = interpolate_position(vehicle, current_time)
            if pos is not None:
                x, y, angle, speed = pos
                veh_elem = ET.SubElement(timestep, "vehicle")
                veh_elem.set("id", vehicle.id)
                veh_elem.set("x", f"{x:.2f}")
                veh_elem.set("y", f"{y:.2f}")
                veh_elem.set("z", "1.50")  # 車両高さ
                veh_elem.set("angle", f"{angle:.2f}")
                veh_elem.set("type", "passenger_car")
                veh_elem.set("speed", f"{speed:.2f}")
                veh_elem.set("pos", "0.00")
                veh_elem.set("lane", "unknown_0")
                veh_elem.set("slope", "0.00")

        current_time += step

    # XMLを整形して出力
    xml_str = ET.tostring(root, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="    ")

    # XML宣言を修正（minidomが追加する余分な空行を削除）
    lines = pretty_xml.split('\n')
    lines = [line for line in lines if line.strip()]
    pretty_xml = '\n'.join(lines)

    # ディレクトリを作成
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        # ルート要素以降を書き込み
        for line in lines[1:]:
            f.write(line + '\n')

    print(f"Generated FCD file: {output_path}")


def main():
    """メイン関数"""
    # 出力パス
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    output_path = project_dir / "output/scenarios/corner_intersection/fcd/fcd_output.xml"

    print("=" * 60)
    print("FCD Generator for Corner Intersection Scenario")
    print("=" * 60)

    # 車両を作成
    vehicles = create_vehicles()
    print(f"Created {len(vehicles)} vehicles")

    # FCD XMLを生成
    generate_fcd_xml(vehicles, str(output_path), duration=100.0, step=1.0)

    # サマリー
    print("\nSummary:")
    print(f"  - Total vehicles: {len(vehicles)}")
    print(f"  - Simulation duration: 100 seconds")
    print(f"  - Time step: 1.0 second")
    print(f"  - Output file: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
