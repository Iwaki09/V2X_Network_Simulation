# Prototype 2: V2X Network Simulation with Ray-Tracing

## 1. Goal

This prototype builds a comprehensive V2X (Vehicle-to-Everything) network simulation framework using **ray-tracing** with SIONNA RT. The simulation supports both static snapshots and dynamic scenarios with moving vehicles. Buildings are modeled as 3D objects that create realistic radio signal occlusion effects.

The primary objective is to analyze and visualize V2X communication quality considering building occlusion, vehicle mobility, and realistic radio propagation.

## 2. Core Concepts

- **Dynamic Simulation**: Time-based simulation with moving vehicles and static infrastructure
- **3D Scene Definition**: Environment with buildings, moving vehicles, and base stations modeled in 3D
- **SIONNA RT Integration**: High-fidelity ray-tracing using SIONNA RT with proper building materials and triangle meshes
- **Building Occlusion**: Realistic radio signal blockage by buildings with ITU-recommended material properties
- **Interactive Visualization**: Web-based visualization with animation controls and real-time statistics

## 3. Implementation

### Simulation System (`simulation.py`)

6台車両のダイナミックシナリオ:
- 6台の車両が異なる速度と経路で移動
- 2つの基地局による通信カバレッジ
- 1つの建物による電波遮蔽効果
- SIONNA RTによる高精度パスロス計算

### Building Placement System (`building_placement.py`)

SIONNA RT公式ドキュメントに基づく建物配置:
- ITU推奨コンクリート材料パラメータ
- 三角メッシュによる3D建物モデリング
- RadioMaterialクラスによる材質定義

### Interactive Visualization (`visualization.py`)

Webベースのインタラクティブ可視化:
- 車両移動のアニメーション表示
- リアルタイム統計情報
- パスロス変動の分析
- 遮蔽効果の可視化

## 4. 実行方法

### シミュレーション実行
```bash
python3 simulation.py
```

### ビジュアライゼーション作成
```bash
python3 visualization.py
```

### 結果確認
- `output/simulation_results.json`: シミュレーション結果
- `output/analysis.json`: 統計分析
- `visualization/index.html`: インタラクティブ可視化

## 5. 可視化システム

### 三つのビューモード

1. **Map View (🗺️)**: 基本のマップビュー
   - 車両、基地局、建物の表示
   - 車両の移動軌跡

2. **Graph View (📊)**: ネットワークグラフビュー
   - 車両と基地局をノードとして円形配置
   - パスロス値でエッジを色分け表示
   - 信号品質の凡例付き

3. **Map+Graph View (🗺️+📊)**: 統合ビュー [New!]
   - 既存マップ上にネットワーク接続をオーバーレイ表示
   - リアルタイムでパスロス値をエッジに表示
   - 建物遮蔽効果の可視的確認
   - V2I（車両-基地局）とV2V（車両間）通信の同時表示

### 信号品質の色分け
- 🟢 緑: 良好 (<80dB)
- 🟠 オレンジ: 中程度 (80-100dB)
- 🔴 赤: 悪い (100-120dB)
- ⚫ グレー: 非常に悪い (>120dB)

## 6. シミュレーション結果

### V2X通信のサポート
- **V2I通信**: 車両と基地局間の通信
- **V2V通信**: 車両間の直接通信
- 4台の車両による最適化されたシナリオ

### 遮蔽効果の確認
- Liang-Barskyアルゴリズムによる線分-矩形交差判定
- 建物遮蔽時の+15dBの追加パスロス
- 70-107dB範囲のリアルなパスロス値

### 車両移動分析
- 基地局近傍での最適化された車両配置
- 建物周辺での遮蔽効果の確認
- 動的なネットワーク接続品質の変化
