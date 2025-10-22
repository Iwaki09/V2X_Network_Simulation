"""
V2X通信シミュレーション - メインスクリプト

SUMOシミュレーション、チャネル計算、グラフ最適化、可視化を統合
"""

import sys
import numpy as np
from typing import List, Dict
import traci

from sumo_simulation import SUMOSimulation, VehicleState
from channel_model import ChannelModel, ChannelParameters
from graph_optimizer import GraphOptimizer, PathInfo
from visualizer import Visualizer


def main():
    """メイン関数"""
    print("=" * 80)
    print(" V2X Communication Simulation with SUMO")
    print("=" * 80)

    # 設定
    config_file = "sumo_scenarios/config.sumocfg"
    use_gui = "--gui" in sys.argv
    snapshot_interval = 50  # スナップショット保存間隔（ステップ数）

    # 初期化
    print("\nInitializing components...")
    sumo_sim = SUMOSimulation(config_file, use_gui=use_gui)
    channel_model = ChannelModel(ChannelParameters())
    optimizer = GraphOptimizer()
    visualizer = Visualizer()

    print(f"  - SUMO config: {config_file}")
    print(f"  - GUI mode: {'ON' if use_gui else 'OFF'}")
    print(f"  - Channel frequency: {channel_model.params.frequency / 1e9:.1f} GHz")
    print(f"  - Max communication range: {channel_model.params.max_range_m} m")

    # SUMOシミュレーション開始
    sumo_sim.start()
    print("\nSimulation started!")
    print("-" * 80)

    # データ収集用リスト
    time_series = []
    avg_snr_series = []
    num_links_series = []
    position_snapshots = []
    graph_snapshots = []
    path_snapshots = []

    step_count = 0

    # シミュレーションループ
    while sumo_sim.is_running():
        # SUMOシミュレーションを1ステップ進める
        vehicle_states = sumo_sim.step()

        if len(vehicle_states) == 0:
            step_count += 1
            continue

        # 現在時刻
        current_time = traci.simulation.getTime()

        # 車両位置を抽出
        positions = {veh_id: state.position for veh_id, state in vehicle_states.items()}

        # チャネル行列を計算
        channel_matrix, veh_map, dist_matrix = channel_model.calculate_channel_matrix(positions)

        # グラフを構築
        optimizer.build_graph(positions, channel_matrix, veh_map, snr_threshold_db=5.0)

        # 統計情報を計算
        if optimizer.graph.number_of_edges() > 0:
            # 平均SNRを計算
            snr_values = [data['snr'] for _, _, data in optimizer.graph.edges(data=True)]
            avg_snr = np.mean(snr_values)
            num_links = optimizer.graph.number_of_edges()
        else:
            avg_snr = 0.0
            num_links = 0

        # データを記録
        time_series.append(current_time)
        avg_snr_series.append(avg_snr)
        num_links_series.append(num_links)

        # 最適経路を計算（始点・終点が存在する場合）
        vehicle_ids = sorted(vehicle_states.keys())
        optimal_path = None
        if len(vehicle_ids) >= 2:
            # 最初の車両から最後の車両への経路を計算
            source = vehicle_ids[0]
            target = vehicle_ids[-1]
            optimal_path = optimizer.find_shortest_path(source, target, weight_type='weight')

        # 定期的にスナップショットを保存
        if step_count % snapshot_interval == 0:
            position_snapshots.append(positions.copy())
            graph_snapshots.append(optimizer.graph.copy())
            path_snapshots.append(optimal_path)

            # 進捗表示
            print(f"\nTime: {current_time:.1f}s (Step {step_count})")
            print(f"  Vehicles: {len(vehicle_states)}")
            print(f"  Communication links: {num_links}")
            print(f"  Average SNR: {avg_snr:.2f} dB")

            if optimal_path:
                print(f"  Optimal path ({optimal_path.source} -> {optimal_path.target}):")
                print(f"    Route: {' -> '.join(optimal_path.path)}")
                print(f"    Hops: {optimal_path.hop_count}")
                print(f"    Min link quality: {optimal_path.min_link_quality:.2f} dB")

            # 可視化を保存
            snapshot_path = f"figures/snapshot_t{int(current_time):03d}.png"
            visualizer.plot_snapshot(positions, optimizer.graph, optimal_path,
                                    time=current_time, save_path=snapshot_path)

        step_count += 1

    print("\n" + "-" * 80)
    print("Simulation completed!")

    # 統計情報を可視化
    print("\nGenerating statistics plots...")
    visualizer.plot_statistics(
        time_series,
        avg_snr_series,
        num_links_series,
        save_path="figures/statistics.png"
    )

    # 最終サマリー
    print("\n" + "=" * 80)
    print(" Simulation Summary")
    print("=" * 80)
    print(f"  Total simulation steps: {step_count}")
    print(f"  Total vehicles: {len(sumo_sim.vehicle_traces)}")
    print(f"  Simulation duration: {time_series[-1]:.1f}s" if time_series else "  Simulation duration: 0s")
    print(f"  Average SNR: {np.mean(avg_snr_series):.2f} dB" if avg_snr_series else "  Average SNR: N/A")
    print(f"  Average number of links: {np.mean(num_links_series):.1f}" if num_links_series else "  Average number of links: N/A")

    # 車両軌跡を保存
    print(f"\nSaving vehicle traces...")
    sumo_sim.save_traces("output/vehicle_traces.json")

    # グラフメトリクスの最終値
    if optimizer.graph.number_of_nodes() > 0:
        metrics = optimizer.calculate_graph_metrics()
        print(f"\nFinal Graph Metrics:")
        for key, value in metrics.items():
            print(f"  {key}: {value}")

    # SUMOを終了
    sumo_sim.close()

    print("\n" + "=" * 80)
    print(" All results saved to:")
    print("   - Figures: figures/")
    print("   - Vehicle traces: output/vehicle_traces.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
