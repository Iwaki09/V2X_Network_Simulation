# SIONNA RT XMLシーンマテリアル定義ガイド

このドキュメントは、SIONNA RTで正しく動作するXMLシーンファイルのマテリアル定義方法について詳細にまとめたものです。

## 概要

SIONNA RTは、Mitsuba 3をベースとしたレイトレーシングライブラリですが、無線通信シミュレーション用の特別なマテリアル定義が必要です。通常のMitsuba 3 BSDFタイプではなく、SIONNA RT固有の無線マテリアルを使用する必要があります。

## 1. サポートされているBSDFタイプ

SIONNA RTでサポートされている主要なBSDFタイプは以下の通りです：

### 1.1 ITU無線マテリアル（推奨）
```xml
<bsdf type="itu-radio-material" id="concrete_material">
    <string name="type" value="concrete"/>
    <float name="thickness" value="0.2"/>
</bsdf>
```

### 1.2 一般的な無線マテリアル
```xml
<bsdf type="radio-material" id="custom_material">
    <float name="eta_r" value="5.24"/>
    <float name="sigma" value="0.123"/>
    <float name="thickness" value="0.1"/>
</bsdf>
```

### 1.3 基本的なMitsuba 3 BSDFタイプ（制限あり）
```xml
<!-- 拡散反射 -->
<bsdf type="diffuse" id="simple_material">
    <rgb name="reflectance" value="0.5, 0.5, 0.5"/>
</bsdf>

<!-- 誘電体 -->
<bsdf type="dielectric" id="dielectric_material">
    <float name="int_ior" value="1.5"/>
    <float name="ext_ior" value="1.0"/>
</bsdf>

<!-- 導体 -->
<bsdf type="conductor" id="conductor_material">
    <string name="material" value="Au"/>
</bsdf>
```

## 2. Holder-Materialの問題とエラー回避

### 2.1 問題の背景
`holder-material`タイプは、SIONNA RT v1.0.2で削除または変更されており、以下のエラーが発生します：
```
Plugin 'holder-material' not found
```

### 2.2 回避策
以下のいずれかの方法でエラーを回避できます：

#### 方法1：ITU無線マテリアルの直接使用
```xml
<!-- 問題のあるコード -->
<bsdf type="holder-material" id="concrete">
    <bsdf type="itu" id="concrete_itu">
        <string name="itu_type" value="concrete"/>
        <float name="thickness" value="0.2"/>
    </bsdf>
</bsdf>

<!-- 修正されたコード -->
<bsdf type="itu-radio-material" id="concrete">
    <string name="type" value="concrete"/>
    <float name="thickness" value="0.2"/>
</bsdf>
```

#### 方法2：基本的なBSDFタイプの使用
```xml
<bsdf type="diffuse" id="concrete">
    <rgb name="reflectance" value="0.5, 0.5, 0.5"/>
</bsdf>
```

## 3. ITUマテリアルの正しい定義方法

### 3.1 利用可能なITUマテリアルタイプ
- `concrete`：コンクリート（建物の壁）
- `brick`：レンガ
- `plasterboard`：石膏ボード
- `wood`：木材
- `glass`：ガラス
- `metal`：金属

### 3.2 ITUマテリアルの詳細例
```xml
<!-- コンクリート -->
<bsdf type="itu-radio-material" id="concrete">
    <string name="type" value="concrete"/>
    <float name="thickness" value="0.2"/>
</bsdf>

<!-- 金属 -->
<bsdf type="itu-radio-material" id="metal">
    <string name="type" value="metal"/>
    <float name="thickness" value="0.01"/>
</bsdf>

<!-- ガラス -->
<bsdf type="itu-radio-material" id="glass">
    <string name="type" value="glass"/>
    <float name="thickness" value="0.006"/>
</bsdf>
```

### 3.3 自動変換機能
SIONNA RTは、マテリアルIDが以下のパターンの場合、自動的にITU無線マテリアルに変換します：
- `mat-itu_`で始まるID
- `itu_`で始まるID

例：
```xml
<bsdf type="diffuse" id="itu_concrete">
    <!-- 自動的にITU無線マテリアルに変換される -->
</bsdf>
```

## 4. 建物用マテリアルの実用的な例

