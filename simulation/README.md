# SUMO + SIONNA RT 統合V2Xシミュレーション

## 概要

本プロジェクトは、交通流シミュレータ**SUMO**とレイトレーシング無線伝搬シミュレータ**SIONNA RT**を連携させたV2Xシミュレーション環境です。SUMOが生成する車両の動的な位置情報を基に、SIONNA RTによって28GHz帯ミリ波における以下の通信リンク品質を計算します：

- **V2I (Vehicle-to-Infrastructure)**: 基地局-車両間の通信
- **V2V (Vehicle-to-Vehicle)**: 車両間の直接通信

---

## クイックスタート

```bash
# Python仮想環境のアクティベート
source ../.venv/bin/activate

# Ray Tracingのみ実行（既存のFCDを使用）
./run_simulation.sh

# SUMOシミュレーション込みで実行
./run_simulation.sh --sumo

# 全パイプライン実行（SUMO→RT→スループット→最適化）
./run_simulation.sh --all
```

---

## ディレクトリ構造

```
simulation/
├── src/                              # ソースコードパッケージ
│   ├── __init__.py
│   ├── parsers/                      # データ解析モジュール
│   │   ├── __init__.py
│   │   └── fcd_parser.py             # SUMO FCD XMLパーサー
│   ├── core/                         # コアシミュレーションモジュール
│   │   ├── __init__.py
│   │   ├── raytracing.py             # 28GHz帯レイトレーシング
│   │   └── throughput.py             # シャノン公式スループット計算
│   ├── optimization/                 # 最適化アルゴリズム
│   │   ├── __init__.py
│   │   ├── distributed.py            # 分散型制御（ベースライン）
│   │   └── global_optimizer.py       # ILPグローバル最適化
│   └── visualization/                # 可視化モジュール
│       ├── __init__.py
│       ├── link_visualizer.py        # V2Xリンク時系列可視化
│       └── plots.py                  # 各種グラフ生成
├── scripts/                          # 実行スクリプト
│   ├── run_raytracing.py             # レイトレーシング実行
│   ├── run_throughput.py             # スループット計算実行
│   ├── run_optimization.py           # 最適化実行
│   └── run_visualization.py          # 可視化実行
├── sumo_config/                      # SUMO設定ファイル
│   ├── road.net.xml                  # 道路ネットワーク定義
│   ├── traffic.rou.xml               # 交通流定義
│   └── simulation.sumocfg            # SUMO設定
├── output/                           # 出力データ
│   ├── fcd/                          # SUMO FCD出力
│   ├── raytracing/                   # レイトレーシング結果
│   ├── throughput/                   # スループット計算結果
│   ├── baseline/                     # ベースライン比較結果
│   └── visualizations/               # 可視化出力
├── run_simulation.sh                 # 統合実行スクリプト
├── requirements.txt                  # Python依存パッケージ
└── README.md                         # 本ドキュメント
```

---

## インストール

### 必要な環境

- Python 3.10以上
- SUMO 1.24.0以上
- TensorFlow（GPU対応推奨）
- SIONNA RT

### パッケージインストール

```bash
# Python仮想環境の作成とアクティベート
python -m venv ../.venv
source ../.venv/bin/activate

# 必要なパッケージのインストール
pip install -r requirements.txt
```

---

## 使用方法

### シミュレーション実行

#### 統合スクリプト

```bash
# Ray Tracingのみ実行（既存のFCDを使用）
./run_simulation.sh

# SUMOシミュレーション込みで実行
./run_simulation.sh --sumo

# 全パイプライン実行
./run_simulation.sh --all
```

#### 個別スクリプト

