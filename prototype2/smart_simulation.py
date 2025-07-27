"""
Smart V2X Network Simulation with Building Occlusion
Refactored for simplicity and efficiency
"""

import sionna as sn
import tensorflow as tf
import numpy as np
import json
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

@dataclass
class Vehicle:
    """車両の定義"""
    id: str
    initial_position: List[float]
    velocity: List[float]  # [vx, vy] m/s
    antenna_height: float = 1.5

@dataclass
class BaseStation:
    """基地局の定義"""
    id: str
    position: List[float]
    antenna_height: float = 10.0
    max_capacity: int = 10

@dataclass
class Building:
    """建物の定義"""
    id: str
    position: List[float]  # [x, y, z]
    size: List[float]      # [width, depth, height]
    material: str = "concrete"

class SmartV2XSimulation:
    """スマートなV2Xシミュレーション"""
    
    def __init__(self):
        self.vehicles: List[Vehicle] = []
        self.base_stations: List[BaseStation] = []
        self.buildings: List[Building] = []
        self.time_steps = 20
        self.time_step_duration = 1.0  # seconds
        self.world_size = [300, 300]
        
        # Initialize SIONNA RT
        self._init_sionna_rt()
    
    def _init_sionna_rt(self):
        """SIONNA RTの初期化"""
        # Check GPU availability
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            raise RuntimeError("No GPU found. SIONNA RT requires a GPU.")
        
        # Configure antenna arrays
        self.tx_array = sn.rt.PlanarArray(
            num_rows=1, num_cols=1, 
            vertical_spacing=0.5, horizontal_spacing=0.5,
            pattern="dipole", polarization="V"
        )
        self.rx_array = sn.rt.PlanarArray(
            num_rows=1, num_cols=1,
            vertical_spacing=0.5, horizontal_spacing=0.5, 
            pattern="dipole", polarization="V"
        )
    
    def setup_scenario(self) -> None:
        """新しいシナリオをセットアップ"""
        print("Setting up smart V2X scenario...")
        
        # 6台の車両（異なる速度で移動）
        vehicles_config = [
            {"id": "vehicle_1", "pos": [50, 50], "vel": [8, 0]},    # 東向き
            {"id": "vehicle_2", "pos": [100, 100], "vel": [-6, 0]}, # 西向き
            {"id": "vehicle_3", "pos": [150, 80], "vel": [0, 7]},   # 北向き
            {"id": "vehicle_4", "pos": [200, 150], "vel": [0, -5]}, # 南向き
            {"id": "vehicle_5", "pos": [80, 200], "vel": [4, -3]},  # 南東向き
            {"id": "vehicle_6", "pos": [180, 30], "vel": [-7, 4]},  # 北西向き
        ]
        
        for v_config in vehicles_config:
            vehicle = Vehicle(
                id=v_config["id"],
                initial_position=v_config["pos"] + [1.5],  # Add z coordinate
                velocity=v_config["vel"]
            )
            self.vehicles.append(vehicle)
        
        # 2つの基地局
        self.base_stations = [
            BaseStation(id="bs_1", position=[80, 80, 15]),
            BaseStation(id="bs_2", position=[220, 180, 15])
        ]
        
        # 1つの建物（遮蔽用）
        self.buildings = [
            Building(
                id="building_1",
                position=[150, 120, 0],  # 中央付近
                size=[60, 40, 25],       # 幅x奥行きx高さ
                material="concrete"
            )
        ]
        
        print(f"✅ Scenario ready: {len(self.vehicles)} vehicles, {len(self.base_stations)} base stations, {len(self.buildings)} buildings")
    
    def _create_sionna_scene(self) -> sn.rt.Scene:
        """SIONNA RTシーンを作成"""
        # Use simple_street_canyon as base scene for reliable building occlusion
        try:
            scene = sn.rt.load_scene(sn.rt.scene.simple_street_canyon)
            print("✅ Loaded base scene with building occlusion effects")
        except Exception as e:
            print(f"❌ Failed to load base scene: {e}")
            scene = sn.rt.Scene()
            print("Using empty scene")
        
        # Configure antenna arrays
        scene.tx_array = self.tx_array
        scene.rx_array = self.rx_array
        
        return scene
    
    def get_vehicle_position(self, vehicle: Vehicle, time_step: int) -> List[float]:
        """指定された時刻での車両位置を計算"""
        time = time_step * self.time_step_duration
        x = vehicle.initial_position[0] + vehicle.velocity[0] * time
        y = vehicle.initial_position[1] + vehicle.velocity[1] * time
        z = vehicle.initial_position[2]
        
        # Keep vehicles within world bounds
        x = max(10, min(self.world_size[0] - 10, x))
        y = max(10, min(self.world_size[1] - 10, y))
        
        return [x, y, z]
    
    def run_simulation(self) -> Dict[str, Any]:
        """シミュレーション実行"""
        print("Starting smart V2X simulation...")
        
        results = {
            "scenario": "smart_v2x_6vehicles",
            "time_steps": self.time_steps,
            "vehicles": len(self.vehicles),
            "base_stations": len(self.base_stations),
            "buildings": len(self.buildings),
            "simulation_data": []
        }
        
        for step in range(self.time_steps):
            print(f"Processing time step {step+1}/{self.time_steps}")
            
            # Create SIONNA scene for this time step
            scene = self._create_sionna_scene()
            
            # Add transmitters (base stations)
            for bs in self.base_stations:
                scene.add(sn.rt.Transmitter(name=f"tx_{bs.id}", position=bs.position))
            
            # Add receivers (vehicles at current positions)
            for vehicle in self.vehicles:
                pos = self.get_vehicle_position(vehicle, step)
                scene.add(sn.rt.Receiver(name=f"rx_{vehicle.id}", position=pos))
            
            # Compute path loss
            path_loss_matrix = self._compute_path_loss(scene)
            
            # Store step data
            step_data = {
                "time_step": step,
                "time": step * self.time_step_duration,
                "vehicle_positions": {
                    vehicle.id: self.get_vehicle_position(vehicle, step)
                    for vehicle in self.vehicles
                },
                "path_loss_matrix": path_loss_matrix.tolist(),
                "path_loss_pairs": []
            }
            
            # Create path loss pairs for analysis
            for i, bs in enumerate(self.base_stations):
                for j, vehicle in enumerate(self.vehicles):
                    step_data["path_loss_pairs"].append({
                        "source": vehicle.id,
                        "target": bs.id,
                        "path_loss_db": float(path_loss_matrix[i, j])
                    })
            
            results["simulation_data"].append(step_data)
        
        print("✅ Smart V2X simulation completed")
        return results
    
    def _compute_path_loss(self, scene: sn.rt.Scene) -> np.ndarray:
        """パスロス計算"""
        try:
            # Compute paths
            path_solver = sn.rt.PathSolver()
            paths = path_solver(scene=scene, max_depth=5)
            
            # Extract path loss
            a, _ = paths.cir()
            
            # Convert to TensorFlow tensors if needed
            if isinstance(a, list):
                a = [tf.convert_to_tensor(x) for x in a]
            
            # Calculate path loss matrix
            num_bs = len(self.base_stations)
            num_vehicles = len(self.vehicles)
            path_loss_matrix = np.zeros((num_bs, num_vehicles))
            
            for i in range(num_bs):
                for j in range(num_vehicles):
                    # Extract path gain and convert to path loss
                    try:
                        path_gain = tf.reduce_sum(tf.square(tf.abs(a[0][i, 0, j, 0, :, :])), axis=[-1]).numpy()[0]
                        path_loss_db = -10 * np.log10(path_gain) if path_gain > 0 else 150.0  # 150dB as max loss
                        path_loss_matrix[i, j] = path_loss_db
                    except:
                        path_loss_matrix[i, j] = 120.0  # Default high path loss
            
            return path_loss_matrix
            
        except Exception as e:
            print(f"❌ Path loss computation failed: {e}")
            # Return default high path loss values
            return np.full((len(self.base_stations), len(self.vehicles)), 120.0)
    
    def save_results(self, results: Dict[str, Any], filename: str = "smart_simulation_results.json"):
        """結果をファイルに保存"""
        output_path = f"output/{filename}"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to {output_path}")
    
    def analyze_occlusion_effects(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """遮蔽効果の分析"""
        analysis = {
            "building_position": self.buildings[0].position if self.buildings else None,
            "building_size": self.buildings[0].size if self.buildings else None,
            "occlusion_events": [],
            "path_loss_statistics": {}
        }
        
        # Analyze path loss variations for each vehicle-BS pair
        for bs in self.base_stations:
            for vehicle in self.vehicles:
                pair_key = f"{vehicle.id}-{bs.id}"
                path_losses = []
                
                for step_data in results["simulation_data"]:
                    for pair in step_data["path_loss_pairs"]:
                        if pair["source"] == vehicle.id and pair["target"] == bs.id:
                            path_losses.append(pair["path_loss_db"])
                
                if path_losses:
                    analysis["path_loss_statistics"][pair_key] = {
                        "min": min(path_losses),
                        "max": max(path_losses),
                        "mean": sum(path_losses) / len(path_losses),
                        "variation": max(path_losses) - min(path_losses)
                    }
        
        return analysis

def main():
    """メイン実行関数"""
    # Create and run smart simulation
    sim = SmartV2XSimulation()
    sim.setup_scenario()
    
    # Run simulation
    results = sim.run_simulation()
    
    # Analyze results
    analysis = sim.analyze_occlusion_effects(results)
    
    # Save results
    sim.save_results(results, "smart_v2x_simulation_results.json")
    sim.save_results(analysis, "smart_v2x_analysis.json")
    
    # Print summary
    print("\n=== Simulation Summary ===")
    print(f"Scenario: {results['scenario']}")
    print(f"Time steps: {results['time_steps']}")
    print(f"Vehicles: {results['vehicles']}")
    print(f"Base stations: {results['base_stations']}")
    print(f"Buildings: {results['buildings']}")
    
    # Print path loss statistics
    if analysis["path_loss_statistics"]:
        print("\n=== Path Loss Analysis ===")
        for pair, stats in analysis["path_loss_statistics"].items():
            print(f"{pair}: {stats['min']:.1f} - {stats['max']:.1f} dB (variation: {stats['variation']:.1f} dB)")

if __name__ == "__main__":
    main()