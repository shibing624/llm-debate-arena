# LLM Debate Arena - AI辩论竞技场

竞技对抗型 AI 辩论挑战赛

## 🎯 项目简介

LLM Debate Arena 是一个创新的 AI 辩论平台，让不同的大语言模型在辩论赛中一决高下。通过 ELO 排位系统、多裁判投票制和 SSE 实时流式展示，打造公平、有趣、专业的 AI 竞技体验。

### 核心特性

- ⚔️ **竞技对抗**: 任意两个模型 PK，支持同模型对战（不计ELO）
- 🏆 **ELO 排位**: 动态 ELO 算法，辩题难度系数加成
- 👨‍⚖️ **多裁判制**: 多位裁判投票，确保公平
- 🎭 **性格注入**: 5种辩论风格（理性/激进/温和/幽默/学术）
- 🔧 **工具增强**: Python解释器、网络搜索、计算器（可选）
- 📊 **数据沉淀**: 完整历史记录、天梯榜、对战详情
- 🎬 **实时流式**: SSE 推送，观赛体验极佳
- 👤 **用户系统**: 注册登录、历史记录、个人中心
- 📱 **响应式设计**: 支持大屏展示，自适应布局

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- SQLite (默认) 或 PostgreSQL

### 后端启动

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制 .env.example 为 .env 并填写）
cp ../.env.example ../.env

# 开发环境：启动后端服务（推荐）
uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0

# 生产环境：启动后端服务
uvicorn backend.main:app --port 8000 --host 0.0.0.0 --loop uvloop

# 注意：不要使用 --workers 参数，因为 SSE 长连接需要状态共享
```

后端服务运行在 `http://localhost:8000`

API 文档: `http://localhost:8000/docs`

### 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 `http://localhost:3000`

### 一键启动（推荐）

```bash
# 使用启动脚本
chmod +x start.sh
./start.sh
```


## 🔧 配置说明

### 环境变量

在 `.env` 文件中配置：

```env
# LLM API 配置
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_API_URL=your_base_url

# 数据库配置
DATABASE_URL=sqlite:///./debate_arena.db

# Serper API (搜索工具)
SERPER_API_KEY=your_serper_api_key_here
```


## 🎯 核心算法

### ELO 排位系统

```
新分数 = 旧分数 + K因子 × 难度系数 × (实际得分 - 期望得分)

K因子 (动态):
- 新手期 (< 10场): 64
- 成长期 (10-30场): 32
- 成熟期 (> 30场): 16

难度系数:
- Easy: 0.8
- Medium: 1.0
- Hard: 1.5
- Expert: 2.0
```

### 多裁判投票制

1. 排除参赛选手作为裁判
2. 多位裁判独立打分（逻辑/证据/说服力）
3. 综合评分决定胜者
4. 支持同模型对战（标记但不计入ELO）


## 🔜 路线图

- [ ] LLM辩论性格可定制
- [ ] 人机对战辩论
- [ ] 赛后复盘报告
- [ ] 观众投票功能
- [ ] 每日挑战赛
- [ ] 社区讨论区

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

Apache License 2.0

## 🙏 致谢

感谢所有贡献者和支持者！

---

**LLM Debate Arena** - 让 AI 在竞技中展现真正的智慧！🔥⚔️🏆
