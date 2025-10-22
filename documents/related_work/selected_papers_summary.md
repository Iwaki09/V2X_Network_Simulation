# Selected Papers for V2X Network Simulation Research

This document summarizes 40 selected papers highly relevant to the research theme "Global Optimization of Networks Integrating Physical Propagation Simulation in V2X Communication Environments." The selection prioritizes papers on resource allocation, optimization techniques (especially ML/GNN), physical layer propagation, ray tracing, and key simulation tools (SUMO, Sionna, ns-3).

## Paper List

### 1. Resource Allocation in V2X Networks: From Classical Optimization to Machine Learning-based Solutions
- **ID**: 1
- **Author**: Parvini, S. et al.
- **Year**: 2024
- **Publisher**: IEEE Open Journal of the Communications Society
- **Summary**: この論文では、V2X（Vehicle-to-Everything）ネットワークにおけるリソース割り当て問題について、従来の最適化手法と機械学習ベースの手法を比較検討しています。特に、車両プラトーン走行における通信の信頼性と安定性を確保するための無線リソース管理（RRM）問題に焦点を当てています。まず、基地局が車両間（V2V）の通信品質を完全に把握しているという前提のもと、差分凸関数計画（d.c. programming）に基づいた中央集権的なアプローチを考案します。次に、各送信車両を自律的なエージェントとみなし、マルチエージェント強化学習（MARL）を用いた分散型のリソース割り当て手法を開発します。さらに、連合学習（FL）を分散型MARLアルゴリズムに統合することの潜在的な利点も調査しています。これらの古典的な手法と機械学習ベースの手法を比較することで、強化学習ベースのリソース割り当てアルゴリズムによって学習されたポリシーの堅牢性、感度、有効性に関する重要な観察結果を導き出しています。
- **Keywords**: Reinforcement Learning, Multi-agent Reinforcement Learning - MARL, Platooning, Radio Resource Management - RRM, Federated Learning - FL

### 2. DDQN-Based Centralized Spectrum Allocation and Distributed Power Control for V2X Communications
- **ID**: 2
- **Author**: Zhang, Y. et al.
- **Year**: 2024
- **Publisher**: IEEE Transactions on Vehicular Technology
- **Summary**: 機械学習、特にディープラーニングが高度に移動性の高い車両ネットワークで広く利用されるに伴い、V2X（Vehicle-to-Everything）通信は学術界や産業界から多くの注目を集めています。しかし、高速で動的なネットワーク環境は、V2X通信におけるリソース割り当て問題に大きな課題をもたらしています。動的な車両ネットワーク環境においてチャネル状態情報（CSI）を正確に取得することの難しさを考慮し、本論文では、スペクトルリソースをより効果的に利用し、V2Xリンク間の多重干渉を削減するために、Double Deep Q-Network（DDQN）に基づいた集中型スペクトル割り当てと分散型電力制御を組み合わせたアルゴリズムを提案します。このアプローチは2段階で構成されます。第1段階では、グラフ理論に基づいた集中型スペクトルマッチング方式を提示し、V2V（Vehicle-to-Vehicle）リンクとV2I（Vehicle-to-Infrastructure）リンク間の多重干渉を低減し、車両ネットワークのシステム容量を向上させます。第2段階では、局所的に取得したCSI情報に基づいて端末車両の将来の動的なCSIトレンドを予測することにより、システムの信頼性を高め、端末ユーザーの体験品質要件を満たすための分散型DDQNベースの電力制御方式を提案します。
- **Keywords**: V2X Communications, Resource Allocation, Spectrum Allocation, Power Control, Deep Reinforcement Learning, Double Deep Q-Network (DDQN), Interference Management, Channel State Information (CSI)

