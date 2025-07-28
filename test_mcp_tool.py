#!/usr/bin/env python3
"""
GitHub MCP工具测试脚本
用于验证工具的基本功能
"""

import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from github_client import GitHubClient

async def test_github_client():
    """测试GitHub客户端基本功能"""
    
    print("🔍 测试GitHub MCP工具...")
    
    # 检查Token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ 错误: 未找到GITHUB_TOKEN环境变量")
        print("请先配置GitHub Personal Access Token:")
        print("1. 复制config_template.env为.env")
        print("2. 在.env文件中设置GITHUB_TOKEN")
        return False
    
    try:
        client = GitHubClient(token)
        print("✅ GitHub客户端初始化成功")
        
        # 测试获取仓库信息
        print("\n📋 测试获取仓库信息...")
        repo_info = await client.get_repository_info("octocat/Hello-World")
        print(f"✅ 仓库名称: {repo_info['name']}")
        print(f"✅ 描述: {repo_info['description']}")
        print(f"✅ 星标数: {repo_info['stars']}")
        
        # 测试获取文件内容
        print("\n📄 测试获取文件内容...")
        file_content = await client.get_file_content("octocat/Hello-World", "README")
        print(f"✅ 文件路径: {file_content['path']}")
        print(f"✅ 文件大小: {file_content['size']} bytes")
        print(f"✅ 内容预览: {file_content['content'][:100]}...")
        
        # 测试列出目录
        print("\n📁 测试列出目录内容...")
        directory = await client.list_directory("octocat/Hello-World")
        print(f"✅ 文件数量: {len(directory['files'])}")
        print(f"✅ 目录数量: {len(directory['directories'])}")
        if directory['files']:
            print(f"✅ 第一个文件: {directory['files'][0]['name']}")
        
        # 测试获取分支
        print("\n🌿 测试获取分支列表...")
        branches = await client.get_branches("octocat/Hello-World")
        print(f"✅ 默认分支: {branches['default_branch']}")
        print(f"✅ 总分支数: {branches['total_branches']}")
        
        # 测试获取提交历史
        print("\n📝 测试获取提交历史...")
        commits = await client.get_commits("octocat/Hello-World", limit=3)
        print(f"✅ 获取到 {len(commits['commits'])} 个提交")
        if commits['commits']:
            latest = commits['commits'][0]
            print(f"✅ 最新提交: {latest['message'][:50]}...")
            print(f"✅ 作者: {latest['author']['name']}")
        
        print("\n🎉 所有测试通过！GitHub MCP工具运行正常。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def test_mcp_tools_info():
    """显示可用的MCP工具信息"""
    print("\n🛠️  可用的MCP工具:")
    tools = [
        ("get_repository_info", "获取GitHub仓库基本信息"),
        ("get_file_content", "读取仓库中的文件内容"),
        ("list_directory", "列出目录中的文件和子目录"),
        ("search_code", "在仓库中搜索代码内容"),
        ("get_repository_structure", "获取仓库的完整目录结构"),
        ("get_branches", "获取仓库的所有分支"),
        ("get_commits", "获取仓库的提交历史")
    ]
    
    for tool_name, description in tools:
        print(f"  • {tool_name}: {description}")
    
    print("\n💡 使用示例:")
    print("通过MCP协议调用这些工具来实现AI辅助的代码阅读和问答功能。")

async def main():
    """主测试函数"""
    print("=" * 60)
    print("GitHub MCP工具 - 功能测试")
    print("=" * 60)
    
    # 显示工具信息
    test_mcp_tools_info()
    
    # 运行基本功能测试
    success = await test_github_client()
    
    if success:
        print("\n🚀 工具已准备就绪，可以启动MCP服务器：")
        print("   python github_mcp_server.py")
    else:
        print("\n⚠️  请修复上述问题后重新测试。")

if __name__ == "__main__":
    asyncio.run(main()) 