# Prototype 4: SUMO-based V2X Communication Simulation

SUMOを使った交通シミュレーションと車両間通信（V2V）のグラフ最適化を統合したシミュレーションシステム。

## 概要

このプロトタイプは以下の機能を提供します：

1. **SUMOによる交通シミュレーション**: 6台の車両が道路上を移動
2. **車両位置情報の取得**: TraCIを使ってリアルタイムで車両位置を取得
3. **通信チャネルモデル**: 距離ベースのパスロスモデルで通信品質を計算
4. **グラフ最適化**: NetworkXを使って車両間の最適通信経路を計算
5. **可視化**: matplotlibで車両位置、通信リンク、最適経路を可視化

## ディレクトリ構造

```
prototype4/
├── sumo_scenarios/          # SUMOシナリオファイル
│   ├── network.net.xml      # 道路ネットワーク定義
│   ├── routes.rou.xml       # 車両ルート定義
│   └── config.sumocfg       # SUMO設定ファイル
├── output/                  # シミュレーション結果出力
│   └── vehicle_traces.json  # 車両軌跡データ
├── figures/                 # 可視化結果保存
│   ├── snapshot_t*.png      # 各時刻のスナップショット
│   └── statistics.png       # 統計情報グラフ
├── sumo_simulation.py       # SUMO-Python統合
├── channel_model.py         # 通信チャネルモデル
├── graph_optimizer.py       # グラフ最適化
├── visualizer.py            # 可視化モジュール
├── main.py                  # メインシミュレーション
└── README.md                # このファイル
```

## 実行方法

### 1. 依存パッケージのインストール

```bash
# 仮想環境を有効化
source ../.venv/bin/activate

# 必要なパッケージ（既にインストール済み）
# - networkx
# - matplotlib
# - numpy
# - traci
```

### 2. メインシミュレーションの実行

```bash
# GUIなしで実行（推奨）
python main.py

# SUMO GUIを使用して実行
python main.py --gui
```

### 3. 個別モジュールのテスト

各モジュールは単独でテスト可能です：

```bash
# SUMOシミュレーションのみ
python sumo_simulation.py

# チャネルモデルのテスト
python channel_model.py

# グラフ最適化のテスト
python graph_optimizer.py

# 可視化のテスト
python visualizer.py
```

## シミュレーション設定

### 車両設定（`routes.rou.xml`）

- **車両数**: 6台
- **出発時刻**: 0s, 1s, 2s, 3s, 5s, 7s
- **初期位置**: 0m, 80m, 50m, 150m, 100m, 200m
- **速度**: 15-22 m/s

### 通信チャネルパラメータ（`channel_model.py`）

- **周波数**: 5.9 GHz（V2X専用帯域）
- **送信電力**: 20 dBm
- **アンテナゲイン**: 3 dBi（送受信）
- **ノイズフロア**: -95 dBm
- **パスロス指数**: 2.5
- **最大通信距離**: 300 m
- **最小SNR閾値**: 5 dB

## 出力結果

### 1. 可視化画像

- **スナップショット** (`figures/snapshot_t*.png`):
  - 各時刻の車両位置と通信リンクを表示
  - SNRに応じてリンクの色を変更（緑=高品質、橙=中品質、赤=低品質）
  - 最適経路を青色でハイライト

- **統計グラフ** (`figures/statistics.png`):
  - 平均SNRの時系列変化
  - 通信リンク数の時系列変化

### 2. データファイル

- **車両軌跡** (`output/vehicle_traces.json`):
  - 各車両の時系列位置データ
  - 速度、角度などの情報を含む

## シミュレーション結果の例

```
Simulation Summary
================================================================================
  Total simulation steps: 671
  Total vehicles: 6
  Simulation duration: 67.0s
  Average SNR: 26.42 dB
  Average number of links: 10.4
```

### 最適経路の例

```
Time: 20.1s
  Vehicles: 6
  Communication links: 15
  Average SNR: 32.85 dB
  Optimal path (veh0 -> veh5):
    Route: veh0 -> veh5
    Hops: 1
    Min link quality: 25.50 dB
```

## 主要な技術要素

### 1. SUMOシミュレーション (`sumo_simulation.py`)

- TraCIを使用してSUMOと連携
- リアルタイムで車両位置・速度・角度を取得
- 車両軌跡をJSON形式で保存

### 2. 通信チャネルモデル (`channel_model.py`)

- **自由空間パスロス**: Friis伝送公式
- **対数距離パスロス**: 実環境を考慮したモデル
- **SNR計算**: 受信電力とノイズフロアから計算
- **データレート推定**: Shannon容量の簡易版

### 3. グラフ最適化 (`graph_optimizer.py`)

- NetworkXを使用してグラフ構築
- 車両をノード、通信リンクをエッジとして表現
- Dijkstra法による最短経路計算
- 重み付け: SNRの逆数（高品質=小さい重み）

### 4. 可視化 (`visualizer.py`)

- matplotlibによる2Dプロット
- 車両位置と通信リンクの表示
- グラフ構造の可視化
- 統計情報の時系列グラフ

## カスタマイズ

### 車両数の変更

`routes.rou.xml`を編集して車両を追加/削除：

```xml
<vehicle id="vehX" type="car" route="route0"
         depart="10.0" departPos="300.0" departSpeed="18.0"/>
```

### 通信パラメータの調整

`channel_model.py`の`ChannelParameters`クラスを編集：

```python
@dataclass
class ChannelParameters:
    frequency: float = 5.9e9  # 周波数
    tx_power_dbm: float = 20.0  # 送信電力
    max_range_m: float = 300.0  # 最大通信距離
    # ...
```

### 道路ネットワークの変更

`netgenerate`コマンドで新しいネットワークを生成：

```bash
netgenerate --grid --grid.x-number=3 --grid.y-number=2 \
            --grid.x-length=500 --output-file=network.net.xml
```

## トラブルシューティング

### SUMOが起動しない

- SUMOのインストールを確認: `sumo --version`
- パスが正しいか確認: `/opt/homebrew/bin/sumo`

### TraCI接続エラー

- ポートが使用中でないか確認
- SUMOのバージョンとTraCIライブラリのバージョンが一致しているか確認

### 可視化が表示されない

- matplotlibのバックエンドを確認
- 画像は`figures/`ディレクトリに保存されます

## 今後の拡張案

- [ ] より複雑な道路ネットワーク（交差点、複数車線）
- [ ] マルチホップルーティングプロトコルの実装
- [ ] 建物による遮蔽効果の考慮
- [ ] アニメーションGIF/動画の生成
- [ ] リアルタイム可視化（GUI）

## 参考文献

- SUMO Documentation: https://sumo.dlr.de/docs/
- TraCI Python API: https://sumo.dlr.de/docs/TraCI/Interfacing_TraCI_from_Python.html
- NetworkX: https://networkx.org/
- V2X通信規格: IEEE 802.11p / C-V2X

---

**作成日**: 2025-10-02
**プロジェクト**: V2X Network Simulation - Prototype 4
