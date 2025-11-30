# LLM Debate Arena - Frontend

大模型辩论竞技场前端应用，基于 React + TypeScript + Vite 构建的现代化单页应用。

## 📁 项目结构

```
frontend/
├── index.html              # HTML 入口
├── favicon.svg             # 网站图标
├── package.json            # 项目配置和依赖
├── tsconfig.json           # TypeScript 配置
├── vite.config.ts          # Vite 构建配置
├── tailwind.config.js      # Tailwind CSS 配置
├── postcss.config.js       # PostCSS 配置
└── src/
    ├── main.tsx            # 应用入口
    ├── App.tsx             # 根组件（路由配置）
    ├── index.css           # 全局样式
    ├── components/         # 可复用组件
    │   ├── DebateViewer.tsx    # 辩论实时展示组件
    │   └── Toast.tsx           # 消息提示组件
    ├── pages/              # 页面组件
    │   ├── Arena.tsx           # 辩论竞技场主页
    │   ├── Leaderboard.tsx     # 排行榜页面
    │   ├── MatchHistory.tsx    # 历史记录页面
    │   ├── Login.tsx           # 登录页面
    │   └── Register.tsx        # 注册页面
    └── hooks/              # 自定义 Hooks
        ├── useSSE.ts           # SSE 流式通信 Hook
        └── useToast.ts         # Toast 提示 Hook
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

应用将在 `http://localhost:5173` 启动（默认端口）。

### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 4. 预览生产构建

```bash
npm run preview
```

## 🎨 技术栈

### 核心框架

- **React 18.2**: 用户界面库
- **TypeScript 5.2**: 类型安全的 JavaScript
- **Vite 5.0**: 下一代前端构建工具

### UI 和样式

- **Tailwind CSS 3.3**: 实用优先的 CSS 框架
- **Framer Motion 10.16**: 强大的动画库
- **Lucide React 0.294**: 开源图标库

### 路由

- **React Router v6.20**: 声明式路由

### 状态管理

- **Zustand 4.4**: 轻量级状态管理（未大量使用，主要用 React 本地状态）

### 数据可视化

- **Recharts 2.10**: 图表库（用于 ELO 评分曲线等）

### Markdown 渲染

- **React Markdown 9.0**: 支持 Markdown 格式的辩论内容渲染

### 工具库

- **clsx 2.0**: 条件类名组合
- **tailwind-merge 2.1**: Tailwind 类名智能合并

## 🎯 核心功能

### 1. 辩论竞技场 (`Arena.tsx`)

主页面，包含侧边栏和辩论区域：

- **辩论配置**：
  - 选择正方/反方模型
  - 设置辩论主题
  - 配置性格类型（理性、激进、温和、幽默、学术）
  - 选择回合数（1-5 回合）
  - 选择裁判（至少 2 个）
  - 启用工具（Python、搜索、计算器）
  
- **实时辩论观看**：
  - SSE（Server-Sent Events）流式接收辩论内容
  - 实时显示双方发言
  - 工具调用展示（Python 代码执行、搜索结果等）
  - 裁判评分进度展示
  
- **历史记录侧边栏**：
  - 显示最近的比赛记录
  - 点击可回放历史比赛
  - 侧边栏可折叠

### 2. 排行榜 (`Leaderboard.tsx`)

ELO 评分排名系统：

- **排行榜展示**：
  - 按 ELO 评分排序
  - 显示胜率、对战场次
  - 胜/负/平统计
  
- **历史记录展开**：
  - 点击模型可展开该模型的历史对战
  - 显示对手、结果、时间
  - 胜利/失败/平局用不同颜色标识

### 3. 历史记录 (`MatchHistory.tsx`)

全局比赛历史查看：

- 所有用户的比赛记录
- 按时间倒序排列
- 显示辩论主题、对战双方、结果
- 点击可回放完整辩论过程

### 4. 辩论查看器 (`DebateViewer.tsx`)

核心展示组件：

- **流式内容渲染**：
  - 处理 SSE 消息流
  - 实时更新发言内容（`turn_delta`）
  - 支持 Markdown 格式
  
- **工具调用展示**：
  - Python 代码高亮显示
  - 工具执行结果展示
  - Loading 状态提示
  
- **裁判评分**：
  - 多裁判评分展示
  - 各维度评分（论点、逻辑、证据等）
  - 最终胜负判定
  
- **ELO 更新**：
  - 显示比赛后的 ELO 变化
  - 箭头指示升降

- **卡片折叠功能**：
  - 点击回合标题可折叠/展开
  - 优化长辩论的阅读体验

### 5. 用户系统

- **登录** (`Login.tsx`)：支持用户登录
- **注册** (`Register.tsx`)：新用户注册
- **用户状态**：显示登录用户信息

## 🔧 开发指南

### SSE 通信 (`useSSE.ts`)

使用 Server-Sent Events 实现实时通信：

```tsx
import { useSSE } from '../hooks/useSSE'

const { messages, isConnected, currentMatchId, connect, clearMessages } = useSSE()

// 开始新比赛
const startMatch = async () => {
  const config = {
    topic: '辩题',
    proponent_model: 'gpt-4o',
    opponent_model: 'claude-3.5-sonnet',
    rounds: 3,
  }
  
  const isDev = window.location.hostname === 'localhost'
  const url = isDev 
    ? 'http://localhost:8000/api/debate/start_stream'
    : '/api/debate/start_stream'
    
  connect(url, config)
}
```

