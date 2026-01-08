#!/bin/bash

##############################################################################
# SUMO + SIONNA RT 統合シミュレーション実行スクリプト
#
# 使用方法:
#   ./run_simulation.sh         : Ray Tracingのみ実行（既存のFCD使用）
#   ./run_simulation.sh --sumo  : SUMOシミュレーション実行後にRay Tracing実行
#   ./run_simulation.sh --all   : 全パイプライン実行（SUMO→RT→スループット→最適化）
#   ./run_simulation.sh --scenario corner_intersection --all : 交差点シナリオで実行
#   ./run_simulation.sh --scenario corner_intersection --sionna-rt --all : GPU版Sionna RTで実行
#
# オプション:
#   --sionna-rt          : GPU加速されたSionna RTマルチパス計算を使用（デフォルトは簡易モデル）
#
# シナリオ:
#   default              : デフォルトシナリオ（直線道路、1km）
#   corner_intersection  : 交差点シナリオ（十字交差点、4棟の角ビル）
#
##############################################################################

set -e  # エラーが発生したら即座に終了

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルトシナリオ
SCENARIO="default"

# ディレクトリ設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# シナリオに応じたパス設定関数
setup_paths() {
    # すべてのシナリオで統一されたパス構造を使用
    # output/scenarios/{scenario_name}/{fcd,raytracing,throughput,optimization,analysis,figures}
    if [ "$SCENARIO" = "default" ]; then
        SUMO_CONFIG_DIR="${SCRIPT_DIR}/sumo_config"
    else
        SUMO_CONFIG_DIR="${SCRIPT_DIR}/sumo_config/${SCENARIO}"
    fi
    SUMO_CONFIG_FILE="${SUMO_CONFIG_DIR}/simulation.sumocfg"
    OUTPUT_DIR="${SCRIPT_DIR}/output/scenarios/${SCENARIO}"
    FCD_OUTPUT="${OUTPUT_DIR}/fcd/fcd_output.xml"
    LINK_QUALITY_CSV="${OUTPUT_DIR}/raytracing/link_quality_results.csv"
}

# Python仮想環境
VENV_PATH="${SCRIPT_DIR}/../.venv"

# PYTHONPATHを設定（モジュールインポート用）
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

##############################################################################
# 関数定義
##############################################################################

print_header() {
    echo -e "${BLUE}========================================================================${NC}"
    echo -e "${BLUE}  SUMO + SIONNA RT Integrated Simulation${NC}"
    echo -e "${BLUE}========================================================================${NC}"
}

print_section() {
    echo ""
    echo -e "${GREEN}[Step $1]${NC} $2"
    echo -e "${GREEN}------------------------------------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ Error: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "$1 command not found. Please install $1."
        exit 1
    fi
}

activate_venv() {
    if [ -d "$VENV_PATH" ]; then
        print_success "Activating Python virtual environment: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    else
        print_warning "Virtual environment not found: $VENV_PATH"
        print_warning "Continuing without virtual environment..."
    fi
}

run_sumo_simulation() {
    print_section "1" "Running SUMO Traffic Simulation"

    check_command "sumo"

    if [ ! -f "$SUMO_CONFIG_FILE" ]; then
        print_error "SUMO config file not found: $SUMO_CONFIG_FILE"
        exit 1
    fi

    echo "SUMO config: $SUMO_CONFIG_FILE"
    echo "FCD output: $FCD_OUTPUT"

    # 出力ディレクトリを作成
    mkdir -p "$(dirname "$FCD_OUTPUT")"

    # SUMOシミュレーション実行
    cd "$SUMO_CONFIG_DIR"
    sumo -c simulation.sumocfg --no-warnings
    cd "$SCRIPT_DIR"

    if [ ! -f "$FCD_OUTPUT" ]; then
        print_error "FCD output file not generated: $FCD_OUTPUT"
        exit 1
    fi

    print_success "SUMO simulation completed!"
}

run_raytracing_simulation() {
    print_section "2" "Running Ray Tracing Simulation"

    activate_venv

    if [ ! -f "$FCD_OUTPUT" ]; then
        print_error "FCD output file not found: $FCD_OUTPUT"
        print_error "Please run SUMO simulation first using: $0 --sumo"
        exit 1
    fi

    echo "Input FCD: $FCD_OUTPUT"
    echo "Output CSV: $LINK_QUALITY_CSV"

    # 出力ディレクトリを作成
    mkdir -p "$(dirname "$LINK_QUALITY_CSV")"

    # Ray Tracingシミュレーション実行（シナリオを渡す）
    if [ "$USE_SIONNA_RT" = true ]; then
        echo "Mode: Sionna RT (GPU-accelerated multi-path)"
        python "${SCRIPT_DIR}/scripts/run_raytracing.py" --scenario "$SCENARIO" --sionna-rt
    else
        echo "Mode: Simple model (single-path)"
        python "${SCRIPT_DIR}/scripts/run_raytracing.py" --scenario "$SCENARIO"
    fi

    if [ ! -f "$LINK_QUALITY_CSV" ]; then
        print_error "Link quality CSV not generated: $LINK_QUALITY_CSV"
        exit 1
    fi

    print_success "Ray Tracing simulation completed!"
}

