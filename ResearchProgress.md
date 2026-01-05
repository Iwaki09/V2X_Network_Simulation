## 研究テーマ概要

### 研究テーマ
V2X通信環境における物理伝搬シミュレーションを統合したネットワークのグローバル最適化手法

### 背景と課題
自動運転を支えるV2X通信では、車両の移動や周辺環境による電波遮蔽が頻発し通信品質が大きく揺らぐ。従来の分散型・リアクティブなネットワーク制御は各車両が局所的な品質情報のみで基地局を選択するため、特定基地局への集中によるリソース不足など全体最適を損なう課題が残る。

### 研究目的
高精度な物理伝搬シミュレーションから得られるリアルタイムのリンク品質情報を活用し、集中制御型のグローバル最適化によって総スループット、公平性、遅延などネットワーク全体の指標を最大化する手法を提案・検証する。

### 提案手法の概要
中央コントローラー（MECサーバー想定）が交通流シミュレーターからの車両動態情報とレイトレーシングによるリンク品質情報を統合し、動的グラフとして状態を表現したうえで、数理最適化あるいは将来的にはグラフニューラルネットワークを用いてネットワーク全体の大域的最適化を行い、得られた接続・リソース割当計画を各車両や基地局へ指示する。

### シミュレーション環境
- 交通流シミュレーター: SUMO
- 物理伝搬シミュレーター: SIONNA RT
- ネットワークシミュレーター: NS-3
- グラフネットワーク最適化: Python

### 期待される効果と新規性
- 分散型制御と比較した場合の総スループット向上、通信の安定化、リソース利用効率の改善。
- レイトレーシングに基づく現実的な物理伝搬情報を直接最適化に取り込む点、および中央集権的枠組みでV2Xの動的環境に対する大域的最適化を追求する点が新規性となる。

## 2025-10-22
- V2X通信で動的に変化するリンク品質を中央集権的に最適化する研究テーマを整理。物理伝搬シミュレーションを取り込んだグローバル最適化を目指す方針を明文化。
- 利用コンポーネント: SUMOで1km直線道路上の交通流を生成しFCDを出力、SIONNA RTとTensorFlowで28GHz帯のレイトレーシング評価、Pythonスクリプト群でデータ連携と最適化入力の整形、Bashスクリプトでワークフロー自動化、matplotlibで時系列可視化を構成。
- 構築済みパイプライン: run_simulation.shによりSUMO再実行オプションを含む一括実行を提供し、FCD解析→遮蔽判定付きリンク品質算出→link_quality_results.csv集計→visualize.pyによるLoS/NLoS可視化フレーム生成まで接続。
- 物理シナリオ: 基地局(500,150,30m)、建物遮蔽物(500,50,20×20×100m)、車両アンテナ高1.5mを固定し、遮蔽物貫通時の追加損失を含めた受信電力・パスロス評価を実施。
- 取得可能な成果物: タイムステップごとのtimestamp/vehicle_id/受信電力/遅延スプレッド/パスロス/LoSフラグを含むCSVと、基地局-車両リンク状態を描いた連番PNGを生成し、集中制御アルゴリズムの検証データとして利用可能な状態に整理。

## 2025-10-23
- V2I（基地局-車両）シミュレーションを拡張し、V2V（車両間）通信のリンク品質計算を追加実装。
- raytracing_simulation.pyを修正: LinkQualityデータクラスにlink_type（"V2I"/"V2V"）とrx_id（旧vehicle_id）フィールドを追加。_calculate_single_linkメソッドで単一リンク計算を共通化し、V2Iとv2vの両方を統一的に処理。
- V2V送信電力を23dBm、V2I送信電力を30dBmに設定し、calculate_link_qualityメソッドで各タイムステップにおいてN台の車両に対し、N個のV2Iリンク+N×(N-1)個のV2Vリンクを計算するよう変更。
- run_raytracing.pyのCSV出力フォーマットを変更: timestamp/link_type/tx_id/rx_id/received_power/path_loss/delay_spread/is_line_of_sightの順に列を再構成し、V2I/V2Vリンクの統計情報をサマリー表示に追加。
- simulation/README.mdを更新: 概要にV2V通信の追加を明記、無線パラメータセクションにV2V送信電力（23dBm）を追記、link_quality_results.csvの列定義とサンプル出力を新フォーマットに更新、V2Iは車両数N個、V2Vは N×(N-1)個のリンクが生成されることを注釈で説明。
- これにより、集中制御アルゴリズムはV2IとV2Vの両リンク品質を統合的に活用した動的ネットワーク最適化が可能となり、車両間の直接通信を含めたより現実的なV2Xシナリオでの検証が可能に。

