"""
GitHub客户端封装
提供GitHub API的异步操作接口
"""

import asyncio
import base64
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
import fnmatch

import aiohttp
from github import Github, GithubException
from loguru import logger


class GitHubClient:
    """GitHub API客户端"""
    
    def __init__(self, token: Optional[str] = None):
        """初始化GitHub客户端"""
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token is required")
        
        self.github = Github(self.token)
        
    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """解析仓库URL，返回owner和repo名称"""
        # 支持多种格式的输入
        if repo_url.startswith("https://github.com/"):
            # https://github.com/owner/repo
            parsed = urlparse(repo_url)
            parts = parsed.path.strip('/').split('/')
            if len(parts) >= 2:
                return parts[0], parts[1]
        elif "/" in repo_url and not repo_url.startswith("http"):
            # owner/repo 格式
            parts = repo_url.split("/")
            if len(parts) == 2:
                return parts[0], parts[1]
        
        raise ValueError(f"无效的仓库URL格式: {repo_url}")
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """获取仓库基本信息"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "size": repo.size,
                "default_branch": repo.default_branch,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "clone_url": repo.clone_url,
                "html_url": repo.html_url,
                "topics": repo.get_topics(),
                "license": repo.license.name if repo.license else None,
                "readme": await self._get_readme_content(repo)
            }
        except GithubException as e:
            logger.error(f"获取仓库信息失败: {e}")
            raise Exception(f"获取仓库信息失败: {e}")
    
    async def _get_readme_content(self, repo) -> Optional[str]:
        """获取README文件内容"""
        try:
            readme_files = ["README.md", "README.rst", "README.txt", "README"]
            for readme_name in readme_files:
                try:
                    readme = repo.get_contents(readme_name)
                    if hasattr(readme, 'content'):
                        content = base64.b64decode(readme.content).decode('utf-8')
                        return content[:2000] + ("..." if len(content) > 2000 else "")  # 限制长度
                except:
                    continue
            return None
        except:
            return None
    
    async def get_file_content(self, repo_url: str, file_path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """获取文件内容"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            # 如果没有指定分支，使用默认分支
            if not branch:
                branch = repo.default_branch
            
            # 获取文件内容
            file_content = repo.get_contents(file_path, ref=branch)
            
            if file_content.type != "file":
                raise Exception(f"路径 {file_path} 不是文件")
            
            # 解码文件内容
            content = base64.b64decode(file_content.content).decode('utf-8')
            
            return {
                "path": file_path,
                "name": file_content.name,
                "size": file_content.size,
                "content": content,
                "sha": file_content.sha,
                "branch": branch,
                "encoding": file_content.encoding,
                "download_url": file_content.download_url
            }
            
        except GithubException as e:
            logger.error(f"获取文件内容失败: {e}")
            raise Exception(f"获取文件内容失败: {e}")
    
    async def list_directory(self, repo_url: str, directory_path: str = "", branch: Optional[str] = None) -> Dict[str, Any]:
        """列出目录内容"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            # 获取目录内容
            contents = repo.get_contents(directory_path, ref=branch)
            
            files = []
            directories = []
            
            # 如果返回的是单个文件而不是列表
            if not isinstance(contents, list):
                contents = [contents]
            
            for content in contents:
                item_info = {
                    "name": content.name,
                    "path": content.path,
                    "size": content.size,
                    "sha": content.sha,
                    "download_url": content.download_url
                }
                
                if content.type == "file":
                    files.append(item_info)
                elif content.type == "dir":
                    directories.append(item_info)
            
            return {
                "path": directory_path,
                "branch": branch,
                "files": files,
                "directories": directories,
                "total_items": len(files) + len(directories)
            }
            
        except GithubException as e:
            logger.error(f"列出目录内容失败: {e}")
            raise Exception(f"列出目录内容失败: {e}")
    
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
            
            # 执行搜索
            search_results = self.github.search_code(search_query)
            
            results = []
            for item in search_results[:20]:  # 限制结果数量
                results.append({
                    "name": item.name,
                    "path": item.path,
                    "sha": item.sha,
                    "url": item.html_url,
                    "score": item.score,
                    "repository": item.repository.full_name
                })
            
            return {
                "query": query,
                "total_count": search_results.totalCount,
                "results": results
            }
            
        except GithubException as e:
            logger.error(f"搜索代码失败: {e}")
            raise Exception(f"搜索代码失败: {e}")
    
    async def get_repository_structure(self, repo_url: str, branch: Optional[str] = None, max_depth: int = 3) -> Dict[str, Any]:
        """获取仓库目录结构"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            async def build_tree(path: str = "", depth: int = 0) -> List[Dict[str, Any]]:
                if depth >= max_depth:
                    return []
                
                contents = repo.get_contents(path, ref=branch)
                if not isinstance(contents, list):
                    contents = [contents]
                
                tree = []
                for content in contents:
                    item = {
                        "name": content.name,
                        "path": content.path,
                        "type": content.type,
                        "size": content.size if content.type == "file" else None
                    }
                    
                    if content.type == "dir" and depth < max_depth - 1:
                        item["children"] = await build_tree(content.path, depth + 1)
                    
                    tree.append(item)
                
                return tree
            
            structure = await build_tree()
            
            return {
                "repository": f"{owner}/{repo_name}",
                "branch": branch,
                "max_depth": max_depth,
                "structure": structure
            }
            
        except GithubException as e:
            logger.error(f"获取仓库结构失败: {e}")
            raise Exception(f"获取仓库结构失败: {e}")
    
    async def get_branches(self, repo_url: str) -> Dict[str, Any]:
        """获取仓库分支列表"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            branches = []
            for branch in repo.get_branches():
                branches.append({
                    "name": branch.name,
                    "sha": branch.commit.sha,
                    "protected": branch.protected,
                    "commit_message": branch.commit.commit.message,
                    "commit_date": branch.commit.commit.author.date.isoformat() if branch.commit.commit.author.date else None
                })
            
            return {
                "repository": f"{owner}/{repo_name}",
                "default_branch": repo.default_branch,
                "total_branches": len(branches),
                "branches": branches
            }
            
        except GithubException as e:
            logger.error(f"获取分支列表失败: {e}")
            raise Exception(f"获取分支列表失败: {e}")
    
    async def get_commits(self, repo_url: str, branch: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """获取提交历史"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            commits = []
            for commit in repo.get_commits(sha=branch)[:limit]:
                commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": {
                        "name": commit.commit.author.name,
                        "email": commit.commit.author.email,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author.date else None
                    },
                    "committer": {
                        "name": commit.commit.committer.name,
                        "email": commit.commit.committer.email,
                        "date": commit.commit.committer.date.isoformat() if commit.commit.committer.date else None
                    },
                    "url": commit.html_url,
                    "stats": {
                        "additions": commit.stats.additions,
                        "deletions": commit.stats.deletions,
                        "total": commit.stats.total
                    } if commit.stats else None
                })
            
            return {
                "repository": f"{owner}/{repo_name}",
                "branch": branch,
                "total_commits": len(commits),
                "commits": commits
            }
            
        except GithubException as e:
            logger.error(f"获取提交历史失败: {e}")
            raise Exception(f"获取提交历史失败: {e}") 