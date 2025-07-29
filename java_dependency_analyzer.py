#!/usr/bin/env python3
"""
Java代码依赖分析器
追踪Java项目中的包依赖关系，查找上游代码实现
"""

import re
import asyncio
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
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
    
    async def analyze_dependency_chain(self, repo_url: str, target_class: str) -> Dict[str, Any]:
        """分析类的完整依赖链"""
        try:
            print(f"🔍 开始分析 {target_class} 的完整依赖链...")
            
            dependency_chain = []
            visited_classes = set()
            
            async def trace_class(class_name: str, depth: int = 0) -> Optional[Dict]:
                if depth > 5 or class_name in visited_classes:  # 防止无限递归
                    return None
                
                visited_classes.add(class_name)
                print(f"{'  ' * depth}📋 分析类: {class_name}")
                
                # 查找类定义
                class_info = await self._find_class_definition(repo_url, class_name)
                if not class_info:
                    return None
                
                # 查找上游依赖
                upstream = await self._find_upstream_dependency(repo_url, class_name)
                
                result = {
                    "class_name": class_name,
                    "depth": depth,
                    "file_path": class_info.get("file_path"),
                    "code_snippet": class_info.get("code_snippet", "")[:1000],  # 限制代码片段长度
                    "upstream_dependencies": []
                }
                
                if upstream:
                    upstream_result = await trace_class(upstream.get("class_name"), depth + 1)
                    if upstream_result:
                        result["upstream_dependencies"].append(upstream_result)
                
                return result
            
            # 开始追踪
            root_analysis = await trace_class(target_class)
            
            return {
                "target_class": target_class,
                "repository": repo_url,
                "dependency_chain": root_analysis,
                "total_classes_analyzed": len(visited_classes),
                "max_depth_reached": 5
            }
            
        except Exception as e:
            print(f"❌ 依赖链分析失败: {e}")
            return {
                "error": str(e),
                "target_class": target_class,
                "repository": repo_url
            }
    
    async def smart_code_review(self, repo_url: str, focus_area: str = "all", max_files: int = 5) -> Dict[str, Any]:
        """智能代码审查，自动选择重要文件"""
        try:
            print(f"🔍 开始智能代码审查: {repo_url}")
            
            # 1. 获取仓库结构
            structure = await self.github_client.get_repository_structure(repo_url, max_depth=2)
            
            # 2. 识别重要文件
            important_files = self._identify_important_files(structure, focus_area, max_files)
            
            # 3. 分析选中的文件
            review_results = []
            total_size = 0
            MAX_TOTAL_SIZE = 200000  # 总字符数限制
            
            for file_info in important_files:
                if total_size > MAX_TOTAL_SIZE:
                    break
                    
                try:
                    file_content = await self.github_client.get_file_content(
                        repo_url, file_info["path"]
                    )
                    
                    if not file_content.get("truncated", False):
                        content_size = len(file_content.get("content", ""))
                        if total_size + content_size <= MAX_TOTAL_SIZE:
                            review_results.append({
                                "file": file_info,
                                "content": file_content,
                                "priority": file_info.get("priority", "medium")
                            })
                            total_size += content_size
                        else:
                            # 文件过大，只包含摘要信息
                            review_results.append({
                                "file": file_info,
                                "content": {
                                    "path": file_content["path"],
                                    "size": file_content["size"],
                                    "content": "[文件已跳过: 会导致上下文过大]",
                                    "truncated": True
                                },
                                "priority": file_info.get("priority", "medium")
                            })
                    else:
                        review_results.append({
                            "file": file_info,
                            "content": file_content,
                            "priority": file_info.get("priority", "medium")
                        })
                        
                except Exception as e:
                    print(f"⚠️ 无法获取文件 {file_info['path']}: {e}")
                    continue
            
            return {
                "repository": repo_url,
                "focus_area": focus_area,
                "files_reviewed": len(review_results),
                "total_context_size": total_size,
                "review_data": review_results,
                "recommendations": self._generate_review_recommendations(focus_area),
                "context_safe": total_size <= MAX_TOTAL_SIZE
            }
            
        except Exception as e:
            print(f"❌ 智能代码审查失败: {e}")
            return {
                "error": str(e),
                "repository": repo_url,
                "focus_area": focus_area
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

    def _identify_important_files(self, structure: Dict, focus_area: str, max_files: int) -> List[Dict]:
        """识别重要文件进行审查"""
        files = []
        
        def extract_files(items, path_prefix=""):
            for item in items:
                if item["type"] == "file":
                    priority = self._calculate_file_priority(item, focus_area)
                    if priority > 0:
                        files.append({
                            "path": item["path"],
                            "name": item["name"],
                            "size": item.get("size", 0),
                            "priority": priority,
                            "reason": self._get_priority_reason(item, focus_area)
                        })
                elif item["type"] == "dir" and item.get("children"):
                    extract_files(item["children"], item["path"])
        
        extract_files(structure.get("structure", []))
        
        # 按优先级排序并限制数量
        files.sort(key=lambda x: x["priority"], reverse=True)
        return files[:max_files]
    
    def _calculate_file_priority(self, file_item: Dict, focus_area: str) -> int:
        """计算文件审查优先级"""
        name = file_item["name"].lower()
        path = file_item["path"].lower()
        size = file_item.get("size", 0)
        
        # 跳过过大的文件
        if size > 500000:  # 500KB
            return 0
        
        priority = 0
        
        # 基础优先级
        if any(ext in name for ext in ['.py', '.java', '.js', '.ts', '.go', '.cpp', '.c']):
            priority += 5
        
        # 根据focus_area调整优先级
        if focus_area == "security" or focus_area == "all":
            if any(keyword in path for keyword in ['auth', 'login', 'security', 'password', 'token']):
                priority += 10
            if any(keyword in name for keyword in ['auth', 'security', 'crypto', 'hash']):
                priority += 8
        
        if focus_area == "performance" or focus_area == "all":
            if any(keyword in path for keyword in ['cache', 'optimization', 'performance']):
                priority += 10
            if any(keyword in name for keyword in ['cache', 'optimize', 'performance', 'benchmark']):
                priority += 8
        
        if focus_area == "maintainability" or focus_area == "all":
            if any(keyword in name for keyword in ['main', 'index', 'app', 'server', 'client']):
                priority += 10
            if any(keyword in path for keyword in ['src/', 'lib/', 'core/']):
                priority += 5
        
        # 配置文件重要性
        if any(keyword in name for keyword in ['config', 'setting', 'env', 'dockerfile', 'package.json', 'requirements.txt', 'pom.xml']):
            priority += 7
        
        return priority
    
    def _get_priority_reason(self, file_item: Dict, focus_area: str) -> str:
        """获取优先级选择原因"""
        name = file_item["name"].lower()
        path = file_item["path"].lower()
        
        reasons = []
        
        if any(keyword in path for keyword in ['auth', 'security']):
            reasons.append("安全相关")
        if any(keyword in path for keyword in ['cache', 'performance']):
            reasons.append("性能相关")
        if any(keyword in name for keyword in ['main', 'index', 'app']):
            reasons.append("核心文件")
        if any(keyword in name for keyword in ['config', 'setting']):
            reasons.append("配置文件")
        
        return ", ".join(reasons) if reasons else "通用代码文件"
    
    def _generate_review_recommendations(self, focus_area: str) -> List[str]:
        """生成审查建议"""
        base_recommendations = [
            "检查代码风格和命名规范",
            "验证错误处理和边界条件",
            "评估代码可读性和维护性"
        ]
        
        if focus_area == "security" or focus_area == "all":
            base_recommendations.extend([
                "检查输入验证和SQL注入防护",
                "验证身份认证和授权机制",
                "检查敏感信息泄露风险"
            ])
        
        if focus_area == "performance" or focus_area == "all":
            base_recommendations.extend([
                "分析算法时间复杂度",
                "检查内存使用和垃圾回收",
                "评估数据库查询效率"
            ])
        
        if focus_area == "maintainability" or focus_area == "all":
            base_recommendations.extend([
                "评估模块化和依赖关系",
                "检查测试覆盖率",
                "分析代码重复和重构机会"
            ])
        
        return base_recommendations

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