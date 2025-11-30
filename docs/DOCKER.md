# Docker 部署指南

本文档介绍如何使用 Docker 部署 LLM Debate Arena。

## 📋 前置要求

- Docker 20.10+
- Docker Compose 2.0+ (可选，推荐)

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

最简单的部署方式，一键启动所有服务。

#### 1. 准备配置文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写必要的配置
nano .env
```

必需的环境变量：

```env
# LLM API 配置
OPENROUTER_API_KEY=your_openai_api_key_here
OPENROUTER_API_URL=https://api.openai.com/v1

# 可用模型列表（逗号分隔）
AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet,gpt-5.1

# Serper API（搜索工具，可选）
SERPER_API_KEY=your_serper_api_key_here
```

#### 2. 启动服务

```bash
# 构建并启动服务（首次启动）
docker-compose up -d --build

# 后续启动（不重新构建）
docker-compose up -d
```

#### 3. 查看日志

```bash
# 查看所有日志
docker-compose logs -f

# 查看最近 100 行日志
docker-compose logs -f --tail=100
```

#### 4. 访问服务

- **前端界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

#### 5. 停止服务

```bash
# 停止服务（保留数据）
docker-compose down

# 停止服务并删除数据卷
docker-compose down -v
```

### 方式二：Docker 直接运行

不使用 Docker Compose，直接运行单个容器。

#### 1. 构建镜像

```bash
docker build -t llm-debate-arena:latest .
```

#### 2. 运行容器

```bash
docker run -d \
  --name debate-arena \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e OPENROUTER_API_KEY=your_api_key \
  -e OPENROUTER_API_URL=https://api.openai.com/v1 \
  -e AVAILABLE_MODELS=gpt-4o,gpt-4o-mini,claude-3.5-sonnet \
  -e SERPER_API_KEY=your_serper_api_key \
  llm-debate-arena:latest
```

#### 3. 查看日志

```bash
docker logs -f debate-arena
```

#### 4. 停止和删除容器

```bash
# 停止容器
docker stop debate-arena

# 删除容器
docker rm debate-arena
```

## 🔧 高级配置

### 自定义端口

修改 `docker-compose.yml` 中的端口映射：

```yaml
services:
  debate-arena:
    ports:
      - "3000:8000"  # 将服务映射到宿主机的 3000 端口
```

### 数据持久化

数据库文件默认保存在 Docker volume `debate-data` 中。

#### 查看数据卷

```bash
docker volume ls
docker volume inspect llm-debate-arena_debate-data
```

#### 备份数据

```bash
# 备份数据卷
docker run --rm \
  -v llm-debate-arena_debate-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/debate-data-$(date +%Y%m%d).tar.gz /data
```

#### 恢复数据

```bash
# 恢复数据卷
docker run --rm \
  -v llm-debate-arena_debate-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/debate-data-20240101.tar.gz -C /
```

### 使用外部数据库

如果不想使用 SQLite，可以使用 PostgreSQL：

#### 1. 修改 `docker-compose.yml`

```yaml
services:
  debate-arena:
    # ... 其他配置
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/debate_arena
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    container_name: debate-postgres
    environment:
      - POSTGRES_DB=debate_arena
      - POSTGRES_USER=debate_user
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  debate-data:
  postgres-data:
```

#### 2. 更新后端依赖

在 `backend/requirements.txt` 中添加：

```
psycopg2-binary>=2.9.0
```

### 配置 HTTPS

使用 Nginx 作为反向代理：

#### 1. 创建 `nginx.conf`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://debate-arena:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }
}
```

#### 2. 更新 `docker-compose.yml`

```yaml
services:
  nginx:
    image: nginx:alpine
    container_name: debate-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - debate-arena

  debate-arena:
    # ... 其他配置
    expose:
      - "8000"
```

## 🐛 故障排查

### 容器无法启动

```bash
# 查看容器状态
docker ps -a

# 查看详细日志
docker logs debate-arena

# 检查配置
docker inspect debate-arena
```

### 健康检查失败

```bash
# 手动测试健康检查
docker exec debate-arena curl -f http://localhost:8000/health

# 查看健康状态
docker inspect --format='{{.State.Health.Status}}' debate-arena
```

### 数据库锁定问题

SQLite 在高并发下可能出现锁定。解决方案：

1. 使用 PostgreSQL 替代 SQLite（推荐）
2. 减少并发请求
3. 使用 WAL 模式（已在代码中启用）

### 内存不足

```bash
# 限制容器内存使用
docker run -d \
  --memory="2g" \
  --memory-swap="2g" \
  ... 其他参数

# 或在 docker-compose.yml 中配置
services:
  debate-arena:
    deploy:
      resources:
        limits:
          memory: 2G
```

## 🔒 安全建议

1. **不要在生产环境中暴露 API 密钥**
   - 使用 Docker secrets 或环境变量
   - 定期轮换密钥

2. **使用非 root 用户运行**
   - Dockerfile 中已配置

3. **限制容器权限**
   ```bash
   docker run --read-only --tmpfs /tmp ...
   ```

4. **使用 HTTPS**
   - 生产环境必须使用 HTTPS
   - 使用 Let's Encrypt 免费证书

5. **定期更新镜像**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 📊 监控和日志

### 日志持久化

在 `docker-compose.yml` 中配置日志驱动：

```yaml
services:
  debate-arena:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 集成监控

推荐使用 Prometheus + Grafana：

```yaml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
```

## 🚀 生产环境部署

### 云平台部署

#### AWS ECS

```bash
# 推送镜像到 ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag llm-debate-arena:latest <account>.dkr.ecr.us-east-1.amazonaws.com/debate-arena:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/debate-arena:latest
```

#### Google Cloud Run

```bash
# 推送到 Google Container Registry
gcloud builds submit --tag gcr.io/<project-id>/debate-arena
gcloud run deploy debate-arena --image gcr.io/<project-id>/debate-arena --platform managed
```

#### Azure Container Instances

```bash
# 推送到 Azure Container Registry
az acr build --registry <registry-name> --image debate-arena:latest .
az container create --resource-group <rg> --name debate-arena --image <registry>.azurecr.io/debate-arena:latest
```

## 📚 相关资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目主 README](../README.md)
- [后端 README](../backend/README.md)
- [前端 README](../frontend/README.md)