```bash
# レイトレーシング実行（簡易モデル - 単一パス）
python scripts/run_raytracing.py

# レイトレーシング実行（Sionna RT - マルチパス対応）
python scripts/run_raytracing.py --sionna-rt

# Sionna RTのパラメータ指定
python scripts/run_raytracing.py --sionna-rt --max-depth 5 --num-samples 2000000

# スループット計算（デフォルト: Shannon公式）
python scripts/run_throughput.py

# スループット計算（MCSベース - 離散レートモデル）
python scripts/run_throughput.py --rate-model mcs

# スループット計算（Shannon + MCS比較モード）
python scripts/run_throughput.py --rate-model both

# 最適化（分散型 + グローバル）
python scripts/run_optimization.py

# 分散型のみ
python scripts/run_optimization.py --distributed

# グローバル最適化のみ
python scripts/run_optimization.py --global

# 最適化でMCSベースのスループット列を使用
python scripts/run_optimization.py --throughput-col throughput_mbps_mcs

# Shannon vs MCS 分析・可視化
python scripts/analyze_throughput_models.py

# 分析結果の出力先を指定
python scripts/analyze_throughput_models.py --outdir results/analysis --rmin-mbps 10

# 可視化（すべて）
python scripts/run_visualization.py --all

# フレーム生成のみ
python scripts/run_visualization.py --frames

# グラフ生成
python scripts/run_visualization.py --network   # ネットワークサマリー
python scripts/run_visualization.py --baseline  # ベースライン比較
python scripts/run_visualization.py --final     # 最終比較
```

---

## API リファレンス

### パーサーモジュール (`src.parsers`)

#### `parse_fcd_xml(filepath, antenna_height=1.5)`

SUMO FCD XMLファイルをパースして車両位置情報を抽出します。

**引数:**
- `filepath` (str): FCD XMLファイルのパス
- `antenna_height` (float, optional): 車両アンテナ高さ [m]. デフォルト: 1.5

**戻り値:**
- `List[TimestepData]`: タイムステップごとの車両情報リスト

**使用例:**
```python
from src.parsers import parse_fcd_xml
data = parse_fcd_xml("output/fcd/fcd_output.xml")
```

#### `get_vehicle_positions(timestep_data)`

タイムステップデータから車両位置を取得します。

**引数:**
- `timestep_data` (TimestepData): タイムステップデータ

**戻り値:**
- `Dict[str, List[float]]`: 車両ID → [x, y, z]座標のマッピング

### コアモジュール (`src.core`)

#### `RayTracingSimulator`

28GHz帯ミリ波レイトレーシングシミュレータ。2つのモードをサポート:
- **簡易モデル** (`use_sionna_rt=False`): フリスの伝搬式による単一パス計算
- **Sionna RTモード** (`use_sionna_rt=True`): 本格的なレイトレーシングによるマルチパス計算

**コンストラクタ引数:**
- `base_station` (BaseStation): 基地局設定
- `building` (Building): 建物設定
- `frequency_ghz` (float, optional): 周波数 [GHz]. デフォルト: 28.0
- `v2v_tx_power_dbm` (float, optional): V2V送信電力 [dBm]. デフォルト: 23.0
- `use_sionna_rt` (bool, optional): Sionna RTモードを有効化. デフォルト: False
- `max_depth` (int, optional): レイトレーシングの最大反射回数. デフォルト: 3
- `num_samples` (int, optional): レイトレーシングのサンプル数. デフォルト: 1000000

**主要メソッド:**
- `calculate_link_quality(timestamp, vehicle_positions)`: 全リンク（V2I+V2V）の品質を計算

**使用例:**
```python
from src.core import RayTracingSimulator, BaseStation, Building

bs = BaseStation(id="BS_1", position=[500.0, 150.0, 30.0], tx_power_dbm=30.0)
bldg = Building(id="Building_1", center=[500.0, 50.0, 0.0], size=[20.0, 20.0, 100.0])

# 簡易モデル（デフォルト）
simulator = RayTracingSimulator(base_station=bs, building=bldg)

# Sionna RTモード（マルチパス対応）
simulator_rt = RayTracingSimulator(
    base_station=bs, building=bldg,
    use_sionna_rt=True, max_depth=5
)

link_qualities = simulator.calculate_link_quality(timestamp=0.0, vehicle_positions=positions)
```

#### `calculate_theoretical_throughput(df, rate_model='shannon')`

リンク品質DataFrameに理論的スループットを追加します。

**引数:**
- `df` (DataFrame): link_quality_results.csvから読み込んだDataFrame
- `rate_model` (str): レートモデル ('shannon', 'mcs', 'both')
  - `'shannon'`: シャノン公式のみ（デフォルト、後方互換）
  - `'mcs'`: MCSベースのみ
  - `'both'`: 両方の列を出力

