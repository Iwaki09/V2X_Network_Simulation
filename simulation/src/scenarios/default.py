"""
デフォルトシナリオ（既存の直線道路シナリオ）の設定

既存の後方互換性を維持するためのシナリオ設定
"""

from dataclasses import dataclass, field
from typing import List
from pathlib import Path

from ..core.raytracing import BaseStation, Building


@dataclass
class DefaultScenarioConfig:
    """デフォルトシナリオ（直線道路）の設定"""

    name: str = "default"
    description: str = "直線道路シナリオ（1km道路、建物1棟）"

    # ディレクトリ設定
    sumo_config_dir: str = "sumo_config"
    output_base_dir: str = "output/scenarios/default"

    # 座標オフセット（FCDからRTへの変換時に適用）
    # デフォルトシナリオではオフセットなし
    coord_offset_x: float = 0.0
    coord_offset_y: float = 0.0

    # 基地局設定
    base_station: BaseStation = field(default_factory=lambda: BaseStation(
        id="BS_1",
        position=[500.0, 150.0, 30.0],
        tx_power_dbm=30.0
    ))

    # 建物設定（単一の建物）
    buildings: List[Building] = field(default_factory=lambda: [
        Building(
            id="Building_1",
            center=[500.0, 50.0, 0.0],
            size=[20.0, 20.0, 100.0]
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

    # 後方互換性のために単一建物プロパティを維持
    @property
    def building(self) -> Building:
        """単一建物への参照（後方互換性）"""
        return self.buildings[0] if self.buildings else None
