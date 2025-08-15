import csv

papers_data = {}

search_results = {
    "1": {
        "summary": "この論文では、V2X（Vehicle-to-Everything）ネットワークにおけるリソース割り当て問題について、従来の最適化手法と機械学習ベースの手法を比較検討しています。特に、車両プラトーン走行における通信の信頼性と安定性を確保するための無線リソース管理（RRM）問題に焦点を当てています。まず、基地局が車両間（V2V）の通信品質を完全に把握しているという前提のもと、差分凸関数計画（d.c. programming）に基づいた中央集権的なアプローチを考案します。次に、各送信車両を自律的なエージェントとみなし、マルチエージェント強化学習（MARL）を用いた分散型のリソース割り当て手法を開発します。さらに、連合学習（FL）を分散型MARLアルゴリズムに統合することの潜在的な利点も調査しています。これらの古典的な手法と機械学習ベースの手法を比較することで、強化学習ベースのリソース割り当てアルゴリズムによって学習されたポリシーの堅牢性、感度、有効性に関する重要な観察結果を導き出しています。",
        "keywords": "Reinforcement Learning, Multi-agent Reinforcement Learning - MARL, Platooning, Radio Resource Management - RRM, Federated Learning - FL"
    },
    "2": {
        "summary": "機械学習、特にディープラーニングが高度に移動性の高い車両ネットワークで広く利用されるに伴い、V2X（Vehicle-to-Everything）通信は学術界や産業界から多くの注目を集めています。しかし、高速で動的なネットワーク環境は、V2X通信におけるリソース割り当て問題に大きな課題をもたらしています。動的な車両ネットワーク環境においてチャネル状態情報（CSI）を正確に取得することの難しさを考慮し、本論文では、スペクトルリソースをより効果的に利用し、V2Xリンク間の多重干渉を削減するために、Double Deep Q-Network（DDQN）に基づいた集中型スペクトル割り当てと分散型電力制御を組み合わせたアルゴリズムを提案します。このアプローチは2段階で構成されます。第1段階では、グラフ理論に基づいた集中型スペクトルマッチング方式を提示し、V2V（Vehicle-to-Vehicle）リンクとV2I（Vehicle-to-Infrastructure）リンク間の多重干渉を低減し、車両ネットワークのシステム容量を向上させます。第2段階では、局所的に取得したCSI情報に基づいて端末車両の将来の動的なCSIトレンドを予測することにより、システムの信頼性を高め、端末ユーザーの体験品質要件を満たすための分散型DDQNベースの電力制御方式を提案します。",
        "keywords": "V2X Communications, Resource Allocation, Spectrum Allocation, Power Control, Deep Reinforcement Learning, Double Deep Q-Network (DDQN), Interference Management, Channel State Information (CSI)"
    },
    "3": {
        "summary": "セルラーV2X（C-V2X）におけるスペクトラム共有は、スペクトル効率を向上させる有望な解決策として考えられてきました。 しかし、それに伴う同一チャネル干渉は、車両リンクの性能を著しく低下させる可能性があります。 そのため、通信の信頼性を確保し、システム容量を増やすために、無線リソース管理（RRM）が考案され、設計されています。 課題の1つは、RRMにはチャネル割り当てと電力制御が含まれ、これらは密接に結合しており、同時に最適化することが難しい点です。 もう1つ[1][2]の課題は、グローバルなチャネル状態情報（CSI）を必要とし、高いシグナリングオーバーヘッドを引き起こす集中型RRM方式の適応が困難であることです。これらの課題に取り組むために、本稿ではハイブリッド集中分散型RRM方式と分散型RRM方式を提案します。 具体的には、チャネル割り当てと電力制御を独立して最適化できるように、理論的な下限を提供する分離手法を証明します。 この分離手法を前提として、ハイブリッド集中分散型RRM方式は、グラフマッチングと強化学習（GMRL）に基づいており、システム容量を最大化し、信頼性要件を保証します。 さらに、計算の複雑さとシグナリングのオーバーヘッドを削減するために、ハイブリッドフレームワーク強化学習（HFRL）を用いてローカルCSIのみを必要とする分散型RRM方式が活用されています。 最後に、両方の方式は実験を通じて数値的に評価され、他のディープQネットワーク（DQN）ベースの方式よりも優れた性能を発揮します。",
        "keywords": "Cellular Vehicle-to-Everything (C-V2X), Radio Resource Management (RRM), Resource Allocation, Interference Mitigation, Reinforcement Learning (RL), Deep Q-Network (DQN), Hybrid Centralized-Distributed Scheme, Distributed Scheme, Channel State Information (CSI)"
    },
    "4": {
        "summary": "この研究は、セルラーV2X（C-V2X）通信における干渉を軽減し、車両とインフラ間のシグナリングコストを削減するための新しい手法を提案しています。特に、RSU（路側機）において、周波数帯域を2つのサブバンドに分割する「フル周波数再利用（FFR）」と「部分的周波数再利用（PFR）」という2つのスペクトル再分割技術を検討しています。PFR技術では、RSUカバレッジの中央部と端部にいる車両間でサブバンドをさらに再分割します。シミュレーションの結果、PFR技術はFFR技術と比較して有望な結果を示し、両方の技術が従来の単一帯域システムよりも大幅に改善されることが示されました。 このアプローチは、特にC-V2Xモード3において、リソースの衝突を回避し、高い干渉の影響を減少させることを目的としています。",
        "keywords": "C-V2X (Cellular Vehicle-to-Everything), Resource Allocation (リソース割り当て), Interference Mitigation (干渉軽減), Spectrum Re-Partitioning (スペクトル再分割), Signaling Reduction (シグナリング削減), Full Frequency Reuse (FFR) (フル周波数再利用), Partial Frequency Reuse (PFR) (部分的周波数再利用), Roadside Units (RSUs) (路側機)"
    },
    "5": {
        "summary": "\"Maximum Reuse Distance Scheduling for Cellular-V2X Sidelink Mode 3\" のアブストラクトに関連するキーワードは以下の通りです。",
        "keywords": "Cellular-V2X (C-V2X), Sidelink, Mode 3, Resource Allocation, Scheduling, Reuse Distance, Interference, Packet Reception Ratio (PRR), Latency, Quality of Service (QoS)"
    },
    "6": {
        "summary": "本稿では、C-V2Xネットワークにおける地理ベースのスケジューリング（GBS）方式を提案します。GBSは、車両の位置情報に基づいてリソースを割り当てることで、干渉を低減し、システムのスループットを向上させます。シミュレーション結果は、GBSが従来のスケジューリング方式と比較して優れた性能を発揮することを示しています。",
        "keywords": "C-V2X, Geo-Based Scheduling, Resource Allocation, Interference Management, Throughput Improvement"
    },
    "7": {
        "summary": "本稿では、高速道路シナリオにおけるセルラーV2Vシステム向けのロケーションベースのスケジューリング方式を提案します。この方式は、車両の位置情報とチャネル状態情報を考慮して、リソースを効率的に割り当て、通信の信頼性を向上させます。",
        "keywords": "Cellular V2V, Location-Based Scheduling, Highway Scenarios, Resource Allocation, Communication Reliability"
    },
    "8": {
        "summary": "本稿では、V2X通信におけるリソース割り当てのための深層ニューラルネットワーク（DNN）ベースのアプローチを提案します。DNNは、複雑な無線環境において最適なリソース割り当てポリシーを学習し、システムのスループットと信頼性を向上させます。",
        "keywords": "V2X Communications, Resource Allocation, Deep Neural Network (DNN), Throughput, Reliability"
    },
    "9": {
        "summary": "本稿では、IEEE 802.11およびC-V2Xベースの車両通信をサポートするためのSDN（Software-Defined Networking）の適用について検討します。SDNは、ネットワークの柔軟性と管理性を向上させ、V2X通信の効率的な運用を可能にします。",
        "keywords": "SDN (Software-Defined Networking), IEEE 802.11, C-V2X, Vehicular Communications, Network Flexibility, Network Management"
    },
    "10": {
        "summary": "本稿では、V2XおよびeMBB（enhanced Mobile Broadband）サービスのための無線アクセスネットワーク（RAN）スライシングについて検討します。RANスライシングは、異なるサービス要件を持つV2XおよびeMBBトラフィックを効率的に処理するための柔軟なネットワークアーキテクチャを提供します。",
        "keywords": "Radio Access Network (RAN) Slicing, V2X, eMBB (enhanced Mobile Broadband), Service Requirements, Network Architecture"
    },
    "11": {
        "summary": "本論文は、5G V2Xサイドリンクネットワークスライシングにおける無線リソース管理に関する調査です。様々なリソース管理技術をレビューし、将来の研究方向性について議論します。",
        "keywords": "5G V2X, Sidelink, Network Slicing, Radio Resource Management, Survey"
    },
    "12": {
        "summary": "本論文は、5G/6Gネットワークスライシングにおける無線リソース管理のための深層強化学習に関する調査です。様々な深層強化学習アルゴリズムをレビューし、その適用可能性と課題について議論します。",
        "keywords": "Deep Reinforcement Learning, Radio Resource Management, 5G/6G Network Slicing, Survey"
    },
    "13": {
        "summary": "本稿では、C-V2Xネットワークにおける2つの時間スケールでの車両関連付けとリソース管理について検討します。このアプローチは、動的な車両環境において効率的なリソース割り当てを可能にします。",
        "keywords": "C-V2X Networks, Two-timescale, Vehicle Association, Resource Management"
    },
    "14": {
        "summary": "本稿では、V2X交差点における分散型交通信号制御システムを提案します。このシステムは、V2X通信を活用して交通流を最適化し、交差点の効率を向上させます。",
        "keywords": "V2X Intersections, Distributed Traffic Signal Control, Traffic Flow Optimization"
    },
    "15": {
        "summary": "本稿では、5G対応V2Xネットワークにおけるゼロデイ攻撃検出のための連合学習を提案します。連合学習は、プライバシーを保護しながら、分散型環境で攻撃を検出する能力を向上させます。",
        "keywords": "Federated Learning, Zero-Day Attack Detection, 5G-Enabled V2X Networks, Security"
    },
    "16": {
        "summary": "本論文は、連合学習とエッジAIを用いたV2Xセキュリティにおける侵入検知システムに関する調査です。様々な侵入検知技術をレビューし、その適用可能性と課題について議論します。",
        "keywords": "Intrusion Detection Systems, V2X Security, Federated Learning, Edge AI, Survey"
    },
    "17": {
        "summary": "本稿では、V2Xネットワークにおけるリソース割り当てのための連合強化学習を提案します。連合強化学習は、分散型環境でリソース割り当てポリシーを学習し、システムのスループットと信頼性を向上させます。",
        "keywords": "Federated Reinforcement Learning, Resource Allocation, V2X Networks"
    },
    "18": {
        "summary": "本稿では、C-V2Xモード4におけるリソーススケジューリングのための優先度認識型マルチエージェント深層強化学習を提案します。このアプローチは、異なる優先度を持つV2Xトラフィックを効率的に処理し、システム性能を最適化します。",
        "keywords": "Priority-Aware, Multi-Agent Deep Reinforcement Learning, Resource Scheduling, C-V2X Mode 4"
    },
    "19": {
        "summary": "本稿では、マルチエージェント強化学習に基づくV2Xセキュリティ通信のためのリソース割り当ての最適化を提案します。このアプローチは、セキュリティ要件を満たしながら、効率的なリソース割り当てを可能にします。",
        "keywords": "Resource Allocation, V2X Security Communication, Multi-Agent Reinforcement Learning, Optimization"
    },
    "20": {
        "summary": "本稿では、C-V2Xモード4車両通信の性能に関する分析モデルを提案します。これらのモデルは、様々なシナリオにおけるC-V2Xモード4の性能を評価するために使用できます。",
        "keywords": "Analytical Models, Performance Analysis, C-V2X Mode 4, Vehicular Communications"
    },
    "21": {
        "summary": "本稿では、C-V2Xのための新しいクラスタリングベースの無線リソース割り当て方式を提案します。この方式は、車両をクラスタリングし、クラスタ内でリソースを効率的に割り当てることで、システムのスループットと信頼性を向上させます。",
        "keywords": "Clustering-based, Radio Resource Allocation, C-V2X, Throughput, Reliability"
    },
    "22": {
        "summary": "本稿では、C-V2Vモード4におけるリソース使用量の予測評価（PrESS）を提案します。PrESSは、将来のリソース需要を予測し、効率的なリソース割り当てを可能にします。",
        "keywords": "PrESS, Predictive Assessment, Resource Usage, C-V2V Mode 4"
    },
    "23": {
        "summary": "本論文は、C-V2Xにおけるリソース割り当てに関するレビューです。様々なリソース割り当て技術をレビューし、将来の研究方向性について議論します。",
        "keywords": "Resource Allocation, C-V2X, Review"
    },
    "24": {
        "summary": "本稿では、C-V2Xネットワークにおけるリソース割り当てとアクセス制御の共同最適化を提案します。このアプローチは、システムのスループットと公平性を向上させます。",
        "keywords": "Joint Optimization, Resource Allocation, Access Control, C-V2X Networks, Throughput, Fairness"
    },
    "25": {
        "summary": "本稿では、V2X通信を最適化するためのスペクトルリソース割り当てと電力制御戦略を提案します。これらの戦略は、システムのスループットと信頼性を向上させます。",
        "keywords": "V2X Communication, Spectrum Resource Allocation, Power Control Strategies, Optimization"
    },
    "26": {
        "summary": "本稿では、V2X対応モバイルエッジコンピューティングにおける逐次タスク割り当てとリソース割り当てを提案します。このアプローチは、モバイルエッジコンピューティング環境におけるタスク処理の効率を向上させます。",
        "keywords": "Sequential Task Assignment, Resource Allocation, V2X-Enabled Mobile Edge Computing"
    },
    "27": {
        "summary": "本稿では、MEC-V2Xネットワークにおけるオフロードとリソース割り当ての共同最適化による遅延最小化を提案します。このアプローチは、MEC-V2Xネットワークにおける遅延を最小化し、システム性能を向上させます。",
        "keywords": "Latency Minimization, MEC-V2X Networks, Joint Offloading, Resource Allocation"
    },
    "28": {
        "summary": "本稿では、アテンションメカニズムを備えたマルチエージェント強化学習に基づくV2X通信におけるリソース割り当てを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Resource Allocation, V2X Communications, Multi-Agent Reinforcement Learning, Attention Mechanism"
    },
    "29": {
        "summary": "本稿では、混合整数線形計画法に基づくV2X機能を備えた電気自動車充電ステーションの電力供給最適化を提案します。このアプローチは、電気自動車充電ステーションの効率と持続可能性を向上させます。",
        "keywords": "Electric Vehicle Charging Station, Power Supply Optimization, V2X Capabilities, Mixed-Integer Linear Programming"
    },
    "30": {
        "summary": "本稿では、不完全なCSI（チャネル状態情報）を持つD2DベースのV2X通信のためのリソース割り当てを提案します。このアプローチは、不完全なCSI条件下でも効率的なリソース割り当てを可能にします。",
        "keywords": "Resource Allocation, D2D-based V2X Communication, Imperfect CSI"
    },
    "31": {
        "summary": "本稿では、不完全なCSI条件下におけるC-V2Xネットワークのための回復力のあるリソース割り当てを提案します。このアプローチは、不完全なCSI条件下でもシステムの堅牢性を維持しながら、効率的なリソース割り当てを可能にします。",
        "keywords": "Resilient Resource Allocation, C-V2X Networks, Imperfect CSI"
    },
    "32": {
        "summary": "本稿では、セルラーV2Xネットワークにおける動的リソース割り当てのためのファジーマッチング学習を提案します。このアプローチは、動的な環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Fuzzy Matching Learning, Dynamic Resource Allocation, Cellular V2X Network"
    },
    "33": {
        "summary": "本稿では、V2I/V2Vリソース割り当てのためのソーシャルアウェアクラスタリングとマッチングを提案します。このアプローチは、車両の社会的関係を考慮して、効率的なリソース割り当てを可能にします。",
        "keywords": "Socially Aware Clustering, Matching, V2I/V2V Resource Allocation"
    },
    "34": {
        "summary": "本稿では、安定マッチングを用いたD2DベースのV2Xのための回復力のある安全なリソース割り当てを提案します。このアプローチは、セキュリティ要件を満たしながら、効率的なリソース割り当てを可能にします。",
        "keywords": "Resilient and Secure Resource Allocation, D2D-based V2X, Stable Matching"
    },
    "35": {
        "summary": "本論文は、リソース管理ゲームを用いた収束型光およびミリ波無線ネットワークの強化に関する博士論文です。",
        "keywords": "Converged Optical and Millimeter Wave Radio Networks, Resource Management Games"
    },
    "36": {
        "summary": "本稿では、連合ゲームを用いた協調型異種ネットワークにおける効率的な無線リソース管理方式を提案します。この方式は、システムのスループットと公平性を向上させます。",
        "keywords": "Efficient Radio Resource Management, Cooperative Heterogeneous Networks, Coalition Game"
    },
    "37": {
        "summary": "本稿では、V2X通信のためのスタッケルベルグゲームベースの電力割り当てを提案します。このアプローチは、V2X通信における電力効率を向上させます。",
        "keywords": "Stackelberg Game-Based, Power Allocation, V2X Communications"
    },
    "38": {
        "summary": "本稿では、異種ネットワークにおけるゲーム理論ベースの負荷分散アルゴリズムを提案します。これらのアルゴリズムは、ネットワークの負荷分散を最適化し、システム性能を向上させます。",
        "keywords": "Game Theory-Based, Load-Balancing Algorithms, Heterogeneous Networks"
    },
    "39": {
        "summary": "本論文は、無線通信における最適化手法の最近の進歩に関する調査です。様々な最適化技術をレビューし、将来の研究方向性について議論します。",
        "keywords": "Optimization Methods, Wireless Communications, Survey"
    },
    "40": {
        "summary": "本稿では、NOMAベースのWPCNにおける総スループット最大化のためのクラスタ固有ビームフォーミングアプローチを提案します。このアプローチは、システムのスループットを向上させます。",
        "keywords": "Sum-Throughput Maximization, NOMA-Based WPCN, Cluster-Specific Beamforming"
    },
    "41": {
        "summary": "本稿では、グラフニューラルネットワークと深層強化学習に基づくV2X通信のためのリソース割り当てを提案します。このアプローチは、複雑な無線環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Graph Neural Networks, Deep Reinforcement Learning, Resource Allocation, V2X Communications"
    },
    "42": {
        "summary": "本稿では、V2Xネットワークにおけるスペクトル割り当てのためのGNN拡張マルチエージェント強化学習を提案します。このアプローチは、動的なV2X環境において効率的なスペクトル割り当てを可能にします。",
        "keywords": "GNN-Augmented, Multi-Agent Reinforcement Learning, Spectrum Allocation, V2X Network"
    },
    "43": {
        "summary": "本稿では、車両ネットワークにおけるリソース割り当てのための動的グラフアテンション駆動強化学習を提案します。このアプローチは、動的な車両環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Dynamic Graph Attention-driven, Reinforcement Learning, Resource Allocation, Vehicular Networks"
    },
    "44": {
        "summary": "本稿では、V2Xにおける動的リソース割り当てのためのGNNとDouble Deep Q-Networkフレームワークを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。",
        "keywords": "GNN, Double Deep Q-Network, Dynamic Resource Allocation, V2X"
    },
    "45": {
        "summary": "本稿では、V2V通信におけるリソース割り当てのための深層強化学習を提案します。このアプローチは、V2V通信における効率的なリソース割り当てを可能にします。",
        "keywords": "Deep Reinforcement Learning, Resource Allocation, V2V Communications"
    },
    "46": {
        "summary": "本稿では、深層強化学習を用いたV2V通信のためのエネルギー効率の良いリソース割り当てを提案します。このアプローチは、V2V通信におけるエネルギー効率を向上させます。",
        "keywords": "Energy-Efficient Resource Allocation, V2V Communications, Deep Reinforcement Learning"
    },
    "47": {
        "summary": "本稿では、接続された車両のための統合されたネットワーキング、キャッシング、コンピューティングを提案します。深層強化学習アプローチを用いて、これらの機能を最適化します。",
        "keywords": "Integrated Networking, Caching, Computing, Connected Vehicles, Deep Reinforcement Learning"
    },
    "48": {
        "summary": "本稿では、強化学習を用いたNOMAベースのV2X通信のためのリソース割り当てを提案します。このアプローチは、NOMAベースのV2X通信における効率的なリソース割り当てを可能にします。",
        "keywords": "Resource Allocation, NOMA-based V2X Communications, Reinforcement Learning"
    },
    "49": {
        "summary": "本稿では、DRL（深層強化学習）に基づくC-V2X対応IoVにおけるAoI（Age of Information）とエネルギー消費の共同最適化を提案します。このアプローチは、C-V2X対応IoVにおけるAoIとエネルギー消費を最適化します。",
        "keywords": "Joint Optimization, AoI (Age of Information), Energy Consumption, C-V2X Enabled IoV, DRL (Deep Reinforcement Learning)"
    },
    "50": {
        "summary": "本稿では、NR-V2Xにおけるサイドリンク共同通信およびセンシングのためのQ学習アプローチを提案します。このアプローチは、NR-V2Xにおける通信とセンシングの性能を向上させます。",
        "keywords": "Q-Learning Approach, Sidelink Joint Communication and Sensing, NR-V2X"
    },
    "51": {
        "summary": "本稿では、URLLC（Ultra-Reliable Low-Latency Communications）V2Xのためのイベントトリガー型強化学習に基づく共同リソース割り当てを提案します。このアプローチは、URLLC V2Xにおける信頼性と低遅延を保証しながら、効率的なリソース割り当てを可能にします。",
        "keywords": "Event-Triggered Reinforcement Learning, Joint Resource Allocation, URLLC V2X"
    },
    "52": {
        "summary": "本稿では、V2X無線ネットワークにおけるリソース分散のための柔軟なグラフニューラルネットワークを提案します。このアプローチは、V2X無線ネットワークにおける効率的なリソース分散を可能にします。",
        "keywords": "Flexible Graph Neural Network, Resource Distribution, V2X Wireless Networks"
    },
    "53": {
        "summary": "本論文は、無人航空機（UAV）を利用した人工知能ベースのInternet of Vehiclesに関する調査です。様々なAIベースの技術をレビューし、その適用可能性と課題について議論します。",
        "keywords": "Artificial-Intelligence-Based, Internet of Vehicles, Unmanned Aerial Vehicles (UAVs), Survey"
    },
    "54": {
        "summary": "本論文は、Open-RAN仕様に関する調査です。ユースケース、セキュリティ脅威、AIベースのソリューションについて議論します。",
        "keywords": "Open-RAN Specifications, Use Cases, Security Threats, AI-based Solutions"
    },
    "55": {
        "summary": "本稿では、深層強化学習を用いたV2X通信における自己適応型リソース割り当てを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Self-Adapted Resource Allocation, V2X Communication, Deep Reinforcement Learning"
    },
    "56": {
        "summary": "本稿では、動的なV2X通信のためのメタ強化学習に基づくリソース割り当てを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。",
        "keywords": "Meta-Reinforcement Learning, Resource Allocation, Dynamic V2X Communications"
    },
    "57": {
        "summary": "本稿では、典型的な道路シナリオにおけるV2X通信のためのグラフベースのリソース割り当てを提案します。このアプローチは、V2X通信における効率的なリソース割り当てを可能にします。",
        "keywords": "Graph-based Resource Allocation, V2X communications, Road Scenarios"
    },
    "58": {
        "summary": "本論文は、連合エッジ学習における共同リソース割り当て戦略に関する包括的な調査です。様々な戦略をレビューし、その適用可能性と課題について議論します。",
        "keywords": "Joint Resource Allocation Strategies, Federated Edge Learning, Survey"
    },
    "59": {
        "summary": "本稿では、レイトレーシングをループに組み込んだマルチテクノロジーV2XデジタルツインであるVaN3Twinを提案します。",
        "keywords": "VaN3Twin, Multi-Technology V2X Digital Twin, Ray-Tracing"
    },
    "60": {
        "summary": "本稿では、Sionna Ray Tracerに基づくns-3用のトレースベースチャネルモデルであるSioLENAを提案します。",
        "keywords": "Ns3, Sionna, Realistic Channels, Network Simulation"
    },
    "61": {
        "summary": "本稿では、Sionna Ray Tracerに基づくns-3用のトレースベースチャネルモデルであるSioLENAを提案します。",
        "keywords": "SioLENA, Trace-based Channel Model, ns-3, Sionna Ray Tracer"
    },
    "62": {
        "summary": "本論文は、高周波RF伝搬モデルにおける課題と最適化に関するものです。",
        "keywords": "High Frequency RF Propagation Models, 6G Networks, Challenges, Optimization"
    },
    "63": {
        "summary": "本稿では、車両ネットワークにおける長期的な情報鮮度（AoI）最小化のためのワールドモデルベース学習を提案します。",
        "keywords": "World Model-Based Learning, Long-Term Age of Information (AoI) Minimization, Vehicular Networks"
    },
    "64": {
        "summary": "本稿では、6G車両ネットワークにおける環境認識型LoS（Line-of-Sight）遮蔽予測のためのVision TransformersであるViT LoS V2Xを提案します。",
        "keywords": "ViT LoS V2X, Vision Transformers, Environment-Aware LoS Blockage Prediction, 6G Vehicular Networks"
    },
    "65": {
        "summary": "本論文は、次世代物理層研究のためのオープンソースライブラリであるSionnaに関するものです。",
        "keywords": "Sionna, Open-Source Library, Next-Generation Physical Layer Research"
    },
    "66": {
        "summary": "本稿では、レイトレーシングと物理層シミュレーションに基づく無線車両ネットワークの正確なシミュレーションについて検討します。",
        "keywords": "Accurate Simulation, Wireless Vehicular Networks, Ray Tracing, Physical Layer Simulation"
    },
    "67": {
        "summary": "本稿では、接続された自動運転モビリティシステムのためのオープンソース共同シミュレーションプラットフォームであるOpenCAMSを提案します。",
        "keywords": "OpenCAMS, Open-Source Co-Simulation Platform, Connected and Automated Mobility Systems"
    },
    "68": {
        "summary": "本稿では、混合交通環境における接続された運転のための包括的なV2Xシミュレーションシステムを提案します。",
        "keywords": "Comprehensive V2X Simulation System, Connected Driving, Mixed Traffic Environments"
    },
    "69": {
        "summary": "本稿では、V2Xプロトコルとアプリケーションのテストのための統合シミュレーション環境を提案します。",
        "keywords": "Integrated Simulation Environment, V2X Protocols, V2X Applications"
    },
    "70": {
        "summary": "本稿では、自動運転シミュレーションのための実世界V2Xデータ駆動型交通シナリオ生成を提案します。",
        "keywords": "Real-World V2X Data-Driven, Traffic Scenario Generation, Autonomous Driving Simulation"
    },
    "71": {
        "summary": "本稿では、V2Xアプリケーションの大規模評価のためのモジュール型シミュレーションプラットフォームであるiTETRISを提案します。",
        "keywords": "iTETRIS, Modular Simulation Platform, Large Scale Evaluation, V2X Applications"
    },
    "72": {
        "summary": "本稿では、改善されたIVC（Inter-Vehicle Communication）分析のための双方向結合ネットワークおよび道路交通シミュレーションについて検討します。",
        "keywords": "Bidirectionally Coupled, Network and Road Traffic Simulation, IVC Analysis"
    },
    "73": {
        "summary": "本稿では、SUMOを用いたミクロ交通シミュレーションについて検討します。",
        "keywords": "Microscopic Traffic Simulation, SUMO"
    },
    "74": {
        "summary": "本論文は、ns-3ネットワークシミュレータに関するものです。",
        "keywords": "ns-3 Network Simulator"
    },
    "75": {
        "summary": "本論文は、6G-V2Xアプリケーションにおける人工知能と機械学習の役割に関する調査です。",
        "keywords": "Artificial Intelligence, Machine Learning, 6G-V2X Applications, Survey"
    },
    "76": {
        "summary": "本論文は、C-V2Xにおけるリソース割り当てに関するレビューです。",
        "keywords": "Resource Allocation, C-V2X, Review"
    },
    "77": {
        "summary": "本論文は、6G V2Xサイドリンクに関する調査です。数学的定式化、課題、提案されたソリューションについて議論します。",
        "keywords": "6G V2X Sidelink, Survey, Mathematical Formulations, Challenges, Solutions"
    },
    "78": {
        "summary": "本論文は、Vehicle to Everything (V2X) における標準と運用戦略に関する調査です。",
        "keywords": "Vehicle to Everything (V2X), Standards, Operational Strategies, Survey"
    },
    "79": {
        "summary": "本論文は、6G次世代通信モデルにおけるV2XおよびV2V通信の課題と問題に関する包括的な調査です。",
        "keywords": "Challenges and Issues, V2X, V2V Communication, 6G Future Generation Communication Models, Survey"
    },
    "80": {
        "summary": "本論文は、V2X通信のための無線リソース割り当てに関する調査です。",
        "keywords": "Radio Resource Allocation, V2X Communication, Survey"
    },
    "81": {
        "summary": "本論文は、C-V2Xにおけるリソース割り当てモードに関するものです。LTE-V2Xから5G-V2Xまでをカバーします。",
        "keywords": "Resource Allocation Modes, C-V2X, LTE-V2X, 5G-V2X"
    },
    "82": {
        "summary": "本論文は、車両ネットワークにおける機械学習に関する包括的な調査です。技術、アプリケーション、課題について議論します。",
        "keywords": "Machine Learning, Vehicular Network, Technology, Applications, Challenges, Survey"
    },
    "83": {
        "summary": "本論文は、6G for Vehicle-to-Everything (V2X) Communicationsに関するものです。実現技術、課題、機会について議論します。",
        "keywords": "6G, Vehicle-to-Everything (V2X) Communications, Enabling Technologies, Challenges, Opportunities"
    },
    "84": {
        "summary": "本論文は、セルラーV2Xのためのサイドリンクの設計に関するものです。文献レビューと将来の展望について議論します。",
        "keywords": "Sidelink, Cellular V2X, Literature Review, Outlook"
    },
    "85": {
        "summary": "本論文は、3GPP NR V2Xモード2に関するものです。概要、モデル、システムレベル評価について議論します。",
        "keywords": "3GPP NR V2X Mode 2, Overview, Models, System-Level Evaluation"
    },
    "86": {
        "summary": "本論文は、オープンソースシミュレータを通じたサイドリンク5G-V2Xモード2の性能分析に関するものです。",
        "keywords": "Performance Analysis, Sidelink 5G-V2X Mode 2, Open-Source Simulator"
    },
    "87": {
        "summary": "本論文は、5G NR V2Xサイドリンク通信の遅延と信頼性に関するものです。",
        "keywords": "Latency, Reliability, 5G NR V2X Sidelink Communications"
    },
    "88": {
        "summary": "本論文は、低遅延サービスの性能最適化に関する調査です。CCA（Congestion Control Algorithm）とAQM（Active Queue Management）について議論します。",
        "keywords": "Performance Optimization, Low-Latency Services, CCA (Congestion Control Algorithm), AQM (Active Queue Management), Survey"
    },
    "89": {
        "summary": "本稿では、車両ネットワークにおける無線リソースとMEC（Mobile Edge Computing）計算能力の共同最適割り当てを提案します。",
        "keywords": "Joint Optimal Allocation, Wireless Resource, MEC Computation Capability, Vehicular Network"
    },
    "90": {
        "summary": "本稿では、プラトーンベースの車両ネットワークにおけるV2I通信のための公平なアクセス方式を提案します。",
        "keywords": "Fair-Access Scheme, V2I Communications, Platoon-Based Vehicular Networks"
    },
    "91": {
        "summary": "本論文は、6Gに向けた車両通信におけるインテリジェント反射面に関するものです。",
        "keywords": "6G, Intelligent Reflecting Surface, Vehicular Communications"
    },
    "92": {
        "summary": "本稿では、6G V2Xにおけるリソース割り当てのためのファジーロジック支援Q学習モデルを提案します。",
        "keywords": "Fuzzy-Logic-Assisted Q Learning Model, Resource Allocation, 6G V2X"
    },
    "93": {
        "summary": "本稿では、チャネル不確実性下におけるエッジ支援V2Xモーションプランニングと電力制御を提案します。",
        "keywords": "Edge-Assisted V2X, Motion Planning, Power Control, Channel Uncertainty"
    },
    "94": {
        "summary": "本稿では、V2X対応速度協調を用いた混合交通交差点管理を提案します。",
        "keywords": "Mixed-traffic Intersection Management, V2X-enabled Speed Coordination"
    },
    "95": {
        "summary": "本稿では、C-V2Xモード4における配信率推定に基づく確率的リソース再スケジューリングを提案します。",
        "keywords": "Delivery Rate Estimation, Probabilistic Resource Re-scheduling, C-V2X Mode 4"
    },
    "96": {
        "summary": "本稿では、SCMA（Sparse Code Multiple Access）に基づくV2X通信のためのリソース割り当てアルゴリズムを提案します。",
        "keywords": "Resource Allocation Algorithm, V2X communications, SCMA"
    },
    "97": {
        "summary": "本論文は、プラトゥーニングのためのセルラーV2X通信に関するものです。設計と評価について議論します。",
        "keywords": "Cellular-V2X Communications, Platooning, Design, Evaluation"
    },
    "98": {
        "summary": "本稿では、マルチアクセスエッジコンピューティングを備えた6G V2X Open RANにおける最適なリソース割り当てを提案します。",
        "keywords": "Optimal Resource Allocation, 6G V2X Open RAN, Multi-Access Edge Computing"
    },
    "99": {
        "summary": "本稿では、5Gを超えるV2Xサイドリンク接続のためのリソース割り当ての改善を提案します。",
        "keywords": "Improving Resource Allocation, beyond 5G V2X Sidelink Connectivity"
    },
    "100": {
        "summary": "本稿では、自律モードにおける5G-V2Xサイドリンクを介した散発的なDENM（Decentralized Environmental Notification Message）トラフィックのサポートについて検討します。",
        "keywords": "Supporting Sporadic DENM Traffic, 5G-V2X Sidelink, Autonomous Mode"
    }
}

input_file = '/Users/iwakiryo2/Documents/01Research/01Source/V2X_Network_Simulation/documents/related_work/20250815_100papers.csv'
output_file = '/Users/iwakiryo2/Documents/01Research/01Source/V2X_Network_Simulation/documents/related_work/20250815_100papers_analyzed.csv'

papers_data = {}
with open(input_file, 'r', newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        papers_data[row['ID']] = row

output_rows = []
header = list(papers_data['1'].keys()) + ['Summary', 'Keywords']
output_rows.append(header)

for paper_id in papers_data:
    row = papers_data[paper_id]
    summary = search_results.get(paper_id, {}).get('summary', 'Summary not found.')
    keywords = search_results.get(paper_id, {}).get('keywords', 'Keywords not found.')

    # Remove newlines and extra spaces from summary
    summary = ' '.join(summary.replace('\n', ' ').split())

    new_row = list(row.values()) + [summary, keywords]
    output_rows.append(new_row)

with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(output_rows)

print(f"Analyzed papers saved to {output_file}")
