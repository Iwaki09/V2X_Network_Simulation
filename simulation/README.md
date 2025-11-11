# SUMO + SIONNA RT統合シミュレーション

## 概要

本プロジェクトは、交通流シミュレータ**SUMO**とレイトレーシング無線伝搬シミュレータ**SIONNA RT**を連携させたV2Xシミュレーション環境です。SUMOが生成する車両の動的な位置情報を基に、SIONNA RTによって28GHz帯ミリ波における以下の通信リンク品質を計算します：

- **V2I (Vehicle-to-Infrastructure)**: 基地局-車両間の通信
- **V2V (Vehicle-to-Vehicle)**: 車両間の直接通信

## 主な機能

1. **SUMO交通流シミュレーション**: 片側1車線×2の直線道路で15〜20台の車両が走行
2. **FCD出力**: 車両の位置情報をXML形式で出力
3. **SIONNA RTレイトレーシング**: 建物遮蔽を考慮した電波伝搬シミュレーション
4. **V2I/V2Vリンク品質評価**: 基地局-車両間および車両間のリンク品質を計算
5. **リンク品質評価**: 受信電力、パスロス、遅延スプレッド、LOS/NLOS判定をCSV出力
6. **時系列可視化**: 車両位置と通信リンク（LoS/NLoS）を時系列でプロット

---

## 実行方法

### 必要な環境

- Python 3.10以上
- SUMO 1.24.0以上
- TensorFlow（GPU対応推奨）
- SIONNA RT

### インストール

```bash
# Python仮想環境のアクティベート
source .venv/bin/activate

# 必要なパッケージのインストール（必要に応じて）
pip install tensorflow sionna sumolib traci
```

### シミュレーション実行

#### 1. Ray Tracingのみ実行（デフォルト）

既存の`fcd_output.xml`を使用してレイトレーシングのみを実行します。

```bash
cd simulation
./run_simulation.sh
```

#### 2. SUMOシミュレーション込みで実行

SUMOシミュレーションを再実行してFCDを更新した後、レイトレーシングを実行します。

```bash
cd simulation
./run_simulation.sh --sumo
```

### 出力ファイル

- **`output/fcd/fcd_output.xml`**: SUMOが生成した車両位置情報（FCD形式）
- **`output/raytracing/link_quality_results.csv`**: レイトレーシング結果（CSV形式）

### 可視化

シミュレーション結果を時系列で可視化するスクリプトも用意されています。

#### 可視化の実行

```bash
cd simulation
python visualize.py
```

#### 出力

- **`output/visualizations/frames/frame_XXXX.png`**: 各タイムステップの可視化画像（連番PNG、100フレーム）
  - 基地局（青い三角マーカー）
  - 建物（灰色の四角形）
  - 車両（黒い丸マーカー）
  - V2I通信リンク（緑=LoS、赤=NLoS、実線）
  - V2V通信リンク（cyan=LoS、orange=NLoS、破線）
  - タイムスタンプ表示

#### アニメーション作成

生成されたフレームをffmpegでアニメーションに変換できます。

```bash
# MP4形式のアニメーション生成（フレームレート10fps）
ffmpeg -r 10 -i output/visualizations/frames/frame_%04d.png -vcodec libx264 -pix_fmt yuv420p output/visualizations/animation.mp4

# GIF形式のアニメーション生成
ffmpeg -r 10 -i output/visualizations/frames/frame_%04d.png output/visualizations/animation.gif
```

---

## SUMOシミュレーション設定

### 道路ネットワーク

- **形状**: 直線道路（(0, 0) → (1000, 0)）
- **車線数**: 片側1車線×2（合計2車線）
- **車線幅**: 各3.5m（道路全体幅7m）
- **道路中心**: Y=0

### 交通流設定

- **シミュレーション時間**: 100秒
- **初期車両数**: 5台（シミュレーション開始時に配置）
- **追加生成**: 平均10秒間隔でランダムに追加生成
- **合計車両数**: 15〜20台程度
- **最高速度**: 60 km/h（16.67 m/s）
- **車両タイプ**: 乗用車

### 設定ファイル

- **道路ネットワーク**: `sumo_config/road.net.xml`
- **交通流定義**: `sumo_config/traffic.rou.xml`
- **SUMO設定**: `sumo_config/simulation.sumocfg`

---

## Ray Tracingシナリオ設定

### 物理環境

#### 基地局（Base Station）

- **ID**: `BS_1`
- **座標**: (X=500, Y=150, Z=30) [m]
- **アンテナ**: 等方性アンテナ
- **送信電力**: 30 dBm

#### 建物（遮蔽物）

- **ID**: `Building_1`
- **中心座標**: (X=500, Y=50, Z=0) [m]
- **サイズ**: X=20m, Y=20m, Z(高さ)=100m
- **形状**: 直方体

