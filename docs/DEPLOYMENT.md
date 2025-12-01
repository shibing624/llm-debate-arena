# 🚀 生产环境部署指南

本文档详细说明如何将 LLM Debate Arena 部署到生产环境。

## 📋 目录

- [问题背景](#问题背景)
- [解决方案](#解决方案)
- [部署步骤](#部署步骤)
- [Nginx 配置](#nginx-配置)
- [后端 HTTPS 配置](#后端-https-配置)
- [故障排查](#故障排查)

---

## 🔍 问题背景

### Mixed Content 错误

当前端部署在 HTTPS 域名 时，如果后端使用 HTTP 协议，浏览器会阻止请求：

**原因**：现代浏览器的安全策略禁止 HTTPS 页面请求 HTTP 资源。

---

## ✅ 解决方案

### 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案 1: Nginx 反向代理** | ✅ 安全<br>✅ 简单<br>✅ 统一域名 | 需要配置 Nginx | ⭐⭐⭐⭐⭐ |
| **方案 2: 后端启用 HTTPS** | ✅ 直接访问 | ❌ 需要证书<br>❌ 暴露后端端口 | ⭐⭐⭐ |

**推荐使用方案 1**：通过 Nginx 反向代理，前端使用相对路径访问 API。

---

## 🛠️ 部署步骤

### 1️⃣ 配置前端环境变量

**编辑 `frontend/.env`**：

```bash
# 生产环境配置
VITE_API_BASE_URL=http://localhost:8000  # 保持默认值
VITE_IS_DEV=false                        # 设置为 false
```

**说明**：
- `VITE_IS_DEV=false`：生产模式，使用相对路径（如 `/api/...`）
- `VITE_API_BASE_URL` 保持默认值，不使用完整 URL

### 2️⃣ 构建前端

```bash
cd frontend
npm install
npm run build
```

构建产物位于 `frontend/dist/` 目录。

### 3️⃣ 配置 Nginx

#### 3.1 安装 Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

#### 3.2 创建配置文件

将项目根目录的 `nginx.conf` 复制到 Nginx 配置目录：

```bash
sudo cp nginx.conf /etc/nginx/sites-available/debate-arena
sudo ln -s /etc/nginx/sites-available/debate-arena /etc/nginx/sites-enabled/
```

#### 3.3 修改配置

编辑 `/etc/nginx/sites-available/debate-arena`，修改以下内容：

```nginx
server {
    listen 443 ssl http2;
    server_name debate.mulanai.com;  # 修改为你的域名

    # ⚠️ 修改为你的 SSL 证书路径
    ssl_certificate /path/to/your/ssl/certificate.crt;
    ssl_certificate_key /path/to/your/ssl/private.key;

    # ⚠️ 修改为你的前端构建目录
    root /path/to/llm-debate-arena/frontend/dist;

    # ...（其余配置保持不变）

    # ⚠️ 修改为你的后端地址
    location /api/ {
        proxy_pass http://180.76.159.241:8009;
        # ...
    }
}
```

#### 3.4 测试并重启 Nginx

```bash
# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx

# 设置开机自启
sudo systemctl enable nginx
```

### 4️⃣ 启动后端服务

```bash
cd /path/to/llm-debate-arena
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8009
```

**推荐使用 Systemd 管理后端服务**（见下方）。

---

## 🔧 Nginx 配置详解

### 核心配置说明

```nginx
# 1. 前端静态文件
location / {
    try_files $uri $uri/ /index.html;  # SPA 路由回退到 index.html
}

# 2. 后端 API 代理（关键！）
location /api/ {
    proxy_pass http://180.76.159.241:8009;  # 代理到后端服务器
    
    # SSE 支持（Server-Sent Events，用于实时辩论）
    proxy_buffering off;           # 禁用缓冲
    proxy_cache off;               # 禁用缓存
    chunked_transfer_encoding off; # 禁用分块传输
    
    # 超时设置（辩论可能需要较长时间）
    proxy_read_timeout 300s;       # 5 分钟超时
}
```

### SSL 证书配置

#### 使用 Let's Encrypt 免费证书

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 自动获取证书并配置
sudo certbot --nginx -d debate.mulanai.com

# 自动续期测试
sudo certbot renew --dry-run
```

#### 手动配置证书

如果已有证书，修改 Nginx 配置：

```nginx
ssl_certificate /etc/ssl/certs/your-certificate.crt;
ssl_certificate_key /etc/ssl/private/your-private.key;
```

---

## 🔐 后端 HTTPS 配置（方案 2）

如果不使用 Nginx 反向代理，需要为后端启用 HTTPS。

### 1️⃣ 前端配置

**编辑 `frontend/.env`**：

```bash
# 使用 HTTPS 后端地址
VITE_API_BASE_URL=https://api.mulanai.com:8009
VITE_IS_DEV=false
```

### 2️⃣ 后端启用 HTTPS

**使用 Uvicorn 启动（需要证书）**：

```bash
uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port 8009 \
  --ssl-keyfile=/path/to/private.key \
  --ssl-certfile=/path/to/certificate.crt
```

---

## 🐳 使用 Systemd 管理后端服务

### 创建服务文件

**创建 `/etc/systemd/system/debate-arena-backend.service`**：

```ini
[Unit]
Description=LLM Debate Arena Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/llm-debate-arena
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8009
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start debate-arena-backend

# 设置开机自启
sudo systemctl enable debate-arena-backend

# 查看状态
sudo systemctl status debate-arena-backend

# 查看日志
sudo journalctl -u debate-arena-backend -f
```

---

## 🚨 故障排查

### 问题 1: Mixed Content 错误

**症状**：浏览器控制台报错 `Mixed Content: ...`

**解决**：
1. 确认 `frontend/.env` 中 `VITE_IS_DEV=false`
2. 确认 `VITE_API_BASE_URL` 为默认值 `http://localhost:8000`
3. 重新构建前端 `npm run build`
4. 检查 Nginx 配置中 `location /api/` 是否正确

### 问题 2: API 请求 404

**症状**：前端请求 `/api/...` 返回 404

**解决**：
1. 检查 Nginx 配置中 `proxy_pass` 地址是否正确
2. 确认后端服务正在运行：`curl http://180.76.159.241:8009/api/health`
3. 检查 Nginx 日志：`sudo tail -f /var/log/nginx/debate-arena-error.log`

### 问题 3: SSE 流中断

**症状**：辩论进行中突然中断

**解决**：
1. 增加 Nginx 超时时间：
```nginx
location /api/ {
    proxy_read_timeout 600s;  # 增加到 10 分钟
    proxy_send_timeout 600s;
}
```

2. 禁用缓冲：
```nginx
proxy_buffering off;
proxy_cache off;
```

### 问题 4: CORS 错误

**症状**：浏览器报 CORS 错误

**解决**：
1. 在 Nginx 配置中添加 CORS 头：
```nginx
location /api/ {
    add_header Access-Control-Allow-Origin *;
    add_header Access-Control-Allow-Methods 'GET, POST, PUT, DELETE, OPTIONS';
    add_header Access-Control-Allow-Headers 'Content-Type, Authorization';
}
```

### 问题 5: 静态资源缓存问题

**症状**：更新代码后前端未更新

**解决**：
1. 清除浏览器缓存
2. 修改 Nginx 配置，禁用 HTML 缓存：
```nginx
location / {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

---

## 📊 部署检查清单

完成部署后，请检查：

- [ ] 前端 `.env` 配置正确（`VITE_IS_DEV=false`）
- [ ] 前端已重新构建 `npm run build`
- [ ] Nginx 配置已更新并重启
- [ ] SSL 证书配置正确
- [ ] 后端服务正在运行
- [ ] 访问 `https://debate.mulanai.com` 正常
- [ ] 浏览器控制台无 Mixed Content 错误
- [ ] API 请求成功（检查 Network 面板）
- [ ] SSE 流式辩论正常运行
- [ ] 排行榜、历史记录等页面正常

---

## 🎉 部署成功

如果以上检查都通过，恭喜你成功部署了 LLM Debate Arena！

访问地址：`https://debate.mulanai.com`

---

## 📞 需要帮助？

如遇到问题，请：

1. 查看 Nginx 错误日志：`sudo tail -f /var/log/nginx/debate-arena-error.log`
2. 查看后端日志：`sudo journalctl -u debate-arena-backend -f`
3. 检查浏览器控制台的 Network 面板
4. 提交 Issue 到 GitHub

---

**最后更新**: 2025-12-01
