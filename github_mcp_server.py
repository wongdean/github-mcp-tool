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
from urllib.parse import urlparse

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from loguru import logger

from github_client import GitHubClient

# 加载环境变量
load_dotenv()

# 配置日志
logger.add(sys.stderr, level="INFO")

class GitHubMCPServer:
    """GitHub MCP服务器类"""
    
    def __init__(self):
        self.server = Server("github-mcp")
        self.github_client: Optional[GitHubClient] = None
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
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
            """处理工具调用"""
            try:
                if not self.github_client:
                    self.github_client = GitHubClient()
                
                if name == "get_repository_info":
                    result = await self.github_client.get_repository_info(arguments["repo_url"])
                elif name == "get_file_content":
                    result = await self.github_client.get_file_content(
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
                else:
                    raise ValueError(f"未知的工具: {name}")
                
                return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                
            except Exception as e:
                logger.error(f"工具调用错误 {name}: {str(e)}")
                return [TextContent(type="text", text=f"错误: {str(e)}")]

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
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

def main():
    """主函数"""
    server = GitHubMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main() 