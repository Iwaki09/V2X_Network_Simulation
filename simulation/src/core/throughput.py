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

4. Mode-aware Fading Margin (推定列生成):
   フェージング理論に基づく保守的スループット推定
   - Rayleighフェージング（Dモード）: 下位p分位を保証するSNRマージン
   - Riceanフェージング（Kモード）: 固定の小マージン
   - 最適化の入力（estimate）と評価（truth）を分離
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Literal, Optional

from .mcs_model import (
    select_mcs,
    get_spectral_efficiency,
    calculate_mcs_throughput_mbps,
    print_mcs_table,
    MCS_SNR_THRESHOLDS_DB,
    MCS_SPECTRAL_EFFICIENCY,
)
from .beamforming import BeamformingConfig, compute_link_gains


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

# ============================================================
# Mode-aware Fading Margin (フェージング・マージン)
# ============================================================

# デフォルト設定
DEFAULT_MARGIN_P = 0.10        # 下位p分位 (10%)
DEFAULT_MARGIN_K_DB = 3.0      # Kモード用固定マージン [dB]


def calculate_rayleigh_fading_margin_db(p: float) -> float:
    """
    Rayleighフェージングの下位p分位を保証するSNRマージンを計算

    理論:
    Rayleighフェージングでは、瞬間SNR γ は平均SNR γ̄ に対して指数分布となり、
    下位p分位は γ_p = -γ̄ ln(1-p) で与えられる。

    平均SNRから下位p分位を保証するためのSNRバックオフ（マージン）は:
    M_Rayleigh(p) = 10 log10( 1 / (-ln(1-p)) ) [dB]

    Args:
        p: 目標信頼性（下位p分位を見込む）(0 < p < 1)
           例: 0.10 なら下位10%を保証

    Returns:
        フェージング・マージン [dB]

    Examples:
        >>> calculate_rayleigh_fading_margin_db(0.10)
        9.8...  # 約9.8 dB
        >>> calculate_rayleigh_fading_margin_db(0.05)
        12.8...  # 約12.8 dB
    """
    if p <= 0 or p >= 1:
        raise ValueError(f"p must be in (0, 1), got {p}")

    # M = 10 * log10(1 / (-ln(1-p)))
    margin_db = 10 * np.log10(1 / (-np.log(1 - p)))
    return margin_db


