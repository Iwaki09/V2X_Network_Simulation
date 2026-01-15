# ESSENTIAL: Ray Tracing -> Graph / Optimization

このファイルは、Ray Tracing 実行からグラフ作成までの最短手順のみをまとめています。

## 前提
- 作業ディレクトリは `simulation/`
- Python 仮想環境は `../.venv`
- FCD が未生成の場合は「補足: FCD 生成」を先に実行

## 基本フロー（Ray Tracing -> Throughput -> Optimization -> Graph）
```bash
# 1) 仮想環境
source ../.venv/bin/activate

# 2) Ray Tracing（既存FCDを使用）
python scripts/run_raytracing.py --scenario corner_intersection
# Sionna RT を使う場合
# python scripts/run_raytracing.py --scenario corner_intersection --sionna-rt

# 3) Throughput 計算
python scripts/run_throughput.py --scenario corner_intersection
# MCSベースで計算したい場合
# python scripts/run_throughput.py --scenario corner_intersection --rate-model mcs

# 4) 最適化（分散 + グローバル）
python scripts/run_optimization.py --scenario corner_intersection

# 5) グラフ作成
python scripts/run_visualization.py --scenario corner_intersection --all
```

## 出力先
- Ray Tracing: `output/scenarios/{scenario}/raytracing/link_quality_results.csv`
- Throughput: `output/scenarios/{scenario}/throughput/theoretical_network_results.csv`
- Optimization: `output/scenarios/{scenario}/optimization/`
- グラフ: `output/scenarios/{scenario}/figures/`

## 交差点シナリオで実行したい場合
`--scenario corner_intersection` に置き換えるだけです。

## bs_load_O.png を出したい場合（最終比較プロット）
`bs_load_O.png` は最終比較スクリプトの出力に含まれます。

```bash
# 仮想環境
source ../.venv/bin/activate

# 最終比較（Obj-T / Obj-O を含む）
python ../scripts/run_final_comparison.py \
  --input-theoretical output/scenarios/default/throughput/theoretical_network_results.csv \
  --outdir output/optimization_comparison_full \
  --bs-capacity 10 \
  --rolling-window 10
```

出力先: `output/optimization_comparison_full/plots/bs_load_O.png`

## 補足: FCD 生成（未作成の場合のみ）
```bash
# SUMO -> FCD のみ
./run_simulation.sh --sumo

# SUMO + Ray Tracing まで一括
./run_simulation.sh --sumo --scenario default
# その後に throughput と可視化を実行
python scripts/run_throughput.py --scenario default
python scripts/run_visualization.py --scenario default --all
```

## 参考: フルパイプライン（Optimization まで）
```bash
./run_simulation.sh --all --scenario default
# グラフは別途生成
python scripts/run_visualization.py --scenario default --all
```
