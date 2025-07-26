
import json
import networkx as nx
import os

def build_graphs_from_simulation_results(simulation_results_path, scene_path, output_dir):
    """
    シミュレーション結果とシーン情報からグラフを構築し、JSON形式で保存する。

    Args:
        simulation_results_path (str): simulation_results.json のパス
        scene_path (str): ベースとなる scene.json のパス
        output_dir (str): グラフデータを保存するディレクトリ
    """
    os.makedirs(output_dir, exist_ok=True)

    with open(simulation_results_path, 'r') as f:
        simulation_results = json.load(f)

    with open(scene_path, 'r') as f:
        base_scene = json.load(f)

    all_graphs_data = []

    # シーンから車両と基地局のIDを取得
    vehicle_ids = [v['id'] for v in base_scene.get('vehicles', [])]
    base_station_ids = [bs['id'] for bs in base_scene.get('base_stations', [])]

    for result in simulation_results:
        timestamp = result['timestamp']
        path_loss_matrix = result['path_loss_matrix']

        G = nx.Graph()

        # ノードの追加
        for vid in vehicle_ids:
            G.add_node(vid, type='vehicle')
        for bsid in base_station_ids:
            G.add_node(bsid, type='base_station')

        # エッジの追加 (車両 -> 基地局)
        # path_loss_matrix の行が車両、列が基地局に対応すると仮定
        for i, vehicle_id in enumerate(vehicle_ids):
            for j, bs_id in enumerate(base_station_ids):
                # パスロス値が有効な場合のみエッジを追加
                if i < len(path_loss_matrix) and j < len(path_loss_matrix[i]):
                    path_loss = path_loss_matrix[i][j]
                    G.add_edge(vehicle_id, bs_id, weight=path_loss)

        # グラフデータを辞書形式で保存
        graph_data = {
            "timestamp": timestamp,
            "nodes": [{"id": node, "type": G.nodes[node]['type']} for node in G.nodes()],
            "edges": [{"source": u, "target": v, "weight": G.edges[u,v]['weight']} for u, v in G.edges()]
        }
        all_graphs_data.append(graph_data)

    output_file_path = os.path.join(output_dir, 'graph_data.json')
    with open(output_file_path, 'w') as f:
        json.dump(all_graphs_data, f, indent=4)
    
    print(f"Graphs saved to: {output_file_path}")

if __name__ == '__main__':
    # テスト用のパス (必要に応じて調整)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir) # prototype2 ディレクトリ
    
    sim_results_path = os.path.join(base_dir, 'output', 'simulation_results.json')
    base_scene_path = os.path.join(base_dir, 'scene.json')
    output_graph_dir = os.path.join(base_dir, 'output')

    build_graphs_from_simulation_results(sim_results_path, base_scene_path, output_graph_dir)
