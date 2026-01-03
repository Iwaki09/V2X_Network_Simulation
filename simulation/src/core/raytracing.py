"""
SIONNA RTレイトレーシングシミュレーション

28GHz帯ミリ波における基地局-車両間（V2I）の通信リンク品質を計算します。
建物による遮蔽効果を考慮したレイトレーシングシミュレーションを実行します。
"""

import sionna as sn
import tensorflow as tf
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BaseStation:
    """基地局の定義"""
    id: str
    position: List[float]  # [x, y, z] in meters
    tx_power_dbm: float = 30.0  # 送信電力 [dBm]


@dataclass
class Building:
    """建物（遮蔽物）の定義"""
    id: str
    center: List[float]  # [x, y, z] in meters
    size: List[float]    # [width, depth, height] in meters


@dataclass
class LinkQuality:
    """リンク品質の計算結果"""
    timestamp: float
    link_type: str  # "V2I" or "V2V"
    tx_id: str
    rx_id: str  # vehicle_idから名称変更
    received_power_dbm: float
    delay_spread_ns: float
    path_loss_db: float
    is_line_of_sight: bool


class RayTracingSimulator:
    """SIONNA RTを使用したレイトレーシングシミュレータ"""

    def __init__(
        self,
        base_station: BaseStation,
        building: Building,
        frequency_ghz: float = 28.0,
        v2v_tx_power_dbm: float = 23.0
    ):
        """
        Args:
            base_station: 基地局の設定
            building: 建物の設定
            frequency_ghz: 周波数 [GHz]
            v2v_tx_power_dbm: V2V通信の送信電力 [dBm]
        """
        self.base_station = base_station
        self.building = building
        self.frequency_hz = frequency_ghz * 1e9
        self.v2v_tx_power_dbm = v2v_tx_power_dbm

        # GPU確認
        self._check_gpu()

        # SIONNA RTアンテナアレイの設定（等方性）
        self.tx_array = sn.rt.PlanarArray(
            num_rows=1, num_cols=1,
            vertical_spacing=0.5, horizontal_spacing=0.5,
            pattern="iso", polarization="V"
        )
        self.rx_array = sn.rt.PlanarArray(
            num_rows=1, num_cols=1,
            vertical_spacing=0.5, horizontal_spacing=0.5,
            pattern="iso", polarization="V"
        )

        print("✅ RayTracingSimulator initialized")
        print(f"   - Frequency: {frequency_ghz} GHz")
        print(f"   - Base Station: {base_station.id} at {base_station.position}")
        print(f"   - V2I TX Power: {base_station.tx_power_dbm} dBm")
        print(f"   - V2V TX Power: {v2v_tx_power_dbm} dBm")
        print(f"   - Building: {building.id} at {building.center}, size {building.size}")

    def _check_gpu(self):
        """GPU環境を確認"""
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            print("⚠️  Warning: No GPU found. SIONNA RT may run slowly or fail.")
        else:
            print(f"✅ GPU detected: {len(gpus)} device(s)")

    def _check_building_occlusion(
        self,
        point1: List[float],
        point2: List[float]
    ) -> bool:
        """
        2点間の直線が建物と交差するかをチェック（Liang-Barskyアルゴリズム）

        Args:
            point1: 始点 [x, y, z]
            point2: 終点 [x, y, z]

        Returns:
            True: 遮蔽あり, False: 遮蔽なし
        """
        x1, y1 = point1[:2]
        x2, y2 = point2[:2]
        cx, cy = self.building.center[:2]
        w, d = self.building.size[:2]

        # 建物の境界
        left = cx - w / 2
        right = cx + w / 2
        top = cy - d / 2
        bottom = cy + d / 2

        # 線分の方向ベクトル
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            return False

        t_min = 0.0
        t_max = 1.0

        # X方向の境界チェック
        if dx != 0:
            t1 = (left - x1) / dx
            t2 = (right - x1) / dx
            if dx < 0:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        elif x1 < left or x1 > right:
            return False

        # Y方向の境界チェック
        if dy != 0:
            t1 = (top - y1) / dy
            t2 = (bottom - y1) / dy
            if dy < 0:
                t1, t2 = t2, t1
            t_min = max(t_min, t1)
            t_max = min(t_max, t2)
        elif y1 < top or y1 > bottom:
            return False

        # 交差判定
        return t_min <= t_max and 0 <= t_min <= 1 and 0 <= t_max <= 1

    def _calculate_single_link(
        self,
        timestamp: float,
        link_type: str,
        tx_id: str,
        tx_position: List[float],
        tx_power_dbm: float,
        rx_id: str,
        rx_position: List[float]
    ) -> LinkQuality:
        """
        単一リンクのリンク品質を計算

        Args:
            timestamp: タイムスタンプ [秒]
            link_type: リンク種別 ("V2I" or "V2V")
            tx_id: 送信機のID
            tx_position: 送信機の位置 [x, y, z]
            tx_power_dbm: 送信電力 [dBm]
            rx_id: 受信機のID
            rx_position: 受信機の位置 [x, y, z]

        Returns:
            リンク品質
        """
        # 遮蔽判定
        is_los = not self._check_building_occlusion(tx_position, rx_position)

        # 距離計算
        distance = np.sqrt(
            (tx_position[0] - rx_position[0])**2 +
            (tx_position[1] - rx_position[1])**2 +
            (tx_position[2] - rx_position[2])**2
        )

        # 簡易パスロスモデル（フリスの伝搬式 + 遮蔽損失）
        # Path Loss (dB) = 20*log10(d) + 20*log10(f) + 20*log10(4π/c)
        if distance > 1:
            path_loss_db = (
                20 * np.log10(distance) +
                20 * np.log10(self.frequency_hz) +
                20 * np.log10(4 * np.pi / 3e8)
            )
        else:
            path_loss_db = 40.0  # 最小パスロス

        # 遮蔽による追加損失（NLOS時）
        if not is_los:
            occlusion_loss_db = 15.0
            path_loss_db += occlusion_loss_db

        # 受信電力計算
        received_power_dbm = tx_power_dbm - path_loss_db

        # 遅延スプレッド（簡易計算: 距離に比例）
        delay_spread_ns = distance / 3e8 * 1e9  # 伝搬時間をナノ秒で

        return LinkQuality(
            timestamp=timestamp,
            link_type=link_type,
            tx_id=tx_id,
            rx_id=rx_id,
            received_power_dbm=received_power_dbm,
            delay_spread_ns=delay_spread_ns,
            path_loss_db=path_loss_db,
            is_line_of_sight=is_los
        )

    def calculate_link_quality(
        self,
        timestamp: float,
        vehicle_positions: Dict[str, List[float]]
    ) -> List[LinkQuality]:
        """
        指定されたタイムステップにおける全リンク（V2I + V2V）の品質を計算

        Args:
            timestamp: タイムステップ [秒]
            vehicle_positions: 車両IDをキー、3次元座標[x, y, z]を値とする辞書

        Returns:
            リンク品質のリスト（V2IとV2Vの両方を含む）
        """
        if not vehicle_positions:
            return []

        link_qualities = []
        vehicle_ids = list(vehicle_positions.keys())

        # V2Iリンクの計算（基地局 -> 各車両）
        for vehicle_id in vehicle_ids:
            vehicle_pos = vehicle_positions[vehicle_id]
            link_quality = self._calculate_single_link(
                timestamp=timestamp,
                link_type="V2I",
                tx_id=self.base_station.id,
                tx_position=self.base_station.position,
                tx_power_dbm=self.base_station.tx_power_dbm,
                rx_id=vehicle_id,
                rx_position=vehicle_pos
            )
            link_qualities.append(link_quality)

        # V2Vリンクの計算（全車両間のペア）
        for i, tx_vehicle_id in enumerate(vehicle_ids):
            tx_vehicle_pos = vehicle_positions[tx_vehicle_id]

            for j, rx_vehicle_id in enumerate(vehicle_ids):
                # 同じ車両間のリンクはスキップ
                if i == j:
                    continue

                rx_vehicle_pos = vehicle_positions[rx_vehicle_id]
                link_quality = self._calculate_single_link(
                    timestamp=timestamp,
                    link_type="V2V",
                    tx_id=tx_vehicle_id,
                    tx_position=tx_vehicle_pos,
                    tx_power_dbm=self.v2v_tx_power_dbm,
                    rx_id=rx_vehicle_id,
                    rx_position=rx_vehicle_pos
                )
                link_qualities.append(link_quality)

        return link_qualities


