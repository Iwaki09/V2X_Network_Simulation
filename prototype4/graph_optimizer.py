"""
グラフ最適化モジュール

NetworkXを使用して車両通信グラフを構築し、最適経路を計算
"""

import networkx as nx
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PathInfo:
    """経路情報"""
    source: str
    target: str
    path: List[str]
    total_cost: float
    hop_count: int
    min_link_quality: float  # 経路上の最悪リンク品質


class GraphOptimizer:
    """車両通信グラフの最適化"""

    def __init__(self):
        """初期化"""
        self.graph = nx.Graph()

    def build_graph(
        self,
        vehicle_positions: Dict[str, np.ndarray],
        channel_matrix: np.ndarray,
        vehicle_ids_map: Dict[int, str],
        snr_threshold_db: float = 5.0
    ):
        """
        車両通信グラフを構築

        Args:
            vehicle_positions: 車両位置 {veh_id: np.array([x, y])}
            channel_matrix: チャネル行列 (SNR値)
            vehicle_ids_map: インデックスから車両IDへのマッピング
            snr_threshold_db: SNR閾値 (dB)
        """
        # グラフをクリア
        self.graph.clear()

        # ノード（車両）を追加
        for veh_id, pos in vehicle_positions.items():
            self.graph.add_node(veh_id, pos=pos)

        # エッジ（通信リンク）を追加
        n_vehicles = len(vehicle_ids_map)
        for i in range(n_vehicles):
            for j in range(i + 1, n_vehicles):  # 無向グラフなので上三角のみ
                veh_i = vehicle_ids_map[i]
                veh_j = vehicle_ids_map[j]

                snr = channel_matrix[i, j]

                # SNRが閾値以上の場合のみエッジを追加
                if snr > snr_threshold_db and not np.isinf(snr):
                    # 距離を計算
                    distance = np.linalg.norm(
                        vehicle_positions[veh_i] - vehicle_positions[veh_j]
                    )

                    # エッジの重み: 距離またはSNRの逆数
                    # ここでは「最高品質経路」を求めるため、SNRの逆数を重みとする
                    # （小さい重み = 高品質）
                    weight = 1.0 / snr if snr > 0 else np.inf

                    self.graph.add_edge(
                        veh_i, veh_j,
                        weight=weight,
                        distance=distance,
                        snr=snr
                    )

    def find_shortest_path(
        self,
        source: str,
        target: str,
        weight_type: str = 'weight'
    ) -> Optional[PathInfo]:
        """
        最短経路を計算

        Args:
            source: 始点車両ID
            target: 終点車両ID
            weight_type: 重みの種類 ('weight', 'distance')

        Returns:
            PathInfo または None（経路が存在しない場合）
        """
        if source not in self.graph or target not in self.graph:
            return None

        try:
            # Dijkstraアルゴリズムで最短経路を計算
            path = nx.shortest_path(
                self.graph,
                source=source,
                target=target,
                weight=weight_type
            )

            # 経路のコストを計算
            total_cost = sum(
                self.graph[path[i]][path[i + 1]][weight_type]
                for i in range(len(path) - 1)
            )

            # 経路上の最悪リンク品質を計算
            min_snr = min(
                self.graph[path[i]][path[i + 1]]['snr']
                for i in range(len(path) - 1)
            )

            return PathInfo(
                source=source,
                target=target,
                path=path,
                total_cost=total_cost,
                hop_count=len(path) - 1,
                min_link_quality=min_snr
            )

        except nx.NetworkXNoPath:
            # 経路が存在しない
            return None

    def find_all_shortest_paths(
        self,
        weight_type: str = 'weight'
    ) -> Dict[Tuple[str, str], PathInfo]:
        """
        すべての車両ペア間の最短経路を計算

        Args:
            weight_type: 重みの種類 ('weight', 'distance')

        Returns:
            {(source, target): PathInfo} の辞書
        """
        all_paths = {}
        nodes = list(self.graph.nodes())

        for i, source in enumerate(nodes):
            for target in nodes[i + 1:]:
                path_info = self.find_shortest_path(source, target, weight_type)
                if path_info:
                    all_paths[(source, target)] = path_info

        return all_paths

    def calculate_graph_metrics(self) -> Dict[str, float]:
        """
        グラフの統計指標を計算

        Returns:
            統計指標の辞書
        """
        if len(self.graph) == 0:
            return {}

        metrics = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'is_connected': nx.is_connected(self.graph),
        }

        # 連結な場合のみ計算可能な指標
        if metrics['is_connected']:
            metrics['average_shortest_path_length'] = nx.average_shortest_path_length(
                self.graph, weight='weight'
            )
            metrics['diameter'] = nx.diameter(self.graph)

        # 平均次数
        degrees = [deg for node, deg in self.graph.degree()]
        metrics['average_degree'] = np.mean(degrees) if degrees else 0

        return metrics

    def get_connected_components(self) -> List[List[str]]:
        """
        連結成分を取得

        Returns:
            連結成分のリスト
        """
        return [list(c) for c in nx.connected_components(self.graph)]

    def visualize_graph_structure(self) -> str:
        """
        グラフ構造を文字列で表現

        Returns:
            グラフ構造の文字列表現
        """
        lines = []
        lines.append(f"Graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        lines.append("\nEdges:")

        for u, v, data in self.graph.edges(data=True):
            lines.append(
                f"  {u} <-> {v}: distance={data['distance']:.1f}m, "
                f"SNR={data['snr']:.2f}dB, weight={data['weight']:.4f}"
            )

        return "\n".join(lines)


if __name__ == "__main__":
    # テストコード
    print("Graph Optimizer Test")
    print("=" * 60)

    # テスト用の車両位置
    test_positions = {
        'veh0': np.array([0.0, 0.0]),
        'veh1': np.array([50.0, 0.0]),
        'veh2': np.array([100.0, 0.0]),
        'veh3': np.array([150.0, 0.0]),
        'veh4': np.array([200.0, 0.0]),
    }

    # テスト用のチャネル行列 (SNR値)
    # 実際にはchannel_modelから計算されるが、ここでは簡略化
    test_channel_matrix = np.array([
        [np.inf, 30.0, 20.0, 10.0, 3.0],
        [30.0, np.inf, 30.0, 20.0, 10.0],
        [20.0, 30.0, np.inf, 30.0, 20.0],
        [10.0, 20.0, 30.0, np.inf, 30.0],
        [3.0, 10.0, 20.0, 30.0, np.inf]
    ])

    test_veh_map = {i: f'veh{i}' for i in range(5)}

    # グラフ最適化
    optimizer = GraphOptimizer()
    optimizer.build_graph(test_positions, test_channel_matrix, test_veh_map, snr_threshold_db=5.0)

    # グラフ構造を表示
    print(optimizer.visualize_graph_structure())

    # グラフ指標を計算
    print("\nGraph Metrics:")
    metrics = optimizer.calculate_graph_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    # 最短経路を計算
    print("\nShortest Paths (by quality - minimum weight):")
    path_info = optimizer.find_shortest_path('veh0', 'veh4', weight_type='weight')
    if path_info:
        print(f"  {path_info.source} -> {path_info.target}")
        print(f"  Path: {' -> '.join(path_info.path)}")
        print(f"  Hops: {path_info.hop_count}")
        print(f"  Total cost: {path_info.total_cost:.4f}")
        print(f"  Min link quality (SNR): {path_info.min_link_quality:.2f} dB")

    # 距離ベースの最短経路
    print("\nShortest Paths (by distance):")
    path_info_dist = optimizer.find_shortest_path('veh0', 'veh4', weight_type='distance')
    if path_info_dist:
        print(f"  {path_info_dist.source} -> {path_info_dist.target}")
        print(f"  Path: {' -> '.join(path_info_dist.path)}")
        print(f"  Hops: {path_info_dist.hop_count}")
        print(f"  Total distance: {path_info_dist.total_cost:.1f} m")

    print("\n" + "=" * 60)
