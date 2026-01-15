#!/usr/bin/env python3
"""
RandomとGreedyのベースライン手法を再実行するスクリプト
"""

import sys
from pathlib import Path
import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.optimization.methods import random_assignment, greedy_assignment
from src.optimization.plotting import calculate_summary


def main():
    # 既存の候補データを読み込み
    input_dir = Path('output/optimization_comparison_corner_fixed')
    candidates_df = pd.read_csv(input_dir / 'candidates.csv')

    bs_capacity = 10
    seed = 42

    print("=" * 60)
    print("Random/Greedyベースライン再実行")
    print("=" * 60)
    print(f"候補数: {len(candidates_df)}")
    print(f"BS容量: {bs_capacity}")
    print()

    # Random割当
    print("Random割当を実行中...")
    result_random = random_assignment(candidates_df, bs_capacity, seed)

    # 評価指標計算
    outage_rate = (result_random['accepted'] == 0).sum() / len(result_random)
    mean_throughput = result_random['truth_rate_mcs_effective'].mean()
    relay_ratio = (result_random[result_random['accepted'] == 1]['selected_action_type'] == 'relay').sum() / (result_random['accepted'] == 1).sum()

    print(f"  ✓ 完了")
    print(f"    - アウテージ率: {outage_rate:.3f} ({outage_rate*100:.1f}%)")
    print(f"    - 平均スループット: {mean_throughput:.2f} Mbps")
    print(f"    - リレー率: {relay_ratio:.3f} ({relay_ratio*100:.1f}%)")
    print()

    # 結果を保存
    result_random.to_csv(input_dir / 'assignment_random.csv', index=False)
    print(f"  保存: {input_dir / 'assignment_random.csv'}")
    print()

    # Greedy割当
    print("Greedy (MCS) 割当を実行中...")
    result_greedy = greedy_assignment(candidates_df, bs_capacity)

    # 評価指標計算
    outage_rate = (result_greedy['accepted'] == 0).sum() / len(result_greedy)
    mean_throughput = result_greedy['truth_rate_mcs_effective'].mean()
    relay_ratio = (result_greedy[result_greedy['accepted'] == 1]['selected_action_type'] == 'relay').sum() / (result_greedy['accepted'] == 1).sum()

    print(f"  ✓ 完了")
    print(f"    - アウテージ率: {outage_rate:.3f} ({outage_rate*100:.1f}%)")
    print(f"    - 平均スループット: {mean_throughput:.2f} Mbps")
    print(f"    - リレー率: {relay_ratio:.3f} ({relay_ratio*100:.1f}%)")
    print()

    # 結果を保存
    result_greedy.to_csv(input_dir / 'assignment_greedy_mcs.csv', index=False)
    print(f"  保存: {input_dir / 'assignment_greedy_mcs.csv'}")

    print()
    print("=" * 60)
    print("完了！")
    print("=" * 60)


if __name__ == '__main__':
    main()
