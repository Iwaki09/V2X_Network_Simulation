"""
理論的スループット計算モジュール

2つのレートモデルをサポート:

1. Shannon（デフォルト）:
   シャノンのチャネル容量公式を用いて理論的最大スループットを計算
   計算式: C = B * log2(1 + SNR)

2. MCS（Modulation and Coding Scheme）:
   離散的なMCSテーブルによるレート選択
   SNR閾値ベースでMCSを選択し、対応するスペクトル効率からスループットを計算

3. both:
   ShannonとMCS両方の列を出力し比較可能にする
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Literal

from .mcs_model import (
    select_mcs,
    get_spectral_efficiency,
    calculate_mcs_throughput_mbps,
    print_mcs_table,
    MCS_SNR_THRESHOLDS_DB,
    MCS_SPECTRAL_EFFICIENCY,
)


# ============================================================
# シミュレーション前提条件
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


def dbm_to_watts(power_dbm: float) -> float:
    """
    dBm を Watts に変換

    Args:
        power_dbm: 電力 [dBm]

    Returns:
        電力 [Watts]
    """
    return (10 ** (power_dbm / 10)) / 1000


def calculate_snr(received_power_watts: float, noise_power_watts: float = NOISE_POWER_WATTS) -> float:
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


# レートモデルの型定義
RateModel = Literal['shannon', 'mcs', 'both']


def calculate_theoretical_throughput(
    df: pd.DataFrame,
    rate_model: RateModel = 'shannon'
) -> pd.DataFrame:
    """
    リンク品質DataFrameに理論的スループットを追加

    Args:
        df: link_quality_results.csv から読み込んだDataFrame
            必須列: received_power (dBm)
        rate_model: レートモデル ('shannon', 'mcs', 'both')
            - 'shannon': シャノン公式のみ（デフォルト、後方互換）
            - 'mcs': MCSベースのみ
            - 'both': 両方の列を出力

    Returns:
        以下の列が追加されたDataFrame:
        - received_power_watts
        - snr
        - snr_db
        - theoretical_throughput_bps (shannon/both)
        - theoretical_throughput_mbps (shannon/both)
        - mcs_index (mcs/both)
        - spectral_efficiency_bpshz (mcs/both)
        - throughput_mbps_mcs (mcs/both)
    """
    result_df = df.copy()

    # dBm → Watts への変換
    result_df['received_power_watts'] = result_df['received_power'].apply(dbm_to_watts)

    # SNR の計算
    result_df['snr'] = result_df['received_power_watts'].apply(
        lambda p: calculate_snr(p, NOISE_POWER_WATTS)
    )

    # SNR (dB) の計算（可視化用）
    result_df['snr_db'] = 10 * np.log10(result_df['snr'])

    # Shannon計算（shannon または both モード）
    if rate_model in ('shannon', 'both'):
        result_df['theoretical_throughput_bps'] = result_df['snr'].apply(
            lambda snr: calculate_shannon_capacity(BANDWIDTH_HZ, snr)
        )
        result_df['theoretical_throughput_mbps'] = result_df['theoretical_throughput_bps'] / 1_000_000

    # MCS計算（mcs または both モード）
    if rate_model in ('mcs', 'both'):
        # MCSインデックスを選択
        result_df['mcs_index'] = result_df['snr_db'].apply(select_mcs)

        # スペクトル効率を取得
        result_df['spectral_efficiency_bpshz'] = result_df['mcs_index'].apply(get_spectral_efficiency)

        # MCSベーススループットを計算
        result_df['throughput_mbps_mcs'] = result_df['spectral_efficiency_bpshz'].apply(
            lambda se: calculate_mcs_throughput_mbps(BANDWIDTH_HZ, se)
        )

    return result_df


def process_link_quality_data(
    input_csv: str,
    output_csv: str,
    rate_model: RateModel = 'shannon'
):
    """
    リンク品質データから理論的スループットを計算

    Args:
        input_csv: 入力CSVファイルパス (link_quality_results.csv)
        output_csv: 出力CSVファイルパス (theoretical_network_results.csv)
        rate_model: レートモデル ('shannon', 'mcs', 'both')
    """
    rate_model_names = {
        'shannon': 'シャノン公式ベース',
        'mcs': 'MCS（離散レート）ベース',
        'both': 'シャノン + MCS 比較モード'
    }

    print("=" * 70)
    print(f"理論的スループット計算 ({rate_model_names.get(rate_model, rate_model)})")
    print("=" * 70)
    print("\n【シミュレーション前提条件】")
    print(f"  帯域幅 (B):              {BANDWIDTH_HZ / 1e6:.1f} MHz")
    print(f"  受信機温度 (T):          {NOISE_TEMPERATURE_K:.1f} K")
    print(f"  ボルツマン定数 (k_B):     {BOLTZMANN_CONSTANT:.2e} J/K")
    print(f"  熱雑音電力 (P_N):         {NOISE_POWER_DBM:.2f} dBm ({NOISE_POWER_WATTS:.2e} W)")

    # MCSテーブルを表示（mcsまたはbothモード）
    if rate_model in ('mcs', 'both'):
        print_mcs_table()

    print()
    print("【処理開始】")
    print(f"  入力ファイル: {input_csv}")
    print(f"  レートモデル: {rate_model}")
    print()

    # CSVファイルを読み込む
    df = pd.read_csv(input_csv)
    print(f"✅ データ読み込み完了: {len(df)} レコード")
    print(f"   - V2Iリンク数: {len(df[df['link_type'] == 'V2I'])}")
    print(f"   - V2Vリンク数: {len(df[df['link_type'] == 'V2V'])}")
    print()

    # スループット計算
    print("【計算中】受信電力を dBm → Watts に変換...")
    print("【計算中】SNR (信号対雑音比) を計算...")

    if rate_model in ('shannon', 'both'):
        print("【計算中】シャノン公式でスループットを計算...")
    if rate_model in ('mcs', 'both'):
        print("【計算中】MCSベースでスループットを計算...")

    df = calculate_theoretical_throughput(df, rate_model=rate_model)

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

    # Shannon統計（shannon/bothモード）
    if rate_model in ('shannon', 'both'):
        print(f"  理論的スループット - Shannon (Mbps):")
        print(f"    - 平均: {df['theoretical_throughput_mbps'].mean():.2f} Mbps")
        print(f"    - 最小: {df['theoretical_throughput_mbps'].min():.2f} Mbps")
        print(f"    - 最大: {df['theoretical_throughput_mbps'].max():.2f} Mbps")
        print()

    # MCS統計（mcs/bothモード）
    if rate_model in ('mcs', 'both'):
        print(f"  MCSインデックス分布:")
        mcs_counts = df['mcs_index'].value_counts().sort_index()
        for mcs_idx, count in mcs_counts.items():
            se = MCS_SPECTRAL_EFFICIENCY[mcs_idx]
            print(f"    - MCS {mcs_idx} (SE={se:.2f}): {count} リンク ({100*count/len(df):.1f}%)")
        print()
        print(f"  理論的スループット - MCS (Mbps):")
        print(f"    - 平均: {df['throughput_mbps_mcs'].mean():.2f} Mbps")
        print(f"    - 最小: {df['throughput_mbps_mcs'].min():.2f} Mbps")
        print(f"    - 最大: {df['throughput_mbps_mcs'].max():.2f} Mbps")
        print()

    # bothモードの場合、比較を表示
    if rate_model == 'both':
        print("  【Shannon vs MCS 比較】")
        shannon_avg = df['theoretical_throughput_mbps'].mean()
        mcs_avg = df['throughput_mbps_mcs'].mean()
        ratio = mcs_avg / shannon_avg * 100 if shannon_avg > 0 else 0
        print(f"    - Shannon平均: {shannon_avg:.2f} Mbps")
        print(f"    - MCS平均:     {mcs_avg:.2f} Mbps")
        print(f"    - MCS/Shannon: {ratio:.1f}%")
        print()

    # CSVファイルに保存
    df.to_csv(output_csv, index=False)
    print(f"✅ 出力ファイル保存完了: {output_csv}")
    print()
    print("=" * 70)


def main():
    """メイン処理"""
    script_dir = Path(__file__).parent.parent.parent
    input_csv = str(script_dir / 'output/data/raytracing/link_quality_results.csv')
    output_csv = str(script_dir / 'output/data/throughput/theoretical_network_results.csv')

    process_link_quality_data(input_csv, output_csv)


if __name__ == "__main__":
    main()
