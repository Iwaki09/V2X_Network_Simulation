# SIONNA RT の仕様とハマりやすいポイント (詳細版)

このドキュメントは、Sionna RT を使用する際に遭遇しやすい具体的な問題点と、それに関連するSionna RTの主要なAPI仕様を詳細にまとめたものです。これまでのデバッグセッションで実際に直面した「ハマりやすいポイント」に焦点を当てて解説します。

## 2.1 シーンの初期化とオブジェクトの追加

### 仕様
`sionna.rt.Scene` クラスは、シミュレーション環境を定義するための基盤となります。シーン内の物理的なオブジェクト（建物、送信機、受信機など）は、`Scene` オブジェクトの `add()` メソッドを使用して個別にシーンに追加する必要があります。

### ハマりやすいポイント

*   **XMLファイルの直接ロードの誤解**:
    *   **誤ったコード例**:
        ```python
        import sionna.rt as sn
        # ... mitsuba_xml_path が定義されているとする
        rt_scene = sn.rt.Scene(xml_file=mitsuba_xml_path)
        ```
    *   **エラーメッセージ**:
        ```
        TypeError: Scene.__init__() got an unexpected keyword argument 'xml_file'
        ```
    *   **原因**: Sionna RT の `Scene` クラスのコンストラクタは、Mitsuba 3 のXMLファイルを直接ロードするための引数 `xml_file` を持っていません。Mitsuba 3 のXMLファイルは、Mitsuba 3 レンダリングエンジンがシーンを定義するために使用するものであり、Sionna RT の `Scene` オブジェクトは、Python API を通じてプログラム的に構築されることを想定しています。
    *   **解決策**: `rt_scene = sn.rt.Scene()` のように引数なしで `Scene` オブジェクトを初期化し、その後 `rt_scene.add(sn.rt.Transmitter(...))` や `rt_scene.add(sn.rt.Receiver(...))` のように、個々のオブジェクトを `add()` メソッドを使ってシーンに追加します。建物などの複雑な形状は、Sionna RT が提供するプリミティブ（例: `sn.rt.Box`）や、外部ツール（Blenderなど）で作成したモデルをインポートする機能（ただし、これは `Scene` コンストラクタの引数ではない）を利用して追加します。

## 2.2 アンテナアレイの設定

### 仕様
`PathSolver` がレイトレーシングによるパス計算を実行するためには、シーンに送信機アレイ (`scene.tx_array`) と受信機アレイ (`scene.rx_array`) が設定されている必要があります。これらのアレイは、`sionna.rt.PlanarArray` などのクラスを使用して定義され、シーン内のすべての送信機および受信機に適用されるデフォルトのアンテナ特性を決定します。

### ハマりやすいポイント

*   **アレイ設定の不足**:
    *   **誤ったコード例**:
        ```python
        import sionna.rt as sn
        # ... rt_scene が初期化され、Transmitter/Receiver が追加されているとする
        path_solver = sn.rt.PathSolver()
        paths = path_solver(scene=rt_scene, max_depth=5) # tx_array/rx_array が未設定
        ```
    *   **エラーメッセージ**:
        ```
        ValueError: Transmitter array not set
        ```
    *   **原因**: `PathSolver` は、パス計算を実行する際に、送信機と受信機のアンテナ構成に関する情報が `Scene` オブジェクトに設定されていることを期待します。個々の `Transmitter` や `Receiver` オブジェクトを `rt_scene.add()` で追加するだけでは、アンテナアレイの全体的な設定が不足していると判断されます。
    *   **解決策**: `Scene` オブジェクトの初期化後、`rt_scene.tx_array` および `rt_scene.rx_array` 属性に `sn.rt.PlanarArray(...)` などの適切なアンテナアレイオブジェクトを設定します。
        ```python
        import sionna.rt as sn
        # ...
        rt_scene = sn.rt.Scene()
        rt_scene.tx_array = sn.rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                             horizontal_spacing=0.5, pattern="dipole", polarization="V")
        rt_scene.rx_array = sn.rt.PlanarArray(num_rows=1, num_cols=1, vertical_spacing=0.5,
                                             horizontal_spacing=0.5, pattern="dipole", polarization="V")
        # ... Transmitter/Receiver の追加
        ```

## 2.3 パス計算 (`PathSolver`)

