# AI 学习助手 PRD v2.0

> 状态：需求确认完毕，待技术方案 | 2026-06-26

---

## 1. 产品概要

| 维度 | 说明 |
|---|---|
| **产品名** | AI 学习助手（FlashFlow） |
| **一句话** | 像多邻国一样复习闪卡，用游戏化积分驱动持续学习 |
| **目标用户** | C 端个人学习者（考证/考研/技术自学） |
| **对标产品** | Anki（算法复习） + 多邻国（游戏化反馈） |
| **当前阶段** | 作品集项目，展示 AI + 全栈 + 产品能力 |
| **技术栈** | GitHub Pages（前端） + FastAPI Python（后端） + Supabase（数据） |

> **核心设计决策**：闪卡生成不在产品内做。用户写完压缩笔记后，由 **Claude Code 一次性完成挖空+入库**。产品只负责复习、测验、积分、统计。

---

## 2. 用户故事

### 2.1 核心闭环

```
写压缩笔记 → Claude Code 挖空直入 Supabase → 每日复习闪卡 → 答对积分 → 兑换奖励 → 坚持学习
         ↑__ 产品外（一次性）__↑            ↑_______________ 产品内 _______________↑
```

### 2.2 典型场景

1. **小王学 Python**：写完一篇压缩笔记，在飞书告诉 Claude Code"入库"，Claude Code 自动识别 `⭐` 标记的关键词挖空，生成闪卡 + 题目直接写入 Supabase。每天打开页面，点"今日学习"，像刷多邻国一样刷 10 张卡。连续答对 10 题积分翻 1.2 倍，攒够 500 分解锁"Python 大师"徽章。
2. **小王复习一周后**：在统计页看到 GitHub 风格的知识点热力图，发现 Pandas 相关知识点一片红（薄弱），点击进入针对性复习。

---

## 3. 功能清单

### 3.0 产品外工作流：Claude Code 闪卡入库

> 写笔记 → Claude Code 挖空 → 直写 Supabase。一次性完成，与产品解耦。

| 步骤 | 执行者 | 说明 |
|---|---|---|
| 写压缩笔记 | 用户 | 按模板写 Markdown（⭐ 标记核心术语） |
| 一句话入库 | 用户 → Claude Code | 飞书/终端说"入库 <笔记路径>" |
| 解析 + 挖空 | Claude Code | 识别 ⭐/加粗/表格/代码，挖掉术语，生成干扰项 |
| 写入 Supabase | Claude Code | 直写 `flashcard_bank` + `quiz_questions` + `mastery_scores` |
| 刷新页面即可复习 | 用户 | 打开 GitHub Pages，新卡已在库中 |

### 3.1 V1.0 MVP（产品内功能）

| 模块 | 功能 | 优先级 | 说明 |
|---|---|---|---|
| **闪卡复习** | 三种入口模式 | P0 | 今日学习（遗忘曲线）/ 继续章节 / 本周复习 |
| | 挖空闪卡 | P0 | 正面：挖空题干 + 4 个选项；反面：完整原文 + 解释 |
| | 多邻国式反馈 | P0 | 答对 🎉 动画 + 连击计数；答错 💡 正确答案 + 纠错提示 |
| **测验** | Claude 批改 | P0 | 保留现有批改链路（/internal/pending → /internal/grade） |
| **积分系统** | +1 积分/题 | P0 | 答对即得分 |
| | 连击加成 | P0 | 连续答对 10 题，倍率 +0.2（1.0 → 1.2 → 1.4…封顶 3.0） |
| | 断连重置 | P0 | 答错重置连击数和倍率 |
| **奖品库** | 虚拟徽章 | P1 | "连续 7 天"、"Python 大师"、"百题斩" 等 |
| | 功能解锁 | P1 | 解锁自定义复习策略 / 夜间模式等 |
| | 实物标记 | P1 | "你已获得一杯咖啡 ☕"（虚拟标记，非实际兑换） |
| **统计面板** | 基础统计 | P0 | 总复习/总答题/正确率/薄弱 Top3（保留现有） |
| | 积分卡片 | P0 | 总分 / 当前倍率 / 连击数 |
| | 知识热力图 | P1 | GitHub 贡献图风格，知识点 × 日期矩阵 |
| | 答题记录 | P1 | 按日期展开的答题历史 + 对错详情 |
| **单用户** | 无需登录 | P0 | GitHub Pages 部署，单人使用 |

