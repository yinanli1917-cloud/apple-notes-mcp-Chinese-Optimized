# 本地服务器部署指南

本指南介绍如何将 Apple Notes MCP 部署为本地服务器，以便接入 Poke AI、Web 客户端或其他 MCP 应用。

## 概述

Apple Notes MCP 现在提供三种运行模式：

1. **Claude Desktop 模式** - 使用 `server.py`，通过 stdio 传输
2. **本地 HTTP 服务器模式** - 使用 `server_http.py` 或 `server_enhanced.py`，通过 HTTP/SSE 传输
3. **云端部署模式** - 部署到 Fly.io、Railway 等云平台

本文档重点介绍第 2 种：本地 HTTP 服务器模式。

---

## 快速开始

### 基础版（5 分钟）

使用原有的 HTTP 服务器（简单易用）：

```bash
cd ~/Documents/apple-notes-mcp/scripts
python3 server_http.py
```

服务器将在 `http://localhost:8000/sse` 启动。

### 增强版（推荐）

使用新的增强版服务器（更多功能）：

```bash
cd ~/Documents/apple-notes-mcp
chmod +x server_manager.sh

# 前台启动（方便调试）
./server_manager.sh start

# 后台启动（生产环境）
./server_manager.sh start --daemon

# 查看状态
./server_manager.sh status
```

---

## 增强版服务器功能

### 新增特性

1. **多种端点支持**
   - MCP SSE: `http://localhost:8000/sse` (用于 Poke AI)
   - 健康检查: `http://localhost:8000/health`
   - Web 界面: `http://localhost:8000/` (即将推出)

2. **完整的日志系统**
   - 结构化日志输出
   - 自动日志文件保存到 `~/apple-notes-mcp-server.log`
   - 支持多种日志级别

3. **灵活的配置**
   - 自定义端口: `--port 9000`
   - API 密钥认证: `--api-key your-secret`
   - 日志级别控制: `--log-level DEBUG`

4. **更多 MCP 工具**
   - `search_notes` - 语义搜索
   - `refine_search` - 精细搜索（带日期过滤）
   - `refresh_index` - 刷新索引
   - `get_stats` - 查看统计信息
   - `health_check` - 健康检查

5. **进程管理**
   - 使用 `server_manager.sh` 脚本管理
   - 支持前台/后台运行
   - 支持系统服务集成（launchd/systemd）

---

## 使用 server_manager.sh

### 基本命令

```bash
# 启动服务器（前台）
./server_manager.sh start

# 启动服务器（后台）
./server_manager.sh start --daemon

# 指定端口
./server_manager.sh start --port 9000 --daemon

# 停止服务器
./server_manager.sh stop

# 重启服务器
./server_manager.sh restart

# 查看状态
./server_manager.sh status

# 查看日志（最后 50 行）
./server_manager.sh logs

# 实时跟踪日志
./server_manager.sh follow

# 测试连接
./server_manager.sh test
```

### 状态输出示例

```
========================================
  Apple Notes MCP 服务器管理器
========================================

✓ 服务器正在运行

ℹ 进程信息:
  PID: 12345
  命令: python3 server_enhanced.py --port 8000

ℹ 资源使用:
  CPU: 2.5%
  内存: 1.2% (RSS: 450.3 MB, VSZ: 2100.5 MB)

ℹ 运行时间:
  02:30:45

ℹ 监听端口:
  TCP *:8000 (LISTEN)

ℹ 服务端点:
  MCP SSE:  http://localhost:8000/sse
  Web UI:   http://localhost:8000/
  日志文件: /Users/username/apple-notes-mcp-server.log
```

---

## 接入 Poke AI

### 步骤 1: 启动服务器

```bash
./server_manager.sh start --daemon
```

### 步骤 2: 配置 Poke AI

在 Poke AI 的 "New Integration" 页面：

| 字段 | 值 |
|------|-----|
| Name | `Apple Notes Search` |
| Server URL | `http://127.0.0.1:8000/sse` |
| API Key | 留空（或填写自定义密钥） |

### 步骤 3: 测试

在 iMessage 中向 Poke 发送：

```
搜索幽默搞笑的内容
```

详细说明请参考：[Poke AI 集成指南](POKE_INTEGRATION.md)

---

## 接入其他客户端

### Web 浏览器

打开 `scripts/web_interface.html` 文件，可以通过 Web 界面测试服务器：

