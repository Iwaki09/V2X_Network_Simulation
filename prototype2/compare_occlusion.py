#!/usr/bin/env python3
"""
Compare theoretical occlusion with actual simulation results
"""
import json
import numpy as np

def load_simulation_results():
    """シミュレーション結果を読み込み"""
    with open('output/simulation_results.json', 'r') as f:
        return json.load(f)

def analyze_path_loss_consistency():
    """パスロス値の一貫性を分析"""
    results = load_simulation_results()
    
    print("=== Path Loss Consistency Analysis ===")
    print()
    
    # 理論上の遮蔽状況
    expected_occlusions = {
        # (vehicle, base_station): [time_steps_with_occlusion]
        ("vehicle_1", "bs_2"): [0, 5, 10, 15],  # 長距離で建物通過
        ("vehicle_2", "bs_1"): [0, 5],          # 初期時間で建物通過
        ("vehicle_3", "bs_2"): [0, 5, 10],      # 建物通過
        ("vehicle_4", "bs_1"): [0, 5, 10, 15],  # 長距離で建物通過
    }
    
    # 実際のパスロス値を抽出
    actual_path_losses = {}
    
    for step_data in results["simulation_data"]:
        time_step = step_data["time_step"]
        
        for pair in step_data["path_loss_pairs"]:
            if pair["link_type"] == "V2I":  # V2I通信のみ分析
                key = (pair["source"], pair["target"])
                if key not in actual_path_losses:
                    actual_path_losses[key] = []
                actual_path_losses[key].append({
                    "time_step": time_step,
                    "path_loss": pair["path_loss_db"]
                })
    
    # 遮蔽の期待される効果を分析
    print("Expected vs Actual Path Loss Analysis:")
    print("=" * 60)
    
    for pair_key, expected_occlusion_steps in expected_occlusions.items():
        if pair_key in actual_path_losses:
            path_loss_data = actual_path_losses[pair_key]
            
            print(f"\n{pair_key[0]} -> {pair_key[1]}:")
            print(f"Expected occlusion at steps: {expected_occlusion_steps}")
            
            # 遮蔽時と非遮蔽時のパスロス値を分類
            occluded_losses = []
            clear_losses = []
            
            for data in path_loss_data:
                if data["time_step"] in expected_occlusion_steps:
                    occluded_losses.append(data["path_loss"])
                else:
                    clear_losses.append(data["path_loss"])
            
            if occluded_losses and clear_losses:
                avg_occluded = np.mean(occluded_losses)
                avg_clear = np.mean(clear_losses)
                difference = avg_occluded - avg_clear
                
                print(f"  Clear path loss:    {avg_clear:.1f} dB (n={len(clear_losses)})")
                print(f"  Occluded path loss: {avg_occluded:.1f} dB (n={len(occluded_losses)})")
                print(f"  Difference:         {difference:.1f} dB")
                
                if abs(difference) < 5:
                    print(f"  ⚠️  WARNING: Difference too small! Building occlusion may not be working.")
                elif difference > 0:
                    print(f"  ✅ Occlusion effect detected (higher path loss when occluded)")
                else:
                    print(f"  ❓ Unexpected: lower path loss when occluded")
            else:
                print(f"  ⚠️  Insufficient data for comparison")
            
            # 詳細なステップ別表示
            print(f"  Step-by-step breakdown:")
            for data in sorted(path_loss_data, key=lambda x: x["time_step"]):
                status = "🚫 Occluded" if data["time_step"] in expected_occlusion_steps else "✅ Clear"
                print(f"    Step {data['time_step']:2d}: {data['path_loss']:5.1f} dB {status}")
    
    return actual_path_losses

def compare_distance_vs_occlusion():
    """距離とパスロスの関係を分析（遮蔽効果を考慮）"""
    results = load_simulation_results()
    
    print("\n" + "=" * 60)
    print("Distance vs Path Loss Analysis")
    print("=" * 60)
    
    # 車両配置から距離を計算
    vehicles_config = [
        {"id": "vehicle_1", "pos": [60, 90], "vel": [6, 0]},
        {"id": "vehicle_2", "pos": [180, 160], "vel": [-4, 0]},
        {"id": "vehicle_3", "pos": [110, 60], "vel": [0, 5]},
        {"id": "vehicle_4", "pos": [190, 200], "vel": [0, -4]},
    ]
    
    base_stations = [
        {"id": "bs_1", "pos": [80, 80]},
        {"id": "bs_2", "pos": [220, 180]}
    ]
    
    for step_idx, step_data in enumerate(results["simulation_data"][:5]):  # 最初の5ステップ
        print(f"\nTime Step {step_idx}:")
        
        # 車両位置を計算
        vehicle_positions = {}
        for v_config in vehicles_config:
            time = step_idx * 1.0
            x = v_config["pos"][0] + v_config["vel"][0] * time
            y = v_config["pos"][1] + v_config["vel"][1] * time
            x = max(10, min(290, x))
            y = max(10, min(290, y))
            vehicle_positions[v_config["id"]] = [x, y]
        
        # V2Iペアの距離とパスロスを比較
        for pair in step_data["path_loss_pairs"]:
            if pair["link_type"] == "V2I":
                vehicle_id = pair["source"]
                bs_id = pair["target"]
                
                # 距離を計算
                v_pos = vehicle_positions[vehicle_id]
                bs_pos = next(bs["pos"] for bs in base_stations if bs["id"] == bs_id)
                distance = np.sqrt((v_pos[0] - bs_pos[0])**2 + (v_pos[1] - bs_pos[1])**2)
                
                # 理論的なフリースペースパスロス
                theoretical_pl = 40.0 + 20 * np.log10(distance) + 20 * np.log10(5.9/2.4)
                actual_pl = pair["path_loss_db"]
                difference = actual_pl - theoretical_pl
                
                print(f"  {vehicle_id} -> {bs_id}: {distance:5.1f}m, theoretical: {theoretical_pl:5.1f}dB, actual: {actual_pl:5.1f}dB, diff: {difference:+5.1f}dB")

if __name__ == "__main__":
    actual_losses = analyze_path_loss_consistency()
    compare_distance_vs_occlusion()