# Web UI launcher

Files:
- `front.py` — web UI server that relays browser messages to the backend `/chat`
- `launch_stack.sh` — starts backend, frontend, and cloudflared in separate tmux sessions

## Default ports
- Backend: `127.0.0.1:8080`
- Frontend: `127.0.0.1:7860`

## Run
```sh
chmod +x launch_stack.sh
sh launch_stack.sh
```

## Optional environment variables
```sh
FRONT_PORT=7860 FRONT_HOST=127.0.0.1 BACKEND_URL=http://127.0.0.1:8080/chat sh launch_stack.sh
```

## tmux sessions
- `kayden_backend`
- `kayden_frontend`
- `kayden_tunnel`
