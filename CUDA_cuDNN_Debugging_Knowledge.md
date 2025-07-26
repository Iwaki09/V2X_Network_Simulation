# CUDA/cuDNN デバッグから得られた知見

このドキュメントは、TensorFlow (Sionna RTのバックエンド) がGPUを認識しない問題に焦点を当て、その診断プロセス、根本原因、および解決策を詳細にまとめたものです。

## 1.1 問題の概要

Sionna RT を実行しようとした際に、TensorFlowがGPUを正しく認識せず、以下のエラーメッセージが表示されました。

*   `RuntimeError: No GPU found. SIONNA RT requires a GPU.`
*   `E external/local_xla/xla/stream_executor/cuda/cuda_fft.cc:467] Unable to register cuFFT factory: Attempting to register factory for plugin cuFFT when one has already been registered`
*   `E0000 ... cuda_dnn.cc:8579] Unable to register cuDNN factory: Attempting to register factory for plugin cuDNN when one has already been registered`
*   `E0000 ... cuda_blas.cc:1407] Unable to register cuBLAS factory: Attempting to register factory for plugin cuBLAS when one has already been registered`
*   `W0000 ... computation_placer.cc:177] computation placer already registered. Please check linkage and avoid linking the same target more than once.`

これらのエラーは、TensorFlowがCUDAおよびcuDNNライブラリをロードする際に問題が発生していることを示唆していました。

## 1.2 診断プロセスとハマったポイント

### 1.2.1 `ldd` コマンドによるライブラリ依存関係の確認

まず、TensorFlowの主要な共有ライブラリがどの依存関係を持っているかを調査しました。

**実行コマンド:**
```bash
find . -name _pywrap_tensorflow_internal.so
# 出力例: ./.venv/lib/python3.10/site-packages/tensorflow/python/_pywrap_tensorflow_internal.so

ldd ./.venv/lib/python3.10/site-packages/tensorflow/python/_pywrap_tensorflow_internal.so
# および、その依存ライブラリである libtensorflow_cc.so.2, libtensorflow_framework.so.2 に対しても ldd を実行
```

**得られた知見:**
*   `ldd` の出力からは、CUDAやcuDNNのライブラリへの直接的なリンクは確認できませんでした。これは、TensorFlowがこれらのライブラリを動的に（実行時に `dlopen` システムコールなどを使って）ロードするため、`ldd` では表示されないことを示唆していました。

### 1.2.2 `strace` コマンドによるファイルアクセス追跡

次に、プログラムが実行中にどのファイルを開こうとして失敗しているかを詳細に追跡するために `strace` を使用しました。

**実行コマンド:**
```bash
strace -e openat python3 prototype2/main.py
```

**得られた知見:**
*   `strace` の出力から、TensorFlowが `libcudnn.so.9` を探していることが判明しました。
    *   `openat(AT_FDCWD, "/usr/local/lib/libcudnn.so.9", O_RDONLY|O_CLOEXEC) = -1 ENOENT (そのようなファイルやディレクトリはありません)`
    *   `openat(AT_FDCWD, "/usr/local/cuda/lib64/libcudnn.so.9", O_RDONLY|O_CLOEXEC) = -1 ENOENT (そのようなファイルやディレクトリはありません)`
*   しかし、`dpkg -l | grep cudnn` の結果から、システムには `libcudnn8` (バージョン 8.9.7.29) がインストールされていることが確認できました。
    *   `ii libcudnn8 8.9.7.29-1+cuda12.2 amd64 cuDNN runtime libraries`

**ハマったポイント:**
*   TensorFlowが期待するcuDNNのバージョン (`libcudnn.so.9`) と、実際にインストールされているcuDNNのバージョン (`libcudnn8`) が異なっていました。これは、TensorFlowのバイナリが特定のcuDNNバージョンに依存してコンパイルされているため、バージョン不一致がロードエラーを引き起こしていました。
*   `factory ... already registered` のエラーは、複数のCUDA関連ライブラリが混在しているか、TensorFlowが内部的に持つライブラリとシステムにインストールされているライブラリが競合していることを示唆していました。

### 1.2.3 CUDA バージョンの確認と互換性問題

`nvcc` コマンドのパスから、システムにインストールされているCUDAのバージョンを確認しました。

**実行コマンド:**
```bash
find /usr/local/cuda* -name nvcc
# 出力例: /usr/local/cuda-12.9/bin/nvcc
```

**得られた知見:**
*   システムにはCUDA 12.9がインストールされていました。
*   ウェブ検索 (`TensorFlow 2.19.0 CUDA cuDNN compatibility`) により、TensorFlow 2.19.0が公式にサポートするCUDAバージョンは12.3、cuDNNは8.9.7であることが判明しました。

**ハマったポイント:**
*   インストールされているCUDA (12.9) がTensorFlowが公式にサポートするバージョン (12.3) よりも新しかったため、互換性の問題が発生していました。TensorFlowのバイナリが古いCUDAバージョン用にコンパイルされている場合、新しいライブラリとの間で競合やロード失敗が起こりえます。

## 1.3 解決策

上記の問題を解決するために、以下の手順を実行しました。

1.  **`libcudnn9` のインストール**:
    *   TensorFlowが要求する `libcudnn.so.9` を提供するために、システムに `libcudnn9` をインストールしました。
    *   **実行コマンド (ユーザーが手動で実行):**
        ```bash
        sudo apt-get update
        sudo apt-get install libcudnn9-cuda-12
        ```
    *   これにより、TensorFlowが期待するcuDNNバージョンがシステムに提供され、`Unable to register cuDNN factory` などのエラーが解消されました。

2.  **`LD_LIBRARY_PATH` の設定**:
    *   CUDA 12.9 のライブラリパス (`/usr/local/cuda-12.9/lib64`) を `LD_LIBRARY_PATH` 環境変数に設定することで、TensorFlowがGPUライブラリを正しく見つけられるようにしました。
    *   **実行コマンド (Pythonスクリプト実行時に毎回設定):**
        ```bash
bash
export LD_LIBRARY_PATH=/usr/local/cuda-12.9/lib64:$LD_LIBRARY_PATH && python3 prototype2/main.py
        ```
    *   これにより、`RuntimeError: No GPU found` エラーが解消され、TensorFlowがGPUを認識できるようになりました。

## 1.4 重要な教訓

*   **TensorFlowの互換性マトリックスの厳守**: TensorFlowを使用する際は、公式ドキュメントで示されているCUDAおよびcuDNNの互換性マトリックスを厳密に確認し、それに合致するバージョンをインストールすることが極めて重要です。バージョンが新しすぎても問題が発生します。
*   **共有ライブラリの競合の診断**: `ldd` や `strace` といった低レベルのツールは、共有ライブラリのロードに関する問題を診断する上で非常に強力です。特に `strace -e openat` は、プログラムがどのファイルをオープンしようとして失敗しているかを特定するのに役立ちます。
*   **環境変数の適切な設定**: `LD_LIBRARY_PATH` は、プログラムが共有ライブラリを検索するパスを制御するため、GPU関連の問題では常に確認すべき重要な環境変数です。
