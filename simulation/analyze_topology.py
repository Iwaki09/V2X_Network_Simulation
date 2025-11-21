#!/usr/bin/env python3
"""
トポロジー解析モジュール

グローバル最適化結果から、各タイムステップにおける車両の接続形態を分類する:
- Direct V2I Users: 基地局と直接接続している車両
- Relayed Users: V2Vリンク経由で基地局に到達可能な車両（中継機能）
- Island V2V Users: 基地局に到達できないが、他車両とV2Vで接続（ローカルクラスタ）
- Disconnected: どのノードとも接続がない車両
"""

import pandas as pd
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple


# ファイルパス
LINKS_FILE = Path(__file__).parent / "output" / "baseline" / "global_optimization_links.csv"
OUTPUT_DIR = Path(__file__).parent / "output" / "analysis"
OUTPUT_FILE = OUTPUT_DIR / "topology_classification.csv"


class TopologyAnalyzer:
    """V2Xネットワークトポロジーを解析するクラス"""

    def __init__(self, links_df: pd.DataFrame):
        """
        Parameters
        ----------
        links_df : pd.DataFrame
            グローバル最適化結果のリンク情報
        """
        self.links_df = links_df
        self.base_station_id = "BS_1"

    def analyze_timestep(self, timestamp: float) -> Dict[str, any]:
        """
        指定タイムステップのトポロジーを解析

        Parameters
        ----------
        timestamp : float
            解析対象のタイムステップ

        Returns
        -------
        Dict[str, any]
            分類結果の辞書
        """
        # アクティブリンクのみを抽出
        df_t = self.links_df[
            (self.links_df['timestamp'] == timestamp) &
            (self.links_df['is_active'] == True)
        ].copy()

        # 有向グラフを構築（データフローの向き: tx -> rx）
        G = nx.DiGraph()

        # 全車両IDを収集（基地局を除く）
        all_vehicles = set()
        for _, row in df_t.iterrows():
            if row['tx_id'] != self.base_station_id:
                all_vehicles.add(row['tx_id'])
            if row['rx_id'] != self.base_station_id:
                all_vehicles.add(row['rx_id'])

        # エッジを追加
        for _, row in df_t.iterrows():
            G.add_edge(row['tx_id'], row['rx_id'],
                      link_type=row['link_type'],
                      throughput=row['throughput_mbps'])

        # 車両を分類
        direct_v2i = set()
        relayed = set()
        island_v2v = set()
        disconnected = set()

        for vehicle in all_vehicles:
            category = self._classify_vehicle(G, vehicle)
            if category == "Direct V2I":
                direct_v2i.add(vehicle)
            elif category == "Relayed":
                relayed.add(vehicle)
            elif category == "Island V2V":
                island_v2v.add(vehicle)
            else:
                disconnected.add(vehicle)

        total = len(all_vehicles)

        return {
            'timestamp': timestamp,
            'total_vehicles': total,
            'direct_v2i': len(direct_v2i),
            'relayed': len(relayed),
            'island_v2v': len(island_v2v),
            'disconnected': len(disconnected),
            'direct_v2i_ratio': len(direct_v2i) / total if total > 0 else 0,
            'relayed_ratio': len(relayed) / total if total > 0 else 0,
            'island_v2v_ratio': len(island_v2v) / total if total > 0 else 0,
            'disconnected_ratio': len(disconnected) / total if total > 0 else 0,
            # 詳細情報（可視化用）
            'direct_v2i_list': list(direct_v2i),
            'relayed_list': list(relayed),
            'island_v2v_list': list(island_v2v),
            'disconnected_list': list(disconnected)
        }

    def _classify_vehicle(self, G: nx.DiGraph, vehicle_id: str) -> str:
        """
        グラフ探索により車両を分類

        Parameters
        ----------
        G : nx.DiGraph
            ネットワークグラフ
        vehicle_id : str
            分類対象の車両ID

        Returns
        -------
        str
            カテゴリ名
        """
        # 1. Direct V2I: 基地局から直接受信している
        if G.has_edge(self.base_station_id, vehicle_id):
            return "Direct V2I"

        # 2. Relayed: 基地局に到達可能（無向グラフとして探索）
        # データフローは tx->rx だが、到達可能性は双方向で考える
        G_undirected = G.to_undirected()
        if self.base_station_id in G_undirected and vehicle_id in G_undirected:
            try:
                if nx.has_path(G_undirected, self.base_station_id, vehicle_id):
                    return "Relayed"
            except nx.NodeNotFound:
                pass

        # 3. Island V2V: 基地局には到達できないが、他車両と接続
        if G.degree(vehicle_id) > 0:
            return "Island V2V"

        # 4. Disconnected: どのノードとも接続なし
        return "Disconnected"

    def analyze_all_timesteps(self) -> pd.DataFrame:
        """
        全タイムステップのトポロジーを解析

        Returns
        -------
        pd.DataFrame
            各タイムステップの分類結果
        """
        timestamps = sorted(self.links_df['timestamp'].unique())
        results = []

        print(f"トポロジー解析を開始（{len(timestamps)} タイムステップ）")

        for i, timestamp in enumerate(timestamps):
            result = self.analyze_timestep(timestamp)
            results.append({
                'timestamp': result['timestamp'],
                'total_vehicles': result['total_vehicles'],
                'direct_v2i': result['direct_v2i'],
                'relayed': result['relayed'],
                'island_v2v': result['island_v2v'],
                'disconnected': result['disconnected'],
                'direct_v2i_ratio': result['direct_v2i_ratio'],
                'relayed_ratio': result['relayed_ratio'],
                'island_v2v_ratio': result['island_v2v_ratio'],
                'disconnected_ratio': result['disconnected_ratio']
            })

            if (i + 1) % 20 == 0 or (i + 1) == len(timestamps):
                print(f"  - 進捗: {i+1}/{len(timestamps)} ({100*(i+1)/len(timestamps):.1f}%)")

        return pd.DataFrame(results)


