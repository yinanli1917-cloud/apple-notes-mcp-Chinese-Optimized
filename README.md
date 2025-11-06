# 苹果备忘录 AI 搜索助手

> 让 AI 帮你搜索备忘录，就像和朋友聊天一样简单

![GitHub stars](https://img.shields.io/github/stars/yinanli1917-cloud/apple-notes-mcp?style=social)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**作者**: [Yinan Li](https://github.com/yinanli1917-cloud) & [Claude Code](https://claude.ai/claude-code)

---

## 🤔 这是什么？

想象一下：你有几百条甚至上千条备忘录，想找"上个月写的关于 AI 的笔记"，但完全记不清标题是什么...

**传统方式**：一条条翻，用关键词搜索，找半天找不到 😫

**用这个工具**：直接问 AI"帮我找关于 AI 的笔记"，几秒钟就找到了 ✨

---

## ✨ 它能做什么？

### 和 AI 聊天搜索笔记

**不需要记住笔记标题**，只要描述你想找什么：

- 💬 "帮我找幽默搞笑的内容"
- 💬 "上个月关于工作的笔记"
- 💬 "有哪些关于 AI 的想法"

### 理解你的意思

**不是简单的关键词匹配**，而是真正理解语义：

- 搜"幽默" → 也能找到"笑话"、"搞笑"相关的
- 搜"美国政治" → 能找到"代议制"、"三权分立"相关的
- 搜"AI" → 能找到"人工智能"、"机器学习"相关的

### 在多个地方使用

- 🖥️ **Claude Desktop**：在电脑上和 Claude 对话时搜索
- 📱 **Poke AI**：通过 iMessage 搜索（还在测试中）
- 🌐 **任何支持 MCP 的 AI 工具**

---

## 🎯 适合谁用？

### ✅ 适合你，如果：

- 你用苹果备忘录（Apple Notes）
- 你的备忘录很多（几十条以上）
- 你经常找不到笔记在哪
- 你想让 AI 帮你整理和搜索

### ⚠️ 可能不适合，如果：

- 你不用苹果备忘录（目前只支持 Apple Notes）
- 你的笔记很少（几条笔记不需要搜索）
- 你不会用电脑命令行（需要一点点技术基础）

---

## 🚀 5 分钟快速开始

### 第一步：准备工作

**你需要**：
- ✅ 一台 Mac 电脑（因为要导出 Apple Notes）
- ✅ 会用终端（Terminal）运行几个命令
- ✅ （可选）GitHub 账号（如果想要远程访问）

**安装工具**：
```bash
# 确认你有 Python 3.10 或更高版本
python3 --version

# 如果没有，用 Homebrew 安装
brew install python@3.12
```

### 第二步：下载这个项目

```bash
# 下载代码
git clone https://github.com/yinanli1917-cloud/apple-notes-mcp.git
cd apple-notes-mcp

# 安装依赖（需要几分钟）
pip3 install -r requirements.txt
```

### 第三步：导出你的备忘录

```bash
cd scripts
python3 export_notes_fixed.py
```

这会把你的备忘录导出到一个数据库文件（`~/notes.db`）。

### 第四步：建立搜索索引

```bash
python3 indexer.py
```

第一次运行会下载 AI 模型（大约 560MB），然后处理你的笔记。

**预计时间**：3-5 分钟（取决于笔记数量）

**完成后会显示**：
```
✅ 索引构建完成！已索引 XXX 条笔记
```

### 第五步：开始使用

#### 方式 A：在 Claude Desktop 中使用

1. 打开配置文件：
   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. 添加这段配置：
   ```json
   {
     "mcpServers": {
       "apple-notes": {
         "command": "python3",
         "args": [
           "/Users/你的用户名/Documents/apple-notes-mcp/scripts/server.py"
         ]
       }
     }
   }
   ```

   **注意**：把 `/Users/你的用户名` 改成你的实际路径

3. 重启 Claude Desktop（完全退出后重新打开）

4. 在对话中试试：
   ```
   搜索"幽默搞笑的内容"
   ```

#### 方式 B：在手机上使用（通过 Poke AI）

**正在开发中**，目前有连接问题。如果你想试试：

1. 启动服务器：
   ```bash
   cd ~/Documents/apple-notes-mcp
   ./start_poke_server.sh
   ```

2. 在 Poke AI 中配置：
   - Server URL: `http://你的Mac局域网IP:8000/sse`
   - API Key: 留空

详细步骤见 [POKE_INTEGRATION.md](POKE_INTEGRATION.md)

---

## 📊 效果如何？

**基于实际测试**（920 条笔记）：

- ✅ **搜索准确率**：87%
- ✅ **响应速度**：0.1-0.2 秒
- ✅ **理解中文**：非常好（专门优化过）
- ✅ **混合语言**：中英文混合也能搜

**示例效果**：

| 你问 AI | AI 找到的笔记 |
|---------|-------------|
| "幽默搞笑的内容" | 😄 笑话、搞笑段子、讽刺文章 |
| "关于 AI 的想法" | 🤖 AI 应用、机器学习、技术讨论 |
| "美国政治制度" | 🏛️ 代议制、三权分立、批判文章 |

---

## 🛠️ 工作原理（技术细节）

如果你想了解它是怎么工作的：

### 1. 导出笔记
把 Apple Notes 的笔记导出到 SQLite 数据库

### 2. AI 理解
使用 BGE-M3 模型（一个专门理解中文的 AI 模型）把每条笔记转换成"向量"（一串数字，代表笔记的含义）

### 3. 存储索引
把这些向量存储到 ChromaDB（一个向量数据库）

### 4. 搜索
当你搜索时，AI 也把你的问题转换成向量，然后找最相似的笔记

**技术栈**：
- **BGE-M3**：嵌入模型（1024 维向量）
- **ChromaDB**：向量数据库
- **FastMCP**：MCP 协议框架
- **Python 3.12**

---

## 💰 费用和限制

### 本地使用（完全免费）

- ✅ 所有数据在你电脑上
- ✅ 不需要联网（除了下载模型）
- ✅ 隐私完全保护
- ⚠️ 只能在你的 Mac 上用

### 云端部署（需要小额费用）

如果你想在手机上用（通过流量，不限制 WiFi）：

- 💰 **Railway**：约 $5/月
- 💰 **Fly.io**：约 $2-3/月
- ⚠️ 笔记数据会上传到云端（但只有你能访问）

**详细部署教程**：
- [Railway 部署](RAILWAY_DEPLOYMENT.md)
- [Fly.io 部署](FLY_DEPLOYMENT.md)

---

## 🔐 隐私和安全

### 你的数据在哪？

- **本地部署**：所有数据在你的 Mac 上，不会上传
- **云端部署**：笔记会上传到你的私有云服务器（Railway/Fly.io）

### 如何保护？

- ✅ 笔记数据库（notes.db）不会上传到 GitHub
- ✅ 云端部署有 API Key 保护
- ✅ 自动使用 HTTPS 加密

### 敏感信息怎么办？

如果你的笔记包含密码、信用卡等敏感信息：

**建议只用本地部署**，或者：
- 导出前删除敏感笔记
- 或者手动过滤敏感内容

---

## 🆘 常见问题

### Q: 我不会用命令行怎么办？

A: 这个项目目前需要一点点命令行基础。如果完全不会，可以：
1. 找懂技术的朋友帮忙
2. 或者等我们做一个图形界面版本

### Q: 支持其他笔记应用吗？

A: 目前只支持 Apple Notes。如果你用：
- **Notion**、**Evernote**、**Obsidian** 等：可以先导出成纯文本，稍作修改就能用
- 欢迎贡献代码支持更多应用！

### Q: 搜索结果不准确怎么办？

A: 试试这些：
1. 换个说法（比如"幽默"换成"笑话"）
2. 增加返回结果数量（"搜索 XXX，返回 20 条"）
3. 查看文档中的故障排除部分

### Q: 能不能添加自动同步？

A: 目前需要手动运行命令更新索引。自动同步正在计划中！

---

## 📚 完整文档

- 🚀 [云端部署指南](DEPLOY.md) - 部署到服务器，手机也能用
- 📱 [Poke AI 集成](POKE_INTEGRATION.md) - 通过 iMessage 搜索
- 🔧 [开发者文档](PROJECT_LOG.md) - 技术细节和决策记录

---

## 🤝 参与贡献

欢迎任何形式的贡献！

### 你可以：

- 🐛 **报告 Bug**：[提交 Issue](https://github.com/yinanli1917-cloud/apple-notes-mcp/issues)
- 💡 **提建议**：告诉我们你想要什么功能
- 📝 **改进文档**：让文档更清楚易懂
- 💻 **贡献代码**：Fork 项目，提交 Pull Request

### 开发计划：

- [ ] 支持更多笔记应用
- [ ] 图形界面（不需要用命令行）
- [ ] 自动同步功能
- [ ] 更多 AI 客户端支持
- [ ] 完善文档和示例

---

## 🙏 致谢

### 使用的开源项目

- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 协议框架
- [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) - 中文嵌入模型
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

### 灵感来源

这个项目的灵感来自 [ima](https://ima.app) - 一个优秀的苹果备忘录搜索应用。我们的目标是做一个开源版本，让大家都能用上！

---

## 📄 开源协议

MIT License - 详见 [LICENSE](LICENSE)

简单来说：你可以自由使用、修改、分发这个项目，但需要保留原作者信息。

---

## ⭐ 觉得有用？

如果这个项目帮到了你，请给我们一个 Star ⭐！

这是对我们最大的鼓励 💪

---

**Made with ❤️ by Yinan Li & Claude Code**

有问题？[提 Issue](https://github.com/yinanli1917-cloud/apple-notes-mcp/issues) 或 [加入讨论](https://github.com/yinanli1917-cloud/apple-notes-mcp/discussions)
