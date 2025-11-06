# 系统服务安装指南

本目录包含系统服务配置文件，用于将 Apple Notes MCP 服务器设置为开机自启动的系统服务。

## 目录结构

```
service/
├── com.apple-notes-mcp.plist      # macOS launchd 配置
├── apple-notes-mcp.service        # Linux systemd 配置
└── INSTALL.md                     # 本文件
```

---

## macOS 安装 (launchd)

### 步骤 1: 编辑配置文件

编辑 `com.apple-notes-mcp.plist`，替换以下内容：

1. 将所有 `YOUR_USERNAME` 替换为你的用户名
2. 确认 Python 路径正确（运行 `which python3` 查看）
3. 确认项目路径正确

```bash
# 查看你的用户名
whoami

# 查看 Python 路径
which python3

# 编辑配置文件
nano service/com.apple-notes-mcp.plist
```

### 步骤 2: 创建日志目录

```bash
mkdir -p ~/Library/Logs/apple-notes-mcp
```

### 步骤 3: 复制配置文件

```bash
cp service/com.apple-notes-mcp.plist ~/Library/LaunchAgents/
```

### 步骤 4: 加载服务

```bash
launchctl load ~/Library/LaunchAgents/com.apple-notes-mcp.plist
```

### 步骤 5: 验证服务

```bash
# 检查服务状态
launchctl list | grep apple-notes-mcp

# 查看日志
tail -f ~/Library/Logs/apple-notes-mcp/stdout.log
```

### 管理命令

```bash
# 启动服务
launchctl start com.apple-notes-mcp

# 停止服务
launchctl stop com.apple-notes-mcp

# 重启服务
launchctl stop com.apple-notes-mcp && launchctl start com.apple-notes-mcp

# 卸载服务
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.plist

# 查看服务详情
launchctl list com.apple-notes-mcp
```

---

## Linux 安装 (systemd)

### 步骤 1: 编辑配置文件

编辑 `apple-notes-mcp.service`，替换以下内容：

1. 将 `YOUR_USERNAME` 替换为你的用户名
2. 将 `YOUR_USERGROUP` 替换为你的用户组（通常与用户名相同）
3. 确认 Python 路径正确（运行 `which python3` 查看）
4. 确认项目路径正确

```bash
# 查看用户名和组
id

# 查看 Python 路径
which python3

# 编辑配置文件
nano service/apple-notes-mcp.service
```

### 步骤 2: 复制配置文件

#### 用户级服务（推荐）

```bash
# 创建用户服务目录
mkdir -p ~/.config/systemd/user

# 复制配置文件
cp service/apple-notes-mcp.service ~/.config/systemd/user/

# 重载 systemd
systemctl --user daemon-reload

# 启动服务
systemctl --user start apple-notes-mcp

# 设置开机自启
systemctl --user enable apple-notes-mcp
```

#### 系统级服务（需要 root 权限）

```bash
# 复制配置文件
sudo cp service/apple-notes-mcp.service /etc/systemd/system/

# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start apple-notes-mcp

# 设置开机自启
sudo systemctl enable apple-notes-mcp
```

### 步骤 3: 验证服务

```bash
# 查看服务状态
systemctl --user status apple-notes-mcp

# 查看日志
journalctl --user -u apple-notes-mcp -f
```

### 管理命令

```bash
# 启动服务
systemctl --user start apple-notes-mcp

# 停止服务
systemctl --user stop apple-notes-mcp

# 重启服务
systemctl --user restart apple-notes-mcp

# 查看状态
systemctl --user status apple-notes-mcp

# 查看日志（最后 100 行）
journalctl --user -u apple-notes-mcp -n 100

# 实时查看日志
journalctl --user -u apple-notes-mcp -f

# 启用开机自启
systemctl --user enable apple-notes-mcp

# 禁用开机自启
systemctl --user disable apple-notes-mcp
```

---

## 故障排除

### macOS 问题

**问题 1: 服务无法启动**

