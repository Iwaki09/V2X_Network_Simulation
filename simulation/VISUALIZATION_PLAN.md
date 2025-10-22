# 可視化スクリプト実装計画

## 概要

前回作成したSUMO + SIONNA RT統合シミュレーションの出力結果を用いて、シミュレーションの様子を時系列で可視化する。車両、基地局、遮蔽物（建物）の位置関係を2Dマップで表示し、基地局と各車両間の通信リンクがLoS/NLoSかを時系列で可視化する。

## 目的

- 車両、基地局、遮蔽物（建物）の位置関係を2Dマップで表示
- 基地局と各車両間の通信リンクが**見通し内 (LoS)** か **見通し外 (NLoS)** かを時系列で可視化

## 入力ファイル

1. **`output/link_quality_results.csv`**: Ray Tracingによるリンク品質（`is_line_of_sight` など）の結果
2. **`output/fcd_output.xml`**: SUMOによる車両の時系列座標データ

## 出力

- **`frames/frame_XXXX.png`**: 各タイムステップの可視化画像（連番PNG）

---

## 実装フェーズ

### Phase 1: 実装計画の作成とディレクトリ準備
- [x] `simulation/VISUALIZATION_PLAN.md` を作成（詳細実装計画）
- [x] `simulation/frames/` ディレクトリの作成準備を確認

### Phase 2: データ読み込みモジュールの実装
- [x] `visualize.py` ファイル作成
- [x] FCDパース関数実装（`fcd_parser.py`からインポートまたは再実装）
- [x] CSVデータ読み込み（`pandas`）
- [x] データマージロジック実装（`timestamp` + `vehicle_id`キー）

### Phase 3: 静的オブジェクトの描画関数
- [x] 基地局描画関数（BS at (500, 150)）
- [x] 建物描画関数（Rectangle at (500, 50), size 20×20）
- [x] 道路描画関数（X: 0-1000, Y: -3.5~3.5）

### Phase 4: 動的オブジェクトの描画関数
- [x] 車両マーカー描画関数（各timestepの車両位置）
- [x] 通信リンク描画関数（BS→車両）
- [x] LoS/NLoS判定による色分けロジック（緑=LoS、赤=NLoS）

### Phase 5: フレーム生成ループの実装
- [x] 全timestepループ処理
- [x] 各timestepでの図生成（matplotlib）
- [x] タイムスタンプテキスト表示
- [x] 縦横比 `'equal'` 設定
- [x] PNG画像保存（`frames/frame_XXXX.png`形式）

### Phase 6: テストと動作確認
- [ ] 仮想環境での構文チェック
- [ ] サンプルデータでの動作確認（数フレーム生成）
- [ ] 全フレーム生成テスト

### Phase 7: ドキュメント更新
- [ ] `README.md` に可視化セクション追加
  - `visualize.py` の実行方法
  - `frames/` ディレクトリの説明
  - 生成される画像の仕様
- [ ] アニメーション作成方法の記載（ffmpeg例など）

### Phase 8: 最終確認とコミット
- [ ] コード品質確認（docstring、コメント）
- [ ] 全体動作確認
- [ ] 各Phase完了時にgit commit作成

---

## 技術仕様

### 使用ライブラリ

- **matplotlib**: 静止画のプロット
- **pandas**: CSVファイルの効率的な読み込み
- **xml.etree.ElementTree**: SUMOのXMLファイルパース

### データマージロジック

1. `fcd_output.xml` をパースし、各 `timestamp` における各 `vehicle_id` の `x`, `y` 座標を取得
2. `link_quality_results.csv` を読み込む
3. 上記2つのデータを `timestamp` と `vehicle_id` をキーとしてマージ（結合）し、各時刻の「車両ID、X座標、Y座標、LoS/NLoS情報」を紐付ける

### 可視化仕様

#### 静的オブジェクト（常にプロット）

- **道路**: X軸 0〜1000, Y軸 -3.5〜3.5 の範囲
- **基地局 (BS)**: (500, 150) の位置に青色マーカー（`^`）
- **建物 (Obstacle)**: (500, 50) を中心とする 20×20 の灰色四角形（`Rectangle`）

#### 動的オブジェクト（timestepごと）

- **車両 (Vehicles)**: その時刻に存在する全車両の `(x, y)` 座標に黒色マーカー（`o`）
- **通信リンク (Links)**: 基地局 (500, 150) から各車両の `(x, y)` 座標まで直線
  - **LoS (is_line_of_sight == True)**: **緑色**の線
  - **NLoS (is_line_of_sight == False)**: **赤色**の線

#### その他

- グラフの隅に現在の `timestamp` (例: "Time: 10.0s") をテキスト表示
- グラフの縦横比 (aspect ratio) は `'equal'` に設定

---

## ディレクトリ構造（更新後）

```
simulation/
├── sumo_config/
│   ├── road.net.xml
│   ├── traffic.rou.xml
│   └── simulation.sumocfg
├── output/
│   ├── fcd_output.xml
│   └── link_quality_results.csv
├── frames/                     # 新規追加
│   ├── frame_0000.png         # タイムステップ0
│   ├── frame_0001.png         # タイムステップ1
│   └── ...
├── fcd_parser.py
├── raytracing_simulation.py
├── run_raytracing.py
├── run_simulation.sh
├── visualize.py               # 新規追加
├── README.md
├── IMPLEMENTATION_PLAN.md
└── VISUALIZATION_PLAN.md      # このファイル
```

---

## 注意事項

- 各フェーズ完了ごとにコミット作成
- ブランチは`simulation/vis`のまま使用
- commitの作成時に許可を取る必要はない