### 3. Radio Resource Management for C-V2X: From A Hybrid Centralized-Distributed Scheme to A Distributed Scheme
- **ID**: 3
- **Author**: Guo, J. et al.
- **Year**: 2023
- **Publisher**: IEEE Journal on Selected Areas in Communications
- **Summary**: セルラーV2X（C-V2X）におけるスペクトラム共有は、スペクトル効率を向上させる有望な解決策として考えられてきました。 しかし、それに伴う同一チャネル干渉は、車両リンクの性能を著しく低下させる可能性があります。 そのため、通信の信頼性を確保し、システム容量を増やすために、無線リソース管理（RRM）が考案され、設計されています。 課題の1つは、RRMにはチャネル割り当てと電力制御が含まれ、これらは密接に結合しており、同時に最適化することが難しい点です。 もう1つ[1][2]の課題は、グローバルなチャネル状態情報（CSI）を必要とし、高いシグナリングオーバーヘッドを引き起こす集中型RRM方式の適応が困難であることです。これらの課題に取り組むために、本稿ではハイブリッド集中分散型RRM方式と分散型RRM方式を提案します。 具体的には、チャネル割り当てと電力制御を独立して最適化できるように、理論的な下限を提供する分離手法を証明します。 この分離手法を前提として、ハイブリッド集中分散型RRM方式は、グラフマッチングと強化学習（GMRL）に基づいており、システム容量を最大化し、信頼性要件を保証します。 さらに、計算の複雑さとシグナリングのオーバーヘッドを削減するために、ハイブリッドフレームワーク強化学習（HFRL）を用いてローカルCSIのみを必要とする分散型RRM方式が活用されています。 最後に、両方の方式は実験を通じて数値的に評価され、他のディープQネットワーク（DQN）ベースの方式よりも優れた性能を発揮します。
- **Keywords**: Cellular Vehicle-to-Everything (C-V2X), Radio Resource Management (RRM), Resource Allocation, Interference Mitigation, Reinforcement Learning (RL), Deep Q-Network (DQN), Hybrid Centralized-Distributed Scheme, Distributed Scheme, Channel State Information (CSI)

### 4. Spectrum Re-Partitioning in Centralized C-V2X for Interference Mitigation and Signaling Reduction
- **ID**: 4
- **Author**: Al-Absi, A. et al.
- **Year**: 2022
- **Publisher**: Electronics
- **Summary**: この研究は、セルラーV2X（C-V2X）通信における干渉を軽減し、車両とインフラ間のシグナリングコストを削減するための新しい手法を提案しています。特に、RSU（路側機）において、周波数帯域を2つのサブバンドに分割する「フル周波数再利用（FFR）」と「部分的周波数再利用（PFR）」という2つのスペクトル再分割技術を検討しています。PFR技術では、RSUカバレッジの中央部と端部にいる車両間でサブバンドをさらに再分割します。シミュレーションの結果、PFR技術はFFR技術と比較して有望な結果を示し、両方の技術が従来の単一帯域システムよりも大幅に改善されることが示されました。 このアプローチは、特にC-V2Xモード3において、リソースの衝突を回避し、高い干渉の影響を減少させることを目的としています。
- **Keywords**: C-V2X (Cellular Vehicle-to-Everything), Resource Allocation (リソース割り当て), Interference Mitigation (干渉軽減), Spectrum Re-Partitioning (スペクトル再分割), Signaling Reduction (シグナリング削減), Full Frequency Reuse (FFR) (フル周波数再利用), Partial Frequency Reuse (PFR) (部分的周波数再利用), Roadside Units (RSUs) (路側機)

### 5. Deep Neural Network Based Resource Allocation for V2X Communications
- **ID**: 8
- **Author**: Gao, Y. et al.
- **Year**: 2019
- **Publisher**: IEEE Vehicular Technology Conference (VTC-Fall)
- **Summary**: 本稿では、V2X通信におけるリソース割り当てのための深層ニューラルネットワーク（DNN）ベースのアプローチを提案します。DNNは、複雑な無線環境において最適なリソース割り当てポリシーを学習し、システムのスループットと信頼性を向上させます。
- **Keywords**: V2X Communications, Resource Allocation, Deep Neural Network (DNN), Throughput, Reliability

### 6. Radio Access Network Slicing for V2X and eMBB Services
- **ID**: 10
- **Author**: Garcia, M. et al.
- **Year**: 2019
- **Publisher**: International Conference on Cognitive Radio Oriented Wireless Networks
- **Summary**: 本稿では、V2XおよびeMBB（enhanced Mobile Broadband）サービスのための無線アクセスネットワーク（RAN）スライシングについて検討します。RANスライシングは、異なるサービス要件を持つV2XおよびeMBBトラフィックを効率的に処理するための柔軟なネットワークアーキテクチャを提供します。
- **Keywords**: Radio Access Network (RAN) Slicing, V2X, eMBB (enhanced Mobile Broadband), Service Requirements, Network Architecture

