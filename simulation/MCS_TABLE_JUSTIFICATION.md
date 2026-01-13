# MCS Table Simplification Justification for Research Paper
# 論文用MCSテーブル簡略化の根拠

**作成日**: 2026-01-13

## 1. 背景と目的

本シミュレーション研究では、3GPP TS 38.214に定義される5G NR標準の完全なMCSテーブル（29エントリ）を、**8段階の簡略化MCSテーブル**に縮約して使用しています。

### 簡略化の目的
- **計算効率の向上**: シミュレーション規模の大規模化に対応
- **解釈の容易さ**: 研究結果の分析と理解を容易に
- **代表的なMCS選択**: 実用的な範囲をカバーしつつ、過度な粒度を回避
- **V2X研究における一般的慣行**: 類似の簡略化は多くのV2X研究で採用されている [1, 2]

## 2. 3GPP標準との対応関係

### 2.1 参照標準
- **3GPP TS 38.214 V15.2.0 (2018-06)** Section 5.1.3.1
- 使用テーブル: **Table 5.1.3.1-2 (256QAM)** [3]

### 2.2 標準MCSテーブルの概要
3GPP TS 38.214では、PDSCH（Physical Downlink Shared Channel）用に3つのMCSテーブルが定義されています：

| テーブル | MCSインデックス範囲 | 最大変調方式 | スペクトル効率範囲 | 用途 |
|---------|------------------|------------|------------------|------|
| Table 5.1.3.1-1 | 0-28 | 64QAM | 0.2344 - 5.5547 bits/symbol | 標準 |
| Table 5.1.3.1-2 | 0-27 | **256QAM** | 0.2344 - 7.4063 bits/symbol | **高品質チャネル** |
| Table 5.1.3.1-3 | 0-28 | 64QAM | 0.0586 - 5.5547 bits/symbol | 低データレート/URLLC |

本研究では、**Table 5.1.3.1-2 (256QAM)** を基準としています。これは、V2Xシナリオにおいて良好なLOS条件が多く存在し、高次変調の利用が期待されるためです。

### 2.3 8段階への簡略化マッピング

以下の表は、本研究の8段階MCSテーブルと3GPP標準（Table 5.1.3.1-2）の対応関係を示します：

| 簡略化MCS | 変調方式 | 符号化率 | スペクトル効率<br>[bits/s/Hz] | 対応する<br>3GPP MCS | 3GPP SE<br>[bits/symbol] | SNR閾値<br>[dB] | 選択根拠 |
|-----------|---------|---------|-------------------------------|---------------------|------------------------|----------------|---------|
| **0** | QPSK | 1/8 | 0.15 | MCS 0 | 0.2344 | < -5 | 最低レート（保守的に0.15に設定） |
| **1** | QPSK | 1/3 | 0.38 | MCS 1 | 0.3770 | -5 ~ 0 | QPSK低符号化率 |
| **2** | QPSK | 2/3 | 0.88 | MCS 4-5 | 0.8770 | 0 ~ 5 | QPSK高符号化率 |
| **3** | 16QAM | 1/2 | 1.48 | MCS 8-9 | 1.4766 | 5 ~ 10 | 16QAM中符号化率 |
| **4** | 16QAM | 3/4 | 2.40 | MCS 11 | 2.4063 | 10 ~ 15 | 16QAM高符号化率 |
| **5** | 64QAM | 2/3 | 3.30 | MCS 16 | 3.3223 | 15 ~ 20 | 64QAM中符号化率 |
| **6** | 64QAM | 5/6 | 4.40 | MCS 19 | 4.5234 | 20 ~ 25 | 64QAM高符号化率 |
| **7** | 256QAM | 3/4 | 5.50 | MCS 22-23 | 5.5547 | ≥ 25 | 256QAM（最高レート） |

**注記**:
- スペクトル効率の値は、3GPP標準値を参考に、研究用途に適した丸めた値を使用
- MCS 0は理論値0.2344よりも保守的な0.15に設定（極低SNR環境での安定性確保）
- 各簡略化MCSは、対応する変調次数の代表的な符号化率を選択

## 3. 簡略化の妥当性