## 2025-11-10
- 分散型制御ベースラインの実装を完了し、提案手法の改善余地を定量的に評価可能にした。
- **simulate_distributed_control.py**を新規作成: 各車両が他車の状況を考慮せず自身にとって最強のV2Iリンクを1つだけ選択する局所最適アプローチをシミュレート。timestamp×rx_idでグループ化し各グループでtheoretical_throughput_mbpsが最大となるリンクを選択、タイムスタンプごとのV2I総スループットをbaseline_distributed_results.csvに出力。
- 複数基地局シナリオ（BS_1, BS_2...）への将来的拡張を考慮した設計を採用: 各車両が複数のV2I候補から最強リンクを選ぶロジックにより、基地局追加時にも同一アルゴリズムで対応可能。
- **plot_baseline_comparison.py**を新規作成: theoretical_network_results.csvから理論的最大値（V2I+V2V全活用時）を計算し、分散型ベースライン（V2Iのみ）との比較グラフをbaseline_comparison.pngに出力。2系列折れ線グラフ（緑破線=理論的最大値、青実線=分散型ベースライン）に加え、改善余地をグレーエリアで可視化。
- 実験結果: 分散型ベースラインの平均スループットは3124.58 Mbps、理論的最大値の平均は20192.70 Mbpsで、**平均84.5%の改善余地**が存在することを確認。これは、分散型制御ではV2Vリンクが未活用であり、グローバル最適化によるV2I/V2V協調制御で大幅な性能向上が期待できることを示す。
- simulation/README.mdを更新: 「分散型制御ベースラインの評価」セクションを追加し、局所最適アルゴリズムの説明、複数基地局シナリオへの拡張性、ベースライン比較グラフの見方、期待される研究成果（84.5%の改善余地）を詳述。ディレクトリ構造も更新。
- これにより、次フェーズのグローバル最適化手法（数理最適化またはGNN）の実装において、分散型制御との明確な性能比較が可能となり、提案手法の有効性を定量的に示すベースラインが確立された。

## 2025-11-12
- **グローバル最適化（提案手法）の実装完了**: 整数線形計画問題（ILP）として定式化し、PuLPソルバーを用いてシステム全体の総スループットを最大化する集中制御型アルゴリズムを実装した。
- **solve_global_optimization.py**を新規作成: 各タイムスタンプでILP問題を構築・求解し、制約条件（各車両は最大1リンク、基地局BS_1は最大10ユーザー）を満たしつつスループット総和を最大化。100タイムスタンプの最適化を実行し、global_optimization_results.csvに出力。
- **ILP定式化の詳細**:
  - **目的関数**: Σ(theoretical_throughput_mbps × x_link) の最大化（x_linkはバイナリ決定変数）
  - **制約条件1（車両）**: 各車両vについて、tx_id==v または rx_id==v のリンクの合計 ≤ 1（無線リソースが1つのみ）
  - **制約条件2（基地局）**: tx_id=="BS_1" のリンクの合計 ≤ 10（多重接続制限）
- **plot_final_comparison.py**を新規作成: 提案手法（グローバル最適化）と従来手法（分散型ベースライン）の性能比較グラフをfinal_performance_comparison.pngに出力。青実線（Proposed）vs. 紫破線（Baseline）の2系列折れ線グラフに統計情報と性能向上率を表示。
- **実験結果**:
  - **提案手法**: 平均3362.44 Mbps、最大5494.83 Mbps
  - **従来手法**: 平均3124.58 Mbps、最大4796.67 Mbps
  - **性能向上率**: 平均1.08倍（+7.6%）、最大1.15倍（+14.6%）
- **主要な知見**:
  1. 集中制御により全体スループットが平均7.6%向上、ピーク時には14.6%向上
  2. 高品質なV2Vリンクを積極的に活用することで基地局リソース制約を回避
  3. ILP定式化により各タイムステップ平均1秒未満で最適解を取得可能（リアルタイム性の確認）
  4. 理論的最大値（20192.70 Mbps）とは依然として大きなギャップがあり、更なる改善余地が存在
