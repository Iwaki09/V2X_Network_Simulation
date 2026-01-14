"""
コアシミュレーションモジュール

レイトレーシングシミュレーションとスループット計算機能を提供

Note: raytracing モジュールはSIONNA RTを必要とするため、
      SIONNA がインストールされていない環境では直接インポートできません。
      その場合は `from src.core.throughput import ...` を使用してください。
"""

# throughputは常にインポート可能
from .throughput import calculate_theoretical_throughput, process_link_quality_data, RateModel

# MCSモデル
from .mcs_model import (
    select_mcs,
    get_spectral_efficiency,
    calculate_mcs_throughput_mbps,
    MCS_SNR_THRESHOLDS_DB,
    MCS_SPECTRAL_EFFICIENCY,
)

# raytracing は SIONNA 依存のため遅延インポート
def _import_raytracing():
    """SIONNA依存のモジュールを遅延インポート"""
    from .raytracing import (
        RayTracingSimulator,
        BaseStation,
        Building,
        LinkQuality,
    )
    return RayTracingSimulator, BaseStation, Building, LinkQuality


__all__ = [
    "calculate_theoretical_throughput",
    "process_link_quality_data",
    "RateModel",
    # MCSモデル
    "select_mcs",
    "get_spectral_efficiency",
    "calculate_mcs_throughput_mbps",
    "MCS_SNR_THRESHOLDS_DB",
    "MCS_SPECTRAL_EFFICIENCY",
    # 以下はSIONNA環境でのみ利用可能
    # "RayTracingSimulator",
    # "BaseStation",
    # "Building",
    # "LinkQuality",
]
