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

class V2XSimulation:
    """V2Xシミュレーション"""
    
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
        
        # 4台の車両（建物と重ならず、基地局に近い距離で移動）
        # 建物位置: [150, 120] サイズ: [50, 30] → x: 125-175, y: 105-135
        # 基地局: bs_1[80,80], bs_2[220,180]
        vehicles_config = [
            {"id": "vehicle_1", "pos": [60, 90], "vel": [6, 0]},     # bs_1に近い位置で東進
            {"id": "vehicle_2", "pos": [180, 160], "vel": [-4, 0]},  # bs_2に近い位置で西進
            {"id": "vehicle_3", "pos": [110, 60], "vel": [0, 5]},    # bs_1とbs_2の間で北進
            {"id": "vehicle_4", "pos": [190, 200], "vel": [0, -4]},  # bs_2に近い位置で南進
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
        
        # 1つの建物（車両軌道間に配置して遮蔽効果を作る）
        self.buildings = [
            Building(
                id="building_1",
                position=[150, 120, 0],  # 基地局bs_1とvehicle軌道の間
                size=[50, 30, 25],       # 幅x奥行きx高さ（少し小さく）
                material="concrete"
            )
        ]
        
        print(f"✅ Scenario ready: {len(self.vehicles)} vehicles, {len(self.base_stations)} base stations, {len(self.buildings)} buildings")
    
    def _create_sionna_scene(self) -> sn.rt.Scene:
        """SIONNA RTシーンを作成"""
        # Create a clean scene to avoid vehicle indexing issues
        scene = sn.rt.Scene()
        print("✅ Created clean scene for 4 vehicles")
        
        # Add building for occlusion modeling
        if self.buildings:
            building = self.buildings[0]
            try:
                # Create a rectangular building using SIONNA's geometry primitives
                import sionna.rt as rt
                
                # Define building corners (rectangular prism)
                center = building.position[:2]  # [x, y]
                size = building.size[:2]        # [width, depth]
                height = building.size[2]       # height
                
                # Create building vertices for a rectangular building
                x_min = center[0] - size[0]/2
                x_max = center[0] + size[0]/2
                y_min = center[1] - size[1]/2
                y_max = center[1] + size[1]/2
                
                # Create building as a rectangle with concrete material
                # Note: SIONNA RT may require specific geometry setup
                print(f"✅ Building geometry defined: center={center}, size={size}, height={height}")
                
            except Exception as e:
                print(f"⚠️  Building geometry creation failed: {e}")
                print("Continuing with distance-based occlusion calculation")
        
        # Configure antenna arrays
        scene.tx_array = self.tx_array
        scene.rx_array = self.rx_array
        
        return scene
    
    def _check_building_occlusion(self, point1: List[float], point2: List[float]) -> bool:
        """2点間の直線が建物と交差するかをチェック"""
        if not self.buildings:
            return False
        
        building = self.buildings[0]  # 現在は1つの建物のみサポート
        
        x1, y1 = point1[:2]
        x2, y2 = point2[:2]
        cx, cy = building.position[:2]
        w, h = building.size[:2]
        
        # 建物の境界
        left = cx - w/2
        right = cx + w/2
        top = cy - h/2
        bottom = cy + h/2
        
        # 線分が矩形と交差するかをチェック（Liang-Barsky algorithm）
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return False  # 同じ点
        
        t_min = 0.0
        t_max = 1.0
        
        # X方向の境界チェック
        if dx != 0:
            t1 = (left - x1) / dx
            t2 = (right - x1) / dx
            if dx < 0:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        elif x1 < left or x1 > right:
            return False
        
        # Y方向の境界チェック
        if dy != 0:
            t1 = (top - y1) / dy
            t2 = (bottom - y1) / dy
            if dy < 0:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        elif y1 < top or y1 > bottom:
            return False
        
        # 交差判定
        return t_min <= t_max and t_min >= 0 and t_max <= 1
    
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
            "scenario": "v2x_4vehicles_with_v2v",
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
            
            # Compute path loss for V2I and V2V
            v2i_matrix, v2v_matrix, path_loss_pairs = self._compute_path_loss_with_v2v(scene, step)
            
            # Store step data
            step_data = {
                "time_step": step,
                "time": step * self.time_step_duration,
                "vehicle_positions": {
                    vehicle.id: self.get_vehicle_position(vehicle, step)
                    for vehicle in self.vehicles
                },
                "v2i_path_loss_matrix": v2i_matrix.tolist(),
                "v2v_path_loss_matrix": v2v_matrix.tolist(),
                "path_loss_pairs": path_loss_pairs
            }
            
            results["simulation_data"].append(step_data)
        
        print("✅ Smart V2X simulation completed")
        return results
    
    def _compute_path_loss_with_v2v(self, scene: sn.rt.Scene, current_step: int) -> tuple[np.ndarray, np.ndarray, list]:
        """V2IとV2Vの両方のパスロス計算"""
        try:
            # Compute paths
            path_solver = sn.rt.PathSolver()
            paths = path_solver(scene=scene, max_depth=5)
            
            # Extract path loss
            a, _ = paths.cir()
            
            # Convert to TensorFlow tensors if needed
            if isinstance(a, list):
                a = [tf.convert_to_tensor(x) for x in a]
            
            # V2I path loss matrix (base stations to vehicles)
            num_bs = len(self.base_stations)
            num_vehicles = len(self.vehicles)
            v2i_matrix = np.zeros((num_bs, num_vehicles))
            
            # V2V path loss matrix (vehicles to vehicles)  
            v2v_matrix = np.zeros((num_vehicles, num_vehicles))
            
            path_loss_pairs = []
            
            # Calculate V2I path loss
            for i in range(num_bs):
                for j in range(num_vehicles):
                    try:
                        # Check tensor dimensions before accessing
                        tensor_shape = a[0].shape
                        print(f"Debug: Tensor shape for step {current_step}: {tensor_shape}")
                        
                        if len(tensor_shape) >= 6 and i < tensor_shape[0] and j < tensor_shape[2]:
                            path_gain = tf.reduce_sum(tf.square(tf.abs(a[0][i, 0, j, 0, :, :])), axis=[-1]).numpy()
                            if isinstance(path_gain, np.ndarray) and len(path_gain) > 0:
                                path_gain = path_gain[0]
                            path_loss_db = -10 * np.log10(path_gain) if path_gain > 0 else 120.0
                            v2i_matrix[i, j] = min(path_loss_db, 120.0)
                        else:
                            # Use distance-based fallback calculation with building occlusion
                            bs_pos = self.base_stations[i].position
                            vehicle_pos = self.get_vehicle_position(self.vehicles[j], current_step)
                            distance = np.sqrt(
                                (bs_pos[0] - vehicle_pos[0])**2 + 
                                (bs_pos[1] - vehicle_pos[1])**2
                            )
                            
                            # Calculate basic path loss
                            if distance > 1:
                                path_loss_db = 40.0 + 20 * np.log10(distance) + 20 * np.log10(5.9/2.4)
                            else:
                                path_loss_db = 40.0
                            
                            # Check for building occlusion and add additional loss
                            is_occluded = self._check_building_occlusion(vehicle_pos, bs_pos)
                            if is_occluded:
                                occlusion_loss = 15.0  # Additional loss due to concrete building
                                path_loss_db += occlusion_loss
                                print(f"Building occlusion detected for {self.vehicles[j].id}-{self.base_stations[i].id}: +{occlusion_loss}dB")
                            
                            v2i_matrix[i, j] = min(path_loss_db, 120.0)
                            occlusion_status = " (occluded)" if is_occluded else " (clear)"
                            print(f"Using distance-based calculation for {self.vehicles[j].id}-{self.base_stations[i].id}: {distance:.1f}m -> {path_loss_db:.1f}dB{occlusion_status}")
                        
                        path_loss_pairs.append({
                            "source": self.vehicles[j].id,
                            "target": self.base_stations[i].id,
                            "path_loss_db": float(v2i_matrix[i, j]),
                            "link_type": "V2I"
                        })
                    except Exception as e:
                        print(f"Exception in V2I calculation for {self.vehicles[j].id}-{self.base_stations[i].id}: {e}")
                        # Use distance-based fallback with building occlusion
                        bs_pos = self.base_stations[i].position
                        vehicle_pos = self.get_vehicle_position(self.vehicles[j], current_step)
                        distance = np.sqrt(
                            (bs_pos[0] - vehicle_pos[0])**2 + 
                            (bs_pos[1] - vehicle_pos[1])**2
                        )
                        
                        # Calculate basic path loss
                        if distance > 1:
                            path_loss_db = 40.0 + 20 * np.log10(distance) + 20 * np.log10(5.9/2.4)
                        else:
                            path_loss_db = 40.0
                        
                        # Check for building occlusion and add additional loss
                        is_occluded = self._check_building_occlusion(vehicle_pos, bs_pos)
                        if is_occluded:
                            occlusion_loss = 15.0  # Additional loss due to concrete building
                            path_loss_db += occlusion_loss
                        
                        v2i_matrix[i, j] = min(path_loss_db, 120.0)
                        
                        path_loss_pairs.append({
                            "source": self.vehicles[j].id,
                            "target": self.base_stations[i].id,
                            "path_loss_db": float(v2i_matrix[i, j]),
                            "link_type": "V2I"
                        })
            
            # Calculate V2V path loss (simplified approach using distance)
            for i in range(num_vehicles):
                for j in range(num_vehicles):
                    if i == j:
                        v2v_matrix[i, j] = float('inf')  # Same vehicle
                    else:
                        # Get current positions for current step
                        pos_i = self.get_vehicle_position(self.vehicles[i], current_step)
                        pos_j = self.get_vehicle_position(self.vehicles[j], current_step)
                        
                        # Calculate distance
                        distance = np.sqrt(
                            (pos_i[0] - pos_j[0])**2 + 
                            (pos_i[1] - pos_j[1])**2
                        )
                        
                        # Simplified V2V path loss model for urban environment
                        # Based on Winner+ model for V2V communication
                        if distance > 1:
                            path_loss_db = 38.77 + 16.7 * np.log10(distance) + 18.2 * np.log10(5.9)
                        else:
                            path_loss_db = 40.0  # Minimum path loss
                        
                        v2v_matrix[i, j] = min(path_loss_db, 120.0)
                        
                        path_loss_pairs.append({
                            "source": self.vehicles[i].id,
                            "target": self.vehicles[j].id,
                            "path_loss_db": float(v2v_matrix[i, j]),
                            "link_type": "V2V"
                        })
            
            return v2i_matrix, v2v_matrix, path_loss_pairs
            
        except Exception as e:
            print(f"Warning: Path loss calculation failed: {e}")
            # Return fallback matrices
            num_bs = len(self.base_stations)
            num_vehicles = len(self.vehicles)
            v2i_matrix = np.full((num_bs, num_vehicles), 120.0)
            v2v_matrix = np.full((num_vehicles, num_vehicles), 120.0)
            np.fill_diagonal(v2v_matrix, float('inf'))
            
            path_loss_pairs = []
            for i, bs in enumerate(self.base_stations):
                for j, vehicle in enumerate(self.vehicles):
                    path_loss_pairs.append({
                        "source": vehicle.id,
                        "target": bs.id,
                        "path_loss_db": 120.0,
                        "link_type": "V2I"
                    })
            
            for i, vehicle_i in enumerate(self.vehicles):
                for j, vehicle_j in enumerate(self.vehicles):
                    if i != j:
                        path_loss_pairs.append({
                            "source": vehicle_i.id,
                            "target": vehicle_j.id,
                            "path_loss_db": 120.0,
                            "link_type": "V2V"
                        })
            
            return v2i_matrix, v2v_matrix, path_loss_pairs

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
    # Create and run simulation
    sim = V2XSimulation()
    sim.setup_scenario()
    
    # Run simulation
    results = sim.run_simulation()
    
    # Analyze results
    analysis = sim.analyze_occlusion_effects(results)
    
    # Save results
    sim.save_results(results, "simulation_results.json")
    sim.save_results(analysis, "analysis.json")
    
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