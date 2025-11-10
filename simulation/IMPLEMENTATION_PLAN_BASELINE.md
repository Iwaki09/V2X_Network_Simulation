# 分散型制御ベースライン実装計画

## 概要
従来の「分散型・局所最適」な制御をシミュレートし、理論的最大値との比較を可視化する。

## 実装タスク

### Phase 1: ブランチ作成とデータ確認
- [x] 新しいブランチ `feature/distributed-baseline` を作成
- [x] `theoretical_network_results.csv` のデータ構造を確認

### Phase 2: 分散型制御シミュレータの実装
- [x] `simulate_distributed_control.py` のファイル骨格を作成
- [x] CSVファイル読み込み処理を実装
- [x] V2Iリンクのフィルタリング処理を実装
- [x] 各車両が最強V2Iリンクを1つ選択するロジックを実装
  - timestamp と rx_id でグループ化
  - 各グループで theoretical_throughput_mbps が最大の行を選択
- [x] タイムスタンプごとのV2I総スループット計算を実装
- [x] 結果を `baseline_distributed_results.csv` に出力
- [x] 動作確認とデバッグ
- [x] コミット作成: "feat: 分散型制御シミュレータを実装"

### Phase 3: ベースライン性能可視化スクリプトの実装
- [x] `plot_baseline_comparison.py` のファイル骨格を作成
- [x] 理論的総容量（V2I + V2V）の計算処理を実装
- [x] 分散型V2I総容量の読み込み処理を実装
- [x] matplotlibによる2系列の折れ線グラフ描画を実装
  - 理論的最大値（天井）
  - 分散型ベースライン
- [x] グラフの装飾（凡例、軸ラベル、タイトル等）を実装
- [x] `baseline_comparison.png` に保存
- [x] 動作確認とデバッグ
- [x] コミット作成: "feat: ベースライン比較可視化を実装"

### Phase 4: 仕様書の更新
- [x] `simulation/README.md` に分散型制御の説明を追記
  - 局所最適アルゴリズムの説明
  - 複数基地局シナリオへの拡張性について
- [x] ベースライン比較グラフの意味を追記
  - 天井とベースラインのギャップの意義
  - グローバル最適化の改善目標領域
- [x] コミット作成: "docs: 分散型ベースライン仕様を追加"

### Phase 5: 研究進捗の記録
- [x] `ResearchProgress.md` を更新（日付入り）
- [x] コミット作成: "docs: 研究進捗を更新"

### Phase 6: PR作成
- [x] Pull Requestを作成
- [x] PR説明文を記述

## 備考
- 各フェーズ完了ごとにコミットを作成
- commit authorにはclaudeを含めない
- 実装中に問題が発生した場合は、この計画を更新する