```bash
# 启动服务器
./server_manager.sh start --daemon

# 在浏览器中打开 Web 界面
open scripts/web_interface.html
```

Web 界面提供：
- 实时搜索测试
- 服务器状态监控
- 统计信息查看
- 索引管理

### 自定义 MCP 客户端

如果你正在开发自己的 MCP 客户端，可以连接到：

```
Endpoint: http://localhost:8000/sse
Transport: Server-Sent Events (SSE)
Protocol: MCP (Model Context Protocol)
```

示例代码（使用 FastMCP 客户端）：

```python
from fastmcp.client import Client

# 连接到本地服务器
client = Client("http://localhost:8000/sse")

# 调用工具
result = await client.call_tool("search_notes", {
    "query": "AI 人工智能",
    "limit": 5
})

print(result)
```

---

## 系统服务集成

如果你希望服务器开机自启动，可以将其设置为系统服务。

### macOS (launchd)

```bash
# 编辑配置文件（替换用户名和路径）
nano service/com.apple-notes-mcp.plist

# 安装服务
cp service/com.apple-notes-mcp.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.plist

# 管理服务
launchctl start com.apple-notes-mcp
launchctl stop com.apple-notes-mcp
```

### Linux (systemd)

```bash
# 编辑配置文件（替换用户名和路径）
nano service/apple-notes-mcp.service

# 安装用户服务
mkdir -p ~/.config/systemd/user
cp service/apple-notes-mcp.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user start apple-notes-mcp
systemctl --user enable apple-notes-mcp

# 管理服务
systemctl --user status apple-notes-mcp
systemctl --user restart apple-notes-mcp
journalctl --user -u apple-notes-mcp -f
```

详细说明请参考：[service/INSTALL.md](../service/INSTALL.md)

---

## 高级配置

### 自定义端口

```bash
# 使用脚本
./server_manager.sh start --port 9000 --daemon

# 直接运行
python3 scripts/server_enhanced.py --port 9000
```

### 启用 API 密钥认证

```bash
# 方式 1: 命令行参数
python3 scripts/server_enhanced.py --api-key your-secret-key

# 方式 2: 环境变量
export APPLE_NOTES_API_KEY=your-secret-key
python3 scripts/server_enhanced.py

# 方式 3: 系统服务配置
# 编辑 service/com.apple-notes-mcp.plist 或 service/apple-notes-mcp.service
```

### 调整日志级别

```bash
# 调试模式（详细日志）
python3 scripts/server_enhanced.py --log-level DEBUG

# 警告模式（只显示警告和错误）
python3 scripts/server_enhanced.py --log-level WARNING
```

### 监听所有网络接口（局域网访问）

```bash
# 允许局域网内其他设备访问
python3 scripts/server_enhanced.py --host 0.0.0.0 --port 8000
```

⚠️ **安全警告**: 绑定到 `0.0.0.0` 会允许局域网内所有设备访问，建议启用 API 密钥认证。

---

## 性能优化

### 资源使用

典型资源使用情况：

- **内存**: 400-600 MB（取决于索引大小）
- **CPU**: 空闲时 < 1%，搜索时 10-30%
- **启动时间**: 10-15 秒（加载 BGE-M3 模型）

### 优化建议

1. **保持服务器运行**: 避免频繁重启，减少模型加载时间
2. **使用后台模式**: `./server_manager.sh start --daemon`
3. **定期刷新索引**: 每天或每周运行一次 `refresh_index`
4. **监控资源使用**: 使用 `./server_manager.sh status` 检查

---

## 故障排除

### 问题 1: 端口已被占用

```bash
# 查看占用端口的进程
lsof -i :8000

# 停止进程或使用其他端口
./server_manager.sh start --port 9000
```

### 问题 2: 服务器无法启动

```bash
# 检查日志
tail -f ~/apple-notes-mcp-server.log

# 检查依赖
pip3 install -r requirements.txt

# 检查数据库
ls -la ~/notes.db ~/Documents/apple-notes-mcp/chroma_db/
```

### 问题 3: 搜索返回错误

```bash
# 重建索引
cd ~/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py
python3 indexer.py full
```

### 问题 4: 内存占用过高

```bash
# 查看资源使用
./server_manager.sh status

# 重启服务器释放内存
./server_manager.sh restart
```

### 问题 5: 客户端无法连接

```bash
# 测试服务器
curl http://localhost:8000/health

# 检查防火墙设置
# macOS
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Linux
sudo ufw status
```

---

## 安全最佳实践

### 本地使用