- simulation/README.mdを更新: 「グローバル最適化（提案手法）」セクションを追加し、ILP定式化の詳細（目的関数・制約条件）、実行方法、出力フォーマット、研究成果（性能向上率と主要な知見）を詳述。ディレクトリ構造も更新し、solve_global_optimization.py、plot_final_comparison.py、requirements.txtを追加。
- これにより、本研究の核心である「集中制御型グローバル最適化」のベースライン実装が完了し、分散型制御との明確な性能差（7.6%向上）を定量的に示すことができた。今後は、GNNなどの機械学習手法による更なる性能向上や、動的環境での適応性向上を目指す。

## 2026-01-03
- **simulation/ディレクトリのリファクタリング完了**: Pythonファイルをモジュール構造に整理し、保守性と再利用性を向上させた。
- **不要ファイルの削除**:
  - frames/ ディレクトリ（output/visualizations/frames/と重複）
  - 古いバックアップファイル（fcd_output.xml.backup.*）
  - 古いアニメーション（animation.mp4 → animation2.mp4をリネーム）
- **新ディレクトリ構造**:
  ```
  simulation/
  ├── src/                    # ソースコードパッケージ
  │   ├── parsers/           # fcd_parser.py
  │   ├── core/              # raytracing.py, throughput.py
  │   ├── optimization/      # distributed.py, global_optimizer.py
  │   └── visualization/     # link_visualizer.py, plots.py
  ├── scripts/               # 実行スクリプト
  │   ├── run_raytracing.py
  │   ├── run_throughput.py
  │   ├── run_optimization.py
  │   └── run_visualization.py
  └── run_simulation.sh      # 統合実行スクリプト
  ```
- **可視化スクリプトの統合**: plot_network_summary.py, plot_baseline_comparison.py, plot_final_comparison.pyを1つのplots.pyモジュールに統合。
- **README.mdを全面更新**: APIリファレンス、パラメータ一覧、出力フォーマット、トラブルシューティングを含む包括的なドキュメントを作成。
- **SIONNA依存の分離**: src/core/__init__.pyでSIONNA依存のraytracingモジュールを遅延インポートに変更し、GPU環境がなくても他のモジュールが利用可能に。

## 2026-01-04
- **Propagation-Mode Switch (D/K) の実装**: link_quality_results.csvに伝搬モード指標を追加し、将来のマルチパス解析に備えた基盤を構築。
- **新規ファイル追加**:
  - `src/core/propagation_mode.py`: D/K計算のユーティリティモジュール。compute_dk()関数でパス電力リストからDominance (D)、K-factor (K)、伝搬モード (prop_mode) を計算。
- **コード変更**:
  - `src/core/raytracing.py`: LinkQualityデータクラスに7つの新フィールド（num_paths, p_tot_watts, p_max_watts, dominance, k_factor, k_factor_db, prop_mode）を追加。_calculate_single_link()でcompute_dk()を呼び出して各リンクのD/K値を計算。
  - `scripts/run_raytracing.py`: CSV出力に新しい7列を追加。inf値の文字列変換に対応。
- **新しいCSV列の定義**:
  - `num_paths`: パス数（現状は常に1）
  - `p_tot_watts`: 総受信電力 [Watts]
  - `p_max_watts`: 最大パス電力 [Watts]
  - `dominance`: Dominance指標 D = P_max / P_tot (0-1)
  - `k_factor`: K-factor（線形値）。K = P_max / (P_tot - P_max)
  - `k_factor_db`: K-factor [dB]
  - `prop_mode`: 伝搬モード ("D" or "K")。D >= 0.5 なら "D"
- **設計方針**: 現状の簡易パスロスモデル（フリスの式）では単一パスとして計算されるため、すべてのリンクでD=1.0、prop_mode="D"となる。将来的にSionna RTのCIR（Channel Impulse Response）から複数パス情報を取得する拡張に備えた設計。
- **後方互換性**: 既存の列（timestamp, link_type, tx_id, rx_id, received_power, path_loss, delay_spread, is_line_of_sight）は変更なし。throughput/optimization/visualizationの後段パイプラインは正常に動作することを確認。
- simulation/README.mdを更新: link_quality_results.csvの列定義に新しい7列を追加し、Propagation-Mode Switch (D/K) についての説明を追記。