### 3.2 V2.0 规划（商业化预备）

| 功能 | 说明 |
|---|---|
| 多用户 + OAuth 登录 | GitHub/Google/微信登录 |
| 多题库管理 | 用户可创建/切换多个题库 |
| 协作题库 | 分享题库链接，组队学习 |
| 付费订阅 | 高级 AI 出题 / 无限题库 / 去广告 |
| 移动端 PWA | 离线刷题，推送提醒 |

---

## 4. 核心技术方案

### 4.1 闪卡数据结构

> 由 Claude Code 入库时生成，产品侧只读不写。

```json
{
  "id": "uuid",
  "phase": "Python",
  "chapter": "Pandas",
  "title": "五大容器",
  "front": "⭐ ___(1)___ ▸ 5种存多个元素的数据类型：___(2)___, list, tuple, set, dict",
  "back": "⭐ **五大容器** ▸ 5种存多个元素的数据类型：str, list, tuple, set, dict",
  "blanks": [
    {"pos": 1, "answer": "五大容器", "options": ["五大容器", "四大金刚", "六脉神剑", "三大件"]},
    {"pos": 2, "answer": "str",      "options": ["str", "int", "float", "bool"]}
  ],
  "tags": ["python", "容器"]
}
```

**flashcard_bank 表字段映射**：
- `title` → 知识点名（如"五大容器"）
- `content` → JSON 字符串，存 `{front, back, blanks}`
- 前端渲染时 JSON.parse 后按 blanks 位置插入选项

### 4.2 Claude Code 入库规范（产品外）

```
用户说：入库 04-学习大纲/每日学习/Phase X-XXX/压缩笔记/xxx.md

Claude Code 执行：
1. Read 笔记 → 解析 Markdown
2. 识别挖空目标：⭐**术语**、表格关键格、加粗术语、代码参数
3. 每个知识点生成 1 张闪卡 + 1~2 道题
4. 干扰项从当前笔记同一 phase 的术语池中随机抽取
5. 直写 flashcard_bank + quiz_questions + mastery_scores(score=50)
6. 回复："已入库：X 张闪卡，Y 道题"
```

### 4.3 遗忘曲线算法（保留现有）

```python
FORGETTING_CURVE = {1: 1.0, 3: 1.5, 7: 2.0, 14: 2.5, 30: 3.0}
# 优先级 = 遗忘权重 × (1 - 掌握度/100)
priority = forget_weight * (1 - score / 100)
```

### 4.4 积分与连击算法

```python
streak = 0           # 连续答对数
multiplier = 1.0     # 积分倍率

def on_correct():
    streak += 1
    if streak > 0 and streak % 10 == 0:
        multiplier = min(3.0, multiplier + 0.2)
    return 1 * multiplier  # 基础 1 分 × 倍率

def on_wrong():
    streak = 0
    multiplier = 1.0
    return 0
```

### 4.5 知识热力图

- **X 轴**：日期（过去 90 天）
- **Y 轴**：知识点
- **颜色深度**：当天该知识点的答题正确率（绿=高，黄=中，红=低，灰=无数据）
- **实现**：前端用 Canvas 或 SVG 绘制，后端 `/stats/heatmap` 接口返回矩阵

---

## 5. 前端交互规范（多邻国风格）

