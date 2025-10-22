"""
可視化モジュール

matplotlibを使用して車両位置、通信リンク、最適経路を可視化
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation
import networkx as nx
import numpy as np
from typing import Dict, List, Optional
from graph_optimizer import PathInfo


class Visualizer:
    """シミュレーション結果の可視化"""

    def __init__(self, figsize=(14, 6)):
        """
        初期化

        Args:
            figsize: 図のサイズ
        """
        self.figsize = figsize

    def plot_snapshot(
        self,
        vehicle_positions: Dict[str, np.ndarray],
        graph: nx.Graph,
        optimal_path: Optional[PathInfo] = None,
        time: float = 0.0,
        save_path: Optional[str] = None
    ):
        """
        特定時刻のスナップショットを可視化

        Args:
            vehicle_positions: 車両位置
            graph: 通信グラフ
            optimal_path: 最適経路情報（オプション）
            time: 現在時刻
            save_path: 保存先パス（指定しない場合は表示のみ）
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=self.figsize)

        # 左: 車両位置と通信リンク
        self._plot_vehicles_and_links(ax1, vehicle_positions, graph, optimal_path, time)

        # 右: グラフ構造
        self._plot_graph_structure(ax2, graph, optimal_path)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved snapshot to {save_path}")
        else:
            plt.show()

        plt.close()

    def _plot_vehicles_and_links(
        self,
        ax,
        vehicle_positions: Dict[str, np.ndarray],
        graph: nx.Graph,
        optimal_path: Optional[PathInfo],
        time: float
    ):
        """車両位置と通信リンクをプロット"""
        ax.set_title(f'Vehicle Positions and Communication Links (t={int(time)}s)', fontsize=12)
        ax.set_xlabel('X Position (m)')
        ax.set_ylabel('Y Position (m)')
        ax.grid(True, alpha=0.3)

        # 通信リンクを描画
        for u, v, data in graph.edges(data=True):
            pos_u = vehicle_positions[u]
            pos_v = vehicle_positions[v]
            snr = data['snr']

            # SNRに応じて色と太さを変更
            if snr > 25:
                color = 'green'
                linewidth = 2
                alpha = 0.8
            elif snr > 15:
                color = 'orange'
                linewidth = 1.5
                alpha = 0.6
            else:
                color = 'red'
                linewidth = 1
                alpha = 0.4

            ax.plot([pos_u[0], pos_v[0]], [pos_u[1], pos_v[1]],
                   color=color, linewidth=linewidth, alpha=alpha, zorder=1)

        # 最適経路をハイライト（コメントアウト - 青線を非表示）
        # if optimal_path:
        #     path = optimal_path.path
        #     for i in range(len(path) - 1):
        #         pos_u = vehicle_positions[path[i]]
        #         pos_v = vehicle_positions[path[i + 1]]
        #         ax.plot([pos_u[0], pos_v[0]], [pos_u[1], pos_v[1]],
        #                color='blue', linewidth=3, alpha=0.9, zorder=2,
        #                label='Optimal Path' if i == 0 else '')

        # 車両を描画（すべて黄色の丸で統一）
        for veh_id, pos in vehicle_positions.items():
            ax.scatter(pos[0], pos[1], s=150, c='yellow', marker='o',
                      edgecolors='black', linewidths=1.5, zorder=3)

            # 車両IDをラベル表示
            ax.text(pos[0], pos[1] + 5, veh_id, fontsize=9, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))

        # 凡例
        legend_elements = [
            mpatches.Patch(color='green', label='High Quality (SNR>25dB)'),
            mpatches.Patch(color='orange', label='Medium Quality (15<SNR<25dB)'),
            mpatches.Patch(color='red', label='Low Quality (SNR<15dB)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

        # 軸の範囲を調整
        if vehicle_positions:
            positions_array = np.array(list(vehicle_positions.values()))
            x_min, x_max = positions_array[:, 0].min(), positions_array[:, 0].max()
            y_min, y_max = positions_array[:, 1].min(), positions_array[:, 1].max()

            # X軸のマージン
            x_margin = 50
            ax.set_xlim(x_min - x_margin, x_max + x_margin)

            # Y軸の範囲を狭くして拡大表示（車両ラベルが重ならないように）
            y_margin = 20  # マージンを小さくしてY軸範囲を狭める
            ax.set_ylim(y_min - y_margin, y_max + y_margin)

    def _plot_graph_structure(
        self,
        ax,
        graph: nx.Graph,
        optimal_path: Optional[PathInfo]
    ):
        """グラフ構造を可視化"""
        ax.set_title('Communication Graph Structure', fontsize=12)
        ax.axis('off')

        if len(graph) == 0:
            ax.text(0.5, 0.5, 'No graph data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=14)
            return

        # グラフレイアウト
        pos = nx.spring_layout(graph, seed=42)

        # エッジを描画
        for u, v, data in graph.edges(data=True):
            snr = data['snr']

            # SNRに応じて色を変更
            if snr > 25:
                color = 'green'
                width = 3
            elif snr > 15:
                color = 'orange'
                width = 2
            else:
                color = 'red'
                width = 1

            nx.draw_networkx_edges(graph, pos, edgelist=[(u, v)],
                                  width=width, alpha=0.6, edge_color=color, ax=ax)

        # 最適経路をハイライト（コメントアウト - 青線を非表示）
        # if optimal_path:
        #     path_edges = [(optimal_path.path[i], optimal_path.path[i + 1])
        #                  for i in range(len(optimal_path.path) - 1)]
        #     nx.draw_networkx_edges(graph, pos, edgelist=path_edges,
        #                           width=4, alpha=0.9, edge_color='blue', ax=ax)

        # ノードを描画（すべて黄色で統一）
        nx.draw_networkx_nodes(graph, pos, node_color='yellow',
                              node_size=500, edgecolors='black', linewidths=2, ax=ax)

        # ラベルを描画
        nx.draw_networkx_labels(graph, pos, font_size=10, font_weight='bold', ax=ax)

    def plot_statistics(
        self,
        time_series: List[float],
        avg_snr_series: List[float],
        num_links_series: List[int],
        save_path: Optional[str] = None
    ):
        """
        統計情報の時系列グラフを作成

        Args:
            time_series: 時刻のリスト
            avg_snr_series: 平均SNRのリスト
            num_links_series: リンク数のリスト
            save_path: 保存先パス
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 平均SNR
        ax1.plot(time_series, avg_snr_series, 'b-', linewidth=2)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Average SNR (dB)')
        ax1.set_title('Average Communication Quality over Time')
        ax1.grid(True, alpha=0.3)

        # リンク数
        ax2.plot(time_series, num_links_series, 'g-', linewidth=2)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Number of Communication Links')
        ax2.set_title('Network Connectivity over Time')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Saved statistics to {save_path}")
        else:
            plt.show()

        plt.close()

    def create_animation(
        self,
        time_snapshots: List[float],
        position_snapshots: List[Dict[str, np.ndarray]],
        graph_snapshots: List[nx.Graph],
        path_snapshots: List[Optional[PathInfo]],
        save_path: str,
        fps: int = 10
    ):
        """
        アニメーションを作成

        Args:
            time_snapshots: 時刻のリスト
            position_snapshots: 各時刻の車両位置のリスト
            graph_snapshots: 各時刻のグラフのリスト
            path_snapshots: 各時刻の最適経路のリスト
            save_path: 保存先パス
            fps: フレームレート
        """
        fig, ax = plt.subplots(figsize=(12, 8))

        def update(frame):
            ax.clear()
            time = time_snapshots[frame]
            positions = position_snapshots[frame]
            graph = graph_snapshots[frame]
            path = path_snapshots[frame]

            self._plot_vehicles_and_links(ax, positions, graph, path, time)

        anim = FuncAnimation(fig, update, frames=len(time_snapshots),
                           interval=1000 / fps, repeat=True)

        anim.save(save_path, writer='pillow', fps=fps)
        print(f"Saved animation to {save_path}")
        plt.close()


if __name__ == "__main__":
    # テストコード
    print("Visualizer Test")
    print("=" * 60)

    # テスト用データ
    test_positions = {
        'veh0': np.array([0.0, 0.0]),
        'veh1': np.array([100.0, 20.0]),
        'veh2': np.array([200.0, -10.0]),
        'veh3': np.array([300.0, 15.0]),
    }

    # テスト用グラフ
    test_graph = nx.Graph()
    test_graph.add_node('veh0', pos=test_positions['veh0'])
    test_graph.add_node('veh1', pos=test_positions['veh1'])
    test_graph.add_node('veh2', pos=test_positions['veh2'])
    test_graph.add_node('veh3', pos=test_positions['veh3'])

    test_graph.add_edge('veh0', 'veh1', distance=100, snr=28.0, weight=0.036)
    test_graph.add_edge('veh1', 'veh2', distance=100, snr=26.0, weight=0.038)
    test_graph.add_edge('veh2', 'veh3', distance=100, snr=24.0, weight=0.042)
    test_graph.add_edge('veh0', 'veh2', distance=200, snr=18.0, weight=0.056)

    # テスト用最適経路
    from graph_optimizer import PathInfo
    test_path = PathInfo(
        source='veh0',
        target='veh3',
        path=['veh0', 'veh1', 'veh2', 'veh3'],
        total_cost=0.116,
        hop_count=3,
        min_link_quality=24.0
    )

    # 可視化
    visualizer = Visualizer()
    visualizer.plot_snapshot(
        test_positions,
        test_graph,
        test_path,
        time=10.5,
        save_path='figures/test_snapshot.png'
    )

    print("Test visualization saved to figures/test_snapshot.png")
    print("=" * 60)
