#!/bin/bash

##############################################################################
# SUMO + SIONNA RT 統合シミュレーション実行スクリプト
#
# 使用方法:
#   ./run_simulation.sh         : Ray Tracingのみ実行（既存のFCD使用）
#   ./run_simulation.sh --sumo  : SUMOシミュレーション実行後にRay Tracing実行
#   ./run_simulation.sh --all   : 全パイプライン実行（SUMO→RT→スループット→最適化）
#
##############################################################################

set -e  # エラーが発生したら即座に終了

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ディレクトリ設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUMO_CONFIG_DIR="${SCRIPT_DIR}/sumo_config"
SUMO_CONFIG_FILE="${SUMO_CONFIG_DIR}/simulation.sumocfg"
OUTPUT_DIR="${SCRIPT_DIR}/output"
FCD_OUTPUT="${OUTPUT_DIR}/fcd/fcd_output.xml"
LINK_QUALITY_CSV="${OUTPUT_DIR}/raytracing/link_quality_results.csv"

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

    # Ray Tracingシミュレーション実行
    python "${SCRIPT_DIR}/scripts/run_raytracing.py"

    if [ ! -f "$LINK_QUALITY_CSV" ]; then
        print_error "Link quality CSV not generated: $LINK_QUALITY_CSV"
        exit 1
    fi

    print_success "Ray Tracing simulation completed!"
}

run_throughput_calculation() {
    print_section "3" "Calculating Theoretical Throughput"

    activate_venv

    # スループット計算実行
    python "${SCRIPT_DIR}/scripts/run_throughput.py"

    print_success "Throughput calculation completed!"
}

run_optimization() {
    print_section "4" "Running Optimization"

    activate_venv

    # 最適化実行
    python "${SCRIPT_DIR}/scripts/run_optimization.py"

    print_success "Optimization completed!"
}

print_results() {
    print_section "5" "Simulation Results"

    echo "Output files:"
    echo "  - FCD output:          $FCD_OUTPUT"
    echo "  - Link quality CSV:    $LINK_QUALITY_CSV"
    echo "  - Throughput CSV:      ${OUTPUT_DIR}/throughput/theoretical_network_results.csv"
    echo "  - Baseline CSV:        ${OUTPUT_DIR}/baseline/baseline_distributed_results.csv"
    echo "  - Optimization CSV:    ${OUTPUT_DIR}/baseline/global_optimization_results.csv"
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
    print_header

    # コマンドライン引数を解析
    RUN_SUMO=false
    RUN_ALL=false

    for arg in "$@"; do
        case $arg in
            --sumo)
                RUN_SUMO=true
                shift
                ;;
            --all)
                RUN_ALL=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --sumo      Run SUMO simulation before Ray Tracing"
                echo "  --all       Run full pipeline (SUMO→RT→Throughput→Optimization)"
                echo "  -h, --help  Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0              # Run Ray Tracing only (use existing FCD)"
                echo "  $0 --sumo       # Run SUMO simulation then Ray Tracing"
                echo "  $0 --all        # Run full pipeline"
                echo ""
                echo "Individual scripts (in scripts/ directory):"
                echo "  python scripts/run_raytracing.py      # Ray Tracing"
                echo "  python scripts/run_throughput.py      # Throughput calculation"
                echo "  python scripts/run_optimization.py    # Optimization"
                echo "  python scripts/run_visualization.py   # Visualization"
                exit 0
                ;;
            *)
                print_error "Unknown option: $arg"
                echo "Use -h or --help for usage information."
                exit 1
                ;;
        esac
    done

    # 出力ディレクトリを作成
    mkdir -p "$OUTPUT_DIR"

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
