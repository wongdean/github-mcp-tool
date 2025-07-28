# GitHub MCP Tool

一个专注于代码阅读和问答的MCP（模型上下文协议）工具，支持读取和分析GitHub仓库代码。

## 功能概述

本工具专门用于**代码阅读和智能问答场景**，实现以下核心功能：

### 代码读取与分析
- 获取仓库文件内容（支持多种编程语言）
- 浏览目录结构和文件列表
- 在代码中搜索特定内容和模式

### 仓库信息获取
- 获取仓库基本信息和元数据
- 查看分支列表和提交历史
- 获取README和文档内容

### 智能代码导航
- 按路径快速定位文件
- 搜索函数、类、变量定义
- 分析代码依赖关系

### 使用场景
- **AI辅助代码理解**：与AI助手配合分析代码结构
- **代码问答**：基于GitHub代码库回答技术问题  
- **快速代码调研**：快速了解开源项目实现细节
- **学习和研究**：深入理解优秀开源项目

## 技术架构

- **语言**: Python 3.8+
- **协议**: MCP (Model Context Protocol)
- **GitHub API**: GitHub REST API v4
- **依赖管理**: requirements.txt

## 快速开始

### 1. 安装依赖

```bash
# 克隆或下载项目到本地
git clone <your-repo-url>
cd github-mcp-tool

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 配置GitHub Token

1. 在GitHub上创建Personal Access Token：
   - 访问 GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 点击 "Generate new token (classic)"
   - 选择权限：至少需要 `repo` (完整仓库访问权限)
   - 生成并复制token

2. 配置环境变量：
```bash
# 复制配置模板
cp config_template.env .env

# 编辑 .env 文件，填入你的GitHub Token
GITHUB_TOKEN=your_github_personal_access_token_here
```

### 3. 运行MCP服务

```bash
# 直接运行
python github_mcp_server.py

# 或者安装后运行
pip install -e .
github-mcp
```

## 功能演示

### 可用的MCP工具

1. **get_repository_info** - 获取仓库基本信息
2. **get_file_content** - 读取文件内容  
3. **list_directory** - 浏览目录结构
4. **search_code** - 搜索代码内容
5. **get_repository_structure** - 获取完整目录树
6. **get_branches** - 获取分支列表
7. **get_commits** - 获取提交历史

### 示例用法

通过MCP协议调用工具：

```json
{
  "tool": "get_repository_info",
  "arguments": {
    "repo_url": "microsoft/vscode"
  }
}
```

```json
{
  "tool": "get_file_content", 
  "arguments": {
    "repo_url": "microsoft/vscode",
    "file_path": "package.json"
  }
}
```

```json
{
  "tool": "search_code",
  "arguments": {
    "repo_url": "microsoft/vscode",
    "query": "function createWindow",
    "file_extension": ".ts"
  }
}
```

## 集成到AI助手

此工具专门设计用于与AI助手（如Claude、ChatGPT等）集成，实现智能代码问答：

1. **代码理解**: AI可以读取GitHub项目的代码并理解其结构
2. **技术问答**: 基于实际代码回答技术实现问题
3. **学习辅助**: 帮助分析和学习优秀开源项目
4. **代码调研**: 快速了解项目的架构和实现细节

## 配置选项

在 `.env` 文件中可配置：

- `GITHUB_TOKEN`: GitHub Personal Access Token（必需）
- `GITHUB_API_URL`: GitHub API地址（可选，默认为官方API）
- `LOG_LEVEL`: 日志级别（可选，默认INFO）
- `REQUEST_TIMEOUT`: 请求超时时间（可选，默认30秒）

## 故障排除

### 常见问题

1. **Token权限不足**: 确保GitHub Token具有 `repo` 权限
2. **API速率限制**: GitHub API有速率限制，如遇限制请稍后重试
3. **网络连接**: 确保能正常访问 api.github.com

### 调试模式

设置环境变量启用详细日志：
```bash
export LOG_LEVEL=DEBUG
python github_mcp_server.py
```

---

*🎯 专为AI辅助代码问答场景优化设计* 