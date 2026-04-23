#!/usr/bin/env bash
# --- SYSTEM INSTALLER (ENV-AWARE v3.0) ---

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

log() { echo "[INSTALL] $*"; }
warn() { echo "[WARN] $*"; }
fail() { echo "[ERROR] $*" >&2; exit 1; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

OS_FAMILY="unknown"
OS_NAME="unknown"
PKG_MANAGER=""

detect_environment() {
    local uname_out
    uname_out="$(uname -s 2>/dev/null || echo unknown)"

    if [[ "$uname_out" == "Darwin" ]]; then
        OS_FAMILY="macos"
        OS_NAME="macOS"
        if command_exists brew; then
            PKG_MANAGER="brew"
        fi
        return
    fi

    if [[ -f /etc/os-release ]]; then
        # shellcheck disable=SC1091
        source /etc/os-release
        OS_NAME="${PRETTY_NAME:-${NAME:-Linux}}"
        case "${ID:-}" in
            ubuntu|debian|linuxmint|pop)
                OS_FAMILY="linux"
                PKG_MANAGER="apt"
                ;;
            fedora)
                OS_FAMILY="linux"
                PKG_MANAGER="dnf"
                ;;
            rhel|centos|rocky|almalinux)
                OS_FAMILY="linux"
                if command_exists dnf; then
                    PKG_MANAGER="dnf"
                else
                    PKG_MANAGER="yum"
                fi
                ;;
            arch|manjaro)
                OS_FAMILY="linux"
                PKG_MANAGER="pacman"
                ;;
            *)
                OS_FAMILY="linux"
                ;;
        esac
    else
        OS_FAMILY="linux"
        OS_NAME="Linux"
    fi
}

install_system_packages_if_needed() {
    local missing=()
    command_exists python3 || missing+=(python3)
    command_exists git || missing+=(git)

    if command_exists pip3; then
        :
    elif command_exists python3; then
        if ! python3 -m pip --version >/dev/null 2>&1; then
            missing+=(pip3)
        fi
    else
        missing+=(pip3)
    fi

    if command_exists python3; then
        python3 -m venv --help >/dev/null 2>&1 || missing+=(python3-venv)
    fi

    log "Detected OS: $OS_NAME"
    log "Detected package manager: ${PKG_MANAGER:-none}"

    if [[ ${#missing[@]} -eq 0 ]]; then
        log "Base system tools already available."
        return
    fi

    warn "Missing base tools: ${missing[*]}"

    case "$PKG_MANAGER" in
        apt)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv git
            ;;
        dnf)
            sudo dnf install -y python3 python3-pip git
            ;;
        yum)
            sudo yum install -y python3 python3-pip git
            ;;
        pacman)
            sudo pacman -Sy --noconfirm python git
            ;;
        brew)
            brew install python git
            ;;
        *)
            fail "Could not auto-install base tools on this environment. Install python3, pip, git, and venv support manually."
            ;;
    esac
}

setup_python_env() {
    command_exists python3 || fail "python3 missing after system package stage"
    command_exists git || fail "git missing after system package stage"

    local pyver
    pyver="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    log "Python detected: $pyver"

    if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
        fail "Python 3.10+ is required for the current dependency stack."
    fi

    if [[ ! -d .venv ]]; then
        log "Creating virtual environment at .venv"
        python3 -m venv .venv
    else
        log "Using existing virtual environment at .venv"
    fi

    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --upgrade pip setuptools wheel
}

install_python_requirements() {
    local req_file="requirements.txt"
    [[ -f "$req_file" ]] || fail "Missing $req_file"

    log "Installing Python dependencies from $req_file"
    python -m pip install -r "$req_file"
}

