# 更新日志

## [2.0.0] - 2025-01-15

### 新增功能 🎉

#### 本地服务器增强

- **新增 `server_enhanced.py`** - 增强版 HTTP 服务器
  - 支持命令行参数配置（端口、API 密钥、日志级别）
  - 完整的结构化日志系统
  - 自动日志文件保存
  - 健康检查端点
  - 更详细的统计信息
  - 优雅的服务器启动/停止

- **新增 `server_manager.sh`** - 服务器管理脚本
  - 前台/后台启动模式
  - 进程状态监控
  - 资源使用统计
  - 日志查看和跟踪
  - 连接测试
  - 完整的帮助文档

#### 系统服务集成

- **新增 `service/` 目录** - 系统服务配置
  - macOS launchd 配置 (`com.apple-notes-mcp.plist`)
  - Linux systemd 配置 (`apple-notes-mcp.service`)
  - 详细的安装指南 (`service/INSTALL.md`)
  - 支持开机自启动
  - 自动崩溃恢复
  - 资源限制配置

#### Web 界面

- **新增 `scripts/web_interface.html`** - Web 管理界面
  - 实时搜索测试
  - 服务器状态监控
  - 统计信息展示
  - 索引管理
  - 美观的现代化 UI

#### 文档完善

- **新增 `docs/LOCAL_SERVER.md`** - 本地服务器完整指南
  - 详细的使用说明
  - 多种运行模式对比
  - Poke AI 集成步骤
  - 高级配置选项
  - 故障排除指南
  - 性能优化建议

- **更新 `README.md`** - 主文档
  - 添加本地服务器使用说明
  - 更新文档链接
  - 优化使用方式说明

- **完善 `docs/POKE_INTEGRATION.md`** - Poke AI 集成
  - 更详细的配置步骤
  - 多种后台运行方式
  - 完整的故障排除

### 改进 ✨

#### 性能优化

- 优化模型加载流程
- 改进日志输出格式
- 减少不必要的数据库查询
- 更好的错误处理

#### 用户体验

- 更友好的命令行界面
- 彩色输出提示
- 详细的状态信息
- 清晰的错误消息

#### 代码质量

- 添加详细的代码注释
- 改进错误处理
- 统一代码风格
- 增强类型提示

### 功能对比

| 特性 | 1.0 版本 | 2.0 版本 |
|------|---------|---------|
| Claude Desktop | ✅ | ✅ |
| 基础 HTTP 服务器 | ✅ | ✅ |
| 增强 HTTP 服务器 | ❌ | ✅ |
| 命令行参数 | ❌ | ✅ |
| 进程管理脚本 | ❌ | ✅ |
| 系统服务集成 | ❌ | ✅ |
| Web 管理界面 | ❌ | ✅ |
| 结构化日志 | ❌ | ✅ |
| API 密钥认证 | ❌ | ✅ |
| 健康检查 | ❌ | ✅ |

### 兼容性

- ✅ 完全向后兼容 1.0 版本
- ✅ 原有的 `server.py` 和 `server_http.py` 继续可用
- ✅ 所有现有配置继续有效
- ✅ 数据库格式不变

### 升级指南

从 1.0 升级到 2.0 非常简单：

```bash
# 1. 拉取最新代码
cd ~/Documents/apple-notes-mcp
git pull

# 2. 设置执行权限
chmod +x server_manager.sh
chmod +x scripts/server_enhanced.py

# 3. 尝试新功能
./server_manager.sh start --daemon
```

不需要：
- ❌ 重新安装依赖
- ❌ 重建索引
- ❌ 修改现有配置

### 已知问题

- Web 界面目前是静态 HTML，需要手动刷新数据（计划在 2.1 版本改进）
- API 密钥认证是简单实现，不适用于生产环境（计划在 2.1 版本增强）

### 贡献者

- [@yinanli1917-cloud](https://github.com/yinanli1917-cloud) - 主要开发
- Claude Code - AI 辅助开发

---

## [1.0.0] - 2025-01-05

### 初始版本

- Apple Notes 导出功能
- BGE-M3 语义搜索
- ChromaDB 向量数据库
- Claude Desktop 集成
- 基础 HTTP 服务器（Poke AI 支持）
- 中文编码修复
- 基础文档

---

## 未来计划

### 2.1.0（计划中）

- [ ] 交互式 Web 界面（实时更新）
- [ ] REST API 接口（除了 MCP）
- [ ] 增强的 API 认证（JWT）
- [ ] 搜索结果缓存
- [ ] 多用户支持
- [ ] Docker 容器化

### 2.2.0（规划中）

- [ ] 图形化配置工具
- [ ] 搜索历史记录
- [ ] 笔记标签系统
- [ ] 全文导出功能
- [ ] 性能监控面板
- [ ] 自动索引更新

### 未来考虑

- 支持其他笔记应用（Notion、Evernote）
- 移动端 App
- 浏览器扩展
- AI 对话式搜索
- 智能摘要功能

---

## 版本说明

版本号格式：`主版本.次版本.修订版本`

- **主版本**: 重大功能更新或架构变化
- **次版本**: 新功能添加
- **修订版本**: Bug 修复和小改进

---

**查看完整提交历史**: [GitHub Commits](https://github.com/yinanli1917-cloud/apple-notes-mcp/commits)

**报告问题**: [GitHub Issues](https://github.com/yinanli1917-cloud/apple-notes-mcp/issues)
