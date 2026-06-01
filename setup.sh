#!/usr/bin/env bash
set -euo pipefail

# ── colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. System packages ────────────────────────────────────────────────────────
info "Updating package lists..."
sudo apt-get update -qq

# Python 3.11+ and venv
if ! command -v python3 &>/dev/null || ! python3 -c "import sys; assert sys.version_info >= (3,11)" 2>/dev/null; then
  info "Installing Python 3.11..."
  sudo apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip
  sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
else
  info "Python already installed: $(python3 --version)"
fi

# Node.js 20 LTS
if ! command -v node &>/dev/null; then
  info "Installing Node.js 20 LTS..."
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y -qq nodejs
else
  info "Node.js already installed: $(node --version)"
fi

# ── 2. .env file ──────────────────────────────────────────────────────────────
ENV_FILE="$SCRIPT_DIR/backend/.env"
ENV_EXAMPLE="$SCRIPT_DIR/backend/.env.example"

if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE" ]]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    warn "Created backend/.env from .env.example"
    warn "Edit backend/.env and set GOOGLE_API_KEY before continuing."
    echo ""
    warn "  nano $ENV_FILE"
    echo ""
    read -rp "Press Enter once GOOGLE_API_KEY is set, or Ctrl-C to abort..."
  else
    error "backend/.env.example not found."
  fi
else
  info "backend/.env already exists — skipping copy."
fi

if grep -q 'GOOGLE_API_KEY=changeme' "$ENV_FILE"; then
  warn "GOOGLE_API_KEY is still 'changeme' in backend/.env — API calls will fail."
fi

# ── 3. Python virtual environment & dependencies ──────────────────────────────
VENV_DIR="$SCRIPT_DIR/backend/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating Python virtual environment..."
  python3 -m venv "$VENV_DIR"
fi

info "Installing Python dependencies (this may take a few minutes)..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install --no-cache-dir -r "$SCRIPT_DIR/backend/requirements.txt" -q
info "Python dependencies installed."

# ── 4. Node.js dependencies ───────────────────────────────────────────────────
info "Installing frontend npm dependencies..."
cd "$SCRIPT_DIR/frontend"
npm install --prefer-online --silent
info "npm dependencies installed."

# ── 5. Start services ─────────────────────────────────────────────────────────
cd "$SCRIPT_DIR"

# Kill any previous instances
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite"                 2>/dev/null || true
sleep 1

info "Starting backend (uvicorn)..."
cd "$SCRIPT_DIR/backend"
"$VENV_DIR/bin/uvicorn" app.main:app \
  --host 0.0.0.0 --port 8000 \
  --log-level info \
  >> "$SCRIPT_DIR/backend/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$SCRIPT_DIR/backend/backend.pid"
info "Backend PID: $BACKEND_PID  (logs: backend/backend.log)"

info "Starting frontend (vite dev)..."
cd "$SCRIPT_DIR/frontend"
npm run dev -- --host \
  >> "$SCRIPT_DIR/frontend/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "$FRONTEND_PID" > "$SCRIPT_DIR/frontend/frontend.pid"
info "Frontend PID: $FRONTEND_PID  (logs: frontend/frontend.log)"

# ── 6. Health check ───────────────────────────────────────────────────────────
info "Waiting for backend to become healthy..."
MAX=30; COUNT=0
until curl -sf http://localhost:8000/ &>/dev/null; do
  COUNT=$((COUNT + 1))
  if [[ $COUNT -ge $MAX ]]; then
    warn "Backend did not respond after ${MAX}s — check backend/backend.log"
    break
  fi
  sleep 2
done
curl -sf http://localhost:8000/ &>/dev/null && info "Backend is up."

# ── 7. Summary ────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Application is running${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  Backend  →  http://localhost:8000"
echo "  Frontend →  http://localhost:5173"
echo "  API docs →  http://localhost:8000/docs"
echo ""
echo "GCE firewall — allow these ports if accessing externally:"
echo "  gcloud compute firewall-rules create allow-app \\"
echo "    --allow tcp:8000,tcp:5173 \\"
echo "    --target-tags <your-instance-tag>"
echo ""
echo "Logs:   tail -f backend/backend.log   |   tail -f frontend/frontend.log"
echo "Stop:   kill \$(cat backend/backend.pid) \$(cat frontend/frontend.pid)"
echo ""
