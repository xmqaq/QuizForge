#!/usr/bin/env bash
# 本地一键启动 QuizForge 全栈(复用本机 postgres / redis)
# 用法: ./dev.sh   —— Ctrl-C 一并停掉所有子进程
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(pwd)"

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

# 4. 后端 + celery(后台)
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
./.venv/bin/celery -A celery_worker worker --loglevel=warning &
cd "$ROOT"

# 5. 前端:注入 API 地址后静态托管(前端走相对路径,本地无反代故注入)
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
