#!/usr/bin/env python3
"""
スループット計算実行スクリプト

レイトレーシング結果から理論的スループットを計算します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_DIR))

from src.core.throughput import process_link_quality_data


def main():
    """メイン処理"""
    input_csv = PROJECT_DIR / 'output/data/raytracing/link_quality_results.csv'
    output_csv = PROJECT_DIR / 'output/data/throughput/theoretical_network_results.csv'

    # 出力ディレクトリを作成
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    process_link_quality_data(str(input_csv), str(output_csv))


if __name__ == "__main__":
    main()
