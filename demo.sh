#!/bin/bash
################################################################################
# CyberShield AI — One-Command Demo
# 
# Run all 4 modules end-to-end:
#     bash demo.sh --mock-llm
#
# This script:
#   1. Validates environment and dependencies
#   2. Trains Module 1 (anomaly detection)
#   3. Trains Module 2 (phishing detection + Bayesian layer)
#   4. Builds Module 3's unified dataset
#   5. Runs Module 4's orchestrator on sample events
#   6. Reports results and next steps
#
################################################################################

set -e  # Exit on any error
trap 'echo "ERROR at line $LINENO"; exit 1' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOCK_LLM="${1:---mock-llm}"  # Default to mock mode if not specified

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

################################################################################
# 1. VALIDATE ENVIRONMENT
################################################################################
log_info "Validating environment..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_info "Python version: $PYTHON_VERSION"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "module1" ] || [ ! -d "module2" ] || [ ! -d "module3" ] || [ ! -d "module4" ]; then
    log_error "Not in CyberShield-AI root directory. Run this script from the repo root."
    exit 1
fi

log_success "Environment validation passed"

################################################################################
# 2. INSTALL DEPENDENCIES
################################################################################
log_info "Installing dependencies..."

if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
log_info "Virtual environment activated"

log_info "Upgrading pip..."
python3 -m pip install --quiet --upgrade pip

log_info "Installing unified dependencies..."
python3 -m pip install --quiet -r requirements-all.txt

# Install module-specific requirements
log_info "Installing Module 1 dependencies..."
python3 -m pip install --quiet -r module1/requirements.txt

log_info "Installing Module 2 dependencies..."
python3 -m pip install --quiet -r module2/requirements.txt

log_info "Installing Module 3 dependencies..."
python3 -m pip install --quiet -r module3/requirements.txt

log_info "Installing Module 4 dependencies..."
python3 -m pip install --quiet -r module4/requirements.txt

log_success "Dependencies installed"

################################################################################
# 3. TRAIN MODULE 1 (Anomaly Detection)
################################################################################
log_info ""
log_info "========================================"
log_info "MODULE 1: Statistical Anomaly Detection"
log_info "========================================"

cd "$SCRIPT_DIR/module1/src"
log_info "Training Module 1 (IsolationForest + OneClassSVM)..."
python3 train.py

if [ -f "../models/isolation_forest.pkl" ]; then
    log_success "Module 1 training complete"
else
    log_error "Module 1 training failed — models not found"
    exit 1
fi

cd "$SCRIPT_DIR"

################################################################################
# 4. TRAIN MODULE 2 (Phishing Detection + Bayesian)
################################################################################
log_info ""
log_info "========================================"
log_info "MODULE 2: Phishing Detection + Bayesian"
log_info "========================================"

cd "$SCRIPT_DIR/module2/src"
log_info "Training Module 2 (TF-IDF + LightGBM)..."
python3 train.py

log_info "Validating Bayesian layer..."
python3 bayesian_layer.py

if [ -f "../models/lightgbm_model.pkl" ]; then
    log_success "Module 2 training complete"
else
    log_error "Module 2 training failed — models not found"
    exit 1
fi

cd "$SCRIPT_DIR"

################################################################################
# 5. BUILD MODULE 3 DATASET & VERIFY DASHBOARD
################################################################################
log_info ""
log_info "========================================"
log_info "MODULE 3: Explainability Dashboard"
log_info "========================================"

cd "$SCRIPT_DIR/module3/src"
log_info "Building unified threat dataset (Module 1 + Module 2 paired)..."
python3 build_dataset.py

if [ -f "../data/unified_threat_data.csv" ]; then
    log_success "Module 3 dataset built"
else
    log_error "Module 3 dataset build failed"
    exit 1
fi

log_info "Verifying dashboard initialization..."
python3 -c "
import sys
sys.path.insert(0, '.')
from xai_engine import load_dataset, train_surrogate_model
df = load_dataset()
print(f'  Loaded {len(df)} threat events')
model, fidelity = train_surrogate_model()
print(f'  Surrogate fidelity (AUC): {fidelity[\"auc_vs_is_attack\"]:.4f}')
print(f'  Surrogate fidelity (Accuracy): {fidelity[\"accuracy_vs_is_attack\"]:.4f}')
"

log_success "Module 3 dashboard ready (run: streamlit run src/app.py)"

cd "$SCRIPT_DIR"

################################################################################
# 6. RUN MODULE 4 ORCHESTRATOR
################################################################################
log_info ""
log_info "========================================"
log_info "MODULE 4: SOC Assistant Orchestrator"
log_info "========================================"

cd "$SCRIPT_DIR/module4/src"

if [ "$MOCK_LLM" = "--mock-llm" ]; then
    log_info "Running orchestrator with MOCK LLM (no API key needed)..."
    python3 main.py --batch 10 --mock-llm
    DEMO_SUCCESS=$?
else
    log_warning "LLM mock mode disabled. If ANTHROPIC_API_KEY is not set, this will fail."
    python3 main.py --batch 5
    DEMO_SUCCESS=$?
fi

if [ $DEMO_SUCCESS -eq 0 ]; then
    log_success "Module 4 orchestration complete"
else
    log_error "Module 4 orchestration failed"
    exit 1
fi

cd "$SCRIPT_DIR"

################################################################################
# 7. SUMMARY & NEXT STEPS
################################################################################
log_info ""
log_info "========================================"
log_success "DEMO COMPLETE — ALL 4 MODULES WORKING"
log_info "========================================"
log_info ""
log_info "Generated artifacts:"
log_info "  ✓ module1/models/          — Trained anomaly detector"
log_info "  ✓ module1/evaluation/      — Evaluation plots (ROC, confusion matrix, feature importance)"
log_info "  ✓ module2/models/          — Trained phishing classifier + Bayesian layer"
log_info "  ✓ module2/evaluation/      — Model comparison plots"
log_info "  ✓ module3/data/            — Unified threat dataset (3K events)"
log_info "  ✓ module3/models/          — SHAP surrogate model + fidelity metrics"
log_info "  ✓ module4/data/event_log.jsonl  — Orchestrated events with playbooks"
log_info ""
log_info "Next steps:"
log_info "  1. View the interactive dashboard:"
log_info "     cd module3/src && streamlit run app.py"
log_info ""
log_info "  2. Inspect the event log:"
log_info "     cat module4/data/event_log.jsonl | python3 -m json.tool"
log_info ""
log_info "  3. Run a single event with custom content:"
log_info "     cd module4/src && python3 main.py --content 'URGENT verify account' --mock-llm"
log_info ""
log_info "  4. Review the documentation:"
log_info "     cat README.md"
log_info ""

log_success "Setup complete! 🎉"
