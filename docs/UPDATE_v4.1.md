# LLM Debate Arena v4.1 更新日志

## 更新时间
2025-11-30

## 主要更新内容

### 1. ✅ 流式输出优化
**前端适配流式输出**
- ✅ `DebateViewer` 组件已支持实时显示流式内容增量
- ✅ 辩论卡片中的内容实时更新，显示流式输出效果
- ✅ 后端 `query_model_stream` 已支持内容增量输出（流式）
- ✅ 前端通过 `turn_delta` 事件接收并实时渲染增量内容

**技术实现：**
- 前端监听 `turn_delta` 事件，实时累积内容到 `streamingTurns` Map
- 使用 `motion.div` 实现平滑动画效果
- 流式光标（blinking cursor）提示正在输入

### 2. ✅ 历史记录侧边栏
**类似 ChatGPT 的主页布局**
- ✅ 左侧可展开/隐藏的历史记录侧边栏
- ✅ 点击遮罩层或 X 按钮关闭侧边栏
- ✅ 使用 Framer Motion 实现平滑滑出动画
- ✅ 历史记录列表显示辩题、模型、状态、时间
- ✅ 自动刷新历史记录（比赛结束后）

**UI 特点：**
- 侧边栏宽度：320px
- 展开/收起按钮：左上角 ChevronLeft/ChevronRight 图标
- 历史卡片：灰色背景，hover 时变深
- 比赛状态标签：绿色（完成）、灰色（其他）

### 3. ✅ 支持相同模型对战
**允许正反方选择相同模型**
- ✅ 去除前端 "正反方不能选择相同模型" 的限制
- ✅ 后端识别同模型对战，自动跳过 ELO 更新
- ✅ 日志标注：`⚠️ 同模型对战模式: xxx (不计ELO)`
- ✅ 裁判判决和比赛结果正常进行

**后端修改：**
```python
# backend/main.py
same_model_battle = request.proponent_model == request.opponent_model
if same_model_battle:
    logger.info(f"⚠️ 同模型对战模式: {request.proponent_model} (不计ELO)")

# backend/tournament.py
if not same_model_battle:
    elo_changes = await update_elo_ratings(match)
else:
    logger.info("⚠️ 同模型对战，跳过 ELO 更新")
```

### 4. ✅ 性格可选
**默认无特定性格**
- ✅ 添加 "默认 (无特定性格)" 选项
- ✅ 前端默认选中空字符串 `''`
- ✅ 后端处理空字符串或 None，自动转换为 `PersonalityType.RATIONAL`
- ✅ API 兼容性：空字符串、None、枚举值均可

**性格选项：**
- 默认 (无特定性格)
- 🧠 理性分析型
- ⚔️ 激进攻击型
- 🤝 温和外交型
- 😄 幽默讽刺型
- 📚 学术严谨型

**后端处理逻辑：**
```python
prop_personality_enum = PersonalityType.RATIONAL
if prop_personality and prop_personality in [e.value for e in PersonalityType]:
    prop_personality_enum = PersonalityType(prop_personality)
```

### 5. ✅ 主页布局优化
**极简紧凑风格**

#### 整体布局：
- ✅ 去除顶部导航栏（App.tsx）
- ✅ 左侧历史记录侧边栏（可展开/隐藏）
- ✅ 顶部简洁工具栏（标题 + 侧边栏切换按钮）
- ✅ 中间主内容区（配置 + 辩论展示）

#### 配置区优化：
- ✅ 单行模型选择（2列网格）
- ✅ 单行性格选择（可选）
- ✅ 高级设置合并为一行：轮数 | 裁判 | 工具
- ✅ 辩题支持多行输入（3行 textarea）
- ✅ 开始对决按钮紧挨辩题输入框
- ✅ 所有边距、间距缩小（极简风格）

#### 视觉风格：
- 字体：减小标签字体为 `text-xs`
- 边框：统一使用 `border-gray-300`
- 圆角：统一 `rounded-lg`
- 焦点：统一 `focus:ring-1 focus:ring-gray-400`
- 按钮：黑色主题 `bg-gray-900 hover:bg-gray-800`