def get_fading_margin_for_mode(
    prop_mode: str,
    margin_p: float = DEFAULT_MARGIN_P,
    margin_k_db: float = DEFAULT_MARGIN_K_DB,
    margin_d_db_override: float = None
) -> float:
    """
    伝搬モード（D/K）に基づいてフェージング・マージンを取得

    - Dモード（支配的成分なし、Rayleigh寄り）: 計算されたRayleighマージン
    - Kモード（支配的成分あり、Ricean寄り）: 固定の小マージン
    - その他/欠損: 0 dB（保守的に扱う場合はDモードと同じにしてもよい）

    Args:
        prop_mode: 伝搬モード ("D" or "K" or その他)
        margin_p: Dモード用の目標信頼性（下位p分位）
        margin_k_db: Kモード用の固定マージン [dB]
        margin_d_db_override: Dモード用マージンを手動指定する場合（Noneなら計算）

    Returns:
        適用するマージン [dB]
    """
    if prop_mode == 'D':
        if margin_d_db_override is not None:
            return margin_d_db_override
        else:
            return calculate_rayleigh_fading_margin_db(margin_p)
    elif prop_mode == 'K':
        return margin_k_db
    else:
        # その他/欠損の場合は0 dB
        return 0.0


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
    rate_model: RateModel = 'shannon',
    enable_margin_estimate: bool = False,
    margin_p: float = DEFAULT_MARGIN_P,
    margin_k_db: float = DEFAULT_MARGIN_K_DB,
    margin_d_db_override: float = None,
    enable_beamforming: bool = True,
    beamforming_config: Optional[BeamformingConfig] = None
) -> pd.DataFrame:
    """
    リンク品質DataFrameに理論的スループットを追加

    Args:
        df: link_quality_results.csv から読み込んだDataFrame
            必須列: received_power (dBm)
            推定列生成時に必要: prop_mode
        rate_model: レートモデル ('shannon', 'mcs', 'both')
            - 'shannon': シャノン公式のみ（デフォルト、後方互換）
            - 'mcs': MCSベースのみ
            - 'both': 両方の列を出力
        enable_margin_estimate: 推定列生成を有効化（デフォルト: False）
        margin_p: Dモード用の目標信頼性（下位p分位）（デフォルト: 0.10）
        margin_k_db: Kモード用の固定マージン [dB]（デフォルト: 3.0）
        margin_d_db_override: Dモード用マージンを手動指定する場合（デフォルト: None）
        enable_beamforming: BF有効化（デフォルト: True）
        beamforming_config: BFパラメータ（Noneならデフォルト）

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

        推定列生成が有効な場合、さらに以下が追加:
        - margin_db_used: 適用したマージン値 [dB]
        - snr_db_eff_margin: マージン適用後の有効SNR [dB]
        - mcs_index_est: 推定（保守的）MCS index
        - throughput_mbps_mcs_est: 推定（保守的）MCSスループット [Mbps]

        BFが有効な場合、さらに以下が追加:
        - bf_tx_gain_db
        - bf_rx_gain_db
        - tx_element_gain_db
        - received_power_dbm_bf
        - snr_db_bf
        - theoretical_throughput_mbps_bf (shannon/both)
        - mcs_index_bf (mcs/both)
        - throughput_mbps_mcs_bf (mcs/both)
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

    if enable_beamforming:
        if beamforming_config is None:
            beamforming_config = BeamformingConfig()

        result_df['bf_tx_gain_db'] = 0.0
        result_df['bf_rx_gain_db'] = 0.0
        result_df['tx_element_gain_db'] = 0.0
        result_df['received_power_dbm_bf'] = result_df['received_power'].astype(float)

        required_angle_cols = ['aod_theta_deg', 'aod_phi_deg', 'aoa_theta_deg', 'aoa_phi_deg']
        missing_cols = [col for col in required_angle_cols if col not in result_df.columns]
        if missing_cols:
            print(f"⚠️  Beamforming: 角度列が不足しています: {missing_cols}")
            print("    AoD/AoAがないため、BF/素子利得は0dBとして計算します。")
        angles_available = not missing_cols

        link_type_col = result_df['link_type'] if 'link_type' in result_df.columns else None
        if link_type_col is not None:
            target_mask = link_type_col == 'V2I'
        else:
            target_mask = pd.Series([True] * len(result_df), index=result_df.index)

        if len(result_df[target_mask]) > 0 and angles_available:
            gains = result_df.loc[target_mask].apply(
                lambda row: compute_link_gains(
                    row['aod_theta_deg'],
                    row['aod_phi_deg'],
                    row['aoa_theta_deg'],
                    row['aoa_phi_deg'],
                    beamforming_config
                ),
                axis=1,
                result_type='expand'
            )
            gains.columns = ['bf_tx_gain_db', 'bf_rx_gain_db', 'tx_element_gain_db']
            result_df.loc[target_mask, gains.columns] = gains.values

        if angles_available:
            tx_power_adjust_db = 0.0
            if beamforming_config.rt_tx_power_dbm is not None:
                tx_power_adjust_db = beamforming_config.tx_power_dbm - beamforming_config.rt_tx_power_dbm

            result_df.loc[target_mask, 'received_power_dbm_bf'] = (
                result_df.loc[target_mask, 'received_power'].astype(float)
                + tx_power_adjust_db
                - beamforming_config.feeder_loss_db
                + result_df.loc[target_mask, 'tx_element_gain_db']
                + result_df.loc[target_mask, 'bf_tx_gain_db']
                + result_df.loc[target_mask, 'bf_rx_gain_db']
                + beamforming_config.ue_element_gain_db
            )

        received_power_watts_bf = (10 ** (result_df['received_power_dbm_bf'] / 10)) / 1000
        snr_bf = received_power_watts_bf / NOISE_POWER_WATTS
        result_df['snr_db_bf'] = 10 * np.log10(snr_bf)

        if rate_model in ('shannon', 'both'):
            theoretical_bps_bf = calculate_shannon_capacity(BANDWIDTH_HZ, snr_bf)
            result_df['theoretical_throughput_mbps_bf'] = theoretical_bps_bf / 1_000_000

        if rate_model in ('mcs', 'both'):
            result_df['mcs_index_bf'] = result_df['snr_db_bf'].apply(select_mcs)
            spectral_efficiency_bf = result_df['mcs_index_bf'].apply(get_spectral_efficiency)
            result_df['throughput_mbps_mcs_bf'] = spectral_efficiency_bf.apply(
                lambda se: calculate_mcs_throughput_mbps(BANDWIDTH_HZ, se)
            )

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

    # 推定列生成（enable_margin_estimate=Trueの場合）
    if enable_margin_estimate and rate_model in ('mcs', 'both'):
        # prop_mode列の存在確認
        if 'prop_mode' not in result_df.columns:
            raise ValueError(
                "推定列生成には 'prop_mode' 列が必要です。"
                "レイトレーシング結果に prop_mode が含まれていることを確認してください。"
            )

        # 各行のprop_modeに基づいてマージンを計算
        result_df['margin_db_used'] = result_df['prop_mode'].apply(
            lambda mode: get_fading_margin_for_mode(
                mode, margin_p, margin_k_db, margin_d_db_override
            )
        )

        # マージンを適用した有効SNR [dB]
        result_df['snr_db_eff_margin'] = result_df['snr_db'] - result_df['margin_db_used']

        # 有効SNRから推定MCSインデックスを計算
        result_df['mcs_index_est'] = result_df['snr_db_eff_margin'].apply(select_mcs)

        # 推定スペクトル効率を取得
        result_df['spectral_efficiency_bpshz_est'] = result_df['mcs_index_est'].apply(get_spectral_efficiency)

        # 推定MCSスループットを計算
        result_df['throughput_mbps_mcs_est'] = result_df['spectral_efficiency_bpshz_est'].apply(
            lambda se: calculate_mcs_throughput_mbps(BANDWIDTH_HZ, se)
        )

    return result_df


def process_link_quality_data(
    input_csv: str,
    output_csv: str,
    rate_model: RateModel = 'shannon',
    enable_margin_estimate: bool = False,
    margin_p: float = DEFAULT_MARGIN_P,
    margin_k_db: float = DEFAULT_MARGIN_K_DB,
    margin_d_db_override: float = None,
    enable_beamforming: bool = True,
    beamforming_config: Optional[BeamformingConfig] = None
):
    """
    リンク品質データから理論的スループットを計算

    Args:
        input_csv: 入力CSVファイルパス (link_quality_results.csv)
        output_csv: 出力CSVファイルパス (theoretical_network_results.csv)
        rate_model: レートモデル ('shannon', 'mcs', 'both')
        enable_margin_estimate: 推定列生成を有効化（デフォルト: False）
        margin_p: Dモード用の目標信頼性（下位p分位）（デフォルト: 0.10）
        margin_k_db: Kモード用の固定マージン [dB]（デフォルト: 3.0）
        margin_d_db_override: Dモード用マージンを手動指定する場合（デフォルト: None）
        enable_beamforming: BF有効化（デフォルト: True）
        beamforming_config: BFパラメータ（Noneならデフォルト）
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

    # フェージング・マージン設定（推定列生成が有効な場合）
    if enable_margin_estimate:
        print("\n【Mode-aware Fading Margin 設定】")
        print(f"  推定列生成:              有効")
        print(f"  目標信頼性 (p):          {margin_p:.2%} (下位{margin_p*100:.0f}%分位を保証)")
        if margin_d_db_override is not None:
            print(f"  Dモード用マージン:        {margin_d_db_override:.2f} dB (手動指定)")
        else:
            d_margin = calculate_rayleigh_fading_margin_db(margin_p)
            print(f"  Dモード用マージン:        {d_margin:.2f} dB (Rayleigh計算値)")
        print(f"  Kモード用マージン:        {margin_k_db:.2f} dB (固定値)")

    if enable_beamforming:
        if beamforming_config is None:
            beamforming_config = BeamformingConfig()
        print("\n【Beamforming 設定】")
        print(f"  BS配列:                  {beamforming_config.bs_num_rows}x{beamforming_config.bs_num_cols}")
        print(f"  UE配列:                  {beamforming_config.ue_num_rows}x{beamforming_config.ue_num_cols}")
        print(f"  素子間隔:                {beamforming_config.element_spacing_lambda:.2f} λ")
        print(f"  Tx電力 (PA):             {beamforming_config.tx_power_dbm:.2f} dBm")
        if beamforming_config.rt_tx_power_dbm is not None:
            print(f"  RT Tx電力:               {beamforming_config.rt_tx_power_dbm:.2f} dBm")
        print(f"  フィーダ損失:            {beamforming_config.feeder_loss_db:.2f} dB")
        print(f"  BS素子最大利得:          {beamforming_config.bs_element_gain_db:.2f} dBi")
        print(f"  UE素子利得:              {beamforming_config.ue_element_gain_db:.2f} dBi")

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
    if enable_margin_estimate:
        print("【計算中】Mode-aware Fading Margin を適用して推定列を生成...")

    df = calculate_theoretical_throughput(
        df,
        rate_model=rate_model,
        enable_margin_estimate=enable_margin_estimate,
        margin_p=margin_p,
        margin_k_db=margin_k_db,
        margin_d_db_override=margin_d_db_override,
        enable_beamforming=enable_beamforming,
        beamforming_config=beamforming_config
    )

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

    if enable_beamforming:
        v2i_mask = df['link_type'] == 'V2I' if 'link_type' in df.columns else pd.Series([True] * len(df))
        snr_delta = df.loc[v2i_mask, 'snr_db_bf'] - df.loc[v2i_mask, 'snr_db']
        print(f"  SNR (dB) [Beamforming ON]:")
        print(f"    - 平均: {df['snr_db_bf'].mean():.2f} dB")
        print(f"    - 最小: {df['snr_db_bf'].min():.2f} dB")
        print(f"    - 最大: {df['snr_db_bf'].max():.2f} dB")
        print(f"    - Δ平均 (BF-Base, V2I): {snr_delta.mean():.2f} dB")
        print()

        if snr_delta.median() > 50.0 or df['snr_db_bf'].max() > 80.0:
            print("⚠️  BF適用後のSNRが非常に高い可能性があります。")
            print("    RT出力にアンテナ利得が含まれている場合は二重計上の可能性を確認してください。")
            print()

        def _print_quantile_stats(title: str, series: pd.Series) -> None:
            print(f"  {title}:")
            print(f"    - 平均:   {series.mean():.2f}")
            print(f"    - 中央値: {series.median():.2f}")
            print(f"    - P05:    {series.quantile(0.05):.2f}")
            print(f"    - P95:    {series.quantile(0.95):.2f}")
            print()

        print("  【BF OFF vs ON 統計比較】")
        _print_quantile_stats("SNR (OFF) [dB]", df['snr_db'])
        _print_quantile_stats("SNR (ON)  [dB]", df['snr_db_bf'])
        if 'throughput_mbps_mcs' in df.columns and 'throughput_mbps_mcs_bf' in df.columns:
            print("  Throughput (MCS) [Mbps]:")
            print(f"    - OFF 平均:   {df['throughput_mbps_mcs'].mean():.2f}")
            print(f"    - OFF 中央値: {df['throughput_mbps_mcs'].median():.2f}")
            print(f"    - OFF P05:    {df['throughput_mbps_mcs'].quantile(0.05):.2f}")
            print(f"    - ON 平均:    {df['throughput_mbps_mcs_bf'].mean():.2f}")
            print(f"    - ON 中央値:  {df['throughput_mbps_mcs_bf'].median():.2f}")
            print(f"    - ON P05:     {df['throughput_mbps_mcs_bf'].quantile(0.05):.2f}")
            print()

    # Shannon統計（shannon/bothモード）
    if rate_model in ('shannon', 'both'):
        print(f"  理論的スループット - Shannon (Mbps):")
        print(f"    - 平均: {df['theoretical_throughput_mbps'].mean():.2f} Mbps")
        print(f"    - 最小: {df['theoretical_throughput_mbps'].min():.2f} Mbps")
        print(f"    - 最大: {df['theoretical_throughput_mbps'].max():.2f} Mbps")
        print()
        if enable_beamforming and 'theoretical_throughput_mbps_bf' in df.columns:
            print(f"  理論的スループット - Shannon (BF) (Mbps):")
            print(f"    - 平均: {df['theoretical_throughput_mbps_bf'].mean():.2f} Mbps")
            print(f"    - 最小: {df['theoretical_throughput_mbps_bf'].min():.2f} Mbps")
            print(f"    - 最大: {df['theoretical_throughput_mbps_bf'].max():.2f} Mbps")
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
        if enable_beamforming and 'throughput_mbps_mcs_bf' in df.columns:
            print(f"  理論的スループット - MCS (BF) (Mbps):")
            print(f"    - 平均: {df['throughput_mbps_mcs_bf'].mean():.2f} Mbps")
            print(f"    - 最小: {df['throughput_mbps_mcs_bf'].min():.2f} Mbps")
            print(f"    - 最大: {df['throughput_mbps_mcs_bf'].max():.2f} Mbps")
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
        if enable_beamforming and 'throughput_mbps_mcs_bf' in df.columns:
            shannon_bf_avg = df['theoretical_throughput_mbps_bf'].mean()
            mcs_bf_avg = df['throughput_mbps_mcs_bf'].mean()
            ratio_bf = mcs_bf_avg / shannon_bf_avg * 100 if shannon_bf_avg > 0 else 0
            print("  【Shannon vs MCS 比較 (BF)】")
            print(f"    - Shannon平均: {shannon_bf_avg:.2f} Mbps")
            print(f"    - MCS平均:     {mcs_bf_avg:.2f} Mbps")
            print(f"    - MCS/Shannon: {ratio_bf:.1f}%")
            print()

    # 推定列の統計情報を表示
    if enable_margin_estimate and rate_model in ('mcs', 'both'):
        print("  【推定列（Mode-aware Margin適用後）統計】")

        # prop_mode別マージン統計
        print(f"  適用マージン [dB]:")
        mode_margin_stats = df.groupby('prop_mode')['margin_db_used'].agg(['count', 'mean'])
        for mode, stats in mode_margin_stats.iterrows():
            print(f"    - {mode}モード: {stats['mean']:.2f} dB (n={int(stats['count'])})")
        print()

        # 推定MCSインデックス分布
        print(f"  推定MCSインデックス分布:")
        mcs_est_counts = df['mcs_index_est'].value_counts().sort_index()
        for mcs_idx, count in mcs_est_counts.items():
            se = MCS_SPECTRAL_EFFICIENCY[mcs_idx]
            print(f"    - MCS {mcs_idx} (SE={se:.2f}): {count} リンク ({100*count/len(df):.1f}%)")
        print()

        # 推定スループット統計
        print(f"  推定スループット (Mbps):")
        print(f"    - 平均: {df['throughput_mbps_mcs_est'].mean():.2f} Mbps")
        print(f"    - 最小: {df['throughput_mbps_mcs_est'].min():.2f} Mbps")
        print(f"    - 最大: {df['throughput_mbps_mcs_est'].max():.2f} Mbps")
        print()

        # truth vs estimate 比較
        print(f"  【Truth vs Estimate 比較】")
        truth_avg = df['throughput_mbps_mcs'].mean()
        est_avg = df['throughput_mbps_mcs_est'].mean()
        ratio_est = est_avg / truth_avg * 100 if truth_avg > 0 else 0
        print(f"    - Truth平均:    {truth_avg:.2f} Mbps")
        print(f"    - Estimate平均: {est_avg:.2f} Mbps")
        print(f"    - Est/Truth:    {ratio_est:.1f}% (保守化率: {100-ratio_est:.1f}%)")
        print()

    if enable_beamforming:
        print("【保存前処理】BF結果で主要列を上書きして保存します。")
        df['received_power'] = df['received_power_dbm_bf']
        df['received_power_watts'] = df['received_power_dbm_bf'].apply(dbm_to_watts)
        df['snr'] = df['received_power_watts'].apply(
            lambda p: calculate_snr(p, NOISE_POWER_WATTS)
        )
        df['snr_db'] = 10 * np.log10(df['snr'])
        if rate_model in ('shannon', 'both'):
            df['theoretical_throughput_bps'] = df['theoretical_throughput_mbps_bf'] * 1_000_000
            df['theoretical_throughput_mbps'] = df['theoretical_throughput_mbps_bf']
        if rate_model in ('mcs', 'both'):
            df['mcs_index'] = df['mcs_index_bf']
            df['spectral_efficiency_bpshz'] = df['mcs_index'].apply(get_spectral_efficiency)
            df['throughput_mbps_mcs'] = df['throughput_mbps_mcs_bf']

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
