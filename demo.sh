#!/bin/bash
# Bayesian Sentinel — All-in-One Demo Script
# Usage: bash demo.sh [--mock-llm]
#
# This script orchestrates the complete pipeline:
#   1. Train Module 1 (anomaly detection)
#   2. Train Module 2 (phishing classification)
#   3. Build Module 3 dataset & train surrogate
#   4. Run Module 4 orchestrator on sample events

set -e  # Exit on error

MOCK_LLM=${1:-"--mock-llm"}
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_header() {
    echo -e "${BLUE}\n==========================================\n$1\n==========================================\n${NC}"
}

echo_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo_error() {
    echo -e "${RED}✗ $1${NC}"
}

echo_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check Python version
echo_header "Checking environment"
python3 --version 2>/dev/null || python --version

# Determine python command (prefer python3 on Linux/Mac)
if command -v python3 &>/dev/null; then
    PYTHON=python3
else
    PYTHON=python
fi

# Create and activate a virtual environment to avoid PEP 668
# "externally-managed-environment" errors on modern Debian/Ubuntu/WSL.
VENV_DIR="$BASE_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo_warning "No virtual environment found — creating one at $VENV_DIR"
    $PYTHON -m venv "$VENV_DIR" || {
        echo_error "Failed to create virtual environment. Install python3-venv (e.g. sudo apt install python3-venv) and retry."
        exit 1
    }
    echo_success "Virtual environment created"
else
    echo_success "Using existing virtual environment at $VENV_DIR"
fi

# Activate the venv (works in bash/zsh)
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
echo_success "Virtual environment activated ($(which python))"

# Install dependencies
echo_header "Installing dependencies"
if [ -f "$BASE_DIR/requirements-all.txt" ]; then
    pip install -q -r "$BASE_DIR/requirements-all.txt" || {
        echo_error "Failed to install dependencies"
        exit 1
    }
    echo_success "Dependencies installed"
else
    echo_error "requirements-all.txt not found"
    exit 1
fi

# Module 1: Anomaly Detection
echo_header "Module 1: Training Network Anomaly Detector"
cd "$BASE_DIR/module1/src" || exit 1
if python train.py; then
    echo_success "Module 1 training complete"
else
    echo_error "Module 1 training failed"
    exit 1
fi

# Module 2: Phishing Detection
echo_header "Module 2: Training Phishing Classifier"
cd "$BASE_DIR/module2/src" || exit 1
if python train.py; then
    echo_success "Module 2 training complete"
else
    echo_error "Module 2 training failed"
    exit 1
fi

# Module 3: Dashboard Dataset
echo_header "Module 3: Building Explainability Dataset"
cd "$BASE_DIR/module3/src" || exit 1
if python build_dataset.py; then
    echo_success "Module 3 dataset built"
    if python xai_engine.py; then
        echo_success "Module 3 XAI engine initialized"
    else
        echo_warning "Module 3 XAI engine initialization had warnings (non-fatal)"
    fi
else
    echo_error "Module 3 dataset build failed"
    exit 1
fi

# Module 4: SOC Orchestrator
echo_header "Module 4: Running SOC Orchestrator (Batch Mode)"
cd "$BASE_DIR/module4/src" || exit 1
if python main.py --batch 10 $MOCK_LLM; then
    echo_success "Module 4 orchestration complete"
else
    echo_error "Module 4 orchestration failed"
    exit 1
fi

# Summary
echo_header "Demo Complete!"
echo_success "All modules trained and integrated successfully."
echo ""
echo "Next steps:"
echo "  • Review Module 1 evaluation: module1/evaluation/"
echo "  • Review Module 2 evaluation: module2/evaluation/"
echo "  • View threat events: module4/data/event_log.jsonl"
echo "  • Launch dashboard: cd module3/src && streamlit run app.py"
echo ""
echo "For individual module testing:"
echo "  cd module1/src && python predict.py      # Test anomaly detection"
echo "  cd module2/src && python predict.py      # Test phishing classification"
echo "  cd module4/src && python main.py --help  # See orchestrator options"
echo ""