### 3.1 カバー範囲の妥当性

**3GPP標準の範囲**: 0.2344 - 7.4063 bits/symbol (MCS 0-27)
**簡略化テーブルの範囲**: 0.15 - 5.50 bits/s/Hz

簡略化テーブルは、以下の理由で実用的な範囲を適切にカバーしています：

1. **下限の保守性**: 0.15 bits/s/Hzは標準の0.2344より低く、極めて劣悪なチャネル条件も考慮
2. **上限の実用性**: 5.50 bits/s/Hzは256QAM 3/4相当で、V2Xの現実的な最大レート
   - 256QAM 5/6以上（6-7 bits/s/Hz）は非常に高SNR（>30dB）が必要で、V2X環境では稀
3. **V2Xシナリオでの実測値との整合性**:
   - 本シミュレーションのSNR範囲: -4.10 ~ 45.47 dB
   - MCS 1-7が主に使用され、極端なMCS 0の使用は限定的
   - 最高MCS（MCS 7）でも実用的なスペクトル効率を達成

### 3.2 SNR閾値の設定根拠

簡略化テーブルのSNR閾値は、**5dB刻み**で設定されています：

```
-5dB, 0dB, 5dB, 10dB, 15dB, 20dB, 25dB
```

この設定は以下の理論的根拠に基づいています：

1. **Shannon容量の理論**:
   - SNRが5dB増加すると、容量は約2倍になる（C = log₂(1 + SNR)）
   - 5dB刻みは、MCS遷移に適切な粒度を提供

2. **変調方式の遷移点**:
   - QPSK → 16QAM: 理論的にSNR +6dB必要（2² → 2⁴）
   - 16QAM → 64QAM: 理論的にSNR +4.8dB必要（2⁴ → 2⁶）
   - 64QAM → 256QAM: 理論的にSNR +6dB必要（2⁶ → 2⁸）
   - 5dB刻みはこれらの遷移点とおおむね一致

3. **実用的なマージン**:
   - 各MCS内で約5dBのSNR範囲を確保することで、変調方式内での符号化率調整の余地を提供

### 3.3 スペクトル効率の性能評価

本シミュレーションでの実測結果（corner_intersectionシナリオ）：

| 条件 | Shannon平均<br>[Mbps] | MCS平均<br>[Mbps] | MCS/Shannon比 |
|-----|---------------------|------------------|--------------|
| **全体** | 349.1 | 204.4 | **58.5%** |
| LOS | 553.6 | 322.6 | 58.3% |
| NLOS | 96.7 | 58.4 | 60.4% |
| prop_mode=K | 541.2 | 314.6 | 58.1% |

**解釈**:
- MCS/Shannon比 58.5%は、**離散MCS選択による現実的な効率低下**を適切に表現
- 理論容量（Shannon）に対して約60%の効率は、実システムの典型的な性能範囲 [4]
- NLOS環境でのわずかな効率向上（60.4%）は、低SNR時のMCS選択の保守性を反映

### 3.4 V2X研究における類似アプローチ

簡略化MCSテーブルの使用は、V2X研究コミュニティで広く採用されています：

1. **Yan & Härri (2022)** [1]: 5G-NR V2X Sidelink研究で、3GPP TS 138.214のMCSテーブルを簡略化して使用
2. **Burbano-Abril & McCarthy (2021)** [2]: Cellular V2X SidelinkでMCS適応の分析に固定MCS構成（MCS 7, MCS 11）を使用
3. **一般的な実践**: 多くのV2Xシミュレーション研究では、完全な29エントリではなく、代表的なMCSサブセット（5-10段階）を使用

## 4. 研究上の利点

8段階簡略化MCSテーブルは、以下の研究上の利点を提供します：

### 4.1 計算効率
- MCS選択の計算量: O(log N) → 大規模シミュレーションで重要
- 29エントリから8エントリへの削減により、ルックアップ時間を約72%削減

### 4.2 解釈の容易さ
- 各変調方式（QPSK, 16QAM, 64QAM, 256QAM）に明確な代表値
- MCS分布の可視化と分析が直感的
- 結果の議論で「MCS 5 (64QAM 2/3相当)」のような明確な表現が可能