### 仕様
`sionna.rt.PathSolver` クラスは、レイトレーシングアルゴリズムを実行し、シーン内の送信機と受信機間の伝搬パスを特定します。このクラスのインスタンスは、Pythonの関数のように呼び出すことでパス計算を実行します。

### ハマりやすいポイント

*   **`compute_paths` メソッドの誤用**:
    *   **誤ったコード例**:
        ```python
        path_solver = sn.rt.PathSolver()
        paths = path_solver.compute_paths(rt_scene, max_depth=5)
        ```
    *   **エラーメッセージ**:
        ```
        AttributeError: 'PathSolver' object has no attribute 'compute_paths'
        ```
    *   **原因**: `PathSolver` オブジェクトは `compute_paths` という名前の直接のメソッドを持っていません。Sionna RT の設計では、`PathSolver` のインスタンス自体が呼び出し可能オブジェクト (`__call__` メソッドが実装されている) として機能し、パス計算を実行します。
    *   **解決策**: `paths = path_solver(scene=rt_scene, max_depth=5)` のように、`PathSolver` のインスタンスを直接呼び出します。

*   **`num_samples` 引数の誤った渡し方**:
    *   **誤ったコード例**:
        ```python
        path_solver = sn.rt.PathSolver()
        paths = path_solver(scene=rt_scene, max_depth=5, num_samples=1e6)
        ```
    *   **エラーメッセージ**:
        ```
        TypeError: PathSolver.__call__() got an unexpected keyword argument 'num_samples'
        ```
    *   **原因**: `num_samples` (レイトレーシングに使用するサンプルの数) は、`PathSolver` のコンストラクタに渡すべき引数であり、`__call__` メソッドには渡しません。`PathSolver` のインスタンス化時に設定された `num_samples` が内部的に使用されます。
    *   **解決策**: `path_solver = sn.rt.PathSolver(num_samples=1e6)` のようにコンストラクタで `num_samples` を設定し、`paths = path_solver(scene=rt_scene, max_depth=5)` のように `__call__` メソッドからは `num_samples` を削除します。

## 2.4 パス情報からのチャネルインパルス応答 (CIR) 抽出 (`Paths.cir()`)

### 仕様
`PathSolver` の呼び出しによって返される `Paths` オブジェクトは、計算されたすべての伝搬パスに関する詳細な情報を含んでいます。`Paths.cir()` メソッドは、これらのパスを基底帯域等価チャネルインパルス応答 (CIR) に変換します。このメソッドは引数を取らずに呼び出され、すべての送信機-受信機ペアに対するCIRをまとめて返します。

### ハマりやすいポイント

*   **`tx` / `rx` 引数の誤用**:
    *   **誤ったコード例**:
        ```python
        a, _ = paths.cir(tx=f"tx_{bs['id']}", rx=f"rx_{v['id']}")
        ```
    *   **エラーメッセージ**:
        ```
        TypeError: Paths.cir() got an unexpected keyword argument 'tx'
        ```
    *   **原因**: `Paths.cir()` は、特定の送信機や受信機を指定するための引数を持ちません。`Paths` オブジェクトは既にすべてのペアのパス情報を含んでおり、`cir()` はそれらすべてに対するCIRを返します。
    *   **解決策**: `a, _ = paths.cir()` のように引数なしで呼び出し、返されたテンソルから必要なCIRを後で抽出します。

