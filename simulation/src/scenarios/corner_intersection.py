"""
交差点（コーナー）シナリオの設定

目的: LOS/NLOS切替を増やし、prop_mode(K)サンプルを確保
- 十字交差点
- 4棟の角ビル
- BS配置で遮蔽発生を促進
"""

from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from ..core.raytracing import BaseStation, Building


@dataclass
class CornerIntersectionConfig:
    """交差点（コーナー）シナリオの設定"""

    name: str = "corner_intersection"
    description: str = "十字交差点シナリオ（4棟の角ビル、LOS/NLOS切替多発）"

    # ディレクトリ設定
    sumo_config_dir: str = "sumo_config/corner_intersection"
    output_base_dir: str = "output/scenarios/corner_intersection"

    # 座標オフセット（FCDからRTへの変換時に適用）
    # SUMOの交差点中心が(200,200)なので、(0,0)に移動させる
    coord_offset_x: float = -200.0
    coord_offset_y: float = -200.0

    # 基地局設定（複数BS対応）
    # 3基地局を配置して負荷分散の余地を作る
    # BS_1: (+120, +120, 20) - 北東
    # BS_2: (-120, +120, 20) - 北西
    # BS_3: (+120, -120, 20) - 南東
    base_stations: List[BaseStation] = field(default_factory=lambda: [
        BaseStation(
            id="BS_1",
            position=[120.0, 120.0, 20.0],
            tx_power_dbm=40.0
        ),
        BaseStation(
            id="BS_2",
            position=[-120.0, 120.0, 20.0],
            tx_power_dbm=40.0
        ),
        BaseStation(
            id="BS_3",
            position=[120.0, -120.0, 20.0],
            tx_power_dbm=40.0
        )
    ])

    # 建物設定（4棟の角ビル）
    # 道路からのセットバック d=10m、建物サイズ W=60m, H=60m、高さ z=20m
    # 建物の中心座標（矩形）:
    # - NE: (+40, +40)
    # - NW: (-40, +40)
    # - SE: (+40, -40)
    # - SW: (-40, -40)
    buildings: List[Building] = field(default_factory=lambda: [
        Building(
            id="Building_NE",
            center=[40.0, 40.0, 0.0],
            size=[60.0, 60.0, 20.0]
        ),
        Building(
            id="Building_NW",
            center=[-40.0, 40.0, 0.0],
            size=[60.0, 60.0, 20.0]
        ),
        Building(
            id="Building_SE",
            center=[40.0, -40.0, 0.0],
            size=[60.0, 60.0, 20.0]
        ),
        Building(
            id="Building_SW",
            center=[-40.0, -40.0, 0.0],
            size=[60.0, 60.0, 20.0]
        )
    ])

    # 物理パラメータ
    frequency_ghz: float = 28.0
    v2v_tx_power_dbm: float = 23.0

    # 可視化パラメータ
    viz_xlim: tuple = (-150, 150)  # X軸の描画範囲（交差点を中心に）
    viz_ylim: tuple = (-150, 150)  # Y軸の描画範囲（交差点を中心に）
    viz_road_x_range: tuple = (-150, 150)  # 道路のX範囲
    viz_road_y_range: tuple = (-150, 150)  # 道路のY範囲（交差点全体）

    @property
    def sumo_config_path(self) -> Path:
        """SUMO設定ファイルのパス"""
        base = Path(__file__).parent.parent.parent
        return base / self.sumo_config_dir / "simulation.sumocfg"

    @property
    def fcd_output_path(self) -> Path:
        """FCD出力ファイルのパス"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "fcd" / "fcd_output.xml"

    @property
    def raytracing_output_path(self) -> Path:
        """レイトレーシング結果出力パス"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "raytracing" / "link_quality_results.csv"

    @property
    def throughput_output_path(self) -> Path:
        """スループット結果出力パス"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "throughput" / "theoretical_network_results.csv"

    @property
    def optimization_output_dir(self) -> Path:
        """最適化結果出力ディレクトリ"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "optimization"

    @property
    def analysis_output_dir(self) -> Path:
        """分析結果出力ディレクトリ"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "analysis"

    @property
    def figures_output_dir(self) -> Path:
        """可視化出力ディレクトリ"""
        base = Path(__file__).parent.parent.parent
        return base / self.output_base_dir / "figures"

    def transform_coordinates(self, x: float, y: float) -> tuple:
        """FCD座標をRT座標に変換"""
        return (x + self.coord_offset_x, y + self.coord_offset_y)

    # 後方互換性のために単一基地局プロパティを維持
    @property
    def base_station(self) -> BaseStation:
        """最初の基地局への参照（後方互換性）"""
        return self.base_stations[0] if self.base_stations else None

    # 後方互換性のために単一建物プロパティを維持
    @property
    def building(self) -> Building:
        """最初の建物への参照（後方互換性）"""
        return self.buildings[0] if self.buildings else None