| 场景 | 交互 |
|---|---|
| 闪卡加载 | 卡片从右侧滑入 |
| 选择答案 | 选项按下缩放 0.95，松开弹回 |
| 答对 | 绿色脉冲动画 + "🎉 正确！" + 连击计数器 +1 弹出 |
| 答错 | 红色抖动 + "💡 正确答案：XXX" + 底部弹出解释 |
| 连击 5/10/20 | 全屏特效 + 音效（可选静音） |
| 升级 | 进度条填满 → 等级徽章弹出 |
| 连续 7 天 | 弹出成就卡片 |

---

## 6. 数据模型（保留现有 + 新增）

### 6.1 保留表

- `flashcard_bank` — 闪卡库（content 字段存 JSON `{front, back, blanks}`，由 Claude Code 写入）
- `mastery_scores` — 掌握度
- `quiz_questions` — 题库
- `quiz_sessions` — 测验回合
- `quiz_attempts` — 答题记录
- `review_logs` — 复习日志

### 6.2 新增表

```sql
-- 7. 用户积分
CREATE TABLE user_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    total_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    max_streak INT DEFAULT 0,
    multiplier DECIMAL(3,1) DEFAULT 1.0
);

-- 8. 积分日志
CREATE TABLE point_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    points_earned INT NOT NULL,
    multiplier DECIMAL(3,1) DEFAULT 1.0,
    reason TEXT,  -- 'quiz_correct', 'streak_bonus', 'achievement'
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 9. 奖品库（预置数据）
CREATE TABLE prize_library (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT CHECK (type IN ('badge', 'unlock', 'physical')),
    description TEXT,
    icon TEXT,
    cost INT,
    unlock_condition JSONB  -- { streak: 7, points: 500 }
);

-- 10. 用户奖品
CREATE TABLE user_prizes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prize_id UUID REFERENCES prize_library(id),
    earned_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 7. 接口规划

### 7.1 保留接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/modes` | 入口三模式 |
| GET | `/flashcards` | 闪卡列表 |
| GET | `/quiz` | 测验题目 |
| POST | `/quiz/submit` | 提交答案 |
| POST | `/review` | 闪卡复习反馈 |
| GET | `/stats` | 统计面板 |
| GET | `/internal/pending` | Claude 待批改 |
| POST | `/internal/grade` | Claude 批改回写 |

### 7.2 新增接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/points` | 当前积分、连击、倍率 |
| GET | `/points/history` | 积分变动日志 |
| GET | `/prizes` | 奖品库列表 |
| POST | `/prizes/redeem` | 兑换奖品 `{prize_id}` |
| GET | `/prizes/mine` | 我已获得的奖品 |
| GET | `/stats/heatmap` | 知识热力图矩阵数据 |
| GET | `/stats/history` | 答题记录详情（分页） |

---

## 8. 页面结构

```
入口弹窗（/）
├── 📅 今日学习
├── 📑 继续章节
├── 📆 本周复习
└── 🔧 自定义筛选

主界面（Tab 切换）
├── 📇 闪卡 Tab
│   ├── 闪卡正面（挖空 + 4 选项）
│   ├── 闪卡反面（完整原文 + 解释）
│   ├── 👍 掌握了 / 👎 没掌握
│   └── 答对/答错动画反馈
├── 📝 测验 Tab
│   ├── 题目列表
│   ├── 进度条
│   └── 提交 Claude 批改
├── 📊 统计 Tab
│   ├── 积分卡片（总分 / 当前倍率 / 连击数）
│   ├── 知识热力图
│   ├── 薄弱 Top 3
│   └── 最近测验记录
└── 🏆 奖品 Tab（新增）
    ├── 徽章墙
    ├── 可兑换列表
    └── 已获得列表
```

---

## 9. 非功能需求

| 维度 | 要求 |
|---|---|
| **性能** | 闪卡加载 < 500ms，动画 60fps |
| **可用性** | 移动优先（max-width 480px），触控友好 |
| **数据安全** | 公开演示用 Supabase anon key，敏感数据走 service key |
| **可部署** | 前端 GitHub Pages，后端 Render 免费层 |
| **无障碍** | 支持屏幕阅读器，关键操作有 aria-label |