*   **戻り値の型とインデックス付けの誤解**:
    *   **誤ったコード例**:
        ```python
        a, _ = paths.cir()
        # ...
        path_gain = tf.reduce_sum(tf.square(tf.abs(a[i, 0, j, 0, :, :])), axis=[-1]).numpy()[0]
        ```
    *   **エラーメッセージ**:
        ```
        TypeError: list indices must be integers or slices, not tuple
        ```
        または
        ```
        InvalidArgumentError: slice index 1 of dimension 2 out of bounds.
        ```
    *   **原因**:
        1.  `paths.cir()` の戻り値 `a` は、**Pythonのリスト**として返されることがあります。このリストの各要素が、個別の `drjit.cuda.ad.TensorXf` オブジェクト（Sionna RTが内部的に使用するテンソル型）です。
        2.  各 `drjit.cuda.ad.TensorXf` の形状は `(num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time_steps)` です。
        3.  `tf.stack()` を使用してリストを結合しようとすると、新しい次元が追加され、形状が `(num_stacked_elements, num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time_steps)` のようになることがあります。しかし、`drjit.cuda.ad.TensorXf` は直接TensorFlowテンソルではないため、`tf.stack()` の前に明示的な変換が必要です。
        4.  インデックス `a[i, 0, j, 0, :, :]` は、`i` が受信機インデックス、`j` が送信機インデックスとして使用されることを意図していますが、`a` がリストである場合、直接多次元インデックス付けはできません。また、`tf.stack()` 後も、次元の解釈を誤ると `slice index out of bounds` エラーが発生します。特に、`num_rx_ant` や `num_tx_ant` が1の場合、対応する次元のインデックスは0しか許されません。
    *   **解決策**:
        1.  `a` がリストの場合、まず `a` の各要素を `tf.convert_to_tensor(x)` でTensorFlowテンソルに変換します。
        2.  その後、`a` のリストの最初の要素 (`a[0]`) がすべての送信機-受信機ペアのCIRテンソルであると仮定し、そのテンソルに対して正しいインデックス付けを行います。
        3.  **修正後のコード例**:
            ```python
            a, _ = paths.cir()
            # a は drjit.cuda.ad.TensorXf のリストとして返されるため、TensorFlowテンソルに変換
            a = [tf.convert_to_tensor(x) for x in a]
            # ここで a は TensorFlow テンソルのリスト。
            # 複数の要素がある場合、それらが何を表すかによって結合方法が変わる。
            # 今回のケースでは、a[0] が全ての (rx, tx) ペアの CIR を含むテンソルだった。
            # そのため、a[0] を直接使用する。
            
            # パスロス計算ループ内で、a[0] に対してインデックス付けを行う
            for i, bs in enumerate(scene.base_stations): # i は基地局 (tx) のインデックス
                for j, v in enumerate(scene.vehicles): # j は車両 (rx) のインデックス
                    # a[0] の形状は (num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time_steps)
                    # したがって、受信機インデックスが j、送信機インデックスが i の場合、
                    # 正しいアクセスは a[0][j, 0, i, 0, :, :] となる
                    # (num_rx は受信機数、num_tx は送信機数)
                    path_gain = tf.reduce_sum(tf.square(tf.abs(a[0][j, 0, i, 0, :, :])), axis=[-1]).numpy()[0]
                    # ... (残りのパスロス計算ロジック)
            ```
            **注**: 上記の `i` と `j` の役割は、`scene.base_stations` と `scene.vehicles` のループの順序に依存します。もし `i` が `base_stations` のインデックス、`j` が `vehicles` のインデックスであれば、`a[0][j, 0, i, 0, :, :]` が正しいインデックス付けとなります。これは、`a` の最初の次元が受信機、3番目の次元が送信機に対応しているためです。

## 2.5 全体的な注意点

Sionna RT は、Mitsuba 3 をバックエンドとする高度なレイトレーシングライブラリであり、そのAPIは一般的なTensorFlowの操作とは異なる独自のパターンを持つことがあります。

*   **ドキュメントとサンプルコードの徹底的な参照**: エラーに遭遇した際は、Sionna RT の公式ドキュメントやGitHubリポジトリのサンプルコードを注意深く参照し、APIの正しい使用方法を確認することが最も重要です。特に、各クラスのコンストラクタの引数、メソッドの呼び出し方、および戻り値のデータ構造（形状と型）には細心の注意を払う必要があります。
*   **データ構造の理解**: `Paths.cir()` の戻り値のように、一見すると単純なテンソルに見えても、実際にはリストの中にテンソルが格納されているなど、複雑なデータ構造を持つ場合があります。`print(type(var))` や `print(var.shape)` を活用して、変数の型と形状を常に確認することがデバッグの鍵となります。特に、`drjit.cuda.ad.TensorXf` のようなSionna RT独自のテンソル型は、TensorFlowの操作を行う前に `tf.convert_to_tensor()` で明示的に変換する必要があることを忘れないでください。
*   **バージョン互換性**: TensorFlow、CUDA、cuDNN、Sionna RT の各ライブラリのバージョン互換性は非常に重要です。問題が発生した場合は、まずこれらのバージョンが推奨される組み合わせであるかを確認してください。公式ドキュメントで推奨されるバージョンを使用することが、最も安定した動作を保証します。