**戻り値:**
- `DataFrame`: スループット列が追加されたDataFrame

**使用例:**
```python
from src.core.throughput import calculate_theoretical_throughput
df = calculate_theoretical_throughput(df, rate_model='both')
```

#### MCSモデル (`src.core.mcs_model`)

SNRからMCS（Modulation and Coding Scheme）を選択し、離散的なスループットを計算する研究用簡略モデル。

**MCSテーブル（8段階）:**

| MCS Index | SNR範囲 [dB] | スペクトル効率 [bits/s/Hz] | 変調方式相当 |
|-----------|-------------|--------------------------|-------------|
| 0 | < -5 | 0.15 | QPSK 1/8 |
| 1 | -5 ~ 0 | 0.38 | QPSK 1/3 |
| 2 | 0 ~ 5 | 0.88 | QPSK 2/3 |
| 3 | 5 ~ 10 | 1.48 | 16QAM 1/2 |
| 4 | 10 ~ 15 | 2.40 | 16QAM 3/4 |
| 5 | 15 ~ 20 | 3.30 | 64QAM 2/3 |
| 6 | 20 ~ 25 | 4.40 | 64QAM 5/6 |
| 7 | >= 25 | 5.50 | 256QAM 3/4 |

**主要関数:**
- `select_mcs(snr_db)`: SNRからMCSインデックスを選択
- `get_spectral_efficiency(mcs_index)`: MCSに対応するスペクトル効率を取得
- `calculate_mcs_throughput_mbps(bandwidth_hz, spectral_efficiency)`: スループットを計算

### 最適化モジュール (`src.optimization`)

#### `simulate_distributed_control(input_csv=None, output_csv=None)`

分散型制御シミュレーションを実行します。

**引数:**
- `input_csv` (Path, optional): 入力CSVファイルパス
- `output_csv` (Path, optional): 出力CSVファイルパス

**戻り値:**
- `DataFrame`: 結果DataFrame

#### `solve_global_optimization(input_csv=None, output_csv=None)`

ILPによるグローバル最適化を実行します。

**引数:**
- `input_csv` (Path, optional): 入力CSVファイルパス
- `output_csv` (Path, optional): 出力CSVファイルパス

**戻り値:**
- `DataFrame`: 結果DataFrame

### 可視化モジュール (`src.visualization`)

#### `generate_frames(v2i_merged_df, v2v_links_df, output_dir)`

V2Xリンク可視化フレームを生成します。

#### `plot_network_summary(input_csv=None, output_png=None)`

ネットワーク性能サマリーグラフを生成します。

#### `plot_baseline_comparison(...)`

理論的最大値とベースラインの比較グラフを生成します。

#### `plot_final_comparison(...)`

提案手法とベースラインの最終比較グラフを生成します。

---

## パラメータ一覧

### 物理環境パラメータ

| パラメータ | 値 | 単位 | 説明 | 定義場所 |
|-----------|-----|------|------|----------|
| 道路長 | 1000 | m | 直線道路の全長 | sumo_config/road.net.xml |
| 車線数 | 2 | - | 片側1車線×2 | sumo_config/road.net.xml |
| 車線幅 | 3.5 | m | 各車線の幅 | sumo_config/road.net.xml |
| BS位置 | (500, 150, 30) | m | 基地局の3D座標 | src/core/raytracing.py |
| 建物位置 | (500, 50, 0) | m | 建物中心の3D座標 | src/core/raytracing.py |
| 建物サイズ | (20, 20, 100) | m | 幅×奥行×高さ | src/core/raytracing.py |

### 無線通信パラメータ

| パラメータ | 値 | 単位 | 説明 | 定義場所 |
|-----------|-----|------|------|----------|
| 周波数 | 28 | GHz | キャリア周波数 | src/core/raytracing.py |
| 帯域幅 | 100 | MHz | チャネル帯域幅 | src/core/throughput.py |
| V2I送信電力 | 30 | dBm | 基地局送信電力 | src/core/raytracing.py |
| V2V送信電力 | 23 | dBm | 車両送信電力 | src/core/raytracing.py |
| 遮蔽損失 | 15 | dB | NLOS時の追加損失 | src/core/raytracing.py |
| 雑音温度 | 290 | K | 受信機雑音温度 | src/core/throughput.py |

