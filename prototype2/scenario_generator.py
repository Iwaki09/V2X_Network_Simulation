
import json
import os

def generate_scenario(base_scene_path, output_dir, num_steps=10, vehicle_id="tx1", step_size=2.0):
    """
    車両を直線移動させるシナリオを生成し、各ステップのシーンファイルをJSON形式で出力する。

    Args:
        base_scene_path (str): ベースとなるシーンファイルのパス
        output_dir (str): 出力先ディレクトリのパス
        num_steps (int): 生成するタイムステップ数
        vehicle_id (str): 移動させる車両のID
        step_size (float): 各ステップでの移動距離
    """
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)

    # ベースとなるシーンファイルを読み込む
    with open(base_scene_path, 'r') as f:
        base_scene = json.load(f)

    for i in range(num_steps):
        current_scene = base_scene.copy()
        
        # 車両をIDで検索して位置を更新
        vehicle_found = False
        if 'vehicles' in current_scene:
            for vehicle in current_scene['vehicles']:
                if vehicle['id'] == vehicle_id:
                    # X軸方向に移動させる
                    vehicle['position'][0] += i * step_size
                    vehicle_found = True
                    break
        
        if not vehicle_found:
            print(f"Warning: Vehicle with ID '{vehicle_id}' not found in the scene.")
            return

        # 新しいシーンファイルを出力
        output_path = os.path.join(output_dir, f"scene_t{i}.json")
        with open(output_path, 'w') as f:
            json.dump(current_scene, f, indent=4)
        
        print(f"Generated: {output_path}")

if __name__ == '__main__':
    # ベースとなるシーンファイルのパス (prototype2/scene.json)
    base_scene_file = os.path.join(os.path.dirname(__file__), 'scene.json')
    
    # 出力ディレクトリ
    output_directory = os.path.join(os.path.dirname(__file__), 'output/scenario1')

    generate_scenario(base_scene_file, output_directory, num_steps=10, vehicle_id="vehicle1", step_size=5.0)
