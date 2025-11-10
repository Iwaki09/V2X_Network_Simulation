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
├── README.md                             # 本ドキュメント
├── IMPLEMENTATION_PLAN.md                # 実装計画
└── VISUALIZATION_PLAN.md                 # 可視化実装計画
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
