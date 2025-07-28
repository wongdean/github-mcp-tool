#!/usr/bin/env python3
"""
简单的GitHub API客户端测试脚本
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from simple_github_client import SimpleGitHubClient

async def test_github_client():
    """测试GitHub客户端基本功能"""
    
    print("🔍 测试简化版GitHub API客户端...")
    
    # 检查Token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ 错误: 未找到GITHUB_TOKEN环境变量")
        print("请先配置GitHub Personal Access Token:")
        print("1. 复制config_template.env为.env")
        print("2. 在.env文件中设置GITHUB_TOKEN=your_token_here")
        return False
    
    try:
        client = SimpleGitHubClient(token)
        print("✅ GitHub客户端初始化成功")
        
        # 使用一个知名的小仓库进行测试
        test_repo = "octocat/Hello-World"
        
        # 测试获取仓库信息
        print(f"\n📋 测试获取仓库信息: {test_repo}")
        repo_info = await client.get_repository_info(test_repo)
        print(f"✅ 仓库名称: {repo_info['name']}")
        print(f"✅ 描述: {repo_info['description']}")
        print(f"✅ 主要语言: {repo_info['language']}")
        print(f"✅ 星标数: {repo_info['stars']}")
        print(f"✅ 默认分支: {repo_info['default_branch']}")
        
        # 测试列出目录
        print(f"\n📁 测试列出根目录内容...")
        directory = await client.list_directory(test_repo)
        print(f"✅ 找到 {len(directory['files'])} 个文件")
        print(f"✅ 找到 {len(directory['directories'])} 个目录")
        if directory['files']:
            print(f"✅ 文件示例: {directory['files'][0]['name']}")
        
        # 测试获取文件内容
        if directory['files']:
            test_file = directory['files'][0]['path']
            print(f"\n📄 测试获取文件内容: {test_file}")
            file_content = await client.get_file_content(test_repo, test_file)
            print(f"✅ 文件大小: {file_content['size']} bytes")
            print(f"✅ 内容预览: {file_content['content'][:100]}...")
        
        # 测试获取分支
        print(f"\n🌿 测试获取分支列表...")
        branches = await client.get_branches(test_repo)
        print(f"✅ 默认分支: {branches['default_branch']}")
        print(f"✅ 总分支数: {branches['total_branches']}")
        if branches['branches']:
            print(f"✅ 分支示例: {branches['branches'][0]['name']}")
        
        # 测试获取提交历史
        print(f"\n📝 测试获取提交历史...")
        commits = await client.get_commits(test_repo, limit=3)
        print(f"✅ 获取到 {len(commits['commits'])} 个提交")
        if commits['commits']:
            latest = commits['commits'][0]
            print(f"✅ 最新提交: {latest['message'][:50]}...")
            print(f"✅ 作者: {latest['author']['name']}")
        
        print("\n🎉 所有测试通过！GitHub API客户端工作正常。")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("GitHub API客户端 - 功能测试")
    print("=" * 60)
    
    success = await test_github_client()
    
    if success:
        print("\n🚀 客户端已准备就绪！")
        print("\n可以启动API服务器：")
        print("   python github_api_server.py")
        print("\n或者访问API文档：")
        print("   http://localhost:8000/docs")
    else:
        print("\n⚠️  请修复上述问题后重新测试。")

if __name__ == "__main__":
    asyncio.run(main()) 