# Output Directory Structure

シミュレーション出力ファイルの整理されたディレクトリ構造です。

## ディレクトリ構成

```
output/
├── scenarios/                          # シナリオ別出力
│   ├── default/                        # デフォルトシナリオ（直線道路）
│   │   ├── fcd/                        # SUMO Floating Car Data
│   │   ├── raytracing/                 # レイトレーシング結果
│   │   ├── throughput/                 # スループット計算結果
│   │   ├── optimization/               # 最適化結果
│   │   ├── analysis/                   # 分析結果
│   │   └── figures/                    # 可視化画像
│   └── corner_intersection/            # 交差点シナリオ
│       ├── fcd/
│       ├── raytracing/
│       ├── throughput/
│       ├── optimization/
│       ├── analysis/
│       └── figures/
└── README.md
```

## シナリオ別出力

### default（デフォルトシナリオ）
直線道路（1km）上の車両移動シミュレーション

### corner_intersection（交差点シナリオ）
十字交差点（4棟の角ビル）でのLOS/NLOS切り替え多発シミュレーション

## ファイル説明

### fcd/
| ファイル | 説明 |
|---------|------|
| `fcd_output.xml` | SUMOからの車両位置・速度データ |

### raytracing/
| ファイル | 説明 |
|---------|------|
| `link_quality_results.csv` | 各リンクのSNR、パスロス、LOS/NLOS、prop_mode等 |

### throughput/
| ファイル | 説明 |
|---------|------|
| `theoretical_network_results.csv` | 理論スループット計算結果（Shannon/MCS） |

### optimization/
| ファイル | 説明 |
|---------|------|
| `baseline_distributed_results.csv` | 分散型制御の結果 |
| `global_optimization_results.csv` | グローバル最適化の結果 |

### analysis/
| ファイル | 説明 |
|---------|------|
| `summary_shannon_vs_mcs.csv` | Shannon vs MCS 統計サマリー |
| `fig1_cdf_shannon_vs_mcs.png` | CDF比較グラフ |
| `fig2_timeseries_throughput.png` | 時系列スループットグラフ |
| `fig3_cdf_los_nlos.png` | LOS/NLOS別CDFグラフ |
| `fig4_cdf_prop_mode.png` | prop_mode別CDFグラフ |

### figures/
| ファイル | 説明 |
|---------|------|
| `analysis/method_comparison.png` | 提案手法 vs ベースライン比較 |
| `analysis/theoretical_potential.png` | 理論最大値と分散手法の差 |
| `analysis/throughput_summary.png` | V2I+V2V合計スループット推移 |
| `frames/frame_XXXX.png` | アニメーション用連続フレーム |

---
*Last updated: 2026-01-07*
