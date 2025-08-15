# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Language
- ユーザとの対話では常に日本語を使うようにしてください

# Git
- 大きいタスクが完了したら、毎回`git add`と`git commit`、`git push`を行うこと

# Environment
- Pythonの実行にあたっては、常に仮想環境 `.venv`に入って作業をすること

# Common Development Commands

## Prototype 1 (Basic Simulation)
```bash
# メインシミュレーション実行
python3 prototype/main.py

# TypeScript可視化ツールのビルドと実行
cd prototype/visualizer-ts
npm run build  # TypeScriptコンパイル
npm run dev    # 開発サーバー起動
```

## Prototype 2 (SIONNA RT Integration)
```bash
# メインV2Xシミュレーション実行
python3 prototype2/simulation.py

# 可視化生成
python3 prototype2/visualization.py

# 建物遮蔽効果の分析
python3 prototype2/analyze_occlusion.py

# 車両間距離テスト
python3 prototype2/test_v2v_distances.py
```

## Prototype 3 (Web Animation)
```bash
# HTMLアニメーション確認
cd prototype3
python3 -m http.server 13191
```

# Project Architecture

## Core Components
- **Vehicle Simulation**: 車両の移動と通信シミュレーション（4～6台の車両）
- **SIONNA RT Integration**: レイトレーシングによる高精度パスロス計算
- **Building Occlusion**: ITU推奨材料パラメータによる建物遮蔽効果
- **Network Optimization**: 集中制御型のグローバル最適化アルゴリズム
- **Visualization**: Web/TypeScriptベースのインタラクティブ可視化

## Simulation Framework
### Prototype 1 (`prototype/`)
- 基本的なV2Xシミュレーション
- NumPy/SciPyによる簡易的な物理モデル
- TypeScript可視化ツール (`visualizer-ts/`)

### Prototype 2 (`prototype2/`)  
- SIONNA RT統合によるレイトレーシングシミュレーション
- 建物による電波遮蔽効果（+15dB追加パスロス）
- V2I（車両-基地局）とV2V（車両間）通信サポート
- 動的シナリオによる時系列シミュレーション

### Prototype 3 (`prototype3/`)
- Webベースのシンプルなアニメーション

## Dependencies
- **SIONNA**: TensorFlowベースの無線通信シミュレーションライブラリ
- **TensorFlow**: 機械学習とSIONNAバックエンド
- **NumPy**: 数値計算とベクトル演算
- **TypeScript/Vite**: フロントエンド可視化ツール

# Run Server
- javascriptやhtmlなどでブラウザから見れる画面を作った際には、その`index.html`がある場所に移動した上で、`python3 -m http.server 13191`でサーバーを立てること。検証が終わったらサーバーを閉じること。

# Other Rules
- 大きいタスクが完了したら、README.mdを更新すること
- 毎回実装前に計画を立てるようにしてください