### 7. A Survey on Radio Resource Management for 5G V2X Sidelink Network Slicing
- **ID**: 11
- **Author**: Al-Heety, O. et al.
- **Year**: 2021
- **Publisher**: PhD Thesis, UPC
- **Summary**: 本論文は、5G V2Xサイドリンクネットワークスライシングにおける無線リソース管理に関する調査です。様々なリソース管理技術をレビューし、将来の研究方向性について議論します。
- **Keywords**: 5G V2X, Sidelink, Network Slicing, Radio Resource Management, Survey

### 8. Deep Reinforcement Learning for Radio Resource Management in 5G/6G Network Slicing: A Survey
- **ID**: 12
- **Author**: Rojas, O. et al.
- **Year**: 2022
- **Publisher**: Sensors
- **Summary**: 本論文は、5G/6Gネットワークスライシングにおける無線リソース管理のための深層強化学習に関する調査です。様々な深層強化学習アルゴリズムをレビューし、その適用可能性と課題について議論します。
- **Keywords**: Deep Reinforcement Learning, Radio Resource Management, 5G/6G Network Slicing, Survey

### 9. Federated Reinforcement Learning for Resource Allocation in V2X Networks
- **ID**: 17
- **Author**: Zhang, Y. et al.
- **Year**: 2024
- **Publisher**: arXiv
- **Summary**: 本稿では、V2Xネットワークにおけるリソース割り当てのための連合強化学習を提案します。連合強化学習は、分散型環境でリソース割り当てポリシーを学習し、システムのスループットと信頼性を向上させます。
- **Keywords**: Federated Reinforcement Learning, Resource Allocation, V2X Networks

### 10. Priority-Aware Multi-Agent Deep Reinforcement Learning for Resource Scheduling in C-V2X Mode 4
- **ID**: 18
- **Author**: Muhammad-Saad, A. et al.
- **Year**: 2024
- **Publisher**: IEEE Access
- **Summary**: 本稿では、C-V2Xモード4におけるリソーススケジューリングのための優先度認識型マルチエージェント深層強化学習を提案します。このアプローチは、異なる優先度を持つV2Xトラフィックを効率的に処理し、システム性能を最適化します。
- **Keywords**: Priority-Aware, Multi-Agent Deep Reinforcement Learning, Resource Scheduling, C-V2X Mode 4

### 11. Joint Optimization of Resource Allocation and Access Control in C-V2X Networks
- **ID**: 24
- **Author**: Li, X. et al.
- **Year**: 2024
- **Publisher**: IEEE Transactions on Vehicular Technology
- **Summary**: 本稿では、C-V2Xネットワークにおけるリソース割り当てとアクセス制御の共同最適化を提案します。このアプローチは、システムのスループットと公平性を向上させます。
- **Keywords**: Joint Optimization, Resource Allocation, Access Control, C-V2X Networks, Throughput, Fairness

### 12. Latency Minimization for MEC-V2X Networks with Joint Offloading and Resource Allocation
- **ID**: 27
- **Author**: Zhang, H. et al.
- **Year**: 2023
- **Publisher**: IEEE Transactions on Vehicular Technology
- **Summary**: 本稿では、MEC-V2Xネットワークにおけるオフロードとリソース割り当ての共同最適化による遅延最小化を提案します。このアプローチは、MEC-V2Xネットワークにおける遅延を最小化し、システム性能を向上させます。
- **Keywords**: Latency Minimization, MEC-V2X Networks, Joint Offloading, Resource Allocation

### 13. Resource Allocation in V2X Communications Based on Multi-Agent Reinforcement Learning with Attention Mechanism
- **ID**: 28
- **Author**: Sun, Y. et al.
- **Year**: 2022
- **Publisher**: Mathematics
- **Summary**: 本稿では、アテンションメカニズムを備えたマルチエージェント強化学習に基づくV2X通信におけるリソース割り当てを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。
- **Keywords**: Resource Allocation, V2X Communications, Multi-Agent Reinforcement Learning, Attention Mechanism

### 14. Resilient Resource Allocation for C-V2X Networks under Imperfect CSI
- **ID**: 31
- **Author**: Zhang, L. et al.
- **Year**: 2021
- **Publisher**: IEEE Transactions on Wireless Communications
- **Summary**: 本稿では、不完全なCSI条件下におけるC-V2Xネットワークのための回復力のあるリソース割り当てを提案します。このアプローチは、不完全なCSI条件下でもシステムの堅牢性を維持しながら、効率的なリソース割り当てを可能にします。
- **Keywords**: Resilient Resource Allocation, C-V2X Networks, Imperfect CSI

