#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BACKEND_SESSION="kayden_backend"
FRONTEND_SESSION="kayden_frontend"
TUNNEL_SESSION="kayden_tunnel"

FRONT_PORT="${FRONT_PORT:-7860}"
FRONT_HOST="${FRONT_HOST:-127.0.0.1}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8080/chat}"

if ! command -v tmux >/dev/null 2>&1; then
  echo "ERROR: tmux not found"
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "ERROR: cloudflared not found"
  exit 1
fi

if [ ! -f "$ROOT_DIR/front.py" ]; then
  echo "ERROR: front.py not found in $ROOT_DIR"
  exit 1
fi

if [ ! -f "$ROOT_DIR/start.sh" ]; then
  echo "ERROR: start.sh not found in $ROOT_DIR"
  exit 1
fi

if [ -f "$ROOT_DIR/.venv/bin/activate" ]; then
  PY_PREFIX=". '$ROOT_DIR/.venv/bin/activate' && "
else
  PY_PREFIX=""
fi

tmux has-session -t "$BACKEND_SESSION" 2>/dev/null && tmux kill-session -t "$BACKEND_SESSION"
tmux has-session -t "$FRONTEND_SESSION" 2>/dev/null && tmux kill-session -t "$FRONTEND_SESSION"
tmux has-session -t "$TUNNEL_SESSION" 2>/dev/null && tmux kill-session -t "$TUNNEL_SESSION"

tmux new-session -d -s "$BACKEND_SESSION" "cd '$ROOT_DIR' && chmod +x start.sh && $PY_PREFIX ./start.sh"
tmux new-session -d -s "$FRONTEND_SESSION" "cd '$ROOT_DIR' && BACKEND_URL='$BACKEND_URL' FRONT_HOST='$FRONT_HOST' FRONT_PORT='$FRONT_PORT' ${PY_PREFIX}python3 front.py"
tmux new-session -d -s "$TUNNEL_SESSION" "cd '$ROOT_DIR' && cloudflared tunnel --url http://$FRONT_HOST:$FRONT_PORT"

echo "Started tmux sessions:"
echo "  $BACKEND_SESSION"
echo "  $FRONTEND_SESSION"
echo "  $TUNNEL_SESSION"
echo
echo "Attach with:"
echo "  tmux attach -t $BACKEND_SESSION"
echo "  tmux attach -t $FRONTEND_SESSION"
echo "  tmux attach -t $TUNNEL_SESSION"
echo
echo "List sessions:"
echo "  tmux ls"