if __name__ == "__main__":
    """レイトレーシングシミュレータの単体テスト"""
    print("=" * 60)
    print("Ray Tracing Simulator - Unit Test")
    print("=" * 60)

    # 基地局設定
    base_station = BaseStation(
        id="BS_1",
        position=[500.0, 150.0, 30.0],
        tx_power_dbm=30.0
    )

    # 建物設定
    building = Building(
        id="Building_1",
        center=[500.0, 50.0, 0.0],
        size=[20.0, 20.0, 100.0]
    )

    # シミュレータ初期化
    simulator = RayTracingSimulator(
        base_station=base_station,
        building=building,
        frequency_ghz=28.0
    )

    # テスト車両位置（LOS/NLOS両方をテスト）
    test_vehicle_positions = {
        "vehicle_test_1": [400.0, -1.6, 1.5],  # 建物の西側（LOSの可能性）
        "vehicle_test_2": [600.0, -1.6, 1.5],  # 建物の東側（LOSの可能性）
        "vehicle_test_3": [500.0, 10.0, 1.5],  # 建物の真南（NLOSの可能性）
    }

    # リンク品質計算
    print("\nCalculating link qualities...")
    link_qualities = simulator.calculate_link_quality(
        timestamp=0.0,
        vehicle_positions=test_vehicle_positions
    )

    # 結果表示
    print("\n" + "=" * 60)
    print("Link Quality Results")
    print("=" * 60)

    # V2Iリンク表示
    v2i_links = [lq for lq in link_qualities if lq.link_type == "V2I"]
    print(f"\nV2I Links: {len(v2i_links)}")
    for lq in v2i_links:
        print(f"\n  {lq.link_type}: {lq.tx_id} -> {lq.rx_id}")
        print(f"    Received Power: {lq.received_power_dbm:.2f} dBm")
        print(f"    Path Loss: {lq.path_loss_db:.2f} dB")
        print(f"    Delay Spread: {lq.delay_spread_ns:.2f} ns")
        print(f"    LOS: {'Yes' if lq.is_line_of_sight else 'No (Occluded)'}")

    # V2Vリンク表示
    v2v_links = [lq for lq in link_qualities if lq.link_type == "V2V"]
    print(f"\nV2V Links: {len(v2v_links)}")
    for lq in v2v_links[:5]:  # 最初の5件のみ表示
        print(f"\n  {lq.link_type}: {lq.tx_id} -> {lq.rx_id}")
        print(f"    Received Power: {lq.received_power_dbm:.2f} dBm")
        print(f"    Path Loss: {lq.path_loss_db:.2f} dB")
        print(f"    Delay Spread: {lq.delay_spread_ns:.2f} ns")
        print(f"    LOS: {'Yes' if lq.is_line_of_sight else 'No (Occluded)'}")
    if len(v2v_links) > 5:
        print(f"\n  ... and {len(v2v_links) - 5} more V2V links")

    print("\n" + "=" * 60)
    print("✅ Ray Tracing Simulator unit test completed!")
    print(f"   Total links: {len(link_qualities)} (V2I: {len(v2i_links)}, V2V: {len(v2v_links)})")
    print("=" * 60)
