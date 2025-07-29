#!/usr/bin/env python3
"""
GitHub MCP服务器
提供GitHub代码阅读和分析功能的MCP工具
"""

import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    Prompt,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    ServerCapabilities
)
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from loguru import logger

from github_client import GitHubClient
from java_dependency_analyzer import JavaDependencyAnalyzer

# 加载环境变量
load_dotenv()

# 配置日志
logger.add(sys.stderr, level="INFO")

class GitHubMCPServer:
    """GitHub MCP服务器类"""
    
    def __init__(self):
        self.server = Server("github-mcp")
        self.github_client: Optional[GitHubClient] = None
        self.java_analyzer: Optional[JavaDependencyAnalyzer] = None
        self._setup_handlers()
        
    def _setup_handlers(self):
        """设置MCP服务器处理器"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用的工具列表"""
            return [
                Tool(
                    name="get_repository_info",
                    description="获取GitHub仓库的基本信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="get_file_content",
                    description="获取仓库中指定文件的内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "文件路径"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url", "file_path"]
                    }
                ),
                Tool(
                    name="check_file_exists",
                    description="检查文件或目录是否存在，避免404错误。在调用get_file_content之前建议先使用此工具",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "file_path": {
                                "type": "string",
                                "description": "要检查的文件或目录路径"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url", "file_path"]
                    }
                ),
                Tool(
                    name="list_directory",
                    description="列出仓库中指定目录的内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "directory_path": {
                                "type": "string",
                                "description": "目录路径（可选，默认为根目录）"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="search_code",
                    description="在仓库中搜索代码内容",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "query": {
                                "type": "string",
                                "description": "搜索关键词或正则表达式"
                            },
                            "file_extension": {
                                "type": "string",
                                "description": "文件扩展名过滤（如.py, .js等，可选）"
                            },
                            "path_filter": {
                                "type": "string",
                                "description": "路径过滤（可选）"
                            }
                        },
                        "required": ["repo_url", "query"]
                    }
                ),
                Tool(
                    name="get_repository_structure",
                    description="获取仓库的完整目录结构",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            },
                            "max_depth": {
                                "type": "integer",
                                "description": "最大深度（可选，默认为3）"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="get_branches",
                    description="获取仓库的所有分支列表",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="get_commits",
                    description="获取仓库的提交历史",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回的提交数量限制（可选，默认为10）"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="get_user_repositories",
                    description="获取GitHub用户的所有公开仓库列表和统计信息",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "GitHub用户名"
                            },
                            "sort": {
                                "type": "string",
                                "description": "排序方式：updated(最近更新), created(创建时间), pushed(最近推送), full_name(名称)，默认为updated"
                            },
                            "per_page": {
                                "type": "integer",
                                "description": "返回的仓库数量限制（可选，默认为30，最大100）"
                            }
                        },
                        "required": ["username"]
                    }
                ),
                Tool(
                    name="analyze_java_dependencies",
                    description="分析Java项目的依赖关系，解析pom.xml或build.gradle",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "要分析的GitHub仓库URL或owner/repo格式"
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="trace_method_implementation",
                    description="追踪Java方法的具体实现，查找上游依赖中的源码",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "项目仓库URL"
                            },
                            "method_signature": {
                                "type": "string",
                                "description": "方法签名，如'StrUtil.format'或'StringUtils.isEmpty'"
                            }
                        },
                        "required": ["repo_url", "method_signature"]
                    }
                ),
                Tool(
                    name="analyze_dependency_chain",
                    description="分析Java类的完整依赖链，追踪多层上游实现",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "项目仓库URL"
                            },
                            "target_class": {
                                "type": "string",
                                "description": "目标类名，如'StrUtil'或'StringUtils'"
                            }
                        },
                        "required": ["repo_url", "target_class"]
                    }
                ),
                Tool(
                    name="smart_code_review",
                    description="智能代码审查工具，自动选择重要文件进行审查，避免上下文过大",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "focus_area": {
                                "type": "string",
                                "description": "审查重点：security(安全), performance(性能), maintainability(可维护性), all(全面)",
                                "enum": ["security", "performance", "maintainability", "all"]
                            },
                            "max_files": {
                                "type": "integer",
                                "description": "最大审查文件数（默认5）",
                                "default": 5
                            }
                        },
                        "required": ["repo_url"]
                    }
                ),
                Tool(
                    name="smart_path_explorer",
                    description="智能路径探索工具，当路径不存在时自动回退到上级目录并提供建议",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "target_path": {
                                "type": "string", 
                                "description": "要探索的目标路径"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url", "target_path"]
                    }
                ),
                Tool(
                    name="intelligent_file_finder",
                    description="智能文件查找工具，基于模式匹配查找文件，避免路径猜测",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "file_pattern": {
                                "type": "string",
                                "description": "文件名或路径模式（如'filter', 'Controller.java'等）"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url", "file_pattern"]
                    }
                ),
                Tool(
                    name="suggest_exploration_path",
                    description="基于目标概念建议探索路径，用于指导源码分析方向",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "repo_url": {
                                "type": "string",
                                "description": "GitHub仓库URL或owner/repo格式"
                            },
                            "current_path": {
                                "type": "string",
                                "description": "当前所在路径"
                            },
                            "target_concept": {
                                "type": "string",
                                "description": "目标概念（如'filter', 'controller', 'security'等）"
                            },
                            "branch": {
                                "type": "string",
                                "description": "分支名（可选，默认为main/master）"
                            }
                        },
                        "required": ["repo_url", "current_path", "target_concept"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """处理工具调用"""
            try:
                if not self.github_client:
                    self.github_client = GitHubClient()
                    self.java_analyzer = JavaDependencyAnalyzer(self.github_client)
                
                if name == "get_repository_info":
                    result = await self.github_client.get_repository_info(arguments["repo_url"])
                elif name == "get_file_content":
                    result = await self.github_client.get_file_content(
                        arguments["repo_url"],
                        arguments["file_path"],
                        arguments.get("branch")
                    )
                elif name == "check_file_exists":
                    result = await self.github_client.check_file_exists(
                        arguments["repo_url"],
                        arguments["file_path"],
                        arguments.get("branch")
                    )
                elif name == "list_directory":
                    result = await self.github_client.list_directory(
                        arguments["repo_url"],
                        arguments.get("directory_path", ""),
                        arguments.get("branch")
                    )
                elif name == "search_code":
                    result = await self.github_client.search_code(
                        arguments["repo_url"],
                        arguments["query"],
                        arguments.get("file_extension"),
                        arguments.get("path_filter")
                    )
                elif name == "get_repository_structure":
                    result = await self.github_client.get_repository_structure(
                        arguments["repo_url"],
                        arguments.get("branch"),
                        arguments.get("max_depth", 3)
                    )
                elif name == "get_branches":
                    result = await self.github_client.get_branches(arguments["repo_url"])
                elif name == "get_commits":
                    result = await self.github_client.get_commits(
                        arguments["repo_url"],
                        arguments.get("branch"),
                        arguments.get("limit", 10)
                    )
                elif name == "get_user_repositories":
                    result = await self.github_client.get_user_repositories(
                        arguments["username"],
                        arguments.get("sort", "updated"),
                        min(arguments.get("per_page", 30), 100)  # 限制最大值为100
                    )

                elif name == "analyze_java_dependencies":
                    result = await self.java_analyzer.analyze_project_dependencies(
                        arguments["repo_url"]
                    )
                elif name == "trace_method_implementation":
                    result = await self.java_analyzer.trace_method_implementation(
                        arguments["repo_url"],
                        arguments["method_signature"]
                    )
                elif name == "analyze_dependency_chain":
                    result = await self.java_analyzer.analyze_dependency_chain(
                        arguments["repo_url"],
                        arguments["target_class"]
                    )
                elif name == "smart_code_review":
                    result = await self.java_analyzer.smart_code_review(
                        arguments["repo_url"],
                        arguments.get("focus_area", "all"),
                        arguments.get("max_files", 5)
                    )
                elif name == "smart_path_explorer":
                    result = await self.github_client.smart_path_explorer(
                        arguments["repo_url"],
                        arguments["target_path"],
                        arguments.get("branch")
                    )
                elif name == "intelligent_file_finder":
                    result = await self.github_client.intelligent_file_finder(
                        arguments["repo_url"],
                        arguments["file_pattern"],
                        arguments.get("branch")
                    )
                elif name == "suggest_exploration_path":
                    result = await self.github_client.suggest_exploration_path(
                        arguments["repo_url"],
                        arguments["current_path"],
                        arguments["target_concept"],
                        arguments.get("branch")
                    )
                else:
                    raise ValueError(f"未知的工具: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
            except Exception as e:
                logger.error(f"工具调用错误 {name}: {str(e)}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]

        @self.server.list_prompts()
        async def handle_list_prompts() -> List[Prompt]:
            """返回可用的提示词模板列表"""
            return [
                Prompt(
                    name="analyze_repository",
                    description="全面分析GitHub仓库的提示词模板",
                    arguments=[
                        {
                            "name": "repo_url",
                            "description": "要分析的GitHub仓库URL或owner/repo格式",
                            "required": True
                        },
                        {
                            "name": "focus_area", 
                            "description": "分析重点：code_quality(代码质量), architecture(架构), security(安全性), performance(性能)",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="code_review",
                    description="代码审查提示词模板",
                    arguments=[
                        {
                            "name": "repo_url",
                            "description": "要审查的GitHub仓库URL",
                            "required": True
                        },
                        {
                            "name": "file_path",
                            "description": "特定文件路径（可选）",
                            "required": False
                        }
                    ]
                ),
                Prompt(
                    name="tech_stack_analysis", 
                    description="技术栈分析提示词模板",
                    arguments=[
                        {
                            "name": "repo_url",
                            "description": "要分析的GitHub仓库URL",
                            "required": True
                        }
                    ]
                )
            ]

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, Any]) -> str:
            """根据名称和参数生成具体的提示词"""
            repo_url = arguments.get("repo_url", "")
            
            if name == "analyze_repository":
                focus_area = arguments.get("focus_area", "comprehensive")
                focus_prompts = {
                    "code_quality": "重点关注代码质量，包括：代码规范、可读性、可维护性",
                    "architecture": "重点关注架构设计，包括：模块划分、设计模式、系统架构",
                    "security": "重点关注安全问题，包括：依赖安全、代码安全、配置安全",
                    "performance": "重点关注性能优化，包括：算法效率、资源使用、性能瓶颈",
                    "comprehensive": "进行全面分析，包括代码质量、架构设计、安全性和性能"
                }
                focus_text = focus_prompts.get(focus_area, focus_prompts["comprehensive"])
                
                return f"""请作为一名资深软件工程师，全面分析GitHub仓库 {repo_url}。

分析要求：
{focus_text}

请按以下步骤进行分析：
1. 首先获取仓库基本信息，了解项目概况
2. 查看项目结构，理解代码组织方式
3. 分析主要文件和核心代码逻辑
4. 检查依赖关系和技术栈选择
5. 评估项目的维护状态和活跃度

最后请给出：
- 项目亮点和优势
- 存在的问题和改进建议  
- 技术栈评价和建议
- 整体评分（1-10分）

请使用提供的MCP工具来获取仓库信息，不要编造数据。"""

            elif name == "code_review":
                file_path = arguments.get("file_path", "")
                if file_path:
                    return f"""请对GitHub仓库 {repo_url} 中的文件 {file_path} 进行详细的代码审查。

⚠️ 重要提示：在获取文件内容前，请务必：
1. 使用 check_file_exists() 确认文件是否存在
2. 如果文件不存在，使用 smart_path_explorer() 智能探索正确路径
3. 或使用 intelligent_file_finder() 按模式查找文件

审查重点：
1. 代码质量：语法规范、命名规范、注释质量
2. 逻辑设计：算法效率、错误处理、边界条件
3. 安全问题：输入验证、权限控制、敏感信息处理
4. 可维护性：代码结构、模块化、可扩展性

请给出具体的改进建议和最佳实践推荐。"""
                else:
                    return f"""请对GitHub仓库 {repo_url} 进行全面的代码审查。

🔍 **智能审查流程**（重要！避免路径猜测错误）：

第1步：【项目结构了解】
- 使用 get_repository_structure() 了解项目整体结构

第2步：【智能路径探索】
- 如果要查找特定功能（如filter、controller等），使用 suggest_exploration_path() 获取建议路径
- 如果路径不存在，使用 smart_path_explorer() 自动回退并找到正确路径
- 使用 intelligent_file_finder() 按文件名模式查找

第3步：【文件存在性确认】
- 使用 check_file_exists() 确认要审查的文件是否存在

第4步：【智能审查】
- 推荐使用 smart_code_review() 工具进行高效审查
- 或基于确认存在的路径进行详细分析

⚠️ **严禁直接猜测文件路径！** 
❌ 不要直接调用 get_file_content("repo", "猜测的路径")
✅ 先用智能探索工具确认路径存在性

🛠️ **推荐工具组合**：
1. get_repository_structure → 了解结构
2. suggest_exploration_path → 获取建议路径  
3. smart_path_explorer → 智能探索
4. check_file_exists → 验证存在性
5. get_file_content → 获取内容

审查重点：
- 代码规范和最佳实践
- 潜在的bug和安全问题
- 性能优化机会
- 架构改进建议

💡 这样可以避免404错误，确保分析的连续性！"""

            elif name == "tech_stack_analysis":
                return f"""请分析GitHub仓库 {repo_url} 的技术栈选择。

分析维度：
1. 技术栈识别：主要编程语言、框架、库和工具
2. 合理性评估：技术选择是否适合项目需求
3. 现代化程度：技术栈是否跟上最新发展
4. 生态系统：社区支持、文档完整性、长期维护性

请提供：
- 当前技术栈清单
- 优势和劣势分析
- 升级或替换建议
- 同类项目技术栈对比

请使用仓库分析工具获取准确信息，不要基于猜测。"""


            
            else:
                return f"未知的提示词模板: {name}"

    async def run(self):
        """运行MCP服务器"""
        # 验证GitHub Token
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            logger.error("未找到GITHUB_TOKEN环境变量，请设置GitHub Personal Access Token")
            sys.exit(1)
            
        logger.info("启动GitHub MCP服务器...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="github-mcp",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools={},
                        prompts={}
                    ),
                ),
            )

def main():
    """主函数"""
    server = GitHubMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main() 