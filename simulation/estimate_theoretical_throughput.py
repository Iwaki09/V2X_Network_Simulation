"""
理論的スループット計算スクリプト

SUMO + SIONNA RT統合シミュレーションの出力 (link_quality_results.csv) から、
シャノンのチャネル容量公式を用いて各リンクの理論的最大スループットを計算します。

計算式: C = B * log2(1 + SNR)
- C: チャネル容量 [bps]
- B: 帯域幅 [Hz]
- SNR: 信号対雑音比 (Signal-to-Noise Ratio)
"""

import pandas as pd
import numpy as np


# ============================================================
# シミュレーション前提条件 (論文執筆用)
# ============================================================

# 1. 帯域幅 (Bandwidth):
# V2IおよびV2Vの各リンクが利用可能な周波数帯域幅。
# ここでは 100 MHz (ミリ波帯の標準的な値) と仮定する。
BANDWIDTH_HZ = 100e6  # 100 MHz (100 * 10^6 Hz)

# 2. 熱雑音 (Thermal Noise):
# 受信機のノイズレベルを計算するためのパラメータ。
BOLTZMANN_CONSTANT = 1.38e-23  # ボルツマン定数 (J/K)
NOISE_TEMPERATURE_K = 290.0    # 受信機の絶対温度 (Kelvin). 290K (約17°C) を標準値とする。

# --- 定数の計算 ---

# 熱雑音電力 P_N (Watts) の計算
# P_N = k_B * T * B
NOISE_POWER_WATTS = BOLTZMANN_CONSTANT * NOISE_TEMPERATURE_K * BANDWIDTH_HZ

# 熱雑音電力 P_N (dBm) の計算
# P_N (mW) = P_N (Watts) * 1000
# P_N (dBm) = 10 * log10(P_N (mW))
NOISE_POWER_DBM = 10 * np.log10(NOISE_POWER_WATTS * 1000)

print("=" * 70)
print("理論的スループット計算 (シャノン公式ベース)")
print("=" * 70)
print("\n【シミュレーション前提条件】")
print(f"  帯域幅 (B):              {BANDWIDTH_HZ / 1e6:.1f} MHz")
print(f"  受信機温度 (T):          {NOISE_TEMPERATURE_K:.1f} K")
print(f"  ボルツマン定数 (k_B):     {BOLTZMANN_CONSTANT:.2e} J/K")
print(f"  熱雑音電力 (P_N):         {NOISE_POWER_DBM:.2f} dBm ({NOISE_POWER_WATTS:.2e} W)")
print()

# ============================================================


def dbm_to_watts(power_dbm: float) -> float:
    """
    dBm を Watts に変換

    Args:
        power_dbm: 電力 [dBm]

    Returns:
        電力 [Watts]
    """
    return (10 ** (power_dbm / 10)) / 1000


def calculate_snr(received_power_watts: float, noise_power_watts: float) -> float:
    """
    SNR (Signal-to-Noise Ratio) を計算

    研究上の仮定 (Assumption):
    本シミュレーションでは、他の車両や基地局からの「干渉電力 (Interference)」は 0 と仮定する。
    したがって、SINR (信号対干渉雑音電力比) は SNR (信号対雑音電力比) と近似的に等しい (SINR ≈ SNR) ものとして計算する。
    SNR = 受信電力 (P_r) / 熱雑音電力 (P_N)

    Args:
        received_power_watts: 受信電力 [Watts]
        noise_power_watts: 熱雑音電力 [Watts]

    Returns:
        SNR (線形値)
    """
    return received_power_watts / noise_power_watts


def calculate_shannon_capacity(bandwidth_hz: float, snr: float) -> float:
    """
    シャノンのチャネル容量公式を用いてスループットを計算

    C = B * log2(1 + SNR)

    Args:
        bandwidth_hz: 帯域幅 [Hz]
        snr: 信号対雑音比 (線形値)

    Returns:
        チャネル容量 [bps]
    """
    return bandwidth_hz * np.log2(1 + snr)


def process_link_quality_data(input_csv: str, output_csv: str):
    """
    リンク品質データから理論的スループットを計算

    Args:
        input_csv: 入力CSVファイルパス (link_quality_results.csv)
        output_csv: 出力CSVファイルパス (theoretical_network_results.csv)
    """
    print("【処理開始】")
    print(f"  入力ファイル: {input_csv}")
    print()

    # CSVファイルを読み込む
    df = pd.read_csv(input_csv)
    print(f"✅ データ読み込み完了: {len(df)} レコード")
    print(f"   - V2Iリンク数: {len(df[df['link_type'] == 'V2I'])}")
    print(f"   - V2Vリンク数: {len(df[df['link_type'] == 'V2V'])}")
    print()

    # dBm → Watts への変換
    print("【計算中】受信電力を dBm → Watts に変換...")
    df['received_power_watts'] = df['received_power'].apply(dbm_to_watts)

    # SNR の計算
    print("【計算中】SNR (信号対雑音比) を計算...")
    df['snr'] = df['received_power_watts'].apply(
        lambda p: calculate_snr(p, NOISE_POWER_WATTS)
    )

    # SNR (dB) の計算（可視化用）
    df['snr_db'] = 10 * np.log10(df['snr'])

    # 理論的スループットの計算（シャノン公式）
    print("【計算中】シャノン公式でスループットを計算...")
    df['theoretical_throughput_bps'] = df['snr'].apply(
        lambda snr: calculate_shannon_capacity(BANDWIDTH_HZ, snr)
    )

    # Mbps に変換
    df['theoretical_throughput_mbps'] = df['theoretical_throughput_bps'] / 1_000_000

    print("✅ 計算完了")
    print()

    # 統計情報を表示
    print("【統計情報】")
    print(f"  受信電力 (dBm):")
    print(f"    - 平均: {df['received_power'].mean():.2f} dBm")
    print(f"    - 最小: {df['received_power'].min():.2f} dBm")
    print(f"    - 最大: {df['received_power'].max():.2f} dBm")
    print()
    print(f"  SNR (dB):")
    print(f"    - 平均: {df['snr_db'].mean():.2f} dB")
    print(f"    - 最小: {df['snr_db'].min():.2f} dB")
    print(f"    - 最大: {df['snr_db'].max():.2f} dB")
    print()
    print(f"  理論的スループット (Mbps):")
    print(f"    - 平均: {df['theoretical_throughput_mbps'].mean():.2f} Mbps")
    print(f"    - 最小: {df['theoretical_throughput_mbps'].min():.2f} Mbps")
    print(f"    - 最大: {df['theoretical_throughput_mbps'].max():.2f} Mbps")
    print()

    # CSVファイルに保存
    df.to_csv(output_csv, index=False)
    print(f"✅ 出力ファイル保存完了: {output_csv}")
    print()
    print("=" * 70)


def main():
    """メイン処理"""
    input_csv = 'output/raytracing/link_quality_results.csv'
    output_csv = 'output/throughput/theoretical_network_results.csv'

    process_link_quality_data(input_csv, output_csv)


if __name__ == "__main__":
    main()
