# QuizForge

AI 驱动的智能题库与学习系统后端。FastAPI + SQLAlchemy(async) + PostgreSQL + Redis + Celery，AI 出题使用 DeepSeek（兼容 OpenAI 接口）。

## 功能

- JWT 认证（注册 / 登录 / 当前用户），角色：admin / editor / user
- 题库与题目 CRUD、题目审核
- AI 按主题出题（异步 Celery 任务，Redis 记录进度）
- 上传 pdf/docx/txt/md 文件解析后出题
- 答题会话（顺序/随机/错题/模拟四种模式），自动判分
- 错题本（答错自动入库，可标记掌握）
- 学习计划 CRUD
- 学习统计（个人概览 + 题库维度正确率）

## 目录

```
backend/
  app/
    main.py config.py database.py dependencies.py
    models/ schemas/ routers/ services/ tasks/ utils/
  celery_worker.py   # Celery 应用入口 (-A celery_worker)
  alembic/           # 数据库迁移
  test_api.py        # 端到端验证脚本
frontend/
  index.html         # 单文件前端（原生 HTML/CSS/JS，无构建步骤）
docker-compose.yml
```

## 前端

`frontend/index.html` 是一个零依赖的单文件 SPA，直接调用后端 API，覆盖：登录注册、题库管理、AI 出题（带进度）、答题（答题卡判分）、错题本、学习统计。

后端启动后，用任意静态服务器跑起来即可（前端默认连 `http://localhost:8000`）：

```bash
cd frontend && python3 -m http.server 5500
# 打开 http://localhost:5500
```

> 后端 CORS 已对所有来源开放，前后端分端口直接联调无需额外配置。

## 快速启动（Docker，推荐）

```bash
cp backend/.env.example backend/.env      # 填入 DEEPSEEK_API_KEY
docker-compose up --build
```

启动后：
- API 文档： http://localhost:8000/docs
- 健康检查： http://localhost:8000/

应用启动时会自动 `create_all` 建表，无需手动迁移即可跑通。

## 本地启动（不使用 Docker）

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # 改 DATABASE_URL/REDIS_URL 为 localhost，填 DEEPSEEK_API_KEY

# 需本地已运行 postgres 和 redis
uvicorn app.main:app --reload                       # 终端 1：API
celery -A celery_worker worker --loglevel=info      # 终端 2：Celery worker
```

## 数据库迁移（可选，create_all 已可建表）

```bash
cd backend
alembic revision --autogenerate -m "init"   # 需数据库可连接
alembic upgrade head
```

## 验证

后端 + postgres + redis + celery 全部就绪并配置好 `DEEPSEEK_API_KEY` 后：

```bash
cd backend
python test_api.py
```

脚本会依次：注册 → 登录 → 建"网络安全"题库 → 提交 SQL注入 出题任务 → 轮询至完成 → 查询生成的题目。