### 4.1 完全なXMLシーン例
```xml
<scene version="3.0.0">
    <integrator type="direct"/>
    
    <!-- 建物用マテリアル -->
    <bsdf type="itu-radio-material" id="building_concrete">
        <string name="type" value="concrete"/>
        <float name="thickness" value="0.2"/>
    </bsdf>
    
    <!-- 車両用マテリアル -->
    <bsdf type="itu-radio-material" id="vehicle_metal">
        <string name="type" value="metal"/>
        <float name="thickness" value="0.002"/>
    </bsdf>
    
    <!-- 地面用マテリアル -->
    <bsdf type="diffuse" id="ground_material">
        <rgb name="reflectance" value="0.3, 0.8, 0.3"/>
    </bsdf>
    
    <!-- 建物 -->
    <shape type="cube" id="building1">
        <transform name="to_world">
            <translate x="50.0" y="50.0" z="15.0"/>
            <scale x="10.0" y="40.0" z="15.0"/>
        </transform>
        <ref id="building_concrete"/>
    </shape>
    
    <!-- 車両 -->
    <shape type="cube" id="vehicle1">
        <transform name="to_world">
            <translate x="20.0" y="20.0" z="1.75"/>
            <scale x="2.0" y="1.0" z="0.75"/>
        </transform>
        <ref id="vehicle_metal"/>
    </shape>
    
    <!-- 地面 -->
    <shape type="rectangle" id="ground">
        <transform name="to_world">
            <translate x="100.0" y="100.0" z="0"/>
            <scale x="100.0" y="100.0" z="1"/>
        </transform>
        <ref id="ground_material"/>
    </shape>
</scene>
```

### 4.2 フォールバック用シンプル例
```xml
<scene version="3.0.0">
    <integrator type="direct"/>
    
    <!-- 誘電体マテリアル（コンクリート相当） -->
    <bsdf type="dielectric" id="concrete">
        <float name="int_ior" value="1.5"/>
        <float name="ext_ior" value="1.0"/>
    </bsdf>
    
    <!-- 導体マテリアル（金属） -->
    <bsdf type="conductor" id="metal">
        <string name="material" value="Au"/>
    </bsdf>
    
    <!-- 拡散反射（地面） -->
    <bsdf type="diffuse" id="ground">
        <rgb name="reflectance" value="0.3, 0.8, 0.3"/>
    </bsdf>
    
    <!-- 形状とマテリアルの関連付けは上記と同様 -->
</scene>
```

## 5. トラブルシューティング

### 5.1 よくあるエラーと対処法

#### エラー1：Plugin 'holder-material' not found
**原因**：SIONNA RT v1.0.2以降で`holder-material`が非対応
**対処法**：`itu-radio-material`または基本BSDFタイプを使用

#### エラー2：Plugin 'radio-material' not found
**原因**：Mitsuba 3にSIONNA RTプラグインが正しく登録されていない
**対処法**：`itu-radio-material`を使用、またはSIONNA RTの初期化を確認

#### エラー3：Plugin 'itu' not found
**原因**：`itu`タイプは廃止され、`itu-radio-material`に統合
**対処法**：`itu-radio-material`タイプを使用

### 5.2 デバッグのコツ
1. **段階的な検証**：まずシンプルなBSDFタイプ（`diffuse`）で動作を確認
2. **マテリアル名の確認**：`itu_`プレフィックスによる自動変換機能を活用
3. **ログの確認**：SIONNA RTの初期化時のマテリアル登録ログを確認

## 6. パフォーマンスと精度の考慮事項

### 6.1 マテリアル選択の指針
- **高精度が必要**：ITU無線マテリアル（`itu-radio-material`）
- **汎用性重視**：基本BSDFタイプ（`diffuse`, `dielectric`, `conductor`）
- **デバッグ用**：シンプルな`diffuse`マテリアル

### 6.2 周波数依存性
ITU無線マテリアルは周波数に依存して特性が変化します：
```python
# Pythonコードでの周波数設定例
scene.frequency = 2.4e9  # 2.4 GHz
# この設定により、ITUマテリアルの特性が自動更新される
```

## 7. まとめ

SIONNA RTでXMLシーンを正しく動作させるための要点：

1. **holder-materialは使用しない**（v1.0.2以降）
2. **itu-radio-materialを推奨**（無線通信シミュレーション用）
3. **基本BSDFタイプも利用可能**（汎用性とデバッグ用）
4. **マテリアル名のプレフィックスを活用**（`itu_`による自動変換）
5. **段階的な検証でエラーを回避**

このガイドに従って、SIONNA RTで安定して動作するXMLシーンファイルを作成できます。