### 15. A Survey of Recent Advances in Optimization Methods for Wireless Communications
- **ID**: 39
- **Author**: Luo, Z-Q. et al.
- **Year**: 2024
- **Publisher**: IEEE Journal on Selected Areas in Communications
- **Summary**: 本論文は、無線通信における最適化手法の最近の進歩に関する調査です。様々な最適化技術をレビューし、将来の研究方向性について議論します。
- **Keywords**: Optimization Methods, Wireless Communications, Survey

### 16. Graph Neural Networks and Deep Reinforcement Learning Based Resource Allocation for V2X Communications
- **ID**: 41
- **Author**: Ji, M. et al.
- **Year**: 2024
- **Publisher**: IEEE Internet of Things Journal
- **Summary**: 本稿では、グラフニューラルネットワークと深層強化学習に基づくV2X通信のためのリソース割り当てを提案します。このアプローチは、複雑な無線環境において効率的なリソース割り当てを可能にします。
- **Keywords**: Graph Neural Networks, Deep Reinforcement Learning, Resource Allocation, V2X Communications

### 17. GNN-Augmented Multi-Agent Reinforcement Learning for Spectrum Allocation in V2X Network
- **ID**: 42
- **Author**: Wang, J. et al.
- **Year**: 2021
- **Publisher**: IEEE Globecom Workshops
- **Summary**: 本稿では、V2Xネットワークにおけるスペクトル割り当てのためのGNN拡張マルチエージェント強化学習を提案します。このアプローチは、動的なV2X環境において効率的なスペクトル割り当てを可能にします。
- **Keywords**: GNN-Augmented, Multi-Agent Reinforcement Learning, Spectrum Allocation, V2X Network

### 18. Dynamic Graph Attention-driven Reinforcement Learning for Resource Allocation in Vehicular Networks
- **ID**: 43
- **Author**: Chen, Y. et al.
- **Year**: 2025
- **Publisher**: Preprints.org
- **Summary**: 本稿では、車両ネットワークにおけるリソース割り当てのための動的グラフアテンション駆動強化学習を提案します。このアプローチは、動的な車両環境において効率的なリソース割り当てを可能にします。
- **Keywords**: Dynamic Graph Attention-driven, Reinforcement Learning, Resource Allocation, Vehicular Networks

### 19. A GNN and Double Deep Q-Network Framework for Dynamic Resource Allocation in V2X
- **ID**: 44
- **Author**: Li, H. et al.
- **Year**: 2025
- **Publisher**: Computer Materials & Continua
- **Summary**: 本稿では、V2Xにおける動的リソース割り当てのためのGNNとDouble Deep Q-Networkフレームワークを提案します。このアプローチは、動的なV2X環境において効率的なリソース割り当てを可能にします。
- **Keywords**: GNN, Double Deep Q-Network, Dynamic Resource Allocation, V2X

### 20. Deep Reinforcement Learning for Resource Allocation in V2V Communications
- **ID**: 45
- **Author**: Ye, H. & Li, G. Y.
- **Year**: 2018
- **Publisher**: IEEE Wireless Communications Letters
- **Summary**: 本稿では、V2V通信におけるリソース割り当てのための深層強化学習を提案します。このアプローチは、V2V通信における効率的なリソース割り当てを可能にします。
- **Keywords**: Deep Reinforcement Learning, Resource Allocation, V2V Communications

### 21. A Flexible Graph Neural Network for Resource Distribution in V2X Wireless Networks
- **ID**: 52
- **Author**: Kumar, S. et al.
- **Year**: 2024
- **Publisher**: IEEE Vehicular Technology Conference (VTC-Spring)
- **Summary**: 本稿では、V2X無線ネットワークにおけるリソース分散のための柔軟なグラフニューラルネットワークを提案します。このアプローチは、V2X無線ネットワークにおける効率的なリソース分散を可能にします。
- **Keywords**: Flexible Graph Neural Network, Resource Distribution, V2X Wireless Networks

### 22. Graph-based Resource Allocation for V2X communications in typical road scenarios
- **ID**: 57
- **Author**: Jiang, W. et al.
- **Year**: 2022
- **Publisher**: IEEE International Conference on Communications (ICC)
- **Summary**: 本稿では、典型的な道路シナリオにおけるV2X通信のためのグラフベースのリソース割り当てを提案します。このアプローチは、V2X通信における効率的なリソース割り当てを可能にします。
- **Keywords**: Graph-based Resource Allocation, V2X communications, Road Scenarios

