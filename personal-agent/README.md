# Personal Agent — CC Wrapper

一个基于 FastAPI + WebSocket 的 Web IM Bot，用来在浏览器里控制 Claude Code CLI。

## 功能
- 多 Session 并发聊天
- 每个 Session 独立 git worktree
- Claude stream-json 实时流式输出
- 工具调用过滤展示

## 启动
```bash
cd personal-agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

打开 http://localhost:8000

## WebSocket 协议
客户端：
- `{"type":"new_session"}`
- `{"type":"message","session_id":"...","content":"..."}`

服务端：
- `session_created`
- `chunk`
- `tool`
- `done`
- `error`

## 测试
```bash
cd personal-agent
python -m pytest -q
```
