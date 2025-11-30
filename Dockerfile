# ===============================================
# LLM Debate Arena - Multi-stage Docker Build
# ===============================================

# ============ Stage 1: Build Frontend ============
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci --only=production

# 复制前端源码
COPY frontend/ ./

# 构建前端
RUN npm run build

# ============ Stage 2: Build Backend ============
FROM python:3.11-slim AS backend-builder

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖文件
COPY backend/requirements.txt ./backend/

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# ============ Stage 3: Production Image ============
FROM python:3.11-slim

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制 Python 依赖
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# 复制后端代码
COPY backend/ ./backend/
COPY pyproject.toml .

# 从前端构建阶段复制静态文件
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# 创建数据目录
RUN mkdir -p /app/data

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=sqlite:////app/data/debate_arena.db

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 启动命令
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