## 2026-01-04（追加）
- **Sionna RTマルチパス対応を実装**: `--sionna-rt`オプションで本格的なレイトレーシングによるマルチパス計算が可能に。
- **raytracing.pyの拡張**:
  - `use_sionna_rt`フラグで簡易モデル/Sionna RTモードを切り替え可能に
  - `_setup_sionna_scene()`: Sionna RTシーン構築（建物、地面、材質定義）
  - `_compute_paths_sionna()`: レイトレーシング実行、マルチパス電力抽出、RMS遅延スプレッド計算
  - `_calculate_single_link()`: 両モードに対応するよう拡張
- **run_raytracing.pyの更新**:
  - `--sionna-rt`: Sionna RTモードを有効化
  - `--max-depth`: 最大反射回数（デフォルト: 3）
  - `--num-samples`: レイサンプル数（デフォルト: 1000000）
- **D/Kモデルの活用**: Sionna RTモードでは複数パスの電力リストからDominance (D) とK-factorを計算。散乱的なマルチパス環境（D < 0.5）では prop_mode = "K" となり、支配的パスがある環境（D >= 0.5）では prop_mode = "D" となる。
- **注意**: Sionna RTモードはGPU環境（TensorFlow + CUDA）が必要。GPU環境がない場合は簡易モデルを使用。

## 2026-01-05
- `Scene.compute_paths()`を使わず、`PathSolver`でのパス計算に統一してSionna RTのAPIに合わせた。
- `paths.cir()`からCIRと遅延を抽出する処理に整理し、送受信機追加/削除を`try/finally`で保護。
- `raytracing.py`で`scene.tx_array`/`scene.rx_array`を明示設定。
- `PathSolver(num_samples=...)`が未対応の環境向けに`TypeError`フォールバックを追加。

## 2026-01-05（追加）
- **MCS（離散レート）ベースのスループット推定を実装**: Shannon理論容量に加え、現実的な離散MCSテーブルによるスループット計算を追加。
- **新規ファイル追加**:
  - `src/core/mcs_model.py`: MCSテーブル（8段階）とルックアップ関数を提供。SNR閾値ベースでMCSインデックスを選択し、対応するスペクトル効率からスループットを計算。
- **throughput.pyの拡張**:
  - `calculate_theoretical_throughput(df, rate_model)`: rate_model引数を追加（'shannon', 'mcs', 'both'）
  - `process_link_quality_data(input_csv, output_csv, rate_model)`: rate_model引数を追加
  - MCS計算時には統計情報（MCSインデックス分布、Shannon vs MCS比較）を表示
- **run_throughput.pyの更新**:
  - `--rate-model {shannon,mcs,both}`: レートモデル選択オプションを追加（デフォルト: shannon）
  - `--input`, `--output`: 入出力パス指定オプションを追加
- **MCSテーブル仕様（研究用簡略モデル）**:
  | MCS Index | SNR閾値 [dB] | スペクトル効率 [bits/s/Hz] | 変調方式相当 |
  |-----------|-------------|--------------------------|-------------|
  | 0 | < -5 | 0.15 | QPSK 1/8 |
  | 1 | -5 ~ 0 | 0.38 | QPSK 1/3 |
  | 2 | 0 ~ 5 | 0.88 | QPSK 2/3 |
  | 3 | 5 ~ 10 | 1.48 | 16QAM 1/2 |
  | 4 | 10 ~ 15 | 2.40 | 16QAM 3/4 |
  | 5 | 15 ~ 20 | 3.30 | 64QAM 2/3 |
  | 6 | 20 ~ 25 | 4.40 | 64QAM 5/6 |
  | 7 | >= 25 | 5.50 | 256QAM 3/4 |
- **新しいCSV列（mcs/bothモード）**:
  - `mcs_index`: 選択されたMCSインデックス (0-7)
  - `spectral_efficiency_bpshz`: スペクトル効率 [bits/s/Hz]
  - `throughput_mbps_mcs`: MCSベースのスループット [Mbps]
- **動作確認結果**:
  - MCSインデックス分布: MCS 1-7に分散（SNR範囲 -4.10～45.47 dB）
  - Shannon平均: 383.71 Mbps → MCS平均: 219.01 Mbps（MCS/Shannon: 57.1%）
  - 離散化による効率低下は理論通りの挙動
- **後方互換性**: デフォルト（shannon）モードでは既存の`theoretical_throughput_mbps`列のみ出力。最適化・可視化パイプラインは正常動作を確認。
- simulation/README.mdを更新: MCSモデルのAPIリファレンス、MCSテーブル仕様、出力フォーマットにMCS列を追記、更新履歴を追加。
