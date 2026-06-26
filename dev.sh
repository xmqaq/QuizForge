#!/usr/bin/env bash
# 本地一键启动 QuizForge 全栈(复用本机 postgres / redis)
# 用法: ./dev.sh        启动(Ctrl-C 一并停掉所有子进程)
#       ./dev.sh stop   停止残留的服务、释放 8000/8080 端口
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

# 释放某个监听端口(杀掉占用它的进程)
free_port() {
  local pids
  pids="$(lsof -nP -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null || true)"
  [ -n "$pids" ] && kill $pids 2>/dev/null || true
}

# 停止本项目所有服务(子命令 stop 与启动前自愈共用)
stop_services() {
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  pkill -9 -f "celery -A celery_worker" 2>/dev/null || true
  free_port 8000
  free_port 8080
}

# 子命令: ./dev.sh stop
if [ "${1:-}" = "stop" ]; then
  echo "停止 QuizForge 本地服务…"
  stop_services
  sleep 1
  echo "✓ 已停止"
  exit 0
fi

# 1. 依赖检测(本机需已运行 postgres;redis 仅 AI 出题/celery 需要)
nc -z -G1 localhost 5432 >/dev/null 2>&1 || { echo "✗ postgres 未在 localhost:5432 运行,请先启动"; exit 1; }
nc -z -G1 localhost 6379 >/dev/null 2>&1 || echo "⚠ redis 未运行 — AI 出题(celery)将不可用"

# 2. backend 虚拟环境(首次创建并安装依赖)
cd backend
if [ ! -d .venv ]; then
  echo "→ 首次运行:创建 .venv 并安装依赖(稍等)…"
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi

# 3. 覆盖 .env 里的 docker 主机名为 localhost
export DATABASE_URL="postgresql+asyncpg://quizforge:quizforge@localhost:5432/quizforge"
export REDIS_URL="redis://localhost:6379/0"

# 4. 启动前自愈:清掉上次没退干净的残留,释放 8000/8080
if lsof -nP -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 \
   || lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "⚠ 端口被占用,清理上次残留…"
  stop_services
  sleep 1
fi

# 5. 后端 + celery(后台)
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
./.venv/bin/celery -A celery_worker worker --loglevel=warning &
cd "$ROOT"

# 6. 前端:注入 API 地址后静态托管(前端走相对路径,本地无反代故注入)
mkdir -p .dev-serve
sed 's#<body>#<body><script>window.QUIZFORGE_API="http://localhost:8000";</script>#' \
  frontend/index.html > .dev-serve/index.html
( cd .dev-serve && python3 -m http.server 8080 >/dev/null 2>&1 ) &

trap 'echo; echo "停止所有服务…"; kill 0' EXIT INT TERM
echo
echo "  前端  →  http://localhost:8080"
echo "  后端  →  http://localhost:8000/docs"
echo "  (Ctrl-C 停止)"
wait
