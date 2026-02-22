# Personal Agent — Claude Code Web Wrapper

基于 FastAPI + WebSocket 的 Web IM Bot，在浏览器里与 Claude Code CLI 交互。

## 功能

- 多 Session 并发聊天
- 每个 Session 独立 git worktree（代码隔离）
- Claude stream-json 实时流式输出
- 工具调用过滤展示

## 从零开始配置（本地环境）

### 前置条件

| 依赖 | 最低版本 | 说明 |
|------|---------|------|
| Python | 3.11+ | 推荐 3.11 或 3.12 |
| Git | 2.x | worktree 功能依赖 git |
| Claude Code CLI | 最新 | `npm install -g @anthropic-ai/claude-code` |
| Node.js | 18+ | Claude Code CLI 的运行时 |

### 第 1 步：确认 Claude Code CLI 可用

```bash
claude --version
# 应输出类似: 2.x.x (Claude Code)
```

如果没有安装：

```bash
npm install -g @anthropic-ai/claude-code
```

安装后需要登录：

```bash
claude
# 按提示完成 OAuth 登录
```

### 第 2 步：克隆项目

```bash
git clone <你的仓库地址>
cd juju-agent/personal-agent
```

### 第 3 步：创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 第 4 步：环境自检

```bash
python scripts/self_check.py
```

所有项都显示 `[OK]` 才能正常运行。

### 第 5 步：启动服务

```bash
python main.py
```

打开浏览器访问 http://localhost:8000

## 环境变量（可选）

在启动前通过环境变量自定义配置：

```bash
# Claude Code CLI 路径（默认在 PATH 中查找 "claude"）
export CLAUDE_PATH="claude"

# 服务地址和端口
export HOST="0.0.0.0"
export PORT=8000

# 日志级别：DEBUG / INFO / WARNING / ERROR
export LOG_LEVEL="INFO"

# 最大并发 Session 数
export MAX_CONCURRENT_SESSIONS=10

# Session 关闭时自动清理 worktree
export WORKTREE_AUTO_CLEANUP=false
```

## WebSocket 协议

**客户端 → 服务端：**

```json
{"type": "new_session"}
{"type": "message", "session_id": "...", "content": "你的消息"}
```

**服务端 → 客户端：**

| type | 说明 |
|------|------|
| `session_created` | 新 Session 创建，含 session_id 和 worktree_path |
| `chunk` | Claude 流式文本片段 |
| `tool` | 工具调用事件（bash、read_file、write_file 等） |
| `done` | 本轮对话完成 |
| `error` | 错误信息 |

## 测试

```bash
python -m pytest -q
```

## 项目结构

```
personal-agent/
├── main.py              # FastAPI 入口，WebSocket 路由
├── config.py            # 配置项（环境变量读取）
├── requirements.txt     # Python 依赖
├── agent/
│   ├── session.py       # Session 生命周期管理
│   ├── worktree.py      # Git worktree 管理
│   ├── cc_process.py    # Claude Code 子进程封装
│   └── output_filter.py # 事件过滤与格式化
├── frontend/
│   └── index.html       # Web 前端（单文件）
├── memory/              # 记忆模块（预留）
├── scripts/
│   └── self_check.py    # 环境依赖检查
├── tests/               # 单元测试
└── workspace/           # 运行时 worktree 目录（git-ignored）
```

## 常见问题

**Q: 启动后 Claude 返回 "Not logged in"**
A: 先在终端运行 `claude` 完成登录认证。

**Q: Worktree 测试失败**
A: 如果在 CI/沙箱环境中 git commit signing 配置异常，这是环境问题，不影响本地使用。

**Q: 端口被占用**
A: `export PORT=9000` 然后重新启动。