```bash
# 检查配置文件语法
plutil -lint ~/Library/LaunchAgents/com.apple-notes-mcp.plist

# 查看错误日志
tail -f ~/Library/Logs/apple-notes-mcp/stderr.log

# 检查权限
ls -la ~/Library/LaunchAgents/com.apple-notes-mcp.plist
```

**问题 2: 服务频繁重启**

检查 `ThrottleInterval` 设置，确保不会过于频繁重启。

**问题 3: Python 路径错误**

```bash
# 找到正确的 Python 路径
which python3

# 更新配置文件中的路径
nano ~/Library/LaunchAgents/com.apple-notes-mcp.plist
```

### Linux 问题

**问题 1: 服务无法启动**

```bash
# 查看详细错误
systemctl --user status apple-notes-mcp -l

# 查看完整日志
journalctl --user -u apple-notes-mcp --no-pager

# 检查配置文件语法
systemd-analyze verify ~/.config/systemd/user/apple-notes-mcp.service
```

**问题 2: 权限错误**

```bash
# 确保用户有执行权限
chmod +x ~/apple-notes-mcp/scripts/server_enhanced.py

# 检查文件所有权
ls -la ~/apple-notes-mcp/scripts/
```

**问题 3: 用户服务未随用户登录启动**

```bash
# 启用用户服务持久化（需要 root 权限）
sudo loginctl enable-linger $USER

# 验证
loginctl show-user $USER | grep Linger
```

---

## 配置选项

### 修改端口

编辑配置文件，修改 `--port` 参数：

**macOS:**
```xml
<string>--port</string>
<string>9000</string>
```

**Linux:**
```ini
ExecStart=/usr/bin/python3 ... --port 9000
```

### 启用 API 密钥认证

取消注释环境变量设置：

**macOS:**
```xml
<key>APPLE_NOTES_API_KEY</key>
<string>your-secret-key-here</string>
```

**Linux:**
```ini
Environment="APPLE_NOTES_API_KEY=your-secret-key-here"
```

### 调整资源限制

**macOS:**
```xml
<key>MemoryLimit</key>
<integer>4294967296</integer> <!-- 4GB -->
```

**Linux:**
```ini
MemoryLimit=4G
CPUQuota=200%  # 允许使用 2 个 CPU 核心
```

---

## 卸载服务

### macOS

```bash
# 停止并卸载服务
launchctl unload ~/Library/LaunchAgents/com.apple-notes-mcp.plist

# 删除配置文件
rm ~/Library/LaunchAgents/com.apple-notes-mcp.plist

# 清理日志（可选）
rm -rf ~/Library/Logs/apple-notes-mcp
```

### Linux

```bash
# 停止并禁用服务
systemctl --user stop apple-notes-mcp
systemctl --user disable apple-notes-mcp

# 删除配置文件
rm ~/.config/systemd/user/apple-notes-mcp.service

# 重载 systemd
systemctl --user daemon-reload
```

---

## 推荐配置

对于大多数用户，我们建议：

1. **开发环境**: 使用 `./server_manager.sh start` 手动启动
2. **生产环境**: 使用系统服务（launchd/systemd）自动管理
3. **测试环境**: 使用前台模式方便调试

---

## 性能监控

### macOS

```bash
# 查看服务资源使用
top -pid $(pgrep -f server_enhanced.py)

# 或使用 Activity Monitor 图形界面
```

### Linux

```bash
# 查看服务资源使用
systemctl --user status apple-notes-mcp

# 详细性能统计
systemd-cgtop --user

# CPU 和内存使用
ps aux | grep server_enhanced.py
```

---

## 更多信息

- [项目主页](https://github.com/yinanli1917-cloud/apple-notes-mcp)
- [Poke AI 集成指南](../docs/POKE_INTEGRATION.md)
- [服务器管理脚本](../server_manager.sh)
- [技术文档](../docs/PROJECT_LOG.md)

---

**最后更新**: 2025-01-15
**版本**: 1.0