def main():
    """メイン実行関数"""
    print("=" * 60)
    print("V2Xネットワーク トポロジー解析")
    print("=" * 60)

    # データ読み込み
    print(f"\n[1] データ読み込み: {LINKS_FILE}")
    links_df = pd.read_csv(LINKS_FILE)
    print(f"  - 総リンク数: {len(links_df)}")
    print(f"  - アクティブリンク: {links_df['is_active'].sum()}")

    # 解析実行
    print(f"\n[2] トポロジー解析")
    analyzer = TopologyAnalyzer(links_df)
    results_df = analyzer.analyze_all_timesteps()

    # 統計情報を表示
    print(f"\n[3] 解析結果サマリー")
    print(f"  - タイムステップ数: {len(results_df)}")
    print(f"  - 平均車両数: {results_df['total_vehicles'].mean():.1f}")
    print(f"\n  カテゴリ別割合（平均）:")
    print(f"    * Direct V2I: {results_df['direct_v2i_ratio'].mean()*100:.1f}%")
    print(f"    * Relayed: {results_df['relayed_ratio'].mean()*100:.1f}%")
    print(f"    * Island V2V: {results_df['island_v2v_ratio'].mean()*100:.1f}%")
    print(f"    * Disconnected: {results_df['disconnected_ratio'].mean()*100:.1f}%")

    # 詳細な時系列統計
    print(f"\n  Relayed Users詳細:")
    print(f"    * 最大: {results_df['relayed'].max()} 台 ({results_df['relayed_ratio'].max()*100:.1f}%)")
    print(f"    * 最小: {results_df['relayed'].min()} 台 ({results_df['relayed_ratio'].min()*100:.1f}%)")
    print(f"    * Relayed機能が使われたタイムステップ: {(results_df['relayed'] > 0).sum()} / {len(results_df)}")

    # CSV保存
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n[4] 出力ファイル: {OUTPUT_FILE}")
    print(f"  - 保存完了")

    print("\n" + "=" * 60)
    print("トポロジー解析完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
