"""
V2V通信チャネルモデル

距離ベースのパスロスモデルを使用して通信品質を計算
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class ChannelParameters:
    """通信チャネルのパラメータ"""
    frequency: float = 5.9e9  # 周波数 (Hz) - V2X専用帯域
    tx_power_dbm: float = 20.0  # 送信電力 (dBm)
    tx_antenna_gain_dbi: float = 3.0  # 送信アンテナゲイン (dBi)
    rx_antenna_gain_dbi: float = 3.0  # 受信アンテナゲイン (dBi)
    noise_floor_dbm: float = -95.0  # ノイズフロア (dBm)
    path_loss_exponent: float = 2.5  # パスロス指数
    max_range_m: float = 300.0  # 最大通信距離 (m)
    min_snr_db: float = 5.0  # 最小SNR閾値 (dB)


class ChannelModel:
    """V2V通信チャネルモデル"""

    def __init__(self, params: ChannelParameters = None):
        """
        初期化

        Args:
            params: チャネルパラメータ
        """
        self.params = params if params else ChannelParameters()

    def calculate_free_space_path_loss(self, distance_m: float) -> float:
        """
        自由空間パスロスを計算 (Friis伝送公式)

        Args:
            distance_m: 距離 (m)

        Returns:
            パスロス (dB)
        """
        if distance_m < 1.0:
            distance_m = 1.0  # 最小距離を1mに設定

        # 波長 (m)
        wavelength = 3e8 / self.params.frequency

        # 自由空間パスロス (dB)
        path_loss_db = 20 * np.log10(4 * np.pi * distance_m / wavelength)

        return path_loss_db

    def calculate_log_distance_path_loss(self, distance_m: float, reference_distance_m: float = 1.0) -> float:
        """
        対数距離パスロスモデル

        Args:
            distance_m: 距離 (m)
            reference_distance_m: 参照距離 (m)

        Returns:
            パスロス (dB)
        """
        if distance_m < reference_distance_m:
            distance_m = reference_distance_m

        # 参照距離でのパスロス
        pl0 = self.calculate_free_space_path_loss(reference_distance_m)

        # 対数距離パスロスモデル
        path_loss_db = pl0 + 10 * self.params.path_loss_exponent * np.log10(distance_m / reference_distance_m)

        return path_loss_db

    def calculate_received_power(self, distance_m: float) -> float:
        """
        受信電力を計算

        Args:
            distance_m: 距離 (m)

        Returns:
            受信電力 (dBm)
        """
        # パスロス
        path_loss = self.calculate_log_distance_path_loss(distance_m)

        # 受信電力 = 送信電力 + 送信アンテナゲイン + 受信アンテナゲイン - パスロス
        rx_power_dbm = (
            self.params.tx_power_dbm +
            self.params.tx_antenna_gain_dbi +
            self.params.rx_antenna_gain_dbi -
            path_loss
        )

        return rx_power_dbm

    def calculate_snr(self, distance_m: float) -> float:
        """
        SNR (Signal-to-Noise Ratio) を計算

        Args:
            distance_m: 距離 (m)

        Returns:
            SNR (dB)
        """
        rx_power = self.calculate_received_power(distance_m)
        snr_db = rx_power - self.params.noise_floor_dbm

        return snr_db

    def calculate_data_rate(self, snr_db: float, bandwidth_mhz: float = 10.0) -> float:
        """
        データレートを推定 (Shannon容量の簡易版)

        Args:
            snr_db: SNR (dB)
            bandwidth_mhz: 帯域幅 (MHz)

        Returns:
            データレート (Mbps)
        """
        # SNRをリニアスケールに変換
        snr_linear = 10 ** (snr_db / 10)

        # Shannon容量 (bps)
        capacity_bps = bandwidth_mhz * 1e6 * np.log2(1 + snr_linear)

        # Mbpsに変換
        capacity_mbps = capacity_bps / 1e6

        return capacity_mbps

    def is_link_available(self, distance_m: float) -> bool:
        """
        通信リンクが利用可能かどうかを判定

        Args:
            distance_m: 距離 (m)

        Returns:
            True: 通信可能、False: 通信不可
        """
        if distance_m > self.params.max_range_m:
            return False

        snr = self.calculate_snr(distance_m)
        if snr < self.params.min_snr_db:
            return False

        return True

    def calculate_link_quality(self, distance_m: float) -> Dict[str, float]:
        """
        リンク品質を計算

        Args:
            distance_m: 距離 (m)

        Returns:
            リンク品質情報 (distance, path_loss, rx_power, snr, data_rate, available)
        """
        path_loss = self.calculate_log_distance_path_loss(distance_m)
        rx_power = self.calculate_received_power(distance_m)
        snr = self.calculate_snr(distance_m)
        data_rate = self.calculate_data_rate(snr) if snr > 0 else 0.0
        available = self.is_link_available(distance_m)

        return {
            'distance': distance_m,
            'path_loss': path_loss,
            'rx_power': rx_power,
            'snr': snr,
            'data_rate': data_rate,
            'available': available
        }

    def calculate_channel_matrix(self, positions: Dict[str, np.ndarray]) -> Tuple[np.ndarray, Dict]:
        """
        車両間のチャネル行列を計算

        Args:
            positions: 車両IDと位置のマッピング {veh_id: np.array([x, y])}

        Returns:
            (channel_matrix, vehicle_ids_map)
            - channel_matrix: N×Nのチャネル品質行列 (SNR値)
            - vehicle_ids_map: インデックスから車両IDへのマッピング
        """
        vehicle_ids = sorted(positions.keys())
        n_vehicles = len(vehicle_ids)

        # チャネル行列を初期化
        channel_matrix = np.zeros((n_vehicles, n_vehicles))
        distance_matrix = np.zeros((n_vehicles, n_vehicles))

        # 各車両ペアの距離とSNRを計算
        for i, veh_i in enumerate(vehicle_ids):
            for j, veh_j in enumerate(vehicle_ids):
                if i == j:
                    # 自分自身との距離は0、SNRは無限大（実際は使わない）
                    distance_matrix[i, j] = 0.0
                    channel_matrix[i, j] = np.inf
                else:
                    # 距離を計算
                    distance = np.linalg.norm(positions[veh_i] - positions[veh_j])
                    distance_matrix[i, j] = distance

                    # SNRを計算
                    if self.is_link_available(distance):
                        snr = self.calculate_snr(distance)
                        channel_matrix[i, j] = snr
                    else:
                        # 通信不可の場合は-無限大
                        channel_matrix[i, j] = -np.inf

        # 車両IDマッピング
        vehicle_ids_map = {i: veh_id for i, veh_id in enumerate(vehicle_ids)}

        return channel_matrix, vehicle_ids_map, distance_matrix


if __name__ == "__main__":
    # テストコード
    params = ChannelParameters()
    model = ChannelModel(params)

    print("V2V Channel Model Test")
    print("=" * 60)
    print(f"Frequency: {params.frequency / 1e9:.1f} GHz")
    print(f"TX Power: {params.tx_power_dbm} dBm")
    print(f"Max Range: {params.max_range_m} m")
    print(f"Min SNR: {params.min_snr_db} dB")
    print()

    # 各距離でのリンク品質を計算
    distances = [10, 50, 100, 150, 200, 250, 300]
    print(f"{'Distance (m)':<15} {'RX Power (dBm)':<20} {'SNR (dB)':<15} {'Data Rate (Mbps)':<20} {'Available':<10}")
    print("-" * 90)

    for d in distances:
        quality = model.calculate_link_quality(d)
        print(f"{quality['distance']:<15.0f} {quality['rx_power']:<20.2f} {quality['snr']:<15.2f} "
              f"{quality['data_rate']:<20.2f} {'Yes' if quality['available'] else 'No':<10}")

    print()
    print("=" * 60)

    # チャネル行列のテスト
    test_positions = {
        'veh0': np.array([0.0, 0.0]),
        'veh1': np.array([50.0, 0.0]),
        'veh2': np.array([100.0, 0.0]),
        'veh3': np.array([200.0, 0.0])
    }

    channel_matrix, veh_map, dist_matrix = model.calculate_channel_matrix(test_positions)

    print("\nTest Vehicle Positions:")
    for veh_id, pos in test_positions.items():
        print(f"  {veh_id}: ({pos[0]:.1f}, {pos[1]:.1f})")

    print("\nDistance Matrix (m):")
    print(dist_matrix)

    print("\nChannel Matrix (SNR in dB):")
    print(channel_matrix)