---

## 10. 里程碑

| 阶段 | 内容 | 预估 |
|---|---|---|
| **M1 - 闪卡数据结构升级** | flashcard_bank.content → JSON 格式（front/back/blanks），前端适配渲染 | 1-2 天 |
| **M2 - 多邻国反馈** | 动画系统 + 连击显示 + 答对/答错特效 | 2-3 天 |
| **M3 - 积分系统** | 积分累加 + 连击倍率 + 积分日志 + `/points` API | 1-2 天 |
| **M4 - 奖品库** | 预置奖品 + 兑换逻辑 + `/prizes` API + 奖品 Tab UI | 1-2 天 |
| **M5 - 统计升级** | 热力图 + 答题记录详情 + `/stats/heatmap` `/stats/history` API | 2-3 天 |
| **M6 - 集成联调** | GitHub Pages + Supabase 对接 + 种子数据 | 1-2 天 |
| **M7 - Claude Code 入库脚本** | 写好笔记→Claude 自动挖空→直写 Supabase 的工作流 | 1 天 |

---

## 11. 风险与对策

| 风险 | 对策 |
|---|---|
| Claude Code 入库时挖空质量不稳定 | 同批次笔记术语做干扰池；用户可手动 `{{标记}}` 指定挖空位置 |
| 动画性能在低端机上卡顿 | 用 CSS transform/opacity 做动画，避免重排 |
| 单用户无登录体系，数据无法跨设备 | V1 接受此限制；V2 加 OAuth |
| Supabase 免费层配额限制 | 控制数据量，加缓存减少请求 |
| Claude 批改有延迟，用户体验割裂 | 闪卡本地即时反馈 + 测验走 Claude 深度批改双通道 |

---

## 附录 A：Claude Code 入库工作流规范

### 触发命令

```
入库 <压缩笔记路径>
```

### 压缩笔记模板（用户写笔记时遵循）

```markdown
# 标题（作为 phase）

## 章节名（作为 chapter）

⭐ **核心术语** ▸ 定义说明（⭐ 后的 **粗体** 优先挖空）

- **术语**：定义（独立行术语-定义对，挖术语）

| 列1 | 列2 | 列3 |（表格关键格作为备选挖空）

代码块（关键参数/方法名作为备选挖空）
```

### Claude Code 入库执行步骤

1. Read 笔记文件，解析标题/phase/chapter
2. 按优先级提取挖空目标：
   - P1: `⭐` 后紧跟的 `**粗体**`
   - P2: 独立行 `- **术语**：`
   - P3: 表格中关键列的值
   - P4: 代码块中的关键参数/方法名
3. 每个知识点生成 1 条 flashcard_bank 记录，content 为 JSON `{front, back, blanks}`
4. 从同一 phase 的术语池中随机抽取 3 个同类术语作为干扰项
5. 每个知识点生成 1~2 条 quiz_questions 记录（判断/单选）
6. 写入 mastery_scores（score=50）
7. 回复："✅ 已入库：X 张闪卡，Y 道题"

---

## 附录 B：奖品库初始设计

| 名称 | 类型 | 获取条件 | 图标 |
|---|---|---|---|
| 初出茅庐 | badge | 完成第一次复习 | 🌱 |
| 连续 7 天 | badge | 连续 7 天登录复习 | 🔥 |
| 百题斩 | badge | 累计答对 100 题 | ⚔️ |
| Python 大师 | badge | Python 知识点全部 ≥ 80 分 | 🐍 |
| 解锁自定义复习 | unlock | 500 积分 | 🔓 |
| 解锁夜间模式 | unlock | 200 积分 | 🌙 |
| 一杯咖啡 | physical | 1000 积分（虚拟标记） | ☕ |
| 一本好书 | physical | 3000 积分（虚拟标记） | 📚 |
