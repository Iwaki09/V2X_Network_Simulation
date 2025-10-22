# SUMO + SIONNA RT統合シミュレーション

## 概要

本プロジェクトは、交通流シミュレータ**SUMO**とレイトレーシング無線伝搬シミュレータ**SIONNA RT**を連携させたV2Xシミュレーション環境です。SUMOが生成する車両の動的な位置情報を基に、SIONNA RTによって28GHz帯ミリ波における基地局-車両間（V2I）の通信リンク品質を計算します。

## 主な機能

1. **SUMO交通流シミュレーション**: 片側1車線×2の直線道路で15〜20台の車両が走行
2. **FCD出力**: 車両の位置情報をXML形式で出力
3. **SIONNA RTレイトレーシング**: 建物遮蔽を考慮した電波伝搬シミュレーション
4. **リンク品質評価**: 受信電力、パスロス、遅延スプレッド、LOS/NLOS判定をCSV出力

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

- **`output/fcd_output.xml`**: SUMOが生成した車両位置情報（FCD形式）
- **`output/link_quality_results.csv`**: レイトレーシング結果（CSV形式）

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
- **計算項目**:
  - 受信電力（Received Power）[dBm]
  - パスロス（Path Loss）[dB]
  - 遅延スプレッド（Delay Spread）[ns]
  - LOS/NLOS判定（Line of Sight）

---

## 出力フォーマット

### `link_quality_results.csv`

各タイムステップにおける基地局（BS_1）と全車両間のリンク品質が記録されます。

#### 列定義

| 列名 | データ型 | 説明 |
|------|----------|------|
| `timestamp` | float | タイムステップ [秒] |
| `vehicle_id` | string | 車両ID（SUMOが付与） |
| `tx_id` | string | 送信局ID（常に`BS_1`） |
| `received_power` | float | 受信電力 [dBm] |
| `delay_spread` | float | 遅延スプレッド [ns] |
| `path_loss` | float | パスロス [dB] |
| `is_line_of_sight` | boolean | 見通し内通信（True）/ 遮蔽あり（False） |

#### サンプル出力

```csv
timestamp,vehicle_id,tx_id,received_power,delay_spread,path_loss,is_line_of_sight
0.0,vehicle_0,BS_1,-65.2,12.3,95.2,True
0.0,vehicle_1,BS_1,-78.5,45.6,108.5,False
1.0,vehicle_0,BS_1,-66.1,13.1,96.1,True
1.0,vehicle_1,BS_1,-75.2,38.2,105.2,False
```

---

## ディレクトリ構造

```
simulation/
├── sumo_config/
│   ├── road.net.xml           # 道路ネットワーク定義
│   ├── traffic.rou.xml        # 車両ルート定義
│   └── simulation.sumocfg     # SUMO設定ファイル
├── output/
│   ├── fcd_output.xml         # SUMO FCD出力
│   └── link_quality_results.csv  # Ray Tracing結果
├── fcd_parser.py              # FCDパーサー
├── raytracing_simulation.py   # SIONNA RTシミュレーション
├── run_raytracing.py          # 統合実行スクリプト
├── run_simulation.sh          # シェル実行管理スクリプト
├── README.md                  # 本ドキュメント
└── IMPLEMENTATION_PLAN.md     # 実装計画
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