对于本地使用（仅在同一台电脑上访问）：

1. ✅ 绑定到 `127.0.0.1`（默认）
2. ✅ 无需 API 密钥
3. ✅ 无需 HTTPS

### 局域网使用

如果需要局域网内其他设备访问：

1. ✅ 启用 API 密钥认证
2. ✅ 使用强密码
3. ⚠️ 注意防火墙设置
4. ⚠️ 限制访问 IP（使用防火墙规则）

### 公网暴露（不推荐）

❌ **不建议**直接将本地服务器暴露到公网。如需远程访问，请考虑：

1. 部署到云平台（Fly.io、Railway）
2. 使用 VPN 连接
3. 使用反向代理（Nginx + HTTPS）
4. 启用强认证和加密

---

## 对比：基础版 vs 增强版

| 特性 | server_http.py | server_enhanced.py |
|------|----------------|-------------------|
| MCP 协议 | ✅ | ✅ |
| 基础搜索 | ✅ | ✅ |
| 精细搜索 | ✅ | ✅ |
| 健康检查 | ❌ | ✅ |
| 结构化日志 | ❌ | ✅ |
| 命令行参数 | ❌ | ✅ |
| API 密钥认证 | ❌ | ✅ |
| 进程管理脚本 | ❌ | ✅ |
| 系统服务集成 | ❌ | ✅ |
| 性能监控 | ❌ | ✅ |

**建议**:
- 快速测试使用 `server_http.py`
- 生产环境使用 `server_enhanced.py`

---

## 与 Claude Desktop 共存

你可以同时运行两种模式：

1. **Claude Desktop**:
   - 使用 `server.py`（stdio 传输）
   - 由 Claude Desktop 自动管理
   - 配置在 `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **本地 HTTP 服务器**:
   - 使用 `server_enhanced.py`（HTTP/SSE 传输）
   - 手动启动或使用系统服务
   - 监听 8000 端口

两者互不干扰，共享同一个向量数据库。

---

## 监控和维护

### 日常检查

```bash
# 查看服务器状态
./server_manager.sh status

# 查看最近日志
./server_manager.sh logs 100

# 测试连接
./server_manager.sh test
```

### 定期维护

```bash
# 每周刷新索引（如果经常添加新笔记）
cd ~/Documents/apple-notes-mcp/scripts
python3 export_notes_fixed.py
python3 indexer.py

# 清理旧日志（可选）
# 日志文件：~/apple-notes-mcp-server.log
```

### 性能监控

```bash
# macOS
top -pid $(pgrep -f server_enhanced.py)

# Linux
htop -p $(pgrep -f server_enhanced.py)
```

---

## 下一步

- [Poke AI 集成指南](POKE_INTEGRATION.md) - 接入 Poke AI
- [云端部署指南](DEPLOY.md) - 部署到云平台
- [系统服务安装](../service/INSTALL.md) - 设置开机自启
- [技术文档](PROJECT_LOG.md) - 了解技术细节

---

## 常见问题

**Q: 基础版和增强版有什么区别？**

A: 基础版 (`server_http.py`) 更简单，适合快速测试。增强版 (`server_enhanced.py`) 提供更多功能，适合生产环境。

**Q: 可以在 Windows 上运行吗？**

A: 理论上可以，但目前主要在 macOS 和 Linux 上测试。Windows 用户可能需要修改一些脚本。

**Q: 如何让服务器开机自启动？**

A: 参考 [service/INSTALL.md](../service/INSTALL.md) 设置系统服务。

**Q: 可以同时连接多个客户端吗？**

A: 可以。MCP 服务器支持多个客户端同时连接。

**Q: 内存占用可以降低吗？**

A: BGE-M3 模型需要约 400-600 MB 内存，这是正常的。如果需要更小的内存占用，可以考虑使用更小的模型。

**Q: 支持 HTTPS 吗？**

A: 增强版本身不提供 HTTPS，但你可以使用 Nginx 等反向代理添加 HTTPS 支持。

---

## 贡献和反馈

如果你有问题、建议或改进：

- 提交 Issue: https://github.com/yinanli1917-cloud/apple-notes-mcp/issues
- 提交 PR: https://github.com/yinanli1917-cloud/apple-notes-mcp/pulls
- 查看文档: https://github.com/yinanli1917-cloud/apple-notes-mcp/tree/main/docs

---

**最后更新**: 2025-01-15
**版本**: 2.0
**状态**: ✅ 生产就绪