#### 前后对比：
**之前：**
```
- 顶部导航栏占 60px
- 配置区分散在多个板块
- 辩题单行输入
- 高级设置占 3-4 行
- 开始按钮在最下方
```

**现在：**
```
- 无顶部导航栏，节省空间
- 配置区集中在一个卡片内
- 辩题 3 行 textarea
- 高级设置 1 行搞定
- 开始按钮紧挨辩题
```

---

## 技术细节

### 前端改动文件
1. **frontend/src/pages/Arena.tsx**（完全重写）
   - 添加历史记录侧边栏
   - 极简化配置区布局
   - 去除相同模型限制
   - 性格默认为空

2. **frontend/src/App.tsx**
   - 去除顶部导航栏

3. **frontend/src/components/DebateViewer.tsx**
   - 优化 `turn_delta` 事件处理
   - 添加注释说明流式输出

### 后端改动文件
1. **backend/main.py**
   - 去除相同模型检查
   - 添加 `same_model_battle` 标志
   - 传递到 `run_tournament_match`

2. **backend/tournament.py**
   - 添加 `same_model_battle` 参数
   - 条件性跳过 ELO 更新
   - 性格参数改为 `Optional[str]`
   - 转换空字符串为默认枚举值

3. **backend/models.py**
   - `MatchRequest.proponent_personality` 改为 `Optional[str]`
   - `MatchRequest.opponent_personality` 改为 `Optional[str]`

---

## 使用示例

### 相同模型对战
```bash
# 前端选择
正方：GPT-4o
反方：GPT-4o  # ✅ 允许相同

# 后端日志
⚠️ 同模型对战模式: gpt-4o (不计ELO)
⚠️ 同模型对战，跳过 ELO 更新
```

### 默认性格
```bash
# 前端选择
正方性格：默认 (无特定性格)  # 传递 ''
反方性格：🧠 理性分析型      # 传递 'rational'

# 后端处理
prop_personality_enum = PersonalityType.RATIONAL  # '' -> RATIONAL
opp_personality_enum = PersonalityType.RATIONAL   # 'rational' -> RATIONAL
```

### 历史记录侧边栏
```bash
# 点击左上角按钮展开侧边栏
1. 遮罩层显示，点击关闭
2. 侧边栏从左侧滑出
3. 显示最近 20 场比赛
4. 点击比赛卡片查看详情（功能待完善）
```

---

## 待优化项

1. **历史记录详情查看**
   - 当前点击历史卡片会弹出 "功能正在完善中"
   - 需要实现将历史比赛数据加载到 DebateViewer
   - 建议方案：使用全局状态管理（Zustand）或路由参数

2. **辩题建议**
   - 可以添加常用辩题快捷按钮（已有代码注释掉）
   - 或者接入 LLM 自动生成辩题

3. **性能优化**
   - 历史记录可以实现分页加载
   - 流式输出可以考虑防抖优化

---

## 测试建议

### 测试场景
1. **流式输出测试**
   - 启动比赛，观察辩论卡片实时更新
   - 检查流式光标是否显示
   - 验证工具调用结果是否正确显示

2. **相同模型对战测试**
   - 选择相同模型开始比赛
   - 检查后端日志是否标注 "同模型对战"
   - 验证比赛结果区不显示 ELO 变化（或显示"不计ELO"）

3. **性格可选测试**
   - 选择"默认"性格开始比赛
   - 检查后端日志是否使用 RATIONAL
   - 验证辩论风格是否正常

4. **侧边栏测试**
   - 点击展开/收起按钮
   - 检查动画是否流畅
   - 验证历史记录是否正确加载

---

## 兼容性

- ✅ 向后兼容：旧的 API 请求仍然有效
- ✅ 数据库无需迁移
- ✅ 前端无需清除缓存

---

## 总结

本次更新主要聚焦于**用户体验优化**和**功能灵活性提升**：

1. **流式输出** - 让辩论过程更加生动实时
2. **侧边栏** - 类似 ChatGPT 的现代化布局
3. **相同模型对战** - 支持更多实验场景
4. **性格可选** - 降低使用门槛
5. **极简布局** - 信息密度更高，操作更便捷

所有功能均已实现并通过 lint 检查 ✅
