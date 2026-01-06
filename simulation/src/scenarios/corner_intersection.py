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

    # 基地局設定
    # 位置: (+120, +120)、高さ: z_bs = 20m
    # 西側(x<0)や南側(y<0)の車両に対し、角ビルでNLOSが起きやすくする
    base_station: BaseStation = field(default_factory=lambda: BaseStation(
        id="BS_1",
        position=[120.0, 120.0, 20.0],
        tx_power_dbm=30.0
    ))

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

    def transform_coordinates(self, x: float, y: float) -> tuple:
        """FCD座標をRT座標に変換"""
        return (x + self.coord_offset_x, y + self.coord_offset_y)

    # 後方互換性のために単一建物プロパティを維持
    @property
    def building(self) -> Building:
        """最初の建物への参照（後方互換性）"""
        return self.buildings[0] if self.buildings else None
