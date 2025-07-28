#!/usr/bin/env python3
"""
Java代码依赖分析器
追踪Java项目中的包依赖关系，查找上游代码实现
"""

import re
import asyncio
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from github_client import GitHubClient

@dataclass
class Dependency:
    group_id: str
    artifact_id: str
    version: str
    github_repo: Optional[str] = None

@dataclass
class MethodTrace:
    method_name: str
    class_name: str
    package: str
    source_file: str
    implementation: str
    upstream_repo: Optional[str] = None

class JavaDependencyAnalyzer:
    def __init__(self, github_client: GitHubClient):
        self.github_client = github_client
        # 常见Java库的GitHub映射
        self.package_repo_mapping = {
            'cn.hutool': 'hutool/hutool',
            'org.springframework': 'spring-projects/spring-framework', 
            'org.apache.commons': 'apache/commons-lang',
            'com.fasterxml.jackson': 'FasterXML/jackson-core',
            'org.mybatis': 'mybatis/mybatis-3',
            'com.baomidou': 'baomidou/mybatis-plus',
            'org.slf4j': 'qos-ch/slf4j',
            'ch.qos.logback': 'qos-ch/logback'
        }
    
    async def analyze_project_dependencies(self, repo_url: str) -> Dict:
        """分析Java项目的依赖关系"""
        print(f"🔍 分析项目依赖: {repo_url}")
        
        # 1. 获取项目结构
        structure = await self.github_client.get_repository_structure(repo_url)
        
        # 2. 查找构建文件
        build_files = self._find_build_files(structure)
        
        # 3. 解析依赖
        dependencies = []
        for build_file in build_files:
            if build_file.endswith('pom.xml'):
                deps = await self._parse_maven_dependencies(repo_url, build_file)
                dependencies.extend(deps)
            elif build_file.endswith('build.gradle'):
                deps = await self._parse_gradle_dependencies(repo_url, build_file)
                dependencies.extend(deps)
        
        # 4. 映射到GitHub仓库
        for dep in dependencies:
            dep.github_repo = self._map_to_github_repo(dep)
        
        return {
            "project": repo_url,
            "build_files": build_files,
            "dependencies": [
                {
                    "group_id": dep.group_id,
                    "artifact_id": dep.artifact_id, 
                    "version": dep.version,
                    "github_repo": dep.github_repo
                } for dep in dependencies
            ],
            "dependency_count": len(dependencies)
        }
    
    async def trace_method_implementation(self, repo_url: str, method_signature: str) -> Dict:
        """追踪方法的具体实现"""
        print(f"🔎 追踪方法实现: {method_signature} in {repo_url}")
        
        # 1. 在当前项目中搜索方法调用
        usage_results = await self._search_method_usage(repo_url, method_signature)
        
        # 2. 分析import语句，确定来源包
        source_package = await self._identify_source_package(repo_url, method_signature)
        
        # 3. 查找上游实现
        implementation = None
        if source_package and source_package in self.package_repo_mapping:
            upstream_repo = self.package_repo_mapping[source_package]
            implementation = await self._find_upstream_implementation(
                upstream_repo, method_signature
            )
        
        return {
            "method": method_signature,
            "project": repo_url,
            "usage_locations": usage_results,
            "source_package": source_package,
            "upstream_repo": self.package_repo_mapping.get(source_package),
            "implementation": implementation
        }
    
    async def analyze_dependency_chain(self, repo_url: str, target_class: str) -> Dict:
        """分析某个类的完整依赖链"""
        print(f"🔗 分析依赖链: {target_class} in {repo_url}")
        
        chain = []
        current_repo = repo_url
        current_class = target_class
        
        # 最多追踪5层依赖，避免无限循环
        for level in range(5):
            print(f"  📍 第{level+1}层: 在 {current_repo} 中查找 {current_class}")
            
            # 搜索类的定义
            class_info = await self._find_class_definition(current_repo, current_class)
            if not class_info:
                break
            
            chain.append({
                "level": level + 1,
                "repository": current_repo,
                "class": current_class,
                "file_path": class_info.get("file_path"),
                "implementation_snippet": class_info.get("code_snippet", "")[:500]
            })
            
            # 查找这个类的上游依赖
            upstream = await self._find_upstream_dependency(current_repo, current_class)
            if not upstream:
                break
                
            current_repo = upstream["repo"]
            current_class = upstream["class"]
        
        return {
            "target_class": target_class,
            "original_repo": repo_url,
            "dependency_chain": chain,
            "chain_length": len(chain)
        }
    
    def _find_build_files(self, structure: Dict) -> List[str]:
        """查找构建配置文件"""
        build_files = []
        
        # 检查根目录文件
        for file in structure.get("files", []):
            if file["name"] in ["pom.xml", "build.gradle", "build.gradle.kts"]:
                build_files.append(file["path"])
        
        return build_files
    
    async def _parse_maven_dependencies(self, repo_url: str, pom_path: str) -> List[Dependency]:
        """解析Maven依赖"""
        try:
            # 读取pom.xml文件
            pom_content = await self.github_client.get_file_content(repo_url, pom_path)
            
            # 解析XML
            root = ET.fromstring(pom_content)
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            dependencies = []
            deps_element = root.find('.//maven:dependencies', namespace)
            if deps_element is not None:
                for dep in deps_element.findall('maven:dependency', namespace):
                    group_id = dep.find('maven:groupId', namespace)
                    artifact_id = dep.find('maven:artifactId', namespace)
                    version = dep.find('maven:version', namespace)
                    
                    if group_id is not None and artifact_id is not None:
                        dependencies.append(Dependency(
                            group_id=group_id.text,
                            artifact_id=artifact_id.text,
                            version=version.text if version is not None else "unknown"
                        ))
            
            return dependencies
            
        except Exception as e:
            print(f"❌ 解析Maven依赖失败: {e}")
            return []
    
    async def _parse_gradle_dependencies(self, repo_url: str, gradle_path: str) -> List[Dependency]:
        """解析Gradle依赖（基础实现）"""
        try:
            gradle_content = await self.github_client.get_file_content(repo_url, gradle_path)
            
            dependencies = []
            # 简单的正则匹配，实际项目中可能需要更复杂的解析
            patterns = [
                r"implementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                r"compile\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, gradle_content)
                for match in matches:
                    dependencies.append(Dependency(
                        group_id=match[0],
                        artifact_id=match[1],
                        version=match[2]
                    ))
            
            return dependencies
            
        except Exception as e:
            print(f"❌ 解析Gradle依赖失败: {e}")
            return []
    
    def _map_to_github_repo(self, dependency: Dependency) -> Optional[str]:
        """将Maven坐标映射到GitHub仓库"""
        # 尝试精确匹配
        if dependency.group_id in self.package_repo_mapping:
            return self.package_repo_mapping[dependency.group_id]
        
        # 尝试前缀匹配
        for package, repo in self.package_repo_mapping.items():
            if dependency.group_id.startswith(package):
                return repo
        
        return None
    
    async def _search_method_usage(self, repo_url: str, method_signature: str) -> List[Dict]:
        """搜索方法在项目中的使用位置"""
        try:
            # 提取方法名（简单处理）
            method_name = method_signature.split('(')[0].split('.')[-1]
            
            # 在代码中搜索方法调用
            search_results = await self.github_client.search_code(repo_url, method_name)
            
            usage_locations = []
            # search_results是字典，需要访问"results"键
            results_list = search_results.get("results", [])
            for result in results_list[:5]:  # 只取前5个结果
                usage_locations.append({
                    "file": result.get("path", ""),
                    "line_number": result.get("line_number", 0),
                    "code_snippet": result.get("content", "")[:200]
                })
            
            return usage_locations
            
        except Exception as e:
            print(f"❌ 搜索方法使用失败: {e}")
            return []
    
    async def _identify_source_package(self, repo_url: str, method_signature: str) -> Optional[str]:
        """识别方法来源的包"""
        try:
            # 简化实现：基于方法名推断
            if "StrUtil" in method_signature:
                return "cn.hutool"
            elif "StringUtils" in method_signature:
                return "org.apache.commons"
            elif "ObjectMapper" in method_signature:
                return "com.fasterxml.jackson"
            # 可以扩展更多规则
            
            return None
            
        except Exception as e:
            print(f"❌ 识别源包失败: {e}")
            return None
    
    async def _find_upstream_implementation(self, upstream_repo: str, method_signature: str) -> Optional[Dict]:
        """在上游仓库中查找方法实现"""
        try:
            method_name = method_signature.split('(')[0].split('.')[-1]
            class_name = method_signature.split('.')[0]
            
            # 搜索方法定义
            search_results = await self.github_client.search_code(
                upstream_repo, f"public.*{method_name}.*("
            )
            
            # search_results是字典，需要访问"results"键
            results_list = search_results.get("results", [])
            if results_list:
                best_match = results_list[0]
                return {
                    "file_path": best_match.get("path", ""),
                    "line_number": best_match.get("line_number", 0),
                    "implementation": best_match.get("content", "")[:1000]
                }
            
            return None
            
        except Exception as e:
            print(f"❌ 查找上游实现失败: {e}")
            return None
    
    async def _find_class_definition(self, repo_url: str, class_name: str) -> Optional[Dict]:
        """查找类的定义"""
        try:
            # 搜索类定义
            search_results = await self.github_client.search_code(
                repo_url, f"class {class_name}"
            )
            
            # search_results是字典，需要访问"results"键
            results_list = search_results.get("results", [])
            if results_list:
                result = results_list[0]
                # 尝试获取完整文件内容
                file_content = await self.github_client.get_file_content(
                    repo_url, result.get("path", "")
                )
                
                return {
                    "file_path": result.get("path", ""),
                    "code_snippet": file_content[:2000] if file_content else ""
                }
            
            return None
            
        except Exception as e:
            print(f"❌ 查找类定义失败: {e}")
            return None
    
    async def _find_upstream_dependency(self, repo_url: str, class_name: str) -> Optional[Dict]:
        """查找类的上游依赖"""
        # 这里需要更复杂的逻辑来分析import语句和依赖关系
        # 简化实现，返回None表示没有更上游的依赖
        return None

# 使用示例
async def demo_java_analysis():
    """演示Java依赖分析功能"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    github_client = GitHubClient(os.getenv("GITHUB_TOKEN"))
    analyzer = JavaDependencyAnalyzer(github_client)
    
    # 示例1：分析RuoYi项目的依赖
    print("🎯 示例1: 分析RuoYi项目依赖")
    ruoyi_deps = await analyzer.analyze_project_dependencies("yangzongzhuan/RuoYi")
    print(f"发现 {ruoyi_deps['dependency_count']} 个依赖")
    
    # 示例2：追踪StrUtil.format方法
    print("\n🎯 示例2: 追踪StrUtil.format方法")
    method_trace = await analyzer.trace_method_implementation(
        "yangzongzhuan/RuoYi", "StrUtil.format"
    )
    print(f"方法来源包: {method_trace['source_package']}")
    print(f"上游仓库: {method_trace['upstream_repo']}")

if __name__ == "__main__":
    asyncio.run(demo_java_analysis()) 