### 23. VaN3Twin: the Multi-Technology V2X Digital Twin with Ray-Tracing in the Loop
- **ID**: 59
- **Author**: Todisco, V. et al.
- **Year**: 2025
- **Publisher**: arXiv
- **Summary**: 本稿では、レイトレーシングをループに組み込んだマルチテクノロジーV2XデジタルツインであるVaN3Twinを提案します。
- **Keywords**: VaN3Twin, Multi-Technology V2X Digital Twin, Ray-Tracing

### 24. Ns3 meets Sionna: Using Realistic Channels in Network Simulation
- **ID**: 60
- **Author**: Zubow, A. et al.
- **Year**: 2024
- **Publisher**: Proceedings of the 22nd ACM International Conference on Mobile Systems, Applications, and Services
- **Summary**: 本稿では、Sionna Ray Tracerに基づくns-3用のトレースベースチャネルモデルであるSioLENAを提案します。
- **Keywords**: Ns3, Sionna, Realistic Channels, Network Simulation

### 25. SioLENA: A Trace-based Channel Model for ns-3 based on Sionna Ray Tracer
- **ID**: 61
- **Author**: Pilz, Y. et al.
- **Year**: 2025
- **Publisher**: arXiv
- **Summary**: 本稿では、Sionna Ray Tracerに基づくns-3用のトレースベースチャネルモデルであるSioLENAを提案します。
- **Keywords**: SioLENA, Trace-based Channel Model, ns-3, Sionna Ray Tracer

### 26. Sionna: An Open-Source Library for Next-Generation Physical Layer Research
- **ID**: 65
- **Author**: Hoydis, J. et al.
- **Year**: 2022
- **Publisher**: IEEE International Conference on Communications (ICC)
- **Summary**: 本論文は、次世代物理層研究のためのオープンソースライブラリであるSionnaに関するものです。
- **Keywords**: Sionna, Open-Source Library, Next-Generation Physical Layer Research

### 27. Accurate Simulation of Wireless Vehicular Networks Based on Ray Tracing and Physical Layer Simulation
- **ID**: 66
- **Author**: Gaugel, T. et al.
- **Year**: 2012
- **Publisher**: High Performance Computing in Science and Engineering '11
- **Summary**: 本稿では、レイトレーシングと物理層シミュレーションに基づく無線車両ネットワークの正確なシミュレーションについて検討します。
- **Keywords**: Accurate Simulation, Wireless Vehicular Networks, Ray Tracing, Physical Layer Simulation

### 28. OpenCAMS: An Open-Source Co-Simulation Platform for Connected and Automated Mobility Systems
- **ID**: 67
- **Author**: Rahman, M. M. et al.
- **Year**: 2025
- **Publisher**: arXiv
- **Summary**: 本稿では、接続された自動運転モビリティシステムのためのオープンソース共同シミュレーションプラットフォームであるOpenCAMSを提案します。
- **Keywords**: OpenCAMS, Open-Source Co-Simulation Platform, Connected and Automated Mobility Systems

### 29. A Comprehensive V2X Simulation System for Connected Driving in Mixed Traffic Environments
- **ID**: 68
- **Author**: Shi, Y. et al.
- **Year**: 2023
- **Publisher**: MODSIM World Conference
- **Summary**: 本稿では、混合交通環境における接続された運転のための包括的なV2Xシミュレーションシステムを提案します。
- **Keywords**: Comprehensive V2X Simulation System, Connected Driving, Mixed Traffic Environments

### 30. An Integrated Simulation Environment for Testing V2X Protocols and Applications
- **ID**: 69
- **Author**: Choudhury, A. et al.
- **Year**: 2016
- **Publisher**: Procedia Computer Science
- **Summary**: 本稿では、V2Xプロトコルとアプリケーションのテストのための統合シミュレーション環境を提案します。
- **Keywords**: Integrated Simulation Environment, V2X Protocols, V2X Applications

### 31. iTETRIS: A Modular Simulation Platform for the Large Scale Evaluation of V2X Applications
- **ID**: 71
- **Author**: Schiegg, F. A. et al.
- **Year**: 2012
- **Publisher**: Simulation Tools and Techniques (SIMUTools)
- **Summary**: 本稿では、V2Xアプリケーションの大規模評価のためのモジュール型シミュレーションプラットフォームであるiTETRISを提案します。
- **Keywords**: iTETRIS, Modular Simulation Platform, Large Scale Evaluation, V2X Applications

