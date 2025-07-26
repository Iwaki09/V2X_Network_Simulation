# Sionna RT 関連のナレッジベース

このドキュメントは、Sionna RT を使用する際に遭遇した問題とその解決策、およびSionna RTの主要な仕様と注意点をまとめたものです。

## 1. CUDA/cuDNN デバッグから得られた知見

### 問題の概要
TensorFlow (Sionna RTのバックエンド) がGPUを認識せず、`RuntimeError: No GPU found` や `factory ... already registered` といったエラーが発生しました。

### 診断プロセス
1.  **`ldd` コマンドによるライブラリ依存関係の確認**: TensorFlowの内部ライブラリ (`_pywrap_tensorflow_internal.so`, `libtensorflow_cc.so.2`, `libtensorflow_framework.so.2`) がどの共有ライブラリにリンクしているかを調査しました。
2.  **`strace` コマンドによるファイルアクセス追跡**: プログラムが実行中にどのファイルを開こうとして失敗しているかを詳細に追跡し、不足しているライブラリや競合しているライブラリを特定しました。

### 根本原因
*   TensorFlow 2.19.0 が公式にサポートするcuDNNバージョン (8.9.7) と、システムにインストールされていたcuDNNバージョン (8.9.7.29) の間に互換性の問題、またはライブラリの競合が発生していました。特に、TensorFlowが `libcudnn.so.9` を探しているにもかかわらず、システムには `libcudnn8` がインストールされていました。
*   CUDA 12.9 がインストールされていましたが、TensorFlow 2.19.0 は CUDA 12.3 を公式にサポートしており、バージョン間の不一致が問題の一因となっていました。

### 解決策
1.  **`libcudnn9` のインストール**: `sudo apt-get update && sudo apt-get install libcudnn9-cuda-12` コマンドで `libcudnn9` をインストールしました。これにより、TensorFlowが期待するcuDNNバージョンが提供されました。
2.  **`LD_LIBRARY_PATH` の設定**: CUDA 12.9 のライブラリパス (`/usr/local/cuda-12.9/lib64`) を `LD_LIBRARY_PATH` 環境変数に設定することで、TensorFlowがGPUライブラリを正しく見つけられるようになりました。

### 重要な教訓
*   **TensorFlowの互換性マトリックスの確認**: TensorFlowは特定のCUDAおよびcuDNNバージョンとの互換性があります。公式ドキュメントでサポートされているバージョンを常に確認することが重要です。
*   **共有ライブラリの競合**: `factory ... already registered` のようなエラーは、複数のバージョンのライブラリがシステムに存在し、競合している可能性を示唆します。`ldd` や `strace` などのツールが診断に役立ちます。
*   **環境変数の重要性**: `LD_LIBRARY_PATH` は、プログラムが共有ライブラリを検索するパスを決定するため、GPU関連の問題では特に重要です。

## 2. SIONNA RT の仕様とハマりやすいポイント

### 1. シーンの初期化
*   **仕様**: `sn.rt.Scene()` は、XMLファイルを直接引数として受け取りません。シーン内のオブジェクト（送信機、受信機、建物など）は、`scene.add()` メソッドを使用して個別にシーンに追加する必要があります。
*   **ハマりやすいポイント**: `sn.rt.Scene(xml_file=...)` のようにXMLファイルを直接渡すと `TypeError` が発生します。

### 2. アンテナアレイの設定
*   **仕様**: `PathSolver` がパスを計算するためには、`scene.tx_array` (送信機アレイ) と `scene.rx_array` (受信機アレイ) を明示的に設定する必要があります。例えば、`sn.rt.PlanarArray` を使用します。
*   **ハマりやすいポイント**: これらを省略すると `ValueError: Transmitter array not set` のようなエラーが発生します。

### 3. パス計算 (`PathSolver`)
*   **仕様**: `PathSolver` は、まずインスタンス化 (`path_solver = sn.rt.PathSolver()`) され、その後、関数のように呼び出されることでパスを計算します (`paths = path_solver(scene=rt_scene, max_depth=5)` など)。
*   **ハマりやすいポイント**:
    *   `path_solver.compute_paths()` のようにメソッドとして呼び出すと `AttributeError` が発生します。
    *   `num_samples` などのパラメータは、`PathSolver` のコンストラクタ (`sn.rt.PathSolver(num_samples=1e6)`) で設定し、`__call__` メソッドには渡しません。

### 4. パス情報からのチャネルインパルス応答 (CIR) 抽出 (`Paths.cir()`)
*   **仕様**: `paths.cir()` メソッドは引数を取らずに呼び出されます (`a, tau = paths.cir()`)。これは、`PathSolver` が既に計算したすべての送信機-受信機ペアのCIRを返します。
*   **ハマりやすいポイント**:
    *   `paths.cir(tx=..., rx=...)` のように `tx` や `rx` 引数を渡すと `TypeError` が発生します。
    *   `paths.cir()` の戻り値 `a` は、`drjit.cuda.ad.TensorXf` オブジェクトのPython `list` です。
    *   各 `drjit.cuda.ad.TensorXf` の形状は `(num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths, num_time_steps)` です。
    *   特定の送信機-受信機ペアのデータにアクセスするには、まず `tf.convert_to_tensor()` を使用して `drjit.cuda.ad.TensorXf` をTensorFlowテンソルに変換し、その後、適切なインデックス付け (`a[0][rx_idx, 0, tx_idx, 0, :, :]` のように) を行う必要があります。`a` がリストであるため、`a[0]` のようにリストの要素にアクセスしてからテンソルとしてインデックス付けします。

### 全体的な注意点
Sionna RT は強力なツールですが、そのAPIは一般的なTensorFlowのパターンと異なる場合があり、ドキュメントやサンプルコードを注意深く参照することが重要です。
特に、オブジェクトの初期化、メソッドの呼び出し方、および戻り値のデータ構造には注意が必要です。