ensure_runtime_files() {
    mkdir -p identity state state/notes logs core tools patches README

    [[ -f soul.md ]] || cat > soul.md <<'EOL'
# Soul Template
Add the system identity and operating principles here.
EOL

    [[ -f chat_history.json ]] || echo '[]' > chat_history.json
    [[ -f belief_graph.json ]] || echo '{}' > belief_graph.json

    [[ -f .gitignore ]] || cat > .gitignore <<'EOL'
.env
.venv/
__pycache__/
*.pyc
state/
logs/
*.log
EOL
}

configure_env_file() {
    local existing_api_key=""
    local existing_api_base=""
    local existing_model=""

    if [[ -f .env ]]; then
        existing_api_key="$(grep -E '^API_KEY=' .env | tail -n1 | cut -d= -f2- || true)"
        existing_api_base="$(grep -E '^API_BASE_URL=' .env | tail -n1 | cut -d= -f2- || true)"
        existing_model="$(grep -E '^MODEL_NAME=' .env | tail -n1 | cut -d= -f2- || true)"
    fi

    echo
    read -r -p "API_KEY [${existing_api_key:-none}]: " API_KEY
    read -r -p "API_BASE_URL [${existing_api_base:-http://localhost:1234/v1}]: " API_BASE_URL
    read -r -p "MODEL_NAME [${existing_model:-enter-model-name}]: " MODEL_NAME

    API_KEY="${API_KEY:-${existing_api_key:-none}}"
    API_BASE_URL="${API_BASE_URL:-${existing_api_base:-http://localhost:1234/v1}}"
    MODEL_NAME="${MODEL_NAME:-$existing_model}"

    cat > .env <<EOL
API_KEY=$API_KEY
API_BASE_URL=$API_BASE_URL
MODEL_NAME=$MODEL_NAME
EOL

    log ".env written"
}

configure_git_identity() {
    local current_name current_email
    current_name="$(git config --global user.name || true)"
    current_email="$(git config --global user.email || true)"

    echo
    read -r -p "Git username [${current_name:-skip}]: " GIT_NAME
    read -r -p "Git email [${current_email:-skip}]: " GIT_EMAIL

    if [[ -n "${GIT_NAME:-}" ]]; then
        git config --global user.name "$GIT_NAME"
    fi
    if [[ -n "${GIT_EMAIL:-}" ]]; then
        git config --global user.email "$GIT_EMAIL"
    fi

    if [[ ! -d .git ]]; then
        git init
        log "Initialized git repository"
    fi

    read -r -p "Remote origin URL [leave blank to skip]: " REMOTE_URL
    if [[ -n "${REMOTE_URL:-}" ]]; then
        git remote remove origin >/dev/null 2>&1 || true
        git remote add origin "$REMOTE_URL"
        log "Configured git origin"
    fi
}

validate_structure() {
    log "Validating system structure"
    local files=(
        "main.py"
        "start.sh"
        "install.sh"
        "requirements.txt"
        "core/engine.py"
        "core/persistence.py"
        "core/manual_manager.py"
        "core/belief_graph.py"
        "core/patch_bus_driver.py"
        "tools/tools_bridge.py"
        "patches/patches_bridge.py"
        "patches/tool_driver.py"
    )

    local missing=0
    for f in "${files[@]}"; do
        if [[ ! -f "$f" ]]; then
            echo "[ERROR] Missing file: $f" >&2
            missing=1
        fi
    done

    (( missing == 0 )) || fail "System structure validation failed"

    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m py_compile main.py core/*.py patches/*.py tools/*.py
    log "Python syntax validation passed"
}

final_message() {
    cat <<'EOM'

[INSTALL COMPLETE]
Next steps:
1. Activate the environment: source .venv/bin/activate
2. Start the app: ./start.sh
3. Check health: http://127.0.0.1:8080/health
EOM
}

main() {
    log "Booting system installer"
    detect_environment
    install_system_packages_if_needed
    setup_python_env
    install_python_requirements
    ensure_runtime_files
    configure_env_file
    configure_git_identity
    validate_structure
    final_message
}

main "$@"
