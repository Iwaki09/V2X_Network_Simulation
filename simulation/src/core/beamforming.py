"""
ビームフォーミング計算ユーティリティ

- 3GPP TR 38.901の素子パターン（Table 7.3-1）に基づく利得計算
- UPA/ULAの配列応答と理想ビーム利得の算出
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class BeamformingConfig:
    """ビームフォーミング関連パラメータ"""
    bs_num_rows: int = 16
    bs_num_cols: int = 16
    ue_num_rows: int = 1
    ue_num_cols: int = 10
    element_spacing_lambda: float = 0.5
    bs_element_gain_db: float = 8.0
    ue_element_gain_db: float = 0.0
    tx_power_dbm: float = 40.0
    feeder_loss_db: float = 3.0
    theta_3db: float = 65.0
    phi_3db: float = 65.0
    sla_v: float = 30.0
    a_m: float = 30.0
    rt_tx_power_dbm: Optional[float] = None


def wrap_phi_deg(phi_deg: float) -> float:
    """方位角を[-180, 180]に正規化"""
    return (phi_deg + 180.0) % 360.0 - 180.0


def element_pattern_tr38901_gain_db(
    theta_deg: float,
    phi_deg: float,
    g_max_db: float,
    theta_3db: float,
    phi_3db: float,
    sla_v: float,
    a_m: float
) -> float:
    """3GPP TR 38.901素子パターン利得 [dBi]"""
    phi_deg = wrap_phi_deg(phi_deg)
    a_v = min(12.0 * ((theta_deg - 90.0) / theta_3db) ** 2, sla_v)
    a_h = min(12.0 * (phi_deg / phi_3db) ** 2, a_m)
    attenuation = min(a_v + a_h, a_m)
    return g_max_db - attenuation


def array_response_upa(
    num_rows: int,
    num_cols: int,
    spacing_lambda: float,
    theta_deg: float,
    phi_deg: float
) -> np.ndarray:
    """
    UPAの配列応答ベクトル

    前提:
    - 配列面: y-z平面 (boresightは +x 方向)
    - theta: zenith (0=+z), phi: azimuth (0=+x, +yへ反時計回り)
    """
    theta_rad = np.deg2rad(theta_deg)
    phi_rad = np.deg2rad(phi_deg)
    k_y = np.sin(theta_rad) * np.sin(phi_rad)
    k_z = np.cos(theta_rad)

    row_idx = np.arange(num_rows).reshape(-1, 1)
    col_idx = np.arange(num_cols).reshape(1, -1)
    phase = 2.0 * np.pi * spacing_lambda * (row_idx * k_z + col_idx * k_y)
    return np.exp(1j * phase).ravel()


def beamforming_gain_db(
    num_rows: int,
    num_cols: int,
    spacing_lambda: float,
    theta_deg: float,
    phi_deg: float
) -> float:
    """理想ビーム指向時の配列利得 [dB]"""
    if num_rows <= 0 or num_cols <= 0:
        return 0.0
    if num_rows * num_cols == 1:
        return 0.0

    steering = array_response_upa(
        num_rows=num_rows,
        num_cols=num_cols,
        spacing_lambda=spacing_lambda,
        theta_deg=theta_deg,
        phi_deg=phi_deg
    )
    norm = np.linalg.norm(steering)
    if norm == 0:
        return 0.0
    w = steering / norm
    gain_linear = float(np.abs(np.vdot(w, steering)) ** 2)
    if gain_linear <= 0:
        return 0.0
    return 10.0 * np.log10(gain_linear)


def safe_float(value: Optional[float]) -> Optional[float]:
    """NaNやNoneを弾く簡易ヘルパー"""
    if value is None:
        return None
    try:
        if np.isnan(value):
            return None
    except TypeError:
        pass
    return float(value)


def compute_link_gains(
    aod_theta_deg: Optional[float],
    aod_phi_deg: Optional[float],
    aoa_theta_deg: Optional[float],
    aoa_phi_deg: Optional[float],
    config: BeamformingConfig
) -> Tuple[float, float, float]:
    """単一リンクのBF/素子利得 (tx_bf, rx_bf, tx_element) を計算"""
    aod_theta_deg = safe_float(aod_theta_deg)
    aod_phi_deg = safe_float(aod_phi_deg)
    aoa_theta_deg = safe_float(aoa_theta_deg)
    aoa_phi_deg = safe_float(aoa_phi_deg)

    if None in (aod_theta_deg, aod_phi_deg, aoa_theta_deg, aoa_phi_deg):
        return 0.0, 0.0, 0.0

    tx_element_gain_db = element_pattern_tr38901_gain_db(
        theta_deg=aod_theta_deg,
        phi_deg=aod_phi_deg,
        g_max_db=config.bs_element_gain_db,
        theta_3db=config.theta_3db,
        phi_3db=config.phi_3db,
        sla_v=config.sla_v,
        a_m=config.a_m
    )
    bf_tx_gain_db = beamforming_gain_db(
        num_rows=config.bs_num_rows,
        num_cols=config.bs_num_cols,
        spacing_lambda=config.element_spacing_lambda,
        theta_deg=aod_theta_deg,
        phi_deg=aod_phi_deg
    )
    bf_rx_gain_db = beamforming_gain_db(
        num_rows=config.ue_num_rows,
        num_cols=config.ue_num_cols,
        spacing_lambda=config.element_spacing_lambda,
        theta_deg=aoa_theta_deg,
        phi_deg=aoa_phi_deg
    )
    return bf_tx_gain_db, bf_rx_gain_db, tx_element_gain_db
