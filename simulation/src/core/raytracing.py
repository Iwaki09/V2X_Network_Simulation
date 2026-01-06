"""
SIONNA RTレイトレーシングシミュレーション

28GHz帯ミリ波における基地局-車両間（V2I）の通信リンク品質を計算します。
建物による遮蔽効果を考慮したレイトレーシングシミュレーションを実行します。

2つのモード:
- use_sionna_rt=False (デフォルト): 簡易パスロスモデル（フリスの式）
- use_sionna_rt=True: Sionna RTによる本格的なレイトレーシング（マルチパス対応）
"""

import sionna as sn
import tensorflow as tf
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .propagation_mode import compute_dk, dbm_to_watts, watts_to_dbm


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
    # Propagation-Mode Switch (D/K) 関連フィールド
    num_paths: int = 1
    p_tot_watts: float = 0.0
    p_max_watts: float = 0.0
    dominance: float = 1.0  # D = P_max / P_tot
    k_factor: float = float("inf")  # K = P_max / (P_tot - P_max)
    k_factor_db: float = float("inf")
    prop_mode: str = "D"  # "D" or "K"


class RayTracingSimulator:
    """SIONNA RTを使用したレイトレーシングシミュレータ"""

    def __init__(
        self,
        base_station: BaseStation,
        building: Building = None,
        buildings: List[Building] = None,
        frequency_ghz: float = 28.0,
        v2v_tx_power_dbm: float = 23.0,
        use_sionna_rt: bool = False,
        max_depth: int = 3,
        num_samples: int = 1000000
    ):
        """
        Args:
            base_station: 基地局の設定
            building: 建物の設定（後方互換性のため維持、buildingsがある場合は無視）
            buildings: 建物のリスト（複数建物対応）
            frequency_ghz: 周波数 [GHz]
            v2v_tx_power_dbm: V2V通信の送信電力 [dBm]
            use_sionna_rt: TrueならSionna RTでマルチパス計算、Falseなら簡易モデル
            max_depth: レイトレーシングの最大反射回数
            num_samples: レイトレーシングのサンプル数
        """
        self.base_station = base_station

        # 後方互換性: building引数またはbuildings引数をサポート
        if buildings is not None:
            self.buildings = buildings
        elif building is not None:
            self.buildings = [building]
        else:
            self.buildings = []

        # 後方互換性のためにself.buildingも維持
        self.building = self.buildings[0] if self.buildings else None

        self.frequency_ghz = frequency_ghz
        self.frequency_hz = frequency_ghz * 1e9
        self.v2v_tx_power_dbm = v2v_tx_power_dbm
        self.use_sionna_rt = use_sionna_rt
        self.max_depth = max_depth
        self.num_samples = num_samples

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

        # Sionna RTシーンの初期化（use_sionna_rt=Trueの場合）
        self.scene = None
        self._path_solver = None
        if self.use_sionna_rt:
            self._setup_sionna_scene()
            if hasattr(sn.rt, "PathSolver"):
                try:
                    self._path_solver = sn.rt.PathSolver(num_samples=self.num_samples)
                except TypeError:
                    self._path_solver = sn.rt.PathSolver()

        print("✅ RayTracingSimulator initialized")
        print(f"   - Mode: {'Sionna RT (multi-path)' if use_sionna_rt else 'Simple model (single-path)'}")
        print(f"   - Frequency: {frequency_ghz} GHz")
        print(f"   - Base Station: {base_station.id} at {base_station.position}")
        print(f"   - V2I TX Power: {base_station.tx_power_dbm} dBm")
        print(f"   - V2V TX Power: {v2v_tx_power_dbm} dBm")
        print(f"   - Buildings: {len(self.buildings)} building(s)")
        for bldg in self.buildings:
            print(f"     - {bldg.id} at {bldg.center}, size {bldg.size}")
        if use_sionna_rt:
            print(f"   - Max reflection depth: {max_depth}")
            print(f"   - Ray samples: {num_samples}")

    def _check_gpu(self):
        """GPU環境を確認"""
        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            print("⚠️  Warning: No GPU found. SIONNA RT may run slowly or fail.")
        else:
            print(f"✅ GPU detected: {len(gpus)} device(s)")

    def _setup_sionna_scene(self):
        """
        Sionna RTシーンを構築

        - 地面（平面）
        - 建物（直方体）
        - 材質設定（コンクリート、金属など）
        """
        print("🔧 Setting up Sionna RT scene...")

        # 空のシーンを作成
        self.scene = sn.rt.Scene()

        # 周波数設定
        self.scene.frequency = self.frequency_hz

        # 地面を追加（大きな平面）
        # Sionna RTでは通常、地面はシーンの一部として定義
        ground_material = sn.rt.RadioMaterial(
            "ground_concrete",
            relative_permittivity=5.31,  # コンクリート
            conductivity=0.01
        )
        self.scene.add(ground_material)

        # 建物の材質を定義
        building_material = sn.rt.RadioMaterial(
            "building_concrete",
            relative_permittivity=5.31,
            conductivity=0.01
        )
        self.scene.add(building_material)

        # 建物をボックスとして追加
        # Sionna RTではMitsuba形式のシーンファイルを使用するのが一般的だが、
        # ここではプログラマティックに定義
        bldg = self.building
        half_w = bldg.size[0] / 2
        half_d = bldg.size[1] / 2
        height = bldg.size[2]
        cx, cy, cz = bldg.center

        # 建物の頂点を定義（直方体）
        # 注意: Sionna RTのScene APIに応じて調整が必要
        # ここでは概念的な実装を示す
        try:
            # Sionna RTのプリミティブを使用してボックスを追加
            # 実際のAPIに応じて調整
            box = sn.rt.Box(
                name=bldg.id,
                center=[cx, cy, cz + height / 2],  # 中心を高さの半分に
                size=[bldg.size[0], bldg.size[1], height],
                material=building_material
            )
            self.scene.add(box)
        except AttributeError:
            # Sionna RTのバージョンによってはBoxが使えない場合がある
            # その場合はXMLシーンファイルをロードする方式に切り替え
            print("⚠️  Box primitive not available. Using scene file approach.")
            self._create_scene_file()

        if self.scene is not None:
            try:
                self.scene.tx_array = self.tx_array
                self.scene.rx_array = self.rx_array
            except AttributeError:
                pass

        print(f"   - Added building: {bldg.id} at {bldg.center}")
        print("✅ Sionna RT scene setup complete")

    def _create_box_mesh_obj(self, filename: str, center: List[float], size: List[float]):
        """
        直方体の三角メッシュを.obj形式で生成

        Args:
            filename: 出力ファイル名
            center: 中心座標 [x, y, z]
            size: サイズ [幅, 奥行き, 高さ]
        """
        cx, cy, cz = center
        w, d, h = size
        half_w = w / 2
        half_d = d / 2
        half_h = h / 2

        # 8つの頂点（ボックスの角）
        vertices = [
            # 底面（z = cz）
            [cx - half_w, cy - half_d, cz],  # v0
            [cx + half_w, cy - half_d, cz],  # v1
            [cx + half_w, cy + half_d, cz],  # v2
            [cx - half_w, cy + half_d, cz],  # v3
            # 上面（z = cz + h）
            [cx - half_w, cy - half_d, cz + h],  # v4
            [cx + half_w, cy - half_d, cz + h],  # v5
            [cx + half_w, cy + half_d, cz + h],  # v6
            [cx - half_w, cy + half_d, cz + h],  # v7
        ]

        # 12個の三角形（各面2つずつ、6面）
        # OBJ形式では頂点インデックスは1から始まる
        # 反時計回りの頂点順序で定義（外向き法線）
        faces = [
            # 底面（-Z方向、下向き）
            [1, 3, 2], [1, 4, 3],
            # 上面（+Z方向、上向き）
            [5, 6, 7], [5, 7, 8],
            # 前面（-Y方向）
            [1, 2, 6], [1, 6, 5],
            # 背面（+Y方向）
            [4, 7, 3], [4, 8, 7],
            # 左面（-X方向）
            [1, 5, 8], [1, 8, 4],
            # 右面（+X方向）
            [2, 3, 7], [2, 7, 6],
        ]

        # .objファイルに書き出し
        with open(filename, 'w') as f:
            f.write("# Box mesh generated for SIONNA RT\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face in faces:
                f.write(f"f {face[0]} {face[1]} {face[2]}\n")

    def _create_ground_mesh_obj(self, filename: str, size: float = 1000.0):
        """
        地面の三角メッシュ（大きな平面）を.obj形式で生成

        Args:
            filename: 出力ファイル名
            size: 平面のサイズ（正方形）
        """
        half_size = size / 2

        # 4つの頂点（平面の角、z=0）
        vertices = [
            [-half_size, -half_size, 0.0],
            [half_size, -half_size, 0.0],
            [half_size, half_size, 0.0],
            [-half_size, half_size, 0.0],
        ]

        # 2つの三角形
        faces = [
            [1, 2, 3],
            [1, 3, 4],
        ]

        # .objファイルに書き出し
        with open(filename, 'w') as f:
            f.write("# Ground plane mesh generated for SIONNA RT\n")
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for face in faces:
                f.write(f"f {face[0]} {face[1]} {face[2]}\n")

    def _create_scene_file(self):
        """
        Sionna RT用のシーンファイル（XML/Mitsuba形式）を動的に生成

        注意: これは代替手法。Sionna RTのバージョンによって必要な場合がある。
        """
        import tempfile
        import os

        bldg = self.building

        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()

        # 地面メッシュを生成
        ground_obj_path = os.path.join(self.temp_dir, "ground.obj")
        self._create_ground_mesh_obj(ground_obj_path, size=1000.0)

        # 建物メッシュを生成
        building_obj_path = os.path.join(self.temp_dir, "building.obj")
        self._create_box_mesh_obj(
            building_obj_path,
            center=bldg.center,
            size=bldg.size
        )

        # Mitsubaシーン形式のXMLを生成
        # SIONNA RTのサンプルに基づいたフォーマット
        scene_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<scene version="2.1.0">
    <!-- Materials -->
    <bsdf type="itu-radio-material" id="ground-mat">
        <string name="type" value="concrete"/>
    </bsdf>

    <bsdf type="itu-radio-material" id="building-mat">
        <string name="type" value="concrete"/>
    </bsdf>

    <!-- Shapes -->
    <shape type="obj" id="ground">
        <string name="filename" value="{ground_obj_path}"/>
        <boolean name="face_normals" value="true"/>
        <ref id="ground-mat" name="bsdf"/>
    </shape>

    <shape type="obj" id="{bldg.id}">
        <string name="filename" value="{building_obj_path}"/>
        <boolean name="face_normals" value="true"/>
        <ref id="building-mat" name="bsdf"/>
    </shape>
</scene>
'''
        # 一時ファイルに保存
        self.scene_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.xml', delete=False, dir=self.temp_dir
        )
        self.scene_file.write(scene_xml)
        self.scene_file.close()

        # シーンをロード
        self.scene = sn.rt.load_scene(self.scene_file.name)
        self.scene.frequency = self.frequency_hz

        print(f"   - Loaded scene from {self.scene_file.name}")
        print(f"   - Ground mesh: {ground_obj_path}")
        print(f"   - Building mesh: {building_obj_path}")

    def _compute_paths_sionna(
        self,
        tx_position: List[float],
        rx_position: List[float],
        tx_power_dbm: float
    ) -> Tuple[List[float], float, bool]:
        """
        Sionna RTでレイトレーシングを実行し、マルチパス情報を取得

        Args:
            tx_position: 送信機位置 [x, y, z]
            rx_position: 受信機位置 [x, y, z]
            tx_power_dbm: 送信電力 [dBm]

        Returns:
            Tuple[List[float], float, bool]:
                - path_powers_watts: 各パスの受信電力リスト [Watts]
                - delay_spread_ns: RMS遅延スプレッド [ns]
                - is_los: LOS判定
        """
        # 送信機・受信機を設定
        tx = sn.rt.Transmitter(
            name="tx",
            position=tx_position,
            orientation=[0, 0, 0]
        )
        tx.antenna = self.tx_array

        rx = sn.rt.Receiver(
            name="rx",
            position=rx_position,
            orientation=[0, 0, 0]
        )
        rx.antenna = self.rx_array

        # シーンに送受信機を追加
        self.scene.add(tx)
        self.scene.add(rx)

        # パス情報を抽出
        path_powers_watts = []
        delays_ns = []
        is_los = False

        try:
            # レイトレーシングを実行
            path_solver = self._path_solver
            if path_solver is None:
                try:
                    path_solver = sn.rt.PathSolver(num_samples=self.num_samples)
                except TypeError:
                    path_solver = sn.rt.PathSolver()
            paths = path_solver(scene=self.scene, max_depth=self.max_depth)

            def _as_tensor(value):
                if isinstance(value, (list, tuple)):
                    if not value:
                        return None
                    value = value[0]
                if tf.is_tensor(value):
                    return value
                return tf.convert_to_tensor(value)

            a_raw, tau_raw = paths.cir()
            a_tf = _as_tensor(a_raw)
            tau_tf = _as_tensor(tau_raw)

            if a_tf is not None and tau_tf is not None:
                # a: (num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time_steps)
                a_paths = a_tf[0, 0, 0, 0, :, :]
                path_gains = tf.reduce_sum(
                    tf.square(tf.abs(a_paths)),
                    axis=-1
                ).numpy()
                path_gains = np.atleast_1d(path_gains)

                tau_np = np.atleast_1d(np.squeeze(tau_tf.numpy()))
                if tau_np.ndim > 1:
                    tau_np = tau_np[..., 0]
                tau_paths = np.ravel(tau_np)

                tx_power_watts = dbm_to_watts(tx_power_dbm)
                num_paths = min(len(path_gains), len(tau_paths)) if len(tau_paths) else len(path_gains)
                for path_idx in range(num_paths):
                    path_gain = path_gains[path_idx]
                    if path_gain > 0:
                        path_power_watts = path_gain * tx_power_watts
                        path_powers_watts.append(float(path_power_watts))
                        if len(tau_paths) > path_idx:
                            delays_ns.append(float(tau_paths[path_idx] * 1e9))

            types_tf = None
            if hasattr(paths, "types") and paths.types is not None:
                types_tf = _as_tensor(paths.types)
            if types_tf is not None:
                types_np = np.squeeze(types_tf.numpy())
                if types_np.ndim > 1:
                    types_np = types_np[..., 0]
                is_los = bool(np.any(types_np == 0))
            elif len(path_powers_watts) > 0:
                # パスタイプがない場合は、最初のパスが最強ならLOSと仮定
                is_los = (path_powers_watts[0] == max(path_powers_watts))
        finally:
            # シーンから送受信機を削除（次の計算のため）
            self.scene.remove("tx")
            self.scene.remove("rx")

        # RMS遅延スプレッドを計算
        delay_spread_ns = 0.0
        if len(delays_ns) > 1 and len(path_powers_watts) > 0:
            powers = np.array(path_powers_watts)
            delays = np.array(delays_ns)
            total_power = np.sum(powers)
            if total_power > 0:
                mean_delay = np.sum(powers * delays) / total_power
                variance = np.sum(powers * (delays - mean_delay) ** 2) / total_power
                delay_spread_ns = float(np.sqrt(variance))
        elif len(delays_ns) == 1:
            delay_spread_ns = delays_ns[0]

        return path_powers_watts, delay_spread_ns, is_los

    def _check_single_building_occlusion(
        self,
        point1: List[float],
        point2: List[float],
        building: Building
    ) -> bool:
        """
        2点間の直線が単一建物と交差するかをチェック（Liang-Barskyアルゴリズム）

        Args:
            point1: 始点 [x, y, z]
            point2: 終点 [x, y, z]
            building: チェック対象の建物

        Returns:
            True: 遮蔽あり, False: 遮蔽なし
        """
        x1, y1 = point1[:2]
        x2, y2 = point2[:2]
        cx, cy = building.center[:2]
        w, d = building.size[:2]

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

    def _check_building_occlusion(
        self,
        point1: List[float],
        point2: List[float]
    ) -> bool:
        """
        2点間の直線がいずれかの建物と交差するかをチェック（複数建物対応）

        Args:
            point1: 始点 [x, y, z]
            point2: 終点 [x, y, z]

        Returns:
            True: 遮蔽あり, False: 遮蔽なし
        """
        for building in self.buildings:
            if self._check_single_building_occlusion(point1, point2, building):
                return True
        return False

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

        use_sionna_rt=Trueの場合: Sionna RTでマルチパス計算
        use_sionna_rt=Falseの場合: 簡易パスロスモデル（単一パス）

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
        # 距離計算（両モードで使用）
        distance = np.sqrt(
            (tx_position[0] - rx_position[0])**2 +
            (tx_position[1] - rx_position[1])**2 +
            (tx_position[2] - rx_position[2])**2
        )

        if self.use_sionna_rt:
            # ===== Sionna RTモード（マルチパス対応） =====
            path_powers_watts, delay_spread_ns, is_los = self._compute_paths_sionna(
                tx_position=tx_position,
                rx_position=rx_position,
                tx_power_dbm=tx_power_dbm
            )

            # パスが見つからない場合のフォールバック
            if len(path_powers_watts) == 0:
                # 簡易モデルで計算
                is_los = not self._check_building_occlusion(tx_position, rx_position)
                if distance > 1:
                    path_loss_db = (
                        20 * np.log10(distance) +
                        20 * np.log10(self.frequency_hz) +
                        20 * np.log10(4 * np.pi / 3e8)
                    )
                else:
                    path_loss_db = 40.0
                if not is_los:
                    path_loss_db += 15.0
                received_power_dbm = tx_power_dbm - path_loss_db
                path_powers_watts = [dbm_to_watts(received_power_dbm)]
                delay_spread_ns = distance / 3e8 * 1e9

            # D/K計算（マルチパス電力リストを渡す）
            dk_result = compute_dk(path_powers_watts)

            # 総受信電力からdBmとパスロスを計算
            p_tot_watts = dk_result["p_tot_watts"]
            received_power_dbm = watts_to_dbm(p_tot_watts)
            path_loss_db = tx_power_dbm - received_power_dbm

        else:
            # ===== 簡易モデル（単一パス） =====
            # 遮蔽判定
            is_los = not self._check_building_occlusion(tx_position, rx_position)

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

            # D/K計算（単一パス）
            received_power_watts = dbm_to_watts(received_power_dbm)
            dk_result = compute_dk([received_power_watts])

        return LinkQuality(
            timestamp=timestamp,
            link_type=link_type,
            tx_id=tx_id,
            rx_id=rx_id,
            received_power_dbm=received_power_dbm,
            delay_spread_ns=delay_spread_ns,
            path_loss_db=path_loss_db,
            is_line_of_sight=is_los,
            # D/K関連フィールド
            num_paths=dk_result["num_paths"],
            p_tot_watts=dk_result["p_tot_watts"],
            p_max_watts=dk_result["p_max_watts"],
            dominance=dk_result["dominance"],
            k_factor=dk_result["k_factor"],
            k_factor_db=dk_result["k_factor_db"],
            prop_mode=dk_result["prop_mode"]
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