### 最適化パラメータ

| パラメータ | 値 | 単位 | 説明 | 定義場所 |
|-----------|-----|------|------|----------|
| MAX_BS_CONNECTIONS | 10 | - | BS同時接続上限 | src/optimization/global_optimizer.py |

---

## 出力フォーマット

### `link_quality_results.csv`

| 列名 | データ型 | 説明 |
|------|----------|------|
| timestamp | float | タイムステップ [秒] |
| link_type | string | リンク種別（V2I/V2V） |
| tx_id | string | 送信機ID |
| rx_id | string | 受信機ID |
| received_power | float | 受信電力 [dBm] |
| path_loss | float | パスロス [dB] |
| delay_spread | float | 遅延スプレッド [ns] |
| is_line_of_sight | boolean | LOS判定 |
| num_paths | int | パス数（現状は常に1） |
| p_tot_watts | float | 総受信電力 [Watts] |
| p_max_watts | float | 最大パス電力 [Watts] |
| dominance | float | Dominance指標 D = P_max / P_tot (0-1) |
| k_factor | float | K-factor（線形値）。K = P_max / (P_tot - P_max) |
| k_factor_db | float | K-factor [dB] |
| prop_mode | string | 伝搬モード ("D" or "K")。D >= 0.5 なら "D" |

**Propagation-Mode Switch (D/K) について:**

Dominance (D) は最大パス電力が総受信電力に占める割合を示し、マルチパス環境における支配的パスの強さを表します：
- D = 1.0: 単一パス（完全支配）
- D > 0.5: 支配的パスが存在（"D" モード）
- D <= 0.5: 散乱的なマルチパス環境（"K" モード）

現状の簡易パスロスモデルでは単一パスとして計算されるため、すべてのリンクで D = 1.0、prop_mode = "D" となります。将来的にSionna RTのCIR（Channel Impulse Response）から複数パス情報を取得する拡張に備えた設計です。

### `theoretical_network_results.csv`

上記に加え:

| 列名 | データ型 | 説明 | レートモデル |
|------|----------|------|-------------|
| received_power_watts | float | 受信電力 [Watts] | 全モード |
| snr | float | SNR（線形値） | 全モード |
| snr_db | float | SNR [dB] | 全モード |
| theoretical_throughput_bps | float | スループット（Shannon）[bps] | shannon/both |
| theoretical_throughput_mbps | float | スループット（Shannon）[Mbps] | shannon/both |
| mcs_index | int | MCSインデックス (0-7) | mcs/both |
| spectral_efficiency_bpshz | float | スペクトル効率 [bits/s/Hz] | mcs/both |
| throughput_mbps_mcs | float | スループット（MCS）[Mbps] | mcs/both |

**レートモデルオプション:**
- `--rate-model shannon`（デフォルト）: Shannon列のみ出力（後方互換）
- `--rate-model mcs`: MCS列のみ出力
- `--rate-model both`: 両方の列を出力し比較可能

### `baseline_distributed_results.csv`

| 列名 | データ型 | 説明 |
|------|----------|------|
| timestamp | float | タイムステップ [秒] |
| total_v2i_throughput_mbps | float | V2I総スループット [Mbps] |

### `global_optimization_results.csv`

| 列名 | データ型 | 説明 |
|------|----------|------|
| timestamp | float | タイムステップ [秒] |
| optimized_total_throughput_mbps | float | 最適化スループット [Mbps] |

### `summary_shannon_vs_mcs.csv`（分析出力）

| 列名 | データ型 | 説明 |
|------|----------|------|
| condition | string | 条件名（All, LOS, NLOS, prop_mode=D/K 等） |
| count | int | サンプル数 |
| mean_shannon_mbps | float | Shannon平均スループット [Mbps] |
| mean_mcs_mbps | float | MCS平均スループット [Mbps] |
| median_shannon_mbps | float | Shannon中央値 [Mbps] |
| median_mcs_mbps | float | MCS中央値 [Mbps] |
| p05_shannon_mbps | float | Shannon 5%タイル [Mbps] |
| p05_mcs_mbps | float | MCS 5%タイル [Mbps] |
| outage_rate_shannon | float | Shannonアウテージ率 (< Rmin) |
| outage_rate_mcs | float | MCSアウテージ率 (< Rmin) |
| mcs_shannon_ratio | float | MCS/Shannon比 |

