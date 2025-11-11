# グローバル最適化実装計画

## 概要
システム全体の総スループットを最大化する「グローバル最適化（集中制御型）」アルゴリズムを実装し、「分散型ベースライン」との性能比較を行う。

## 実装ステップ

### Phase 1: 環境準備
- [x] 作業用ブランチの作成
- [x] `requirements.txt` の作成/更新（pulpライブラリの追加）
- [x] 入力データの確認（`theoretical_network_results.csv`の存在確認）

### Phase 2: グローバル最適化ソルバーの実装
- [x] `solve_global_optimization.py` の骨組み作成
- [x] データ読み込み処理の実装
- [x] タイムスタンプごとのループ処理の実装
- [x] PuLPによるILP問題の定式化
  - [x] 決定変数の定義（バイナリ変数）
  - [x] 目的関数の定義（スループット最大化）
  - [x] 制約条件1: 車両の制約（1リンクまで）
  - [x] 制約条件2: 基地局の制約（K=10リンクまで）
- [x] ソルバー実行と結果の保存
- [x] `global_optimization_results.csv` の出力

### Phase 3: グローバル最適化の動作確認
- [x] スクリプトの実行テスト
- [x] 出力ファイルの検証
- [x] 結果の妥当性確認

### Phase 4: 比較グラフ作成
- [x] `plot_final_comparison.py` の作成
- [x] データ読み込み処理の実装
- [x] matplotlibによるグラフ描画
  - [x] 提案手法（グローバル最適化）の折れ線グラフ
  - [x] ベースライン（分散型）の折れ線グラフ
  - [x] 軸ラベル、タイトル、凡例の設定
- [x] `final_performance_comparison.png` の出力

### Phase 5: グラフ生成の動作確認
- [ ] スクリプトの実行テスト
- [ ] 出力画像の確認

### Phase 6: ドキュメント更新
- [ ] `simulation/README.md` の更新
  - [ ] グローバル最適化の説明追加
  - [ ] ILP定式化の説明追加
  - [ ] 制約条件の詳細説明追加
  - [ ] 比較グラフの意義説明追加

### Phase 7: 最終確認とPR作成
- [ ] 全体の動作確認
- [ ] ResearchProgress.mdの更新
- [ ] Pull Requestの作成

## パラメータ設定
- `MAX_BS_CONNECTIONS = 10`: 基地局が同時に処理できる最大ユーザー数

## 出力ファイル
1. `simulation/global_optimization_results.csv`
2. `simulation/final_performance_comparison.png`