run_throughput_calculation() {
    print_section "3" "Calculating Theoretical Throughput"

    activate_venv

    # スループット計算実行（シナリオを渡す）
    python "${SCRIPT_DIR}/scripts/run_throughput.py" --scenario "$SCENARIO"

    print_success "Throughput calculation completed!"
}

run_optimization() {
    print_section "4" "Running Optimization"

    activate_venv

    # 最適化実行（シナリオを渡す）
    python "${SCRIPT_DIR}/scripts/run_optimization.py" --scenario "$SCENARIO"

    print_success "Optimization completed!"
}

print_results() {
    print_section "5" "Simulation Results"

    echo "Output files:"
    echo "  - FCD output:          $FCD_OUTPUT"
    echo "  - Link quality CSV:    $LINK_QUALITY_CSV"
    echo "  - Throughput CSV:      ${OUTPUT_DIR}/throughput/theoretical_network_results.csv"
    echo "  - Optimization CSV:    ${OUTPUT_DIR}/optimization/"
    echo ""

    if [ -f "$LINK_QUALITY_CSV" ]; then
        num_records=$(wc -l < "$LINK_QUALITY_CSV")
        num_records=$((num_records - 1))  # ヘッダー行を除く
        print_success "Total link quality records: $num_records"
    fi
}

##############################################################################
# メイン処理
##############################################################################

main() {
    # コマンドライン引数を解析
    RUN_SUMO=false
    RUN_ALL=false
    USE_SIONNA_RT=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --sumo)
                RUN_SUMO=true
                shift
                ;;
            --all)
                RUN_ALL=true
                shift
                ;;
            --sionna-rt)
                USE_SIONNA_RT=true
                shift
                ;;
            --scenario)
                SCENARIO="$2"
                shift 2
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --sumo                Run SUMO simulation before Ray Tracing"
                echo "  --all                 Run full pipeline (SUMO→RT→Throughput→Optimization)"
                echo "  --sionna-rt           Use Sionna RT for multi-path ray tracing (GPU accelerated)"
                echo "  --scenario NAME       Select scenario (default, corner_intersection)"
                echo "  -h, --help            Show this help message"
                echo ""
                echo "Scenarios:"
                echo "  default               Default straight road scenario (1km road)"
                echo "  corner_intersection   Intersection scenario (cross intersection, 4 corner buildings)"
                echo ""
                echo "Examples:"
                echo "  $0                                      # Run Ray Tracing only (use existing FCD)"
                echo "  $0 --sumo                               # Run SUMO simulation then Ray Tracing"
                echo "  $0 --all                                # Run full pipeline"
                echo "  $0 --scenario corner_intersection --all # Run intersection scenario"
                echo "  $0 --scenario corner_intersection --sionna-rt --all # Run with GPU-accelerated Sionna RT"
                echo ""
                echo "Individual scripts (in scripts/ directory):"
                echo "  python scripts/run_raytracing.py      # Ray Tracing"
                echo "  python scripts/run_throughput.py      # Throughput calculation"
                echo "  python scripts/run_optimization.py    # Optimization"
                echo "  python scripts/run_visualization.py   # Visualization"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use -h or --help for usage information."
                exit 1
                ;;
        esac
    done

    # シナリオに応じてパスを設定
    setup_paths

    print_header
    echo -e "${GREEN}Scenario: ${SCENARIO}${NC}"
    echo ""

    # 出力ディレクトリを作成
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$(dirname "$FCD_OUTPUT")"
    mkdir -p "$(dirname "$LINK_QUALITY_CSV")"

    # SUMOシミュレーション実行（--sumoまたは--allオプション時）
    if [ "$RUN_SUMO" = true ] || [ "$RUN_ALL" = true ]; then
        run_sumo_simulation
    else
        print_warning "Skipping SUMO simulation (use --sumo to run)"
    fi

    # Ray Tracingシミュレーション実行
    run_raytracing_simulation

    # --allオプション時は追加の処理を実行
    if [ "$RUN_ALL" = true ]; then
        run_throughput_calculation
        run_optimization
    fi

    # 結果表示
    print_results

    # 完了メッセージ
    echo ""
    echo -e "${BLUE}========================================================================${NC}"
    print_success "All simulations completed successfully!"
    echo -e "${BLUE}========================================================================${NC}"
}

# スクリプト実行
main "$@"
