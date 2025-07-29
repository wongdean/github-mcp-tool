# 🍒 Cherry Studio 演示配置指南

## 🚀 快速配置 (5分钟搞定)

### 1. 确保MCP服务器能运行
```bash
# 测试服务器启动
cd /Users/coco/Git/github-mcp-tool
python github_mcp_server.py

# 看到这个就说明成功：
# 🚀 GitHub MCP Server 启动成功！
# 📡 监听端口：标准输入/输出
# 🔧 可用工具：10个
# 📝 可用模板：4个
```

### 2. Cherry Studio MCP配置
在Cherry Studio中添加MCP服务器：

**方式1：JSON配置**
```json
{
  "name": "GitHub分析助手",
  "command": "python",
  "args": ["github_mcp_server.py"],
  "cwd": "/Users/coco/Git/github-mcp-tool",
  "env": {
    "GITHUB_TOKEN": "your_github_token_here"
  },
  "disabled": false,
  "alwaysAllow": ["get_repository_info", "get_user_repositories"]
}
```

**方式2：逐字段配置**
- 名称：`GitHub分析助手`
- 命令：`python`
- 参数：`["github_mcp_server.py"]`
- 工作目录：`/Users/coco/Git/github-mcp-tool`
- 环境变量：`GITHUB_TOKEN=你的token`

### 3. 验证配置成功
在Cherry Studio中发送测试消息：
```
你好，请列出你可用的GitHub分析工具
```

应该看到类似输出：
```
我可以为您提供以下GitHub分析工具：

基础分析工具：
✅ get_repository_info - 获取仓库基本信息
✅ get_file_content - 读取文件内容
✅ get_repository_structure - 获取项目结构
... (共10个工具)

专业分析模板：
📋 analyze_repository - 仓库分析模板
📋 code_review - 代码审查模板
📋 tech_stack_analysis - 技术栈分析模板
📋 ecosystem_analysis - 生态系统分析模板
```

---

## 🎪 现场演示脚本

### 演示准备清单：
- [ ] MCP服务器正常启动
- [ ] Cherry Studio连接成功
- [ ] 网络连接正常
- [ ] 准备好演示问题

### 演示1：项目快速评估
**开场白**：
> "假设老板让我们调研VS Code这个项目，看看它的技术实力如何，以前我们要手工点击很多页面，现在看看AI助手怎么帮我们"

**演示问题**：
```
帮我分析一下 microsoft/vscode 这个项目，我想了解：
1. 项目的基本情况和技术实力
2. 代码质量如何
3. 维护活跃度怎么样
```

**预期效果**：
- AI自动调用多个工具
- 展示实时GitHub数据
- 给出结构化分析结果

### 演示2：技术选型对比
**开场白**：
> "技术选型是我们经常遇到的问题，比如前端框架选Vue还是React？让AI帮我们对比分析"

**演示问题**：
```
对比分析 vuejs/vue 和 facebook/react 这两个前端框架：
1. 哪个更受欢迎？
2. 技术成熟度如何？
3. 给我一个选择建议
```

**预期效果**：
- 同时分析两个项目
- 数据对比清晰
- 给出实用建议

### 演示3：组织级分析 ⭐ 新功能
**开场白**：
> "有时候我们想了解某个大厂的技术实力，比如微软的开源策略，这就需要组织级的分析"

**演示问题**：
```
分析microsoft组织的开源项目情况：
1. 他们有哪些重点项目？
2. 技术栈偏好是什么？
3. 开源策略如何？
```

**预期效果**：
- 展示组织级数据获取
- 分析技术趋势
- 提供战略洞察

### 演示4：专业模板使用
**开场白**：
> "对于专业的代码审查，我们提供了结构化的分析模板"

**演示问题**：
```
使用代码审查模板分析 typescript-eslint/typescript-eslint 项目
```

**预期效果**：
- 展示专业模板的威力
- 结构化的审查报告
- 具体的改进建议