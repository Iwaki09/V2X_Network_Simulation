# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Rule
コードを更新した後は、必ずResearchProgress.mdも更新すること（日付入りで）

# Language
- ユーザとの対話では常に日本語を使うようにしてください


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