### Toast 提示 (`useToast.ts`)

使用自定义 Toast Hook：

```tsx
import { useToast } from '../hooks/useToast'

const { toast, toasts, removeToast } = useToast()

// 显示不同类型的提示
toast.success('操作成功！')
toast.error('操作失败！')
toast.warning('警告信息')
toast.info('提示信息')
```

### API 调用模式

根据环境自动切换 API 地址：

```tsx
const isDev = window.location.hostname === 'localhost'
const apiUrl = isDev
  ? 'http://localhost:8000/api/endpoint'
  : '/api/endpoint'

const response = await fetch(apiUrl)
const data = await response.json()
```

### 组件开发规范

使用函数式组件和 Hooks：

```tsx
import { useState, useEffect } from 'react'

interface ComponentProps {
  title: string
  count: number
}

export default function MyComponent({ title, count }: ComponentProps) {
  const [state, setState] = useState<string>('')
  
  useEffect(() => {
    // 副作用逻辑
  }, [])
  
  return <div>{title}: {count}</div>
}
```

### 类型定义

为所有数据结构定义 TypeScript 接口：

```tsx
interface Match {
  match_id: string
  topic: string
  proponent_model_id: string
  opponent_model_id: string
  status: string
  created_at: string
  finished_at: string | null
}

interface Competitor {
  model_id: string
  display_name: string
  provider: string
  elo_rating: number
  matches_played: number
  wins: number
  losses: number
  draws: number
  win_rate: number
}
```

## 🎨 样式规范

### Tailwind CSS 使用

项目完全基于 Tailwind CSS 的 utility-first 设计：

```tsx
<div className="min-h-screen bg-gray-50">
  <div className="flex items-center justify-between px-4 py-2">
    <span className="text-lg font-semibold text-gray-900">标题</span>
  </div>
</div>
```

### 自定义颜色主题

在 `tailwind.config.js` 中定义了自定义颜色：

```javascript
colors: {
  proponent: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
  },
  opponent: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
  },
}
```

使用示例：

```tsx
{/* 正方 - 蓝色系 */}
<div className="bg-proponent-50 text-proponent-600">
  正方发言
</div>

{/* 反方 - 红色系 */}
<div className="bg-opponent-50 text-opponent-600">
  反方发言
</div>
```

### 常用颜色约定

- **正方（Proponent）**：蓝色系（Blue）
- **反方（Opponent）**：红色系（Red）
- **胜利**：绿色（Green）- `text-green-600`
- **失败**：红色（Red）- `text-red-600`
- **平局**：黄色（Yellow）- `text-yellow-600`
- **背景**：灰色系（Gray）- `bg-gray-50`, `bg-gray-100`

### 响应式设计

使用 Tailwind 断点：

```tsx
{/* 移动端堆叠，桌面端并排 */}
<div className="flex flex-col lg:flex-row gap-4">
  <div className="w-full lg:w-1/2">左侧</div>
  <div className="w-full lg:w-1/2">右侧</div>
</div>

{/* 网格布局 */}
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id} />)}
</div>
```

### 动画效果

使用 Framer Motion：

```tsx
import { motion, AnimatePresence } from 'framer-motion'

<AnimatePresence>
  {isVisible && (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
    >
      内容
    </motion.div>
  )}
</AnimatePresence>
```

## 📦 构建优化

### 性能优化

- 使用 `React.memo` 避免不必要的重渲染
- 大列表使用分页或虚拟滚动
- 图片懒加载
- 代码分割（React Router 自动支持）

### 环境变量

Vite 环境变量配置：

```bash
# .env
VITE_API_URL=http://localhost:8000
```

在代码中使用：

```tsx
const API_URL = import.meta.env.VITE_API_URL
```

## 🧪 调试

### 开发模式

开发模式自动判断环境：

```tsx
const isDev = window.location.hostname === 'localhost'
```

- **本地开发**：使用 `http://localhost:8000`
- **生产环境**：使用相对路径 `/api`

### 日志输出

SSE 和重要操作都有详细的控制台日志：

```
📡 正在连接 SSE: http://localhost:8000/api/debate/start_stream
✅ SSE 连接成功
📩 收到 SSE 消息: turn_delta
🏁 SSE 流结束
```

## 📱 浏览器支持

- Chrome / Edge (最新)
- Firefox (最新)
- Safari (最新)

## 🛠️ 开发工具推荐

- **VS Code**: 推荐编辑器
- **React Developer Tools**: 浏览器扩展
- **Tailwind CSS IntelliSense**: VS Code 扩展（强烈推荐）
- **TypeScript**: 内置类型检查

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 代码规范

- 使用 TypeScript 严格模式
- 所有接口和类型都要定义
- 组件使用函数式声明
- 使用 Tailwind CSS，避免自定义 CSS
- 遵循 ESLint 规则

### 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
perf: 性能优化
test: 测试相关
chore: 构建/工具链更新
```
