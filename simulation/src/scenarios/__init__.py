"""
シナリオ設定モジュール

各シナリオ（デフォルト、交差点など）の設定を定義します。
"""

from .default import DefaultScenarioConfig
from .corner_intersection import CornerIntersectionConfig

__all__ = ["DefaultScenarioConfig", "CornerIntersectionConfig"]
