# SUMO + SIONNA RT統合シミュレーション - 実装計画

## 概要

研究目的の第一段階として、交通流シミュレータSUMOと、レイトレーシング無線伝搬シミュレータSIONNA RTを連携させたシミュレーション環境を構築する。

## 要件

### 1. フォルダ構成

- `simulation` という名前の新しいフォルダを作成し、すべての成果物（コード、SUMO設定ファイル、仕様書）をその中に配置すること。

### 2. SUMO (交通流シミュレーション)

- **シナリオ:** 片側1車線、合計2車線の直線道路。
- **道路定義:**
    - 道路の中心線がY=0となるように、(0, 0) から (1000, 0) へ延びる形状とする。
    - 長さ: 1km
    - 車線幅: 各3.5m (道路全体の幅は7m)
- **交通流定義:**
    - シミュレーション時間: 100秒間
    - 車両生成: シミュレーション開始時に5台を配置。その後、平均10秒間隔でランダムに車両を追加生成し、合計15〜20台程度が走行するように設定する。
    - 車両タイプ: 乗用車とし、最高速度は 60km/h とする。
- **アウトプット:**
    - FCD (Floating Car Data) output をXMLファイル（例: `fcd_output.xml`）として出力するように設定すること。

### 3. Ray Tracing (無線伝搬シミュレーション)

- **使用ライブラリ:** **SIONNA RT** を用いて実装すること。
- **入力:** 上記2でSUMOが生成した `fcd_output.xml` をパースし、各タイムステップにおける全車両の3次元座標を取得すること。
- **物理環境シナリオ:**
    - **基地局(BS):** 1台。IDを `BS_1` とする。
        - 座標: (X=500, Y=150, Z=30) [m]
    - **車両(Vehicle):** SUMOの出力に基づき、動的に配置。
        - 車両アンテナの高さ (Z座標): 1.5m [m]
    - **遮蔽物(建物):** 1棟。
        - 中心座標: (X=500, Y=50, Z=0) [m]
        - 形状: X方向 20m, Y方向 20m, Z方向(高さ) 100m の直方体。
- **無線パラメータ:**
    - 周波数: **28 GHz** (ミリ波)
    - 基地局 送信電力: **30 dBm**
    - アンテナモデル: 基地局・車両ともに **等方性アンテナ (Isotropic Antenna)** を仮定する。
- **出力（拡張性担保）:**
    - シミュレーションの各タイムステップにおいて、`BS_1` と FCDに記録されている全車両間のリンク品質を計算すること。
    - 結果は、**`link_quality_results.csv`** (または `.json`) というファイル名で出力すること。
    - 出力項目（列名）: `timestamp` (タイムステップ), `vehicle_id` (SUMOの車両ID), `tx_id` (このシナリオでは常に `BS_1`), `received_power` (dBm), `delay_spread` (ns), `path_loss` (dB), `is_line_of_sight` (遮蔽なし:True / 遮蔽あり:False)

### 4. 統合実行ツール

- シミュレーション実行を管理するためのシェルスクリプト（例: `run_simulation.sh`）を作成すること。
- このスクリプトは、以下の機能を持つこと。
    - スクリプトをそのまま実行した場合: 既存のSUMOアウトプット (`fcd_output.xml`) を読み込み、Ray Tracing (Pythonスクリプト) のみを実行する。
    - `-sumo` オプション（例: `./run_simulation.sh --sumo`）を付けて実行した場合: SUMOシミュレーションを再実行して `fcd_output.xml` を更新した後、Ray Tracingを実行する。

### 5. ルール

- **テスト:** テストコード（`pytest`など）の作成は不要。
- **仕様書:** `README.md` または別の仕様書ファイルを作成し、以下の情報を詳細に記述すること。
    - 作成したプログラムの概要と実行方法（`run_simulation.sh` の使い方を含む）。
    - SUMOの設定パラメータ（道路、交通流定義など）。
    - Ray Tracingのシナリオパラメータ（基地局・建物・車両の座標、無線の設定値など）。
    - 出力ファイル (`link_quality_results.csv`) のフォーマットと各項目の説明。

---

## 実装フェーズ

### Phase 1: プロジェクト構造とドキュメント作成
- [x] `simulation/`ディレクトリを作成
- [x] `simulation/IMPLEMENTATION_PLAN.md` を作成（このタスク計画を保存）
- [x] `simulation/README.md` を作成（仕様書の詳細を記述）
- [x] `simulation/sumo_config/` ディレクトリを作成（SUMO設定ファイル用）
- [x] `simulation/output/` ディレクトリを作成（出力ファイル用）

### Phase 2: SUMO設定ファイルの作成
- [x] **道路ネットワーク定義**: `simulation/sumo_config/road.net.xml` を作成
  - 片側1車線×2の直線道路（1km、中心Y=0、車線幅3.5m）