#### 車両（Vehicle）

- **配置**: SUMOのFCD出力に基づき動的に配置
- **アンテナ高さ**: Z=1.5m
- **アンテナ**: 等方性アンテナ

### 無線パラメータ

- **周波数**: 28 GHz（ミリ波）
- **アンテナモデル**: 等方性（Isotropic）
- **送信電力**:
  - V2I（基地局）: 30 dBm
  - V2V（車両）: 23 dBm
- **計算項目**:
  - 受信電力（Received Power）[dBm]
  - パスロス（Path Loss）[dB]
  - 遅延スプレッド（Delay Spread）[ns]
  - LOS/NLOS判定（Line of Sight）

---

## 理論的スループット計算

### 概要

SIONNA RTによるレイトレーシングの出力（受信電力）を基に、**シャノンのチャネル容量公式**を用いて各リンクの理論的最大スループットを計算します。

### 計算式

```
C = B * log2(1 + SNR)
```

- **C**: チャネル容量 [bps]
- **B**: 帯域幅 [Hz]
- **SNR**: 信号対雑音比 (Signal-to-Noise Ratio)

### 前提条件

| パラメータ | 値 | 説明 |
|------------|-----|------|
| 帯域幅 (B) | 100 MHz | V2I/V2Vリンクが利用可能な周波数帯域幅 |
| 受信機温度 (T) | 290 K | 受信機の絶対温度（約17°C） |
| ボルツマン定数 (k_B) | 1.38 × 10⁻²³ J/K | 物理定数 |
| 熱雑音電力 (P_N) | k_B × T × B | 計算値: 約 -84 dBm |

### 研究上の重要な仮定

**干渉 (Interference) をゼロと仮定:**
- 本シミュレーションでは、他の車両や基地局からの干渉電力を0と仮定します。
- したがって、SINR (信号対干渉雑音電力比) ≈ SNR (信号対雑音電力比) として計算します。
- これは、システム全体の上限性能を評価する理想的なシナリオを想定したものです。

### スループット計算の実行

#### 1. 理論的スループット計算

既存の `link_quality_results.csv` から、シャノン公式に基づくスループットを計算します。

```bash
cd simulation
python estimate_theoretical_throughput.py
```

#### 出力ファイル

- **`output/throughput/theoretical_network_results.csv`**: 各リンクの理論的スループット（Mbps）を含むCSV

#### 出力フォーマット

元の `link_quality_results.csv` の全列に加え、以下の列が追加されます：

| 列名 | データ型 | 説明 |
|------|----------|------|
| `received_power_watts` | float | 受信電力 [Watts] |
| `snr` | float | 信号対雑音比（線形値） |
| `snr_db` | float | 信号対雑音比 [dB] |
| `theoretical_throughput_bps` | float | 理論的スループット [bps] |
| `theoretical_throughput_mbps` | float | 理論的スループット [Mbps] |

#### 2. ネットワーク性能サマリーの可視化

時系列での総スループット（全リンクの合計）をグラフ化します。

```bash
cd simulation
python plot_network_summary.py
```

#### 出力ファイル

- **`output/visualizations/network_performance_summary.png`**: 時系列での総スループットグラフ

### 分散型制御ベースラインの評価

従来の「分散型・局所最適」な制御をシミュレートし、理論的最大値との比較を行います。

#### 1. 分散型制御シミュレーション

各車両が他車の状況を考慮せず、自身にとって最強のV2Iリンクを1つだけ選択する局所最適アプローチをシミュレートします。

```bash
cd simulation
python simulate_distributed_control.py
```

**アルゴリズム設計の特徴:**
- **局所最適な意思決定**: 各車両は自身のスループットのみを最大化
- **複数基地局シナリオへの拡張性**: 将来的にBS_1, BS_2...と基地局が増えた場合にも対応可能な設計
- **各時刻・各車両ごとのグループ化**: タイムスタンプとrx_id（車両ID）でグループ化し、各グループで最大スループットのV2Iリンクを選択

#### 出力ファイル

- **`output/baseline/baseline_distributed_results.csv`**: 各タイムスタンプでの分散型V2I総スループット

#### 2. ベースライン性能の可視化

理論的最大値（天井）と分散型ベースラインを比較したグラフを生成します。

```bash
cd simulation
python plot_baseline_comparison.py
```

**グラフの見方:**
- **緑の破線（Theoretical Maximum）**: V2I + V2Vを全て活用した場合の理論的最大値（グローバル最適の上限）
- **青の実線（Baseline）**: 各車両が局所最適に動いた場合の分散型V2I総スループット
- **グレーエリア（Optimization Potential）**: 両者のギャップ = グローバル最適化手法が改善を目指す領域

このギャップこそが、我々のグローバル最適化手法が改善を目指す性能向上の余地を示しています。

