# SQLite 迁移到 MySQL 指南

本文档详细介绍如何将 LLM Debate Arena 从 SQLite 迁移到 MySQL 数据库。

## 为什么迁移到 MySQL？

- **并发性能**：SQLite 在高并发场景下性能受限，MySQL 支持更高的并发连接
- **扩展性**：MySQL 支持主从复制、读写分离，便于水平扩展
- **稳定性**：生产环境推荐使用 MySQL，更适合 500+ 用户的场景

## 一、MySQL 服务端配置

### 1.1 安装 MySQL（如已有远程服务可跳过）

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
sudo systemctl start mysqld

# macOS (Homebrew)
brew install mysql
brew services start mysql
```

### 1.2 创建数据库和用户

登录 MySQL：

```bash
# 本地登录
mysql -u root -p

# 远程登录（替换为你的服务器IP）
mysql -h YOUR_MYSQL_HOST -u root -p
```

执行以下 SQL 创建数据库和用户：

```sql
-- 创建数据库（使用 utf8mb4 支持 emoji 和中文）
CREATE DATABASE debate_arena 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（替换 your_password 为强密码）
CREATE USER 'debate_user'@'%' IDENTIFIED BY 'your_password';

-- 授权（允许从任意 IP 连接）
GRANT ALL PRIVILEGES ON debate_arena.* TO 'debate_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;

-- 验证
SHOW GRANTS FOR 'debate_user'@'%';
```

> **安全提示**：生产环境建议将 `'%'` 改为具体的应用服务器 IP，如 `'192.168.1.100'`

### 1.3 配置 MySQL 允许远程连接

编辑 MySQL 配置文件：

```bash
# Ubuntu/Debian
sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf

# CentOS/RHEL
sudo vim /etc/my.cnf
```

修改 `bind-address`：

```ini
[mysqld]
# 允许所有 IP 连接（或指定具体 IP）
bind-address = 0.0.0.0

# 推荐配置
max_connections = 500
innodb_buffer_pool_size = 1G
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

重启 MySQL：

```bash
sudo systemctl restart mysql
# 或
sudo systemctl restart mysqld
```

### 1.4 防火墙放行 3306 端口

```bash
# Ubuntu (ufw)
sudo ufw allow 3306/tcp

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=3306/tcp
sudo firewall-cmd --reload

# 云服务器安全组
# 请在云控制台添加入站规则：TCP 3306 端口
```

### 1.5 验证远程连接

从应用服务器测试连接：

```bash
mysql -h YOUR_MYSQL_HOST -u debate_user -p debate_arena
```

## 二、应用端配置

### 2.1 安装 MySQL 驱动

```bash
# 安装 PyMySQL（纯 Python 实现，无需编译）
pip install pymysql

# 或安装 mysqlclient（性能更好，需要编译环境）
# Ubuntu: sudo apt install libmysqlclient-dev
# pip install mysqlclient
```

### 2.2 修改环境变量

编辑 `.env` 文件：

```env
# SQLite（旧配置，注释掉）
# DATABASE_URL=sqlite:///./debate_arena.db

# MySQL 配置
DATABASE_URL=mysql+pymysql://debate_user:your_password@YOUR_MYSQL_HOST:3306/debate_arena?charset=utf8mb4
```

**连接字符串格式说明**：

```
mysql+pymysql://用户名:密码@主机:端口/数据库名?charset=utf8mb4
```

**示例**：

```env
# 本地 MySQL
DATABASE_URL=mysql+pymysql://debate_user:MyP@ssw0rd@localhost:3306/debate_arena?charset=utf8mb4

# 远程 MySQL
DATABASE_URL=mysql+pymysql://debate_user:MyP@ssw0rd@192.168.1.100:3306/debate_arena?charset=utf8mb4

# 云数据库（如阿里云 RDS）
DATABASE_URL=mysql+pymysql://debate_user:MyP@ssw0rd@rm-xxx.mysql.rds.aliyuncs.com:3306/debate_arena?charset=utf8mb4
```

> **注意**：密码中如有特殊字符（如 `@`、`#`），需要进行 URL 编码

## 三、数据迁移

### 3.1 导出 SQLite 数据

```bash
cd /path/to/llm-debate-arena

# 使用 Python 脚本导出数据
python backend/migrate_sqlite_to_mysql.py --export
```

### 3.2 迁移脚本

