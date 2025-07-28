"""
简化的GitHub客户端
直接使用requests库调用GitHub REST API
"""

import asyncio
import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from datetime import datetime


class SimpleGitHubClient:
    """简化的GitHub API客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """初始化GitHub客户端"""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required")
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-MCP-Tool/1.0"
        }
    
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """解析仓库URL，返回owner和repo名称"""
        if repo_url.startswith("https://github.com/"):
            parsed = urlparse(repo_url)
            parts = parsed.path.strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif "/" in repo_url and not repo_url.startswith("http"):
            parts = repo_url.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        
        raise ValueError(f"无效的仓库URL格式: {repo_url}")
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """发送HTTP请求到GitHub API"""
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"GitHub API请求失败: {str(e)}")
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """获取仓库基本信息"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            url = f"{self.base_url}/repos/{owner}/{repo_name}"
            
            data = self._make_request(url)
            
            # 尝试获取README
            readme_content = None
            try:
                readme_url = f"{self.base_url}/repos/{owner}/{repo_name}/readme"
                readme_data = self._make_request(readme_url)
                if readme_data.get('content'):
                    readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                    readme_content = readme_content[:2000] + ("..." if len(readme_content) > 2000 else "")
            except:
                pass
            
            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "language": data.get("language"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "size": data.get("size", 0),
                "default_branch": data.get("default_branch"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "clone_url": data.get("clone_url"),
                "html_url": data.get("html_url"),
                "topics": data.get("topics", []),
                "license": data.get("license", {}).get("name") if data.get("license") else None,
                "readme": readme_content
            }
        except Exception as e:
            raise Exception(f"获取仓库信息失败: {str(e)}")
    
    async def get_file_content(self, repo_url: str, file_path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """获取文件内容"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            # 如果没有指定分支，先获取默认分支
            if not branch:
                repo_info = await self.get_repository_info(repo_url)
                branch = repo_info.get("default_branch", "main")
            
            url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/{file_path}"
            params = {"ref": branch} if branch else {}
            
            data = self._make_request(url, params)
            
            if data.get("type") != "file":
                raise Exception(f"路径 {file_path} 不是文件")
            
            # 解码文件内容
            content = base64.b64decode(data["content"]).decode('utf-8')
            
            return {
                "path": file_path,
                "name": data.get("name"),
                "size": data.get("size"),
                "content": content,
                "sha": data.get("sha"),
                "branch": branch,
                "encoding": data.get("encoding"),
                "download_url": data.get("download_url")
            }
            
        except Exception as e:
            raise Exception(f"获取文件内容失败: {str(e)}")
    
    async def list_directory(self, repo_url: str, directory_path: str = "", branch: Optional[str] = None) -> Dict[str, Any]:
        """列出目录内容"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            if not branch:
                repo_info = await self.get_repository_info(repo_url)
                branch = repo_info.get("default_branch", "main")
            
            url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/{directory_path}"
            params = {"ref": branch} if branch else {}
            
            data = self._make_request(url, params)
            
            # 确保返回的是列表
            if not isinstance(data, list):
                data = [data]
            
            files = []
            directories = []
            
            for item in data:
                item_info = {
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "size": item.get("size"),
                    "sha": item.get("sha"),
                    "download_url": item.get("download_url")
                }
                
                if item.get("type") == "file":
                    files.append(item_info)
                elif item.get("type") == "dir":
                    directories.append(item_info)
            
            return {
                "path": directory_path,
                "branch": branch,
                "files": files,
                "directories": directories,
                "total_items": len(files) + len(directories)
            }
            
        except Exception as e:
            raise Exception(f"列出目录内容失败: {str(e)}")
    
    async def search_code(self, repo_url: str, query: str, file_extension: Optional[str] = None, path_filter: Optional[str] = None) -> Dict[str, Any]:
        """在仓库中搜索代码"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            # 构建搜索查询
            search_query = f"{query} repo:{owner}/{repo_name}"
            
            if file_extension:
                if not file_extension.startswith('.'):
                    file_extension = '.' + file_extension
                search_query += f" extension:{file_extension[1:]}"
            
            if path_filter:
                search_query += f" path:{path_filter}"
            
            url = f"{self.base_url}/search/code"
            params = {"q": search_query}
            
            data = self._make_request(url, params)
            
            results = []
            for item in data.get("items", [])[:20]:  # 限制结果数量
                results.append({
                    "name": item.get("name"),
                    "path": item.get("path"),
                    "sha": item.get("sha"),
                    "url": item.get("html_url"),
                    "score": item.get("score"),
                    "repository": item.get("repository", {}).get("full_name")
                })
            
            return {
                "query": query,
                "total_count": data.get("total_count", 0),
                "results": results
            }
            
        except Exception as e:
            raise Exception(f"搜索代码失败: {str(e)}")
    
    async def get_branches(self, repo_url: str) -> Dict[str, Any]:
        """获取仓库分支列表"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            # 获取仓库信息获得默认分支
            repo_info = await self.get_repository_info(repo_url)
            default_branch = repo_info.get("default_branch", "main")
            
            url = f"{self.base_url}/repos/{owner}/{repo_name}/branches"
            data = self._make_request(url)
            
            branches = []
            for branch in data:
                branches.append({
                    "name": branch.get("name"),
                    "sha": branch.get("commit", {}).get("sha"),
                    "protected": branch.get("protected", False),
                    "commit_message": branch.get("commit", {}).get("commit", {}).get("message"),
                    "commit_date": branch.get("commit", {}).get("commit", {}).get("author", {}).get("date")
                })
            
            return {
                "repository": f"{owner}/{repo_name}",
                "default_branch": default_branch,
                "total_branches": len(branches),
                "branches": branches
            }
            
        except Exception as e:
            raise Exception(f"获取分支列表失败: {str(e)}")
    
    async def get_commits(self, repo_url: str, branch: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """获取提交历史"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            if not branch:
                repo_info = await self.get_repository_info(repo_url)
                branch = repo_info.get("default_branch", "main")
            
            url = f"{self.base_url}/repos/{owner}/{repo_name}/commits"
            params = {"sha": branch, "per_page": limit}
            
            data = self._make_request(url, params)
            
            commits = []
            for commit in data:
                commit_info = commit.get("commit", {})
                commits.append({
                    "sha": commit.get("sha"),
                    "message": commit_info.get("message"),
                    "author": {
                        "name": commit_info.get("author", {}).get("name"),
                        "email": commit_info.get("author", {}).get("email"),
                        "date": commit_info.get("author", {}).get("date")
                    },
                    "committer": {
                        "name": commit_info.get("committer", {}).get("name"),
                        "email": commit_info.get("committer", {}).get("email"),
                        "date": commit_info.get("committer", {}).get("date")
                    },
                    "url": commit.get("html_url"),
                    "stats": commit.get("stats")  # 这个可能需要额外的API调用
                })
            
            return {
                "repository": f"{owner}/{repo_name}",
                "branch": branch,
                "total_commits": len(commits),
                "commits": commits
            }
            
        except Exception as e:
            raise Exception(f"获取提交历史失败: {str(e)}")
    
    async def get_repository_structure(self, repo_url: str, branch: Optional[str] = None, max_depth: int = 3) -> Dict[str, Any]:
        """获取仓库目录结构"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            
            if not branch:
                repo_info = await self.get_repository_info(repo_url)
                branch = repo_info.get("default_branch", "main")
            
            async def build_tree(path: str = "", depth: int = 0) -> List[Dict[str, Any]]:
                if depth >= max_depth:
                    return []
                
                url = f"{self.base_url}/repos/{owner}/{repo_name}/contents/{path}"
                params = {"ref": branch} if branch else {}
                
                try:
                    data = self._make_request(url, params)
                    if not isinstance(data, list):
                        data = [data]
                    
                    tree = []
                    for item in data:
                        item_data = {
                            "name": item.get("name"),
                            "path": item.get("path"),
                            "type": item.get("type"),
                            "size": item.get("size") if item.get("type") == "file" else None
                        }
                        
                        if item.get("type") == "dir" and depth < max_depth - 1:
                            try:
                                item_data["children"] = await build_tree(item.get("path", ""), depth + 1)
                            except:
                                item_data["children"] = []
                        
                        tree.append(item_data)
                    
                    return tree
                except:
                    return []
            
            structure = await build_tree()
            
            return {
                "repository": f"{owner}/{repo_name}",
                "branch": branch,
                "max_depth": max_depth,
                "structure": structure
            }
            
        except Exception as e:
            raise Exception(f"获取仓库结构失败: {str(e)}") 