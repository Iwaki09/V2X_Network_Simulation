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

### Smart Simulation System (`smart_simulation.py`)

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

### Interactive Visualization (`smart_visualization.py`)

Webベースのインタラクティブ可視化:
- 車両移動のアニメーション表示
- リアルタイム統計情報
- パスロス変動の分析
- 遮蔽効果の可視化

## 4. 実行方法

### スマートシミュレーション実行
```bash
python3 smart_simulation.py
```

### ビジュアライゼーション作成
```bash
python3 smart_visualization.py
```

### 結果確認
- `output/smart_v2x_simulation_results.json`: シミュレーション結果
- `output/smart_v2x_analysis.json`: 統計分析
- `visualization/smart_index.html`: インタラクティブ可視化

## 5. シミュレーション結果

### 遮蔽効果の確認
- vehicle_2-bs_1間で36dBの大きなパスロス変動を確認
- 建物による電波遮蔽が適切に機能
- 他の車両では通常の自由空間パスロス

### 車両移動分析
- 全6台の車両が異なる軌道で移動
- 最大153mの移動距離
- 建物周辺での遮蔽効果を確認
