"""
MCS（Modulation and Coding Scheme）ベースのスループット推定モジュール

Shannon理論容量の連続レートに対して、離散的なMCSテーブルによるレート選択を提供します。

研究用の簡略離散レートモデル:
- NR（5G）のMCSテーブルを簡略化した8段階のレートモデル
- SNR閾値ベースでMCSインデックスを選択
- 各MCSに対応するスペクトル効率を定義

注意: 本モデルはNR標準の完全再現ではなく、研究用途の離散レートモデルとして設計されています。
"""

from typing import List


# ============================================================
# MCSテーブル定義（研究用簡略モデル）
# ============================================================

# SNR閾値 [dB]: この値以上で次のMCSレベルに移行
# 7つの閾値で8段階のMCSを定義
MCS_SNR_THRESHOLDS_DB: List[float] = [-5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0]

# スペクトル効率 [bits/s/Hz]: MCSインデックスに対応
# MCS 0 (最低) から MCS 7 (最高) まで
# 参考: NR QPSK～256QAM相当のスペクトル効率を簡略化
MCS_SPECTRAL_EFFICIENCY: List[float] = [
    0.15,   # MCS 0: QPSK 1/8 相当 (SNR < -5 dB)
    0.38,   # MCS 1: QPSK 1/3 相当 (-5 <= SNR < 0 dB)
    0.88,   # MCS 2: QPSK 2/3 相当 (0 <= SNR < 5 dB)
    1.48,   # MCS 3: 16QAM 1/2 相当 (5 <= SNR < 10 dB)
    2.40,   # MCS 4: 16QAM 3/4 相当 (10 <= SNR < 15 dB)
    3.30,   # MCS 5: 64QAM 2/3 相当 (15 <= SNR < 20 dB)
    4.40,   # MCS 6: 64QAM 5/6 相当 (20 <= SNR < 25 dB)
    5.50,   # MCS 7: 256QAM 3/4 相当 (25 dB <= SNR)
]


def select_mcs(snr_db: float, thresholds_db: List[float] = None) -> int:
    """
    SNR [dB] に基づいてMCSインデックスを選択

    Args:
        snr_db: 信号対雑音比 [dB]
        thresholds_db: SNR閾値リスト（デフォルト: MCS_SNR_THRESHOLDS_DB）

    Returns:
        MCSインデックス (0 から len(thresholds_db) まで)
    """
    if thresholds_db is None:
        thresholds_db = MCS_SNR_THRESHOLDS_DB

    # SNR閾値を順にチェックし、超えた閾値の数がMCSインデックス
    mcs_index = 0
    for threshold in thresholds_db:
        if snr_db >= threshold:
            mcs_index += 1
        else:
            break

    return mcs_index


def get_spectral_efficiency(mcs_index: int, se_table: List[float] = None) -> float:
    """
    MCSインデックスに対応するスペクトル効率を取得

    Args:
        mcs_index: MCSインデックス
        se_table: スペクトル効率テーブル（デフォルト: MCS_SPECTRAL_EFFICIENCY）

    Returns:
        スペクトル効率 [bits/s/Hz]
    """
    if se_table is None:
        se_table = MCS_SPECTRAL_EFFICIENCY

    # インデックス範囲を制限
    mcs_index = max(0, min(mcs_index, len(se_table) - 1))

    return se_table[mcs_index]


def calculate_mcs_throughput_mbps(bandwidth_hz: float, spectral_efficiency: float) -> float:
    """
    MCSベースのスループットを計算

    Args:
        bandwidth_hz: 帯域幅 [Hz]
        spectral_efficiency: スペクトル効率 [bits/s/Hz]

    Returns:
        スループット [Mbps]
    """
    throughput_bps = bandwidth_hz * spectral_efficiency
    return throughput_bps / 1_000_000


def apply_conservative_mcs(mcs_index: int, steps: int = 1) -> int:
    """
    保守的なMCS選択（指定ステップ数だけ下げる）

    マルチパス環境など、伝搬条件が不安定な場合に使用。
    D/K（Propagation-Mode Switch）の結果に基づいて適用可能。

    Args:
        mcs_index: 元のMCSインデックス
        steps: 下げるステップ数（デフォルト: 1）

    Returns:
        調整後のMCSインデックス（最小0）
    """
    return max(0, mcs_index - steps)


def get_mcs_info(snr_db: float) -> dict:
    """
    SNRからMCS情報を一括取得

    Args:
        snr_db: 信号対雑音比 [dB]

    Returns:
        dict: {
            'mcs_index': int,
            'spectral_efficiency_bpshz': float,
            'snr_db': float
        }
    """
    mcs_index = select_mcs(snr_db)
    se = get_spectral_efficiency(mcs_index)

    return {
        'mcs_index': mcs_index,
        'spectral_efficiency_bpshz': se,
        'snr_db': snr_db
    }


def print_mcs_table():
    """MCSテーブルの内容を表示（デバッグ・確認用）"""
    print("\n【MCSテーブル（研究用簡略モデル）】")
    print("-" * 60)
    print(f"{'MCS Index':<12} {'SNR範囲 [dB]':<20} {'SE [bits/s/Hz]':<15}")
    print("-" * 60)

    thresholds = MCS_SNR_THRESHOLDS_DB
    se_table = MCS_SPECTRAL_EFFICIENCY

    for i, se in enumerate(se_table):
        if i == 0:
            snr_range = f"< {thresholds[0]:.1f}"
        elif i == len(se_table) - 1:
            snr_range = f">= {thresholds[-1]:.1f}"
        else:
            snr_range = f"{thresholds[i-1]:.1f} - {thresholds[i]:.1f}"

        print(f"{i:<12} {snr_range:<20} {se:<15.2f}")

    print("-" * 60)


if __name__ == "__main__":
    # 動作確認
    print_mcs_table()

    print("\n【動作確認テスト】")
    test_snrs = [-10, -5, 0, 5, 10, 15, 20, 25, 30]
    for snr in test_snrs:
        info = get_mcs_info(snr)
        print(f"SNR={snr:4}dB -> MCS={info['mcs_index']}, SE={info['spectral_efficiency_bpshz']:.2f} bits/s/Hz")
