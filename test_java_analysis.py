#!/usr/bin/env python3
"""
测试Java依赖分析功能
"""

import asyncio
import os
from dotenv import load_dotenv
from github_client import GitHubClient
from java_dependency_analyzer import JavaDependencyAnalyzer

async def test_java_analysis():
    """测试Java依赖分析功能"""
    load_dotenv()
    
    print("🧪 Java依赖分析功能测试")
    print("=" * 50)
    
    # 初始化客户端
    github_client = GitHubClient(os.getenv("GITHUB_TOKEN"))
    analyzer = JavaDependencyAnalyzer(github_client)
    
    # 测试1：分析RuoYi项目的依赖
    print("\n🎯 测试1: 分析RuoYi项目的Maven依赖")
    try:
        deps = await analyzer.analyze_project_dependencies("yangzongzhuan/RuoYi")
        print(f"✅ 发现 {deps['dependency_count']} 个依赖")
        
        # 显示前5个依赖
        print("📦 主要依赖:")
        for i, dep in enumerate(deps['dependencies'][:5], 1):
            print(f"  {i}. {dep['group_id']}:{dep['artifact_id']}:{dep['version']}")
            if dep['github_repo']:
                print(f"     → GitHub: {dep['github_repo']}")
        
    except Exception as e:
        print(f"❌ 测试1失败: {e}")
    
    # 测试2：追踪Hutool的StrUtil.format方法
    print("\n🎯 测试2: 追踪StrUtil.format方法实现")
    try:
        trace = await analyzer.trace_method_implementation("yangzongzhuan/RuoYi", "StrUtil.format")
        print(f"✅ 方法来源: {trace['source_package']}")
        print(f"✅ 上游仓库: {trace['upstream_repo']}")
        
        if trace['usage_locations']:
            print("📍 使用位置:")
            for loc in trace['usage_locations'][:3]:
                print(f"  - {loc['file']}:{loc['line_number']}")
        
        if trace['implementation']:
            print("🔍 上游实现:")
            impl = trace['implementation']
            print(f"  文件: {impl.get('file_path', 'unknown')}")
            print(f"  代码片段: {impl.get('implementation', '')[:200]}...")
        
    except Exception as e:
        print(f"❌ 测试2失败: {e}")
    
    # 测试3：分析Spring Boot项目依赖
    print("\n🎯 测试3: 分析Spring Boot项目")
    try:
        deps = await analyzer.analyze_project_dependencies("spring-projects/spring-boot")
        print(f"✅ Spring Boot项目有 {deps['dependency_count']} 个依赖")
        
        # 统计依赖来源
        sources = {}
        for dep in deps['dependencies']:
            group = dep['group_id'].split('.')[0]
            sources[group] = sources.get(group, 0) + 1
        
        print("📊 依赖来源统计:")
        for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {source}: {count}个依赖")
            
    except Exception as e:
        print(f"❌ 测试3失败: {e}")
    
    # 测试4：依赖链分析（如果实现了的话）
    print("\n🎯 测试4: 依赖链分析")
    try:
        chain = await analyzer.analyze_dependency_chain("yangzongzhuan/RuoYi", "StrUtil")
        print(f"✅ 依赖链长度: {chain['chain_length']}")
        
        for level in chain['dependency_chain']:
            print(f"  第{level['level']}层: {level['class']} in {level['repository']}")
            
    except Exception as e:
        print(f"❌ 测试4失败: {e}")
    
    print("\n🎉 Java依赖分析功能测试完成！")

# Cherry Studio 演示用例
def generate_demo_queries():
    """生成Cherry Studio演示用的查询示例"""
    print("\n🍒 Cherry Studio演示查询示例")
    print("=" * 50)
    
    queries = [
        {
            "title": "分析Java项目依赖",
            "query": "帮我分析 yangzongzhuan/RuoYi 这个Java项目的依赖关系，我想了解它用了哪些第三方库",
            "expected_tools": ["analyze_java_dependencies"]
        },
        {
            "title": "追踪方法实现",
            "query": "在RuoYi项目中，StrUtil.format这个方法具体是怎么实现的？请帮我追踪到源码",
            "expected_tools": ["trace_method_implementation"]
        },
        {
            "title": "依赖链分析",
            "query": "分析StringUtils这个工具类的完整依赖链，看看它最终依赖了哪些基础库",
            "expected_tools": ["analyze_dependency_chain"]
        },
        {
            "title": "综合分析",
            "query": "我想了解Hutool这个工具包，请分析它的项目结构和主要功能模块",
            "expected_tools": ["get_repository_info", "get_repository_structure", "analyze_java_dependencies"]
        }
    ]
    
    for i, demo in enumerate(queries, 1):
        print(f"\n📝 演示{i}: {demo['title']}")
        print(f"用户输入: \"{demo['query']}\"")
        print(f"预期调用: {', '.join(demo['expected_tools'])}")

if __name__ == "__main__":
    asyncio.run(test_java_analysis())
    generate_demo_queries() 