### 32. Bidirectionally Coupled Network and Road Traffic Simulation for Improved IVC Analysis
- **ID**: 72
- **Author**: Sommer, C. et al.
- **Year**: 2011
- **Publisher**: IEEE Transactions on Mobile Computing
- **Summary**: 本稿では、改善されたIVC（Inter-Vehicle Communication）分析のための双方向結合ネットワークおよび道路交通シミュレーションについて検討します。
- **Keywords**: Bidirectionally Coupled, Network and Road Traffic Simulation, IVC Analysis

### 33. Microscopic Traffic Simulation using SUMO
- **ID**: 73
- **Author**: Lopez, P. A. et al.
- **Year**: 2018
- **Publisher**: IEEE International Conference on Intelligent Transportation Systems (ITSC)
- **Summary**: 本稿では、SUMOを用いたミクロ交通シミュレーションについて検討します。
- **Keywords**: Microscopic Traffic Simulation, SUMO

### 34. The ns-3 Network Simulator
- **ID**: 74
- **Author**: Riley, G. F. & Henderson, T. R.
- **Year**: 2010
- **Publisher**: Modeling and Tools for Network Simulation
- **Summary**: 本論文は、ns-3ネットワークシミュレータに関するものです。
- **Keywords**: ns-3 Network Simulator

### 35. A Survey on the Role of Artificial Intelligence and Machine Learning in 6G-V2X Applications
- **ID**: 75
- **Author**: Al-Dulaimi, A. et al.
- **Year**: 2025
- **Publisher**: arXiv
- **Summary**: 本論文は、6G-V2Xアプリケーションにおける人工知能と機械学習の役割に関する調査です。
- **Keywords**: Artificial Intelligence, Machine Learning, 6G-V2X Applications, Survey

### 36. Resource Allocation in C-V2X: A review
- **ID**: 76
- **Author**: Tahi, T. Z.
- **Year**: 2024
- **Publisher**: arXiv
- **Summary**: 本論文は、C-V2Xにおけるリソース割り当てに関するレビューです。
- **Keywords**: Resource Allocation, C-V2X, Review

### 37. Towards 6G V2X Sidelink: Survey of Resource Allocation - Mathematical Formulations, Challenges, and Proposed Solutions
- **ID**: 77
- **Author**: Annu & Rajalakshmi, P.
- **Year**: 2024
- **Publisher**: IEEE Open Journal of Vehicular Technology
- **Summary**: 本論文は、6G V2Xサイドリンクに関する調査です。数学的定式化、課題、提案されたソリューションについて議論します。
- **Keywords**: 6G V2X Sidelink, Survey, Mathematical Formulations, Challenges, Solutions

### 38. A Survey on Radio Resource Allocation for V2X Communication
- **ID**: 80
- **Author**: Masmoudi, A. & Frikha, M.
- **Year**: 2019
- **Publisher**: Wireless Communications and Mobile Computing
- **Summary**: 本論文は、V2X通信のための無線リソース割り当てに関する調査です。
- **Keywords**: Radio Resource Allocation, V2X Communication, Survey

### 39. A Comprehensive Survey on Machine Learning in Vehicular Network: Technology, Applications and Challenges
- **ID**: 82
- **Author**: Tang, F. et al.
- **Year**: 2021
- **Publisher**: IEEE Communications Surveys & Tutorials
- **Summary**: 本論文は、車両ネットワークにおける機械学習に関する包括的な調査です。技術、アプリケーション、課題について議論します。
- **Keywords**: Machine Learning, Vehicular Network, Technology, Applications, Challenges, Survey

### 40. 6G for Vehicle-to-Everything (V2X) Communications: Enabling Technologies, Challenges, and Opportunities
- **ID**: 83
- **Author**: Noor-A-Rahim, M. et al.
- **Year**: 2022
- **Publisher**: IEEE Communications Magazine
- **Summary**: 本論文は、6G for Vehicle-to-Everything (V2X) Communicationsに関するものです。実現技術、課題、機会について議論します。
- **Keywords**: 6G, Vehicle-to-Everything (V2X) Communications, Enabling Technologies, Challenges, Opportunities
