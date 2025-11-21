#!/usr/bin/env python3
"""
V2Xネットワークトポロジー可視化

グローバル最適化結果のトポロジーを可視化し、車両のカテゴリ別に色分けする:
- Direct V2I (青): 基地局と直接接続
- Relayed (緑): V2V経由で基地局に到達
- Island V2V (オレンジ): 基地局に到達不可、ローカルV2Vのみ
- Disconnected (灰色): 孤立車両
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET


# ファイルパス
LINKS_FILE = Path(__file__).parent / "output" / "baseline" / "global_optimization_links.csv"
FCD_FILE = Path(__file__).parent / "output" / "fcd" / "fcd_output.xml"
OUTPUT_DIR = Path(__file__).parent / "output" / "visualizations" / "topology"

# 可視化パラメータ
ROAD_LENGTH = 1000  # 道路長さ [m]
ROAD_LANES = 2      # 車線数
LANE_WIDTH = 3.5    # 車線幅 [m]
BASE_STATION_POS = [500, 150, 30]  # 基地局位置 [x, y, z]
BUILDING_POS = [500, 50, 0]        # 建物位置 [x, y, z]
BUILDING_SIZE = [20, 20, 100]      # 建物サイズ [width, depth, height]

# カテゴリ別の色設定
COLORS = {
    'Direct V2I': '#2E86C1',     # 青
    'Relayed': '#28B463',         # 緑
    'Island V2V': '#F39C12',      # オレンジ
    'Disconnected': '#95A5A6'     # 灰色
}

# リンク別の色設定
LINK_COLORS = {
    'V2I': '#2E86C1',            # 青系（実線）
    'V2V': '#28B463'             # 緑系（点線）
}


class TopologyVisualizer:
    """V2Xトポロジー可視化クラス"""

    def __init__(self, links_df: pd.DataFrame, fcd_file: Path):
        """
        Parameters
        ----------
        links_df : pd.DataFrame
            グローバル最適化結果のリンク情報
        fcd_file : Path
            SUMO FCD出力ファイルのパス
        """
        self.links_df = links_df
        self.fcd_file = fcd_file
        self.base_station_id = "BS_1"

        # FCD XMLから車両位置情報を読み込み
        self.vehicle_positions = self._parse_fcd()

    def _parse_fcd(self) -> Dict[float, Dict[str, List[float]]]:
        """
        SUMO FCD XMLファイルをパースして車両位置を取得

        Returns
        -------
        Dict[float, Dict[str, List[float]]]
            {timestamp: {vehicle_id: [x, y]}}
        """
        tree = ET.parse(self.fcd_file)
        root = tree.getroot()

        positions = {}

        for timestep in root.findall('timestep'):
            time = float(timestep.get('time'))
            positions[time] = {}

            for vehicle in timestep.findall('vehicle'):
                vehicle_id = vehicle.get('id')
                x = float(vehicle.get('x'))
                y = float(vehicle.get('y'))
                positions[time][vehicle_id] = [x, y]

        return positions

    def _classify_vehicle(self, timestamp: float, vehicle_id: str,
                         active_links_df: pd.DataFrame) -> str:
        """
        車両をカテゴリ分類（analyze_topology.pyのロジックを簡易実装）

        Parameters
        ----------
        timestamp : float
            タイムステップ
        vehicle_id : str
            車両ID
        active_links_df : pd.DataFrame
            アクティブリンクのDataFrame

        Returns
        -------
        str
            カテゴリ名
        """
        # Direct V2I: 基地局から直接受信している
        direct_v2i_links = active_links_df[
            (active_links_df['tx_id'] == self.base_station_id) &
            (active_links_df['rx_id'] == vehicle_id)
        ]
        if len(direct_v2i_links) > 0:
            return "Direct V2I"

        # V2Vリンクを持つか確認
        v2v_links = active_links_df[
            ((active_links_df['tx_id'] == vehicle_id) |
             (active_links_df['rx_id'] == vehicle_id)) &
            (active_links_df['link_type'] == 'V2V')
        ]
        if len(v2v_links) > 0:
            return "Island V2V"

        # どのリンクも持たない
        return "Disconnected"

    def visualize_timestep(self, timestamp: float, output_file: Path):
        """
        指定タイムステップのトポロジーを可視化

        Parameters
        ----------
        timestamp : float
            可視化対象のタイムステップ
        output_file : Path
            出力ファイルパス
        """
        # アクティブリンクのみを抽出
        active_links = self.links_df[
            (self.links_df['timestamp'] == timestamp) &
            (self.links_df['is_active'] == True)
        ].copy()

        # 車両位置を取得
        if timestamp not in self.vehicle_positions:
            print(f"  [警告] t={timestamp}: 車両位置情報が見つかりません")
            return

        vehicle_pos = self.vehicle_positions[timestamp]

        # 図を作成
        fig, ax = plt.subplots(figsize=(14, 8))

        # 道路を描画
        ax.fill_between([0, ROAD_LENGTH], [-LANE_WIDTH, -LANE_WIDTH],
                        [LANE_WIDTH, LANE_WIDTH], color='#BDC3C7', alpha=0.3)
        ax.plot([0, ROAD_LENGTH], [0, 0], 'k--', linewidth=1, alpha=0.5)

        # 建物を描画
        building_x = BUILDING_POS[0]
        building_y = BUILDING_POS[1]
        building_w = BUILDING_SIZE[0]
        building_h = BUILDING_SIZE[1]
        rect = mpatches.Rectangle(
            (building_x - building_w/2, building_y - building_h/2),
            building_w, building_h,
            linewidth=2, edgecolor='black', facecolor='#7F8C8D', alpha=0.5
        )
        ax.add_patch(rect)
        ax.text(building_x, building_y, 'Building',
                ha='center', va='center', fontsize=10, color='white', weight='bold')

        # 基地局を描画
        bs_x, bs_y = BASE_STATION_POS[0], BASE_STATION_POS[1]
        ax.scatter(bs_x, bs_y, s=300, c='red', marker='^',
                  edgecolors='black', linewidths=2, zorder=10, label='Base Station')
        ax.text(bs_x, bs_y + 20, 'BS_1', ha='center', fontsize=10, weight='bold')

        # リンクを描画（車両より先に描画）
        for _, link in active_links.iterrows():
            tx_id = link['tx_id']
            rx_id = link['rx_id']
            link_type = link['link_type']

            # 送信元の座標
            if tx_id == self.base_station_id:
                tx_pos = [bs_x, bs_y]
            elif tx_id in vehicle_pos:
                tx_pos = vehicle_pos[tx_id]
            else:
                continue

            # 受信先の座標
            if rx_id in vehicle_pos:
                rx_pos = vehicle_pos[rx_id]
            else:
                continue

            # リンクを描画
            color = LINK_COLORS.get(link_type, '#95A5A6')
            linestyle = '-' if link_type == 'V2I' else '--'
            linewidth = 2 if link_type == 'V2I' else 1.5

            ax.annotate('', xy=rx_pos, xytext=tx_pos,
                       arrowprops=dict(arrowstyle='->', color=color,
                                     linestyle=linestyle, linewidth=linewidth,
                                     alpha=0.6))

        # 車両を描画（カテゴリ別に色分け）
        category_counts = {'Direct V2I': 0, 'Relayed': 0,
                          'Island V2V': 0, 'Disconnected': 0}

        for vehicle_id, pos in vehicle_pos.items():
            category = self._classify_vehicle(timestamp, vehicle_id, active_links)
            category_counts[category] += 1

            color = COLORS.get(category, '#95A5A6')
            ax.scatter(pos[0], pos[1], s=150, c=color,
                      edgecolors='black', linewidths=1.5, zorder=5)
            ax.text(pos[0], pos[1] - 10, vehicle_id.replace('vehicle_', 'V'),
                   ha='center', fontsize=8)

        # 統計情報を注釈として追加
        total = sum(category_counts.values())
        stats_text = f"Time: {timestamp:.1f}s | Total Vehicles: {total}\n"
        stats_text += f"Direct V2I: {category_counts['Direct V2I']} ({100*category_counts['Direct V2I']/total:.0f}%)\n"
        stats_text += f"Relayed: {category_counts['Relayed']} ({100*category_counts['Relayed']/total:.0f}%)\n"
        stats_text += f"Island V2V: {category_counts['Island V2V']} ({100*category_counts['Island V2V']/total:.0f}%)\n"
        stats_text += f"Disconnected: {category_counts['Disconnected']} ({100*category_counts['Disconnected']/total:.0f}%)"

        ax.text(0.02, 0.98, stats_text,
               transform=ax.transAxes, fontsize=10,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        # 凡例を作成
        legend_elements = [
            mpatches.Patch(color=COLORS['Direct V2I'], label='Direct V2I'),
            mpatches.Patch(color=COLORS['Relayed'], label='Relayed'),
            mpatches.Patch(color=COLORS['Island V2V'], label='Island V2V'),
            mpatches.Patch(color=COLORS['Disconnected'], label='Disconnected'),
            plt.Line2D([0], [0], color=LINK_COLORS['V2I'], linewidth=2,
                      linestyle='-', label='V2I Link'),
            plt.Line2D([0], [0], color=LINK_COLORS['V2V'], linewidth=1.5,
                      linestyle='--', label='V2V Link')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=9)

        # 軸設定
        ax.set_xlim(-50, ROAD_LENGTH + 50)
        ax.set_ylim(-50, 200)
        ax.set_xlabel('X Position [m]', fontsize=12)
        ax.set_ylabel('Y Position [m]', fontsize=12)
        ax.set_title(f'V2X Network Topology at t={timestamp:.1f}s',
                    fontsize=14, weight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

        # 保存
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()

    def visualize_all_timesteps(self, sample_interval: int = 5):
        """
        全タイムステップのトポロジーを可視化（サンプリング間隔指定可能）

        Parameters
        ----------
        sample_interval : int
            サンプリング間隔（デフォルト: 5秒ごと）
        """
        timestamps = sorted(self.links_df['timestamp'].unique())
        sampled_timestamps = [t for t in timestamps if int(t) % sample_interval == 0]

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        print(f"トポロジー可視化を開始（{len(sampled_timestamps)} / {len(timestamps)} タイムステップ）")

        for i, timestamp in enumerate(sampled_timestamps):
            output_file = OUTPUT_DIR / f"topology_{int(timestamp):04d}.png"
            self.visualize_timestep(timestamp, output_file)

            if (i + 1) % 5 == 0 or (i + 1) == len(sampled_timestamps):
                print(f"  - 進捗: {i+1}/{len(sampled_timestamps)} ({100*(i+1)/len(sampled_timestamps):.1f}%)")


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("V2Xネットワーク トポロジー可視化")
    print("=" * 60)

    # データ読み込み
    print(f"\n[1] データ読み込み")
    print(f"  - リンク情報: {LINKS_FILE}")
    print(f"  - FCD位置情報: {FCD_FILE}")

    links_df = pd.read_csv(LINKS_FILE)
    print(f"  - 総リンク数: {len(links_df)}")
    print(f"  - アクティブリンク: {links_df['is_active'].sum()}")

    # 可視化実行
    print(f"\n[2] トポロジー可視化")
    visualizer = TopologyVisualizer(links_df, FCD_FILE)
    visualizer.visualize_all_timesteps(sample_interval=5)

    print(f"\n[3] 出力ディレクトリ: {OUTPUT_DIR}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("トポロジー可視化完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
