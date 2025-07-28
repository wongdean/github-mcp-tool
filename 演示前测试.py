#!/usr/bin/env python3
"""
演示前快速测试脚本
确保所有功能正常，避免演示时出问题
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from github_client import GitHubClient

class DemoTest:
    def __init__(self):
        print("🔧 演示前功能测试")
        print("=" * 50)
        
        # 检查Token
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            print("❌ 错误：未设置GITHUB_TOKEN环境变量")
            sys.exit(1)
        
        self.client = GitHubClient(self.token)
        self.test_results = []
    
    def add_result(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅" if success else "❌"
        self.test_results.append({
            "name": test_name,
            "success": success,
            "message": message
        })
        print(f"{status} {test_name}: {message}")
    
    async def test_basic_functions(self):
        """测试基础功能"""
        print("\n📊 测试基础功能...")
        
        # 测试1：获取仓库信息
        try:
            repo_info = await self.client.get_repository_info("microsoft/vscode")
            if repo_info.get("name") == "vscode":
                self.add_result("获取仓库信息", True, f"VS Code有{repo_info.get('stars', 0):,}个star")
            else:
                self.add_result("获取仓库信息", False, "返回数据异常")
        except Exception as e:
            self.add_result("获取仓库信息", False, str(e)[:50])
        
        # 测试2：获取项目结构
        try:
            structure = await self.client.get_repository_structure("microsoft/vscode", max_depth=1)
            if structure.get("directories"):
                self.add_result("获取项目结构", True, f"发现{len(structure['directories'])}个目录")
            else:
                self.add_result("获取项目结构", False, "未获取到目录信息")
        except Exception as e:
            self.add_result("获取项目结构", False, str(e)[:50])
        
        # 测试3：获取提交历史
        try:
            commits = await self.client.get_commits("microsoft/vscode", limit=3)
            if commits and len(commits) > 0:
                self.add_result("获取提交历史", True, f"获取到{len(commits)}个最新提交")
            else:
                self.add_result("获取提交历史", False, "未获取到提交信息")
        except Exception as e:
            self.add_result("获取提交历史", False, str(e)[:50])
    
    async def test_advanced_functions(self):
        """测试高级功能"""
        print("\n🚀 测试高级功能...")
        
        # 测试4：获取用户仓库
        try:
            user_repos = await self.client.get_user_repositories("wongdean", per_page=5)
            if user_repos.get("repositories"):
                self.add_result("获取用户仓库", True, f"用户有{len(user_repos['repositories'])}个仓库")
            else:
                self.add_result("获取用户仓库", False, "未获取到用户仓库")
        except Exception as e:
            self.add_result("获取用户仓库", False, str(e)[:50])
        

    
    async def test_demo_scenarios(self):
        """测试演示场景"""
        print("\n🎪 测试演示场景...")
        
        # 演示场景1：VS Code分析
        try:
            vscode_info = await self.client.get_repository_info("microsoft/vscode")
            vscode_structure = await self.client.get_repository_structure("microsoft/vscode", max_depth=1)
            
            if vscode_info and vscode_structure:
                self.add_result("VS Code演示场景", True, "完整信息获取成功")
            else:
                self.add_result("VS Code演示场景", False, "信息获取不完整")
        except Exception as e:
            self.add_result("VS Code演示场景", False, str(e)[:50])
        
        # 演示场景2：Vue vs React对比
        try:
            vue_info = await self.client.get_repository_info("vuejs/vue")
            react_info = await self.client.get_repository_info("facebook/react")
            
            if vue_info and react_info:
                vue_stars = vue_info.get('stars', 0)
                react_stars = react_info.get('stars', 0)
                self.add_result("Vue vs React对比", True, f"Vue:{vue_stars:,} vs React:{react_stars:,}")
            else:
                self.add_result("Vue vs React对比", False, "对比数据获取失败")
        except Exception as e:
            self.add_result("Vue vs React对比", False, str(e)[:50])
    
    def test_mcp_server(self):
        """测试MCP服务器文件"""
        print("\n⚙️  测试MCP服务器...")
        
        # 检查必要文件
        files_to_check = [
            "github_mcp_server.py",
            "github_client.py", 
            "requirements.txt",
            ".env"
        ]
        
        for file in files_to_check:
            if os.path.exists(file):
                self.add_result(f"文件检查: {file}", True, "文件存在")
            else:
                self.add_result(f"文件检查: {file}", False, "文件不存在")
        
        # 检查配置文件
        if os.path.exists("cherry_studio_config.json"):
            self.add_result("Cherry Studio配置", True, "配置文件已准备")
        else:
            self.add_result("Cherry Studio配置", False, "配置文件缺失")
    
    def generate_report(self):
        """生成测试报告"""
        print("\n📊 测试报告")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n失败的测试:")
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            for test in failed_tests:
                print(f"❌ {test['name']}: {test['message']}")
        else:
            print("✅ 所有测试都通过了！")
        
        print("\n🎯 演示建议:")
        if passed_tests >= total_tests * 0.8:
            print("✅ 系统状态良好，可以进行演示")
            print("🎪 建议重点演示以下通过的功能:")
            for test in self.test_results:
                if test["success"] and "演示场景" in test["name"]:
                    print(f"   • {test['name']}")
        else:
            print("⚠️  部分功能存在问题，建议:")
            print("1. 检查网络连接")
            print("2. 验证GitHub Token权限")
            print("3. 使用demo_data.json作为备用方案")

async def main():
    """主测试函数"""
    tester = DemoTest()
    
    # 测试文件和配置
    tester.test_mcp_server()
    
    # 测试基础功能
    await tester.test_basic_functions()
    
    # 测试高级功能
    await tester.test_advanced_functions()
    
    # 测试演示场景
    await tester.test_demo_scenarios()
    
    # 生成报告
    tester.generate_report()
    
    print("\n🎉 测试完成！准备好进行精彩的演示了！")

if __name__ == "__main__":
    asyncio.run(main()) 