#### 出力ファイル

- **`output/baseline/baseline_comparison.png`**: 理論的最大値とベースラインの比較グラフ

#### 期待される研究成果

実験結果によると、分散型ベースラインと理論的最大値の間には**平均84.5%の改善余地**が存在します。これは、以下を意味します：

1. **分散型制御の限界**: 各車両が独立に最適化を行うだけでは、システム全体の性能向上には限界がある
2. **V2Vリンクの未活用**: 分散型制御ではV2Iリンクのみを利用し、高品質なV2Vリンクが活用されていない
3. **グローバル最適化の必要性**: 基地局（またはエッジサーバ）が全車両の状態を把握し、V2I/V2Vを協調制御することで大幅な性能向上が期待できる

---

## グローバル最適化（提案手法）

### 概要

システム全体の総スループットを最大化する「グローバル最適化（集中制御型）」アルゴリズムを実装します。この問題を**整数線形計画問題（ILP: Integer Linear Programming）**として定式化し、最適化ソルバー（PuLP）を用いて解きます。

### アルゴリズムの定式化

#### 目的関数

各タイムスタンプにおいて、アクティブ化されたリンクの理論的スループットの**総和を最大化**します。

```
最大化: Σ (theoretical_throughput_mbps × x_link)
```

ここで、`x_link` はバイナリ決定変数（0: 非アクティブ, 1: アクティブ）です。

#### 制約条件

##### 1. 車両の制約（リソース制約）

各車両は、**同時に1つの通信セッション（送受信のいずれか）しか実行できない**という仮定を設けます。

```
すべての車両 v について:
  Σ (tx_id == v または rx_id == v のリンクの決定変数) ≤ 1
```

この制約は、各車両が持つ無線リソース（アンテナ、トランシーバー）が1つのみであることを意味します。

##### 2. 基地局の制約（多重接続制限）

基地局 BS_1 は、**最大 K = 10 ユーザーまで同時に処理可能**という制約を設けます。

```
Σ (tx_id == "BS_1" のリンクの決定変数) ≤ 10
```

この制約は、基地局の無線リソースが有限であることを反映しています。

### 実行方法

#### 1. グローバル最適化の実行

```bash
cd simulation
python solve_global_optimization.py
```

#### 出力ファイル

- **`global_optimization_results.csv`**: 各タイムスタンプでの最適化されたシステム総スループット

#### 出力フォーマット

| 列名 | データ型 | 説明 |
|------|----------|------|
| `timestamp` | float | タイムステップ [秒] |
| `optimized_total_throughput_mbps` | float | グローバル最適化による総スループット [Mbps] |

#### 2. 最終性能比較グラフの生成

提案手法（グローバル最適化）と従来手法（分散型ベースライン）の性能を比較したグラフを生成します。

```bash
cd simulation
python plot_final_comparison.py
```

#### 出力ファイル

- **`final_performance_comparison.png`**: 提案手法 vs. ベースラインの比較グラフ

**このグラフは、本研究における最も重要な結果を示しています。**

#### グラフの見方

- **青の実線（Proposed）**: グローバル最適化（提案手法）による総スループット
- **紫の破線（Baseline）**: 分散型制御（従来手法）による総スループット

### 研究成果

実験結果によると、以下の性能向上が確認されました：

| 手法 | 平均スループット | 最大スループット | 最小スループット |
|------|-----------------|-----------------|-----------------|
| **提案手法（グローバル最適化）** | 3362.44 Mbps | 5494.83 Mbps | 317.47 Mbps |
| **従来手法（分散型制御）** | 3124.58 Mbps | 4796.67 Mbps | 317.47 Mbps |
| **性能向上率** | **1.08倍 (+7.6%)** | **1.15倍 (+14.6%)** | - |

#### 主要な知見

1. **集中制御の有効性**: グローバルな状態を把握し、協調制御を行うことで、システム全体のスループットが平均7.6%向上しました。

2. **V2Vリンクの活用**: 提案手法では、高品質なV2Vリンクを積極的に活用することで、基地局のリソース制約を回避しつつスループットを向上させています。

3. **ピーク性能の向上**: 最大スループットは14.6%向上しており、トラフィック集中時に特に効果が高いことが確認されました。

4. **実用性**: ILP定式化により、リアルタイム性が求められるV2Xシステムにおいても、比較的短時間（各タイムステップあたり平均1秒未満）で最適解を得ることが可能です。

---

## 出力フォーマット

### `link_quality_results.csv`

各タイムステップにおける全リンク（V2I + V2V）の品質が記録されます。

#### 列定義