创建 `backend/migrate_sqlite_to_mysql.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite 到 MySQL 数据迁移脚本
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

def export_sqlite_data(sqlite_path: str, output_dir: str = "migration_data"):
    """导出 SQLite 数据到 JSON 文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    tables = ['competitors', 'debate_topics', 'users', 'matches']
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            
            # 处理 JSON 字段
            for row in data:
                for key, value in row.items():
                    if isinstance(value, str) and (value.startswith('[') or value.startswith('{')):
                        try:
                            row[key] = json.loads(value)
                        except:
                            pass
            
            output_file = os.path.join(output_dir, f"{table}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"✓ 导出 {table}: {len(data)} 条记录")
        except Exception as e:
            print(f"✗ 导出 {table} 失败: {e}")
    
    conn.close()
    print(f"\n数据已导出到 {output_dir}/ 目录")


def import_to_mysql(data_dir: str = "migration_data"):
    """导入数据到 MySQL"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 从环境变量读取 MySQL 连接
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url or 'mysql' not in database_url:
        print("错误: DATABASE_URL 未配置或不是 MySQL 连接")
        sys.exit(1)
    
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 导入 models 创建表
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from models import Base, CompetitorModel, DebateTopicModel, UserModel, MatchModel
    
    # 创建表结构
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库表结构已创建")
    
    # 导入数据
    table_model_map = {
        'competitors': CompetitorModel,
        'debate_topics': DebateTopicModel,
        'users': UserModel,
        'matches': MatchModel
    }
    
    for table, Model in table_model_map.items():
        json_file = os.path.join(data_dir, f"{table}.json")
        if not os.path.exists(json_file):
            print(f"⚠ 跳过 {table}: 文件不存在")
            continue
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for row in data:
            # 移除 id 字段让 MySQL 自动生成
            row_copy = row.copy()
            if 'id' in row_copy:
                del row_copy['id']
            
            # 处理日期字段
            for key in ['created_at', 'last_match_at', 'last_login', 'finished_at']:
                if key in row_copy and row_copy[key]:
                    if isinstance(row_copy[key], str):
                        try:
                            row_copy[key] = datetime.fromisoformat(row_copy[key].replace('Z', '+00:00'))
                        except:
                            row_copy[key] = None
            
            try:
                obj = Model(**row_copy)
                session.add(obj)
            except Exception as e:
                print(f"⚠ 导入 {table} 记录失败: {e}")
        
        session.commit()
        print(f"✓ 导入 {table}: {len(data)} 条记录")
    
    session.close()
    print("\n✓ 数据迁移完成！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SQLite 到 MySQL 数据迁移")
    parser.add_argument('--export', action='store_true', help='导出 SQLite 数据')
    parser.add_argument('--import', dest='do_import', action='store_true', help='导入数据到 MySQL')
    parser.add_argument('--sqlite', default='debate_arena.db', help='SQLite 数据库文件路径')
    parser.add_argument('--data-dir', default='migration_data', help='数据目录')
    
    args = parser.parse_args()
    
    if args.export:
        # 查找 SQLite 文件
        sqlite_paths = [
            args.sqlite,
            f"./{args.sqlite}",
            f"../{args.sqlite}",
            f"../debate_arena1.db",
        ]
        sqlite_path = None
        for path in sqlite_paths:
            if os.path.exists(path):
                sqlite_path = path
                break
        
        if not sqlite_path:
            print(f"错误: 找不到 SQLite 数据库文件")
            sys.exit(1)
        
        print(f"使用 SQLite 文件: {sqlite_path}")
        export_sqlite_data(sqlite_path, args.data_dir)
    
    elif args.do_import:
        import_to_mysql(args.data_dir)
    
    else:
        parser.print_help()
```

### 3.3 执行迁移

```bash
cd backend

# 步骤1: 导出 SQLite 数据
python migrate_sqlite_to_mysql.py --export --sqlite ../debate_arena1.db

# 步骤2: 确认 .env 中 DATABASE_URL 已改为 MySQL
cat ../.env | grep DATABASE_URL

# 步骤3: 导入数据到 MySQL
python migrate_sqlite_to_mysql.py --import
```

## 四、验证迁移

### 4.1 检查数据完整性

```bash
# 登录 MySQL 检查
mysql -h YOUR_MYSQL_HOST -u debate_user -p debate_arena

# 检查各表记录数
SELECT 'competitors' as tbl, COUNT(*) as cnt FROM competitors
UNION ALL
SELECT 'debate_topics', COUNT(*) FROM debate_topics
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'matches', COUNT(*) FROM matches;
```

### 4.2 启动应用测试

```bash
# 重启后端服务
uvicorn backend.main:app --reload --port 8000

# 测试 API
curl http://localhost:8000/api/tournament/leaderboard
```

## 五、回滚方案

如果迁移出现问题，可以快速回滚到 SQLite：

```bash
# 1. 修改 .env，恢复 SQLite 配置
DATABASE_URL=sqlite:///./debate_arena.db

# 2. 重启服务
uvicorn backend.main:app --reload --port 8000
```

## 六、常见问题

### Q1: 连接被拒绝 (Connection refused)

```bash
# 检查 MySQL 是否运行
sudo systemctl status mysql

# 检查端口监听
netstat -tlnp | grep 3306

# 检查防火墙
sudo ufw status
```

### Q2: 权限不足 (Access denied)

```sql
-- 重新授权
GRANT ALL PRIVILEGES ON debate_arena.* TO 'debate_user'@'%';
FLUSH PRIVILEGES;
```

### Q3: 字符集问题（乱码）

确保连接字符串包含 `?charset=utf8mb4`：

```env
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
```

### Q4: 连接超时

在 MySQL 配置中增加超时时间：

```ini
[mysqld]
wait_timeout = 28800
interactive_timeout = 28800
```

## 七、性能优化建议

### 7.1 连接池配置

代码中已配置连接池，可根据需要调整：

```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,        # 连接池大小
    max_overflow=30,     # 最大溢出连接
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600    # 连接回收时间（秒）
)
```

### 7.2 添加索引

```sql
-- 为常用查询添加索引
CREATE INDEX idx_matches_user_id ON matches(user_id);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_created_at ON matches(created_at);
CREATE INDEX idx_competitors_elo ON competitors(elo_rating);
```

## 八、Docker 环境配置

如果使用 Docker，修改 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://debate_user:your_password@mysql:3306/debate_arena?charset=utf8mb4
    depends_on:
      - mysql

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: debate_arena
      MYSQL_USER: debate_user
      MYSQL_PASSWORD: your_password
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci

volumes:
  mysql_data:
```

---

**迁移完成后，记得删除敏感的迁移数据文件：**

```bash
rm -rf migration_data/
```