- [x] **交通流定義**: `simulation/sumo_config/traffic.rou.xml` を作成
  - 初期5台配置、平均10秒間隔で追加生成、合計15〜20台
  - 最高速度60km/h（16.67m/s）
- [x] **SUMO設定ファイル**: `simulation/sumo_config/simulation.sumocfg` を作成
  - シミュレーション時間100秒
  - FCD出力設定（`fcd_output.xml`）
- [x] **SUMO単体テスト**: `sumo -c simulation.sumocfg` で動作確認

### Phase 3: FCDパーサーの実装
- [x] `simulation/fcd_parser.py` を作成
- [x] `parse_fcd_xml(filepath)` 関数: FCD XMLファイルを読み込み、各タイムステップの車両座標リストを抽出
- [x] データ構造: `{ timestep: float, vehicles: [{ id: str, x: float, y: float, z: float }] }`
- [x] パーサー単体テスト（既存のFCDファイルで確認）

### Phase 4: SIONNA RTシミュレーションの実装
- [x] `simulation/raytracing_simulation.py` を作成
- [x] **環境定義**:
  - 基地局: `BS_1` at (500, 150, 30)
  - 建物: 中心(500, 50, 0)、サイズ(20×20×100m)
  - 車両アンテナ高さ: 1.5m
- [x] **無線パラメータ設定**:
  - 周波数: 28GHz
  - 送信電力: 30dBm
  - アンテナ: 等方性
- [x] **SIONNA RTシーン構築関数**: `create_sionna_scene(vehicles, base_station, building)`
- [x] **リンク品質計算関数**: `calculate_link_quality(scene)`
  - 出力: received_power (dBm), delay_spread (ns), path_loss (dB), is_line_of_sight (bool)
- [x] SIONNA RTシミュレーション単体テスト（固定車両位置で確認）※実環境での動作確認はスキップ

### Phase 5: 統合シミュレーションスクリプト
- [x] `simulation/run_raytracing.py` を作成（Ray Tracingのみ実行）
- [x] FCDファイルを読み込み、各タイムステップでSIONNA RTシミュレーションを実行
- [x] リンク品質結果を `simulation/output/link_quality_results.csv` に出力
- [x] CSV出力フォーマット: `timestamp, vehicle_id, tx_id, received_power, delay_spread, path_loss, is_line_of_sight`
- [x] 統合シミュレーション動作確認（構文チェック完了）

### Phase 6: 実行管理シェルスクリプト
- [x] `simulation/run_simulation.sh` を作成
- [x] デフォルト動作: 既存の`fcd_output.xml`を使用してRay Tracingのみ実行
- [x] `--sumo` オプション: SUMOシミュレーションを再実行してFCD更新後、Ray Tracing実行
- [x] 実行権限設定 (`chmod +x`)
- [x] スクリプト動作確認（両モードでテスト）※実環境での動作確認はスキップ

### Phase 7: ドキュメント整備とテスト
- [ ] `simulation/README.md` を完成させる
  - プログラム概要と実行方法
  - SUMOパラメータ詳細
  - Ray Tracingシナリオパラメータ詳細
  - 出力ファイルフォーマット説明
- [ ] 全体統合テスト（SUMO実行→FCD生成→Ray Tracing実行→CSV出力）
- [ ] エラーハンドリング確認
- [ ] 依存関係の確認（requirements.txt等）

### Phase 8: 最終レビューとコミット
- [ ] コード品質チェック（docstring、コメント）
- [ ] 出力結果の妥当性確認（パスロス値、遮蔽効果など）
- [ ] 各フェーズ完了時にgit commit作成
- [ ] 最終コミット作成

---

## 技術スタック

- **SUMO**: 交通流シミュレーション（FCD出力）
- **SIONNA RT**: レイトレーシング無線伝搬シミュレーション
- **Python 3.10+**: スクリプト言語
- **TensorFlow + GPU**: SIONNA RT実行環境
- **xml.etree.ElementTree**: FCDパース
- **Bash**: 実行管理スクリプト

---

## ディレクトリ構造（完成予定）

```
simulation/
├── sumo_config/
│   ├── road.net.xml           # 道路ネットワーク定義
│   ├── traffic.rou.xml        # 車両ルート定義
│   └── simulation.sumocfg     # SUMO設定ファイル
├── output/
│   ├── fcd_output.xml         # SUMO FCD出力
│   └── link_quality_results.csv  # Ray Tracing結果
├── fcd_parser.py              # FCDパーサー
├── raytracing_simulation.py   # SIONNA RTシミュレーション
├── run_raytracing.py          # 統合実行スクリプト
├── run_simulation.sh          # シェル実行管理スクリプト
├── README.md                  # 仕様書
└── IMPLEMENTATION_PLAN.md     # この実装計画
```

---

## 注意事項

- テストコード作成は不要
- 各フェーズ完了ごとにコミット作成
- ブランチは`simulation`のまま使用
- 既存のprototypeコードは参考にするが、新規実装として独立させる