| 列名 | データ型 | 説明 |
|------|----------|------|
| `timestamp` | float | タイムステップ [秒] |
| `link_type` | string | リンク種別（`V2I` または `V2V`） |
| `tx_id` | string | 送信機のID（V2Iの場合は `BS_1`、V2Vの場合は車両ID） |
| `rx_id` | string | 受信機のID（常に車両ID） |
| `received_power` | float | 受信電力 [dBm] |
| `path_loss` | float | パスロス [dB] |
| `delay_spread` | float | 遅延スプレッド [ns] |
| `is_line_of_sight` | boolean | 見通し内通信（True）/ 遮蔽あり（False） |

#### サンプル出力

```csv
timestamp,link_type,tx_id,rx_id,received_power,path_loss,delay_spread,is_line_of_sight
0.0,V2I,BS_1,vehicle_0,-65.2,95.2,12.3,True
0.0,V2I,BS_1,vehicle_1,-78.5,108.5,45.6,False
0.0,V2V,vehicle_0,vehicle_1,-45.2,68.2,8.5,True
0.0,V2V,vehicle_1,vehicle_0,-45.2,68.2,8.5,True
1.0,V2I,BS_1,vehicle_0,-66.1,96.1,13.1,True
1.0,V2I,BS_1,vehicle_1,-75.2,105.2,38.2,False
```

**注意事項**:
- V2Iリンクは基地局から各車両へのリンク（車両数 N に対して N 個のリンク）
- V2Vリンクは全車両間のペアリンク（車両数 N に対して N×(N-1) 個のリンク）
- V2V送信電力は 23 dBm、V2I送信電力は 30 dBm で計算されます

---

## ディレクトリ構造

```
simulation/
├── sumo_config/
│   ├── road.net.xml                      # 道路ネットワーク定義
│   ├── traffic.rou.xml                   # 車両ルート定義
│   └── simulation.sumocfg                # SUMO設定ファイル
├── output/
│   ├── fcd/
│   │   └── fcd_output.xml                # SUMO FCD出力
│   ├── raytracing/
│   │   └── link_quality_results.csv      # Ray Tracing結果
│   ├── throughput/
│   │   └── theoretical_network_results.csv  # スループット計算結果
│   ├── baseline/
│   │   ├── baseline_distributed_results.csv  # 分散型ベースライン結果
│   │   └── baseline_comparison.png       # ベースライン比較グラフ
│   └── visualizations/
│       ├── frames/                       # 可視化フレーム出力
│       │   ├── frame_0000.png            # タイムステップ0
│       │   ├── frame_0001.png            # タイムステップ1
│       │   └── ...
│       ├── network_performance_summary.png  # スループットグラフ
│       └── animation.mp4                 # アニメーション（オプション）
├── fcd_parser.py                         # FCDパーサー
├── raytracing_simulation.py              # SIONNA RTシミュレーション
├── run_raytracing.py                     # 統合実行スクリプト
├── run_simulation.sh                     # シェル実行管理スクリプト
├── visualize.py                          # V2I/V2V可視化スクリプト
├── estimate_theoretical_throughput.py    # スループット計算スクリプト
├── plot_network_summary.py               # スループットグラフ生成
├── simulate_distributed_control.py       # 分散型制御シミュレータ
├── plot_baseline_comparison.py           # ベースライン比較可視化
├── solve_global_optimization.py          # グローバル最適化ソルバー（ILP）
├── plot_final_comparison.py              # 最終性能比較グラフ生成
├── global_optimization_results.csv       # グローバル最適化結果
├── final_performance_comparison.png      # 最終性能比較グラフ
├── requirements.txt                      # Python依存パッケージ
├── README.md                             # 本ドキュメント
├── IMPLEMENTATION_PLAN.md                # 実装計画
├── IMPLEMENTATION_PLAN_BASELINE.md       # ベースライン実装計画
├── VISUALIZATION_PLAN.md                 # 可視化実装計画
└── GLOBAL_OPTIMIZATION_PLAN.md           # グローバル最適化実装計画
```

---

## トラブルシューティング

### SUMO実行エラー

- SUMOのインストールを確認: `sumo --version`
- 設定ファイルのパスを確認
- FCD出力ディレクトリの書き込み権限を確認

### SIONNA RTエラー

- GPU環境の確認: `nvidia-smi`
- TensorFlowのGPU対応を確認: `python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"`
- SIONNAのインストール確認: `python -c "import sionna; print(sionna.__version__)"`

### FCDパースエラー

- `fcd_output.xml`が存在するか確認
- XMLフォーマットが正しいか確認（SUMOのバージョン差異に注意）

---

## 参考資料

- [SUMO Documentation](https://sumo.dlr.de/docs/)
- [SIONNA RT Documentation](https://nvlabs.github.io/sionna/)
- [IEEE 802.11p (V2X通信規格)](https://standards.ieee.org/)

---

## ライセンス

研究用途のみ。商用利用不可。

---

## 作成日

2025-10-22