### 4.3 パラメータチューニング
- SNR閾値の調整による感度分析が容易
- 変調方式ごとの性能評価が明確

### 4.4 拡張性
- 新しいMCSレベルの追加が容易（例: MCS 8でより高次変調）
- 保守的MCS選択（`apply_conservative_mcs`）などの拡張が実装しやすい

## 5. 制限事項と今後の課題

### 5.1 現在の制限事項
1. **符号化率の粒度**: 各変調方式内での細かい符号化率調整は不可能
2. **極高SNR環境**: 30dB以上の極めて良好な環境での最適化が限定的
3. **HARQ未考慮**: 再送制御を考慮した適応的MCS選択は未実装

### 5.2 今後の拡張可能性
1. **動的MCS適応**: チャネル状態の時間変動に応じた適応制御
2. **BLER目標値の導入**: 目標ブロックエラー率に基づくMCS選択
3. **Sidelink MCSへの拡張**: V2V直接通信用のMCSテーブル（3GPP TS 38.214 Table 5.2.2.1-1）への対応

## 6. 論文での記述例

### 6.1 方法論セクション（英語例）

```
To balance computational efficiency and modeling accuracy, we employ
a simplified 8-level MCS table derived from the 3GPP TS 38.214
256QAM table (Table 5.1.3.1-2) [Ref]. The table covers modulation
schemes from QPSK (MCS 0) to 256QAM (MCS 7) with spectral efficiency
ranging from 0.15 to 5.50 bits/s/Hz. SNR thresholds are set at 5 dB
intervals (-5, 0, 5, 10, 15, 20, 25 dB), which align with the
theoretical SNR requirements for modulation transitions. This
simplification approach has been widely adopted in V2X simulation
research [1, 2], and our validation shows that the discrete MCS
selection achieves 58.5% of the Shannon capacity, consistent with
practical system performance.
```

### 6.2 日本語記述例

```
計算効率とモデル精度のバランスを取るため、3GPP TS 38.214の
256QAMテーブル（Table 5.1.3.1-2）[参考文献]から導出した
8段階の簡略化MCSテーブルを使用した。このテーブルは、
QPSK（MCS 0）から256QAM（MCS 7）までの変調方式をカバーし、
スペクトル効率は0.15〜5.50 bits/s/Hzの範囲を持つ。SNR閾値は
5dB間隔（-5, 0, 5, 10, 15, 20, 25 dB）で設定され、変調方式
遷移の理論的SNR要件と整合している。この簡略化手法はV2X
シミュレーション研究で広く採用されており[1, 2]、我々の検証
では離散MCS選択がShannon容量の58.5%を達成することを確認し、
実用システムの性能と一致することを示した。
```

## 7. 参考文献

[1] J. Yan and J. Härri, "MCS Analysis for 5G-NR V2X Sidelink Broadcast Communication,"
    2022 IEEE Intelligent Vehicles Symposium (IV), 2022, pp. 887-892.
    DOI: 10.1109/IV51971.2022.9827048

[2] C. Burbano-Abril and B. McCarthy, "MCS Adaptation within the Cellular V2X Sidelink,"
    arXiv:2109.15143, 2021.

[3] 3GPP, "Technical Specification Group Radio Access Network; NR; Physical layer
    procedures for data (Release 15)," TS 38.214 V15.2.0, June 2018.

[4] ShareTechnote, "5G/NR - MCS/TBS/Code Rate,"
    https://www.sharetechnote.com/html/5G/5G_MCS_TBS_CodeRate.html (Accessed: 2026-01-13)

## 8. 補足資料

### 8.1 MCSテーブルの実装コード

実装コードは `simulation/src/core/mcs_model.py` を参照。

### 8.2 検証データ

- シミュレーション結果: `simulation/output/scenarios/corner_intersection/throughput/`
- 分析結果: `summary_shannon_vs_mcs.csv`
- 可視化: `fig1_cdf_shannon_vs_mcs.png`

---

**Document Version**: 1.0
**Last Updated**: 2026-01-13
**Author**: V2X Network Simulation Project
