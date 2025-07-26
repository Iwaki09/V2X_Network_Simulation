import os
import glob
import json

from src.scene_parser import load_scene
from src.mitsuba_converter import scene_to_mitsuba_xml
from src.run_raytracing import run_raytracing
from src.graph_builder import build_graphs_from_simulation_results # 追加

def main():
    """
    V2Xネットワークシミュレーションを実行するメイン関数。
    """
    # このスクリプトを含むディレクトリの絶対パスを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # シナリオファイルのパスを取得
    scenario_dir = os.path.join(script_dir, 'output/scenario1')
    scene_files = sorted(glob.glob(os.path.join(scenario_dir, 'scene_t*.json')))

    all_results = []

    for scene_file in scene_files:
        print(f"Processing: {scene_file}")
        
        # 1. JSONファイルからシーンを読み込む
        scene = load_scene(scene_file)
        
        # 2. シーンをMitsuba XMLファイルに変換
        mitsuba_xml_path = os.path.join(scenario_dir, 'generated_scene.xml')
        mitsuba_xml_content = scene_to_mitsuba_xml(scene)
        with open(mitsuba_xml_path, 'w', encoding='utf-8') as f:
            f.write(mitsuba_xml_content)
            
        # 3. レイトレーシングシミュレーションを実行
        path_loss_matrix = run_raytracing(scene, mitsuba_xml_path)
        
        # 4. 結果を保存
        if path_loss_matrix is not None:
            all_results.append({
                "timestamp": os.path.basename(scene_file),
                "path_loss_matrix": path_loss_matrix.tolist()
            })

    # 5. 結果をJSONファイルに出力
    output_path = os.path.join(script_dir, 'output/simulation_results.json')
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=4)
    
    print(f"\nSimulation finished. Results saved to: {output_path}")

    # 6. シミュレーション結果からグラフを構築 (追加)
    base_scene_path = os.path.join(script_dir, 'scene.json')
    output_graph_dir = os.path.join(script_dir, 'output')
    build_graphs_from_simulation_results(output_path, base_scene_path, output_graph_dir)


if __name__ == '__main__':
    main()