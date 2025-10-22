"""
SUMO-Python統合シミュレーション

TraCIを使用してSUMOと連携し、車両情報を取得する
"""

import os
import sys
import traci
import numpy as np
from dataclasses import dataclass
from typing import List, Dict
import json


@dataclass
class VehicleState:
    """車両状態を格納するデータクラス"""
    id: str
    position: np.ndarray  # (x, y)
    speed: float
    angle: float
    time: float


class SUMOSimulation:
    """SUMOシミュレーションを管理するクラス"""

    def __init__(self, config_file: str, use_gui: bool = False):
        """
        初期化

        Args:
            config_file: SUMO設定ファイルのパス
            use_gui: GUIを使用するかどうか
        """
        self.config_file = config_file
        self.use_gui = use_gui
        self.vehicle_traces: Dict[str, List[VehicleState]] = {}

    def start(self):
        """SUMOシミュレーションを開始"""
        # システムにインストールされたSUMOバイナリを使用
        if self.use_gui:
            sumo_binary = "/opt/homebrew/bin/sumo-gui"
        else:
            sumo_binary = "/opt/homebrew/bin/sumo"

        sumo_cmd = [sumo_binary, "-c", self.config_file]

        traci.start(sumo_cmd)
        print(f"SUMO simulation started with config: {self.config_file}")

    def step(self) -> Dict[str, VehicleState]:
        """
        シミュレーションを1ステップ進める

        Returns:
            現在のタイムステップにおける全車両の状態
        """
        traci.simulationStep()
        current_time = traci.simulation.getTime()

        # 全車両のIDを取得
        vehicle_ids = traci.vehicle.getIDList()

        # 各車両の状態を取得
        vehicle_states = {}
        for veh_id in vehicle_ids:
            pos = traci.vehicle.getPosition(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            angle = traci.vehicle.getAngle(veh_id)

            state = VehicleState(
                id=veh_id,
                position=np.array([pos[0], pos[1]]),
                speed=speed,
                angle=angle,
                time=current_time
            )

            vehicle_states[veh_id] = state

            # 軌跡を記録
            if veh_id not in self.vehicle_traces:
                self.vehicle_traces[veh_id] = []
            self.vehicle_traces[veh_id].append(state)

        return vehicle_states

    def is_running(self) -> bool:
        """シミュレーションが実行中かどうか"""
        min_expected_vehicles = traci.simulation.getMinExpectedNumber()
        return min_expected_vehicles > 0

    def close(self):
        """SUMOシミュレーションを終了"""
        traci.close()
        print("SUMO simulation closed")

    def save_traces(self, output_file: str):
        """
        車両軌跡をファイルに保存

        Args:
            output_file: 出力ファイルパス
        """
        # JSON形式で保存
        traces_dict = {}
        for veh_id, states in self.vehicle_traces.items():
            traces_dict[veh_id] = [
                {
                    'time': s.time,
                    'position': s.position.tolist(),
                    'speed': s.speed,
                    'angle': s.angle
                }
                for s in states
            ]

        with open(output_file, 'w') as f:
            json.dump(traces_dict, f, indent=2)

        print(f"Vehicle traces saved to {output_file}")


def main():
    """メイン関数"""
    # 設定
    config_file = "sumo_scenarios/config.sumocfg"
    use_gui = "--gui" in sys.argv

    # SUMOシミュレーション初期化
    sim = SUMOSimulation(config_file, use_gui=use_gui)
    sim.start()

    print("\nSimulation started...")
    print("=" * 60)

    step_count = 0

    # シミュレーションループ
    while sim.is_running():
        vehicle_states = sim.step()

        # 10ステップごとに状態を表示
        if step_count % 100 == 0:
            current_time = traci.simulation.getTime()
            print(f"\nTime: {current_time:.1f}s, Vehicles: {len(vehicle_states)}")
            for veh_id, state in vehicle_states.items():
                print(f"  {veh_id}: pos=({state.position[0]:.1f}, {state.position[1]:.1f}), "
                      f"speed={state.speed:.1f} m/s")

        step_count += 1

    print("\n" + "=" * 60)
    print("Simulation completed!")

    # 軌跡を保存
    output_file = "output/vehicle_traces.json"
    sim.save_traces(output_file)

    # 統計情報を表示
    print(f"\nTotal steps: {step_count}")
    print(f"Total vehicles: {len(sim.vehicle_traces)}")
    for veh_id, trace in sim.vehicle_traces.items():
        print(f"  {veh_id}: {len(trace)} data points")

    # 終了
    sim.close()


if __name__ == "__main__":
    main()