---

## 最適化オプション

### `--throughput-col` オプション

最適化で使用するスループット列を選択できます。Shannon公式ベースとMCSベースを公平に比較するための機能です。

**有効な値:**
- `theoretical_throughput_mbps`（デフォルト）: Shannon公式によるスループット
- `throughput_mbps_mcs`: MCSベースのスループット

**使用例:**
```bash
# Shannonベースで最適化（デフォルト）
python scripts/run_optimization.py

# MCSベースで最適化
python scripts/run_optimization.py --throughput-col throughput_mbps_mcs
```

**注意:** 入力CSVに該当列が存在しない場合、分かりやすいエラーメッセージが表示されます。MCS列がない場合は `--rate-model both` でスループット計算を再実行してください。

---

## 分析・可視化

### Shannon vs MCS 分析スクリプト

`analyze_throughput_models.py` は Shannon と MCS のスループットモデルを比較分析します。

**実行方法:**
```bash
# 基本実行
python scripts/analyze_throughput_models.py

# オプション指定
python scripts/analyze_throughput_models.py --outdir results/analysis --rmin-mbps 10
```

**出力ファイル:**
- `summary_shannon_vs_mcs.csv`: 条件別の統計量
- `fig1_cdf_shannon_vs_mcs.png`: Shannon vs MCS のCDF比較
- `fig2_timeseries_throughput.png`: 時系列総スループット
- `fig3_cdf_los_nlos.png`: LOS/NLOS別CDF
- `fig4_cdf_prop_mode.png`: prop_mode (D/K) 別CDF

---

## 研究成果

### ベースライン評価

分散型ベースラインと理論的最大値の間には**平均84.5%の改善余地**が存在します。

### 提案手法の性能向上

| 手法 | 平均スループット | 最大スループット | 最小スループット |
|------|-----------------|-----------------|-----------------|
| **提案手法（グローバル最適化）** | 3362.44 Mbps | 5494.83 Mbps | 317.47 Mbps |
| **従来手法（分散型制御）** | 3124.58 Mbps | 4796.67 Mbps | 317.47 Mbps |
| **性能向上率** | **1.08倍 (+7.6%)** | **1.15倍 (+14.6%)** | - |

---

## トラブルシューティング

### SUMO実行エラー

```bash
# SUMOのインストール確認
sumo --version

# 設定ファイルのパス確認
ls sumo_config/
```

### SIONNA RTエラー

```bash
# GPU環境の確認
nvidia-smi

# TensorFlow GPU対応確認
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"

# SIONNAインストール確認
python -c "import sionna; print(sionna.__version__)"
```

### モジュールインポートエラー

```bash
# PYTHONPATHを設定
export PYTHONPATH="${PWD}:${PYTHONPATH}"

# または scripts/ ディレクトリから直接実行
python scripts/run_raytracing.py
```

---

## 参考資料

- [SUMO Documentation](https://sumo.dlr.de/docs/)
- [SIONNA RT Documentation](https://nvlabs.github.io/sionna/)
- [IEEE 802.11p (V2X通信規格)](https://standards.ieee.org/)

---

## ライセンス

研究用途のみ。商用利用不可。

---

## 更新履歴

- **2026-01-05**:
  - 最適化スクリプトに `--throughput-col` オプションを追加。Shannon/MCS列を選択して最適化可能に。
  - Shannon vs MCS 分析スクリプト (`analyze_throughput_models.py`) を追加。CDF・時系列図・条件別統計を自動生成。
  - 列不足時の分かりやすいエラーメッセージを追加。
  - MCS（離散レート）ベースのスループット推定を追加。`--rate-model`オプションでShannon/MCS/both切替が可能に。MCSテーブル（8段階）による現実的なレート選択をサポート。
- **2026-01-04**: Sionna RTマルチパス対応を追加。`--sionna-rt`オプションでマルチパス計算が可能に。Propagation-Mode Switch (D/K) 指標をlink_quality_results.csvに追加。
- **2026-01-03**: モジュール構造をリファクタリング、READMEを更新
- **2025-10-22**: 初版作成
