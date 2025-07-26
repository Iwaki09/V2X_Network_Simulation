
import json
import os
import glob

def prepare_visualization_data(
    simulation_results_path,
    scenario_dir,
    base_scene_path,
    output_data_path,
):
    """
    シミュレーション結果とシーン情報から可視化用のデータを準備する。

    Args:
        simulation_results_path (str): simulation_results.json のパス
        scenario_dir (str): scene_t*.json が格納されているディレクトリのパス
        base_scene_path (str): ベースとなる scene.json のパス
        output_data_path (str): 可視化データを保存するJSONファイルのパス
    """
    all_visualization_data = []

    # シミュレーション結果を読み込む
    with open(simulation_results_path, 'r') as f:
        simulation_results = json.load(f)

    # ベースシーンを読み込む (建物、基地局の静的情報用)
    with open(base_scene_path, 'r') as f:
        base_scene = json.load(f)

    # 各タイムステップのシーンファイルを読み込み、データを統合
    scene_files = sorted(glob.glob(os.path.join(scenario_dir, 'scene_t*.json')))

    for i, sim_result in enumerate(simulation_results):
        timestamp = sim_result['timestamp']
        path_loss_matrix = sim_result['path_loss_matrix']

        # 対応するシーンファイルを読み込む
        # timestamp (e.g., "scene_t0.json") からインデックスを抽出
        try:
            time_index = int(timestamp.replace("scene_t", "").replace(".json", ""))
            current_scene_path = scene_files[time_index]
        except (ValueError, IndexError):
            print(f"Warning: Could not find scene file for timestamp {timestamp}. Skipping.")
            continue

        with open(current_scene_path, 'r') as f:
            current_scene = json.load(f)

        # 可視化データ構造の構築
        step_data = {
            "time": time_index, # タイムステップのインデックス
            "world_size": current_scene.get('world_size', [200, 200]),
            "vehicles": [],
            "base_stations": [],
            "buildings": [],
            "path_losses": [], # 車両-基地局間のパスロス
        }

        # 車両情報
        for vehicle in current_scene.get('vehicles', []):
            step_data['vehicles'].append({
                "id": vehicle['id'],
                "position": vehicle['position'][:2], # x, y 座標のみ
            })

        # 基地局情報
        for bs in current_scene.get('base_stations', []):
            step_data['base_stations'].append({
                "id": bs['id'],
                "position": bs['position'][:2], # x, y 座標のみ
            })
        
        # 建物情報 (ベースシーンから取得、静的なので各ステップで同じ)
        for building in base_scene.get('buildings', []):
            step_data['buildings'].append({
                "id": building['id'],
                "position": building['position'][:2], # x, y 座標のみ
                "size": building['size'], # width, height, height 全て含める
            })

        # パスロス情報 (車両IDと基地局IDを紐付けて保存)
        vehicle_ids = [v['id'] for v in current_scene.get('vehicles', [])]
        base_station_ids = [bs['id'] for bs in current_scene.get('base_stations', [])]

        for r_idx, vehicle_id in enumerate(vehicle_ids):
            for c_idx, bs_id in enumerate(base_station_ids):
                if r_idx < len(path_loss_matrix) and c_idx < len(path_loss_matrix[r_idx]):
                    step_data['path_losses'].append({
                        "source": vehicle_id,
                        "target": bs_id,
                        "value": path_loss_matrix[r_idx][c_idx],
                    })

        all_visualization_data.append(step_data)

    # 可視化データをJSONファイルに保存
    os.makedirs(os.path.dirname(output_data_path), exist_ok=True)
    with open(output_data_path, 'w') as f:
        json.dump(all_visualization_data, f, indent=4)

    print(f"Visualization data prepared and saved to: {output_data_path}")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir) # prototype2 ディレクトリ

    sim_results_path = os.path.join(base_dir, 'output', 'simulation_results.json')
    scenario_dir = os.path.join(base_dir, 'output', 'scenario1')
    base_scene_path = os.path.join(base_dir, 'scene.json')
    output_data_path = os.path.join(script_dir, 'data.json')

    prepare_visualization_data(sim_results_path, scenario_dir, base_scene_path, output_data_path)
