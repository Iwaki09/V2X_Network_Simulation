"""
伝搬モード（D/K）計算ユーティリティ

Sionna RTが返す各パスの受信電力からDominance（D）とK-factor（K）を計算します。

定義:
- P_tot = sum(p_i)  # 全パス電力の合計
- P_max = max(p_i)  # 最大パス電力
- Dominance D = P_max / P_tot  (0..1)
- K-factor K = P_max / (P_tot - P_max)  (線形)
- K[dB] = 10*log10(K)
"""

import numpy as np
from typing import Sequence, Dict, Union


# デフォルトの閾値
DEFAULT_D_THRESHOLD = 0.5


def compute_dk(
    path_powers_watts: Sequence[float],
    d_th: float = DEFAULT_D_THRESHOLD
) -> Dict[str, Union[int, float, str]]:
    """
    パス電力リストからDominanceとK-factorを計算

    Args:
        path_powers_watts: 各パスの受信電力 [Watts] のリスト（線形値）
        d_th: Dominance閾値（D >= d_th なら "D" モード、それ以外は "K" モード）

    Returns:
        dict: 以下のキーを持つ辞書
            - num_paths (int): パス数
            - p_tot_watts (float): 総受信電力 [Watts]
            - p_max_watts (float): 最大パス電力 [Watts]
            - dominance (float): Dominance指標 D (0-1)
            - k_factor (float): K-factor（線形）
            - k_factor_db (float): K-factor [dB]
            - prop_mode (str): 伝搬モード ("D" or "K")
    """
    # 入力をnumpy配列に変換
    powers = np.array(path_powers_watts, dtype=np.float64)

    # パス数
    num_paths = len(powers)

    # パスが0本の場合
    if num_paths == 0 or np.all(powers <= 0):
        return {
            "num_paths": 0,
            "p_tot_watts": 0.0,
            "p_max_watts": 0.0,
            "dominance": 0.0,
            "k_factor": 0.0,
            "k_factor_db": float("-inf"),
            "prop_mode": "K"  # パスなしは散乱的扱い
        }

    # 正の電力のみをフィルタ
    positive_powers = powers[powers > 0]
    num_paths = len(positive_powers)

    if num_paths == 0:
        return {
            "num_paths": 0,
            "p_tot_watts": 0.0,
            "p_max_watts": 0.0,
            "dominance": 0.0,
            "k_factor": 0.0,
            "k_factor_db": float("-inf"),
            "prop_mode": "K"
        }

    # 計算
    p_tot = float(np.sum(positive_powers))
    p_max = float(np.max(positive_powers))

    # Dominance: D = P_max / P_tot
    dominance = p_max / p_tot if p_tot > 0 else 0.0

    # K-factor: K = P_max / (P_tot - P_max)
    p_scatter = p_tot - p_max
    if p_scatter > 0:
        k_factor = p_max / p_scatter
        k_factor_db = 10.0 * np.log10(k_factor)
    else:
        # 単一パス（完全支配）の場合は inf
        k_factor = float("inf")
        k_factor_db = float("inf")

    # 伝搬モード判定
    prop_mode = "D" if dominance >= d_th else "K"

    return {
        "num_paths": num_paths,
        "p_tot_watts": p_tot,
        "p_max_watts": p_max,
        "dominance": dominance,
        "k_factor": k_factor,
        "k_factor_db": k_factor_db,
        "prop_mode": prop_mode
    }


def dbm_to_watts(power_dbm: float) -> float:
    """
    dBm を Watts に変換

    Args:
        power_dbm: 電力 [dBm]

    Returns:
        電力 [Watts]
    """
    return (10 ** (power_dbm / 10)) / 1000


def watts_to_dbm(power_watts: float) -> float:
    """
    Watts を dBm に変換

    Args:
        power_watts: 電力 [Watts]

    Returns:
        電力 [dBm]
    """
    if power_watts <= 0:
        return float("-inf")
    return 10 * np.log10(power_watts * 1000)


if __name__ == "__main__":
    """単体テスト"""
    print("=" * 60)
    print("Propagation Mode (D/K) Calculator - Unit Test")
    print("=" * 60)

    # テストケース1: 単一パス（完全支配）
    print("\nTest 1: Single dominant path")
    result = compute_dk([1e-9])  # 1 nW
    print(f"  Input: [1e-9 W]")
    print(f"  Result: {result}")
    assert result["num_paths"] == 1
    assert result["dominance"] == 1.0
    assert result["k_factor"] == float("inf")
    assert result["prop_mode"] == "D"
    print("  ✅ Passed")

    # テストケース2: 2パス（均等）
    print("\nTest 2: Two equal paths")
    result = compute_dk([1e-9, 1e-9])
    print(f"  Input: [1e-9, 1e-9 W]")
    print(f"  Result: {result}")
    assert result["num_paths"] == 2
    assert result["dominance"] == 0.5
    assert result["k_factor"] == 1.0
    assert result["k_factor_db"] == 0.0
    assert result["prop_mode"] == "D"  # D == 0.5で閾値ちょうど
    print("  ✅ Passed")

    # テストケース3: マルチパス（支配パスあり）
    print("\nTest 3: Multi-path with dominant path")
    result = compute_dk([8e-9, 1e-9, 1e-9])  # 80% dominance
    print(f"  Input: [8e-9, 1e-9, 1e-9 W]")
    print(f"  Result: {result}")
    assert result["num_paths"] == 3
    assert abs(result["dominance"] - 0.8) < 0.01
    assert result["prop_mode"] == "D"
    print("  ✅ Passed")

    # テストケース4: マルチパス（散乱的）
    print("\nTest 4: Multi-path scattered")
    result = compute_dk([1e-9, 1e-9, 1e-9, 1e-9])  # 25% dominance
    print(f"  Input: [1e-9, 1e-9, 1e-9, 1e-9 W]")
    print(f"  Result: {result}")
    assert result["num_paths"] == 4
    assert abs(result["dominance"] - 0.25) < 0.01
    assert result["prop_mode"] == "K"
    print("  ✅ Passed")

    # テストケース5: パスなし
    print("\nTest 5: No paths")
    result = compute_dk([])
    print(f"  Input: []")
    print(f"  Result: {result}")
    assert result["num_paths"] == 0
    assert result["dominance"] == 0.0
    assert result["prop_mode"] == "K"
    print("  ✅ Passed")

    # テストケース6: dBmからの変換テスト
    print("\nTest 6: dBm to Watts conversion")
    power_dbm = -60.0  # -60 dBm
    power_watts = dbm_to_watts(power_dbm)
    print(f"  Input: {power_dbm} dBm")
    print(f"  Output: {power_watts:.2e} W")
    expected = 1e-9  # 1 nW
    assert abs(power_watts - expected) < 1e-12
    print("  ✅ Passed")

    print("\n" + "=" * 60)
    print("✅ All unit tests passed!")
    print("=" * 60)
