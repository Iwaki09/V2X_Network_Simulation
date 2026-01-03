# Output Directory Structure

シミュレーション出力ファイルの整理されたディレクトリ構造です。

## ディレクトリ構成

```
output/
├── data/              # データファイル
│   ├── fcd/           # SUMO Floating Car Data (FCD)
│   ├── raytracing/    # レイトレーシング結果（リンク品質）
│   ├── throughput/    # スループット計算結果
│   └── optimization/  # 最適化結果（分散・グローバル）
├── figures/           # 可視化画像
│   ├── analysis/      # 分析結果グラフ
│   └── frames/        # アニメーションフレーム
└── README.md
```

## ファイル説明

### data/
| ファイル | 説明 |
|---------|------|
| `fcd/fcd_output.xml` | SUMOからの車両位置・速度データ |
| `raytracing/link_quality_results.csv` | 各リンクのSNR、パスロス等 |
| `throughput/theoretical_network_results.csv` | 理論スループット計算結果 |
| `optimization/baseline_distributed_results.csv` | 分散最適化の結果 |
| `optimization/global_optimization_results.csv` | グローバル最適化の結果 |

### figures/analysis/
| ファイル | 説明 |
|---------|------|
| `method_comparison.png` | 提案手法（グローバル最適化）vs ベースライン（分散）の直接比較 |
| `theoretical_potential.png` | 理論最大値と分散手法の差（最適化ポテンシャル）を可視化 |
| `throughput_summary.png` | V2I+V2V合計の理論スループット推移（平均線付き） |

### figures/frames/
| ファイル | 説明 |
|---------|------|
| `frame_XXXX.png` | アニメーション用連続フレーム（100枚） |

---
*Last updated: 2025-01-03*
