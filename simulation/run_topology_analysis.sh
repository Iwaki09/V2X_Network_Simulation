#!/bin/bash

# V2Xネットワーク トポロジー解析・可視化 統合実行スクリプト

set -e  # エラー時に停止

echo "============================================================"
echo "V2X Topology Analysis Pipeline"
echo "============================================================"

# 仮想環境をアクティベート
source ../.venv/bin/activate

# Step 1: グローバル最適化（リンク選択情報を保存）
echo ""
echo "[Step 1/3] Running Global Optimization..."
python solve_global_optimization.py

# Step 2: トポロジー解析（車両の分類）
echo ""
echo "[Step 2/3] Running Topology Classification..."
python analyze_topology.py

# Step 3: トポロジー可視化（スナップショット生成）
echo ""
echo "[Step 3/3] Running Topology Visualization..."
python visualize_topology.py

echo ""
echo "============================================================"
echo "Pipeline Completed Successfully!"
echo "============================================================"
echo ""
echo "Output Files:"
echo "  - Global Optimization Results: output/baseline/global_optimization_results.csv"
echo "  - Active Links Details: output/baseline/global_optimization_links.csv"
echo "  - Topology Classification: output/analysis/topology_classification.csv"
echo "  - Topology Visualizations: output/visualizations/topology/*.png"
echo ""
