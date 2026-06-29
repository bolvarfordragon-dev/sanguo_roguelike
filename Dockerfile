# 三国文字Roguelike — Lighthouse 部署镜像
# 基于 Python 3.11 slim，单阶段构建，~150MB

FROM python:3.11-slim

# 容器内的工作目录
WORKDIR /app

# 先装依赖（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# 复制应用代码
COPY . .

# 写权限给 web/ 静态文件和 saves/ 数据目录
RUN mkdir -p /app/saves && chmod -R 755 /app/web

# 暴露端口（运行时由 $PORT 覆盖）
ENV PORT=5000
EXPOSE 5000

# 健康检查 — 命中首页
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/state', timeout=3)" || exit 1

# 单 worker（与原 Railway 配置一致；游戏是单例状态，多 worker 会导致数据竞争）
CMD exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 4 \
    --access-logfile - --error-logfile - \
    --timeout 30 \
    wsgi:app
