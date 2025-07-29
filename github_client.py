"""
GitHub客户端封装
提供GitHub API的异步操作接口
"""

import base64
import os
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

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
            
            # 检查文件大小限制
            MAX_FILE_SIZE = 1024 * 1024  # 1MB 限制
            if file_content.size > MAX_FILE_SIZE:
                return {
                    "path": file_path,
                    "name": file_content.name,
                    "size": file_content.size,
                    "content": f"[文件过大: {file_content.size} bytes > {MAX_FILE_SIZE} bytes]\n请使用 search_code 工具搜索特定代码片段",
                    "sha": file_content.sha,
                    "branch": branch,
                    "encoding": file_content.encoding,
                    "download_url": file_content.download_url,
                    "truncated": True
                }
            
            # 解码文件内容
            content = base64.b64decode(file_content.content).decode('utf-8')
            
            # 额外的字符长度限制
            MAX_CONTENT_LENGTH = 50000  # 50K 字符
            original_length = len(content)
            is_truncated = original_length > MAX_CONTENT_LENGTH
            if is_truncated:
                content = content[:MAX_CONTENT_LENGTH] + f"\n\n[内容已截断，原文件 {original_length} 字符，显示前 {MAX_CONTENT_LENGTH} 字符]"
            
            return {
                "path": file_path,
                "name": file_content.name,
                "size": file_content.size,
                "content": content,
                "sha": file_content.sha,
                "branch": branch,
                "encoding": file_content.encoding,
                "download_url": file_content.download_url,
                "truncated": is_truncated
            }
            
        except GithubException as e:
            if e.status == 404:
                # 文件不存在，提供智能建议
                suggestions = await self._get_similar_files(repo_url, file_path, branch)
                error_msg = f"❌ 文件不存在: {file_path}\n\n"
                
                if suggestions["exact_dir_exists"]:
                    error_msg += f"📁 目录 '{suggestions['directory']}' 存在，但文件不存在。\n"
                    if suggestions["files_in_dir"]:
                        error_msg += f"📄 该目录下的文件:\n"
                        for f in suggestions["files_in_dir"][:5]:  # 最多显示5个
                            error_msg += f"   - {f}\n"
                        if len(suggestions["files_in_dir"]) > 5:
                            error_msg += f"   ... 还有 {len(suggestions['files_in_dir']) - 5} 个文件\n"
                
                if suggestions["similar_files"]:
                    error_msg += f"\n🔍 相似文件建议:\n"
                    for sim_file in suggestions["similar_files"][:3]:  # 最多显示3个建议
                        error_msg += f"   - {sim_file}\n"
                
                error_msg += f"\n💡 建议操作:\n"
                error_msg += f"   1. 使用 list_directory('{suggestions['directory']}') 查看目录内容\n"
                error_msg += f"   2. 使用 get_repository_structure() 了解项目结构\n"
                error_msg += f"   3. 使用 search_code() 搜索相关代码\n"
                
                logger.warning(f"文件不存在: {file_path}, 已提供建议")
                raise Exception(error_msg)
            else:
                logger.error(f"获取文件内容失败: {e}")
                raise Exception(f"获取文件内容失败: {e}")
    
    async def _get_similar_files(self, repo_url: str, file_path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """获取相似文件建议"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            # 解析路径
            import os
            directory = os.path.dirname(file_path) if file_path != os.path.basename(file_path) else ""
            filename = os.path.basename(file_path)
            file_base, file_ext = os.path.splitext(filename)
            
            result = {
                "directory": directory,
                "exact_dir_exists": False,
                "files_in_dir": [],
                "similar_files": []
            }
            
            # 检查目录是否存在并获取文件列表
            try:
                if directory:
                    contents = repo.get_contents(directory, ref=branch)
                else:
                    contents = repo.get_contents("", ref=branch)  # 根目录
                
                result["exact_dir_exists"] = True
                
                if not isinstance(contents, list):
                    contents = [contents]
                
                all_files = []
                for content in contents:
                    if content.type == "file":
                        all_files.append(content.name)
                        result["files_in_dir"].append(content.name)
                
                # 查找相似文件
                similar_files = self._find_similar_filenames(filename, all_files)
                result["similar_files"] = similar_files
                
            except GithubException:
                # 目录也不存在，尝试找父目录
                if directory:
                    parent_dir = os.path.dirname(directory)
                    try:
                        contents = repo.get_contents(parent_dir if parent_dir else "", ref=branch)
                        if not isinstance(contents, list):
                            contents = [contents]
                        
                        # 查找相似的目录和文件
                        for content in contents:
                            if content.type == "dir" and directory.split("/")[-1] in content.name:
                                result["similar_files"].append(f"{content.path}/")
                            elif content.type == "file" and (file_base in content.name or file_ext in content.name):
                                result["similar_files"].append(content.path)
                    except:
                        pass
            
            return result
            
        except Exception as e:
            logger.warning(f"获取相似文件建议失败: {e}")
            return {
                "directory": os.path.dirname(file_path),
                "exact_dir_exists": False, 
                "files_in_dir": [],
                "similar_files": []
            }
    
    def _find_similar_filenames(self, target_filename: str, available_files: List[str]) -> List[str]:
        """查找相似的文件名"""
        import difflib
        
        target_lower = target_filename.lower()
        target_base = os.path.splitext(target_filename)[0].lower()
        target_ext = os.path.splitext(target_filename)[1].lower()
        
        similar_files = []
        
        for file in available_files:
            file_lower = file.lower()
            file_base = os.path.splitext(file)[0].lower()
            file_ext = os.path.splitext(file)[1].lower()
            
            # 1. 完全匹配不同扩展名
            if file_base == target_base and file_ext != target_ext:
                similar_files.append(file)
            
            # 2. 部分文件名匹配
            elif target_base in file_base or file_base in target_base:
                similar_files.append(file)
            
            # 3. 相同扩展名的相似文件名
            elif file_ext == target_ext:
                similarity = difflib.SequenceMatcher(None, target_base, file_base).ratio()
                if similarity > 0.6:  # 60%相似度
                    similar_files.append(file)
        
        # 按相似度排序
        similar_files.sort(key=lambda x: difflib.SequenceMatcher(None, target_lower, x.lower()).ratio(), reverse=True)
        
        return similar_files[:5]  # 返回最相似的5个
    
    async def check_file_exists(self, repo_url: str, file_path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """检查文件或目录是否存在"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            try:
                # 尝试获取路径内容
                content = repo.get_contents(file_path, ref=branch)
                
                if isinstance(content, list):
                    # 这是一个目录
                    return {
                        "exists": True,
                        "type": "directory",
                        "path": file_path,
                        "files_count": len([c for c in content if c.type == "file"]),
                        "dirs_count": len([c for c in content if c.type == "dir"]),
                        "items": [{"name": c.name, "type": c.type, "size": c.size} for c in content[:10]]  # 最多返回10个项目
                    }
                else:
                    # 这是一个文件
                    return {
                        "exists": True,
                        "type": "file",
                        "path": file_path,
                        "name": content.name,
                        "size": content.size,
                        "sha": content.sha,
                        "can_fetch": content.size <= 1024 * 1024,  # 1MB限制
                        "size_readable": self._format_file_size(content.size)
                    }
                    
            except GithubException as e:
                if e.status == 404:
                    # 文件/目录不存在，提供建议
                    suggestions = await self._get_similar_files(repo_url, file_path, branch)
                    return {
                        "exists": False,
                        "path": file_path,
                        "directory": suggestions["directory"],
                        "directory_exists": suggestions["exact_dir_exists"],
                        "files_in_directory": suggestions["files_in_dir"][:10],
                        "similar_files": suggestions["similar_files"][:5],
                        "suggestions": {
                            "use_list_directory": f"list_directory('{suggestions['directory']}')" if suggestions["directory"] else "list_directory('')",
                            "use_repository_structure": "get_repository_structure()",
                            "use_search": f"search_code(query='{os.path.basename(file_path)}')"
                        }
                    }
                else:
                    raise e
                    
        except GithubException as e:
            logger.error(f"检查文件存在性失败: {e}")
            raise Exception(f"检查文件存在性失败: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小为可读格式"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
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
            # 安全地处理搜索结果，避免索引越界
            try:
                result_count = min(search_results.totalCount, 20)  # 限制结果数量
                for i, item in enumerate(search_results):
                    if i >= result_count:
                        break
                    results.append({
                        "name": item.name,
                        "path": item.path,
                        "sha": item.sha,
                        "url": item.html_url,
                        "score": item.score,
                        "repository": item.repository.full_name
                    })
            except Exception as e:
                logger.warning(f"处理搜索结果时出现问题: {e}")
                # 如果处理结果时出错，返回空结果但不抛出异常
            
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
    
    async def get_user_repositories(self, username: str, sort: str = "updated", per_page: int = 30) -> Dict[str, Any]:
        """获取用户的所有公开仓库列表"""
        try:
            user = self.github.get_user(username)
            
            # 获取用户基本信息
            user_info = {
                "login": user.login,
                "name": user.name,
                "bio": user.bio,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "avatar_url": user.avatar_url,
                "html_url": user.html_url
            }
            
            # 获取仓库列表
            repos = user.get_repos(sort=sort, direction="desc")
            repositories = []
            
            count = 0
            for repo in repos:
                if count >= per_page:
                    break
                    
                repositories.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "private": repo.private,
                    "fork": repo.fork,
                    "stars": repo.stargazers_count,
                    "watchers": repo.watchers_count,
                    "forks": repo.forks_count,
                    "language": repo.language,
                    "size": repo.size,
                    "default_branch": repo.default_branch,
                    "created_at": repo.created_at.isoformat() if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                    "html_url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "ssh_url": repo.ssh_url,
                    "topics": list(repo.get_topics()) if hasattr(repo, 'get_topics') else [],
                    "has_issues": repo.has_issues,
                    "has_projects": repo.has_projects,
                    "has_wiki": repo.has_wiki,
                    "has_pages": repo.has_pages,
                    "has_downloads": repo.has_downloads,
                    "archived": repo.archived,
                    "disabled": repo.disabled,
                    "open_issues": repo.open_issues_count,
                    "license": repo.license.name if repo.license else None
                })
                count += 1
            
            # 计算统计信息
            total_stars = sum(repo["stars"] for repo in repositories)
            total_forks = sum(repo["forks"] for repo in repositories)
            languages = {}
            for repo in repositories:
                if repo["language"]:
                    languages[repo["language"]] = languages.get(repo["language"], 0) + 1
            
            return {
                "user": user_info,
                "repositories": repositories,
                "statistics": {
                    "total_repositories": len(repositories),
                    "total_stars": total_stars,
                    "total_forks": total_forks,
                    "primary_languages": dict(sorted(languages.items(), key=lambda x: x[1], reverse=True)),
                    "most_starred_repo": max(repositories, key=lambda x: x["stars"]) if repositories else None,
                    "most_recent_repo": max(repositories, key=lambda x: x["updated_at"] or "") if repositories else None
                },
                "pagination": {
                    "per_page": per_page,
                    "returned": len(repositories),
                    "has_more": user.public_repos > len(repositories)
                }
            }
            
        except GithubException as e:
            logger.error(f"获取用户仓库失败: {e}")
            raise Exception(f"获取用户仓库失败: {e}")

    async def smart_path_explorer(self, repo_url: str, target_path: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """智能路径探索 - 当路径不存在时自动回退探索"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            exploration_history = []  # 记录探索历史，避免循环
            
            def explore_path(path: str, fallback_count: int = 0, original_target: str = None) -> Dict[str, Any]:
                """递归探索路径"""
                if fallback_count > 3:  # 最多回退3层
                    return {
                        "error": f"已回退{fallback_count}层仍未找到有效路径",
                        "exploration_stopped": True,
                        "suggestions": [
                            f"原始目标路径: {original_target or target_path}",
                            f"当前探索到: {path}",
                            "建议使用 get_repository_structure 查看完整目录结构",
                            "或使用 intelligent_file_finder 按模式搜索文件"
                        ]
                    }
                
                # 避免重复探索同一路径
                if path in exploration_history:
                    return {
                        "error": f"检测到循环探索，路径 '{path}' 已探索过",
                        "exploration_history": exploration_history,
                        "suggestions": ["使用其他探索策略"]
                    }
                
                exploration_history.append(path)
                
                try:
                    # 尝试获取路径内容
                    contents = repo.get_contents(path, ref=branch)
                    
                    if isinstance(contents, list):
                        # 这是一个目录
                        directories = []
                        files = []
                        
                        for item in contents:
                            if item.type == "dir":
                                directories.append({
                                    "name": item.name,
                                    "path": item.path,
                                    "type": "directory"
                                })
                            else:
                                files.append({
                                    "name": item.name,
                                    "path": item.path,
                                    "type": "file",
                                    "size": item.size
                                })
                        
                        result = {
                            "success": True,
                            "path": path,
                            "type": "directory",
                            "directories": directories,
                            "files": files,
                            "total_items": len(contents),
                            "fallback_count": fallback_count,
                            "exploration_history": exploration_history
                        }
                        
                        # 如果这是回退后的结果，尝试自动匹配原始目标
                        if fallback_count > 0 and original_target:
                            target_segments = original_target.split("/")
                            current_depth = len(path.split("/")) if path else 0
                            
                            # 尝试找到下一个应该进入的目录
                            if current_depth < len(target_segments):
                                next_target = target_segments[current_depth]
                                auto_match = self._find_best_match(next_target, directories)
                                
                                if auto_match:
                                    print(f"🎯 自动匹配: {next_target} → {auto_match['name']}")
                                    # 递归进入匹配的目录
                                    auto_result = explore_path(auto_match['path'], fallback_count, original_target)
                                    if auto_result.get("success"):
                                        result["auto_navigation"] = {
                                            "matched_directory": auto_match,
                                            "auto_result": auto_result
                                        }
                        
                        return result
                    else:
                        # 这是一个文件
                        return {
                            "success": True,
                            "path": path,
                            "type": "file",
                            "name": contents.name,
                            "size": contents.size,
                            "fallback_count": fallback_count
                        }
                        
                except Exception as e:
                    if "404" in str(e):
                        # 路径不存在，尝试回退到上级目录
                        if "/" not in path or path == "" or fallback_count >= 3:
                            return {
                                "error": f"路径 '{path}' 不存在",
                                "fallback_limit_reached": fallback_count >= 3,
                                "at_root": "/" not in path or path == "",
                                "exploration_history": exploration_history,
                                "suggestions": [
                                    f"回退了{fallback_count}层仍未找到有效路径" if fallback_count >= 3 else "已到达根目录",
                                    "使用 get_repository_structure 查看完整目录结构",
                                    "使用 intelligent_file_finder 按模式搜索"
                                ]
                            }
                        
                        # 回退到上级目录
                        parent_path = "/".join(path.split("/")[:-1])
                        print(f"🔄 路径 '{path}' 不存在，回退到上级目录: '{parent_path}' (第{fallback_count + 1}次回退)")
                        
                        parent_result = explore_path(parent_path, fallback_count + 1, original_target or target_path)
                        
                        if parent_result.get("success"):
                            # 在上级目录中查找相似的目录
                            target_name = path.split("/")[-1]
                            similar_dirs = self._find_similar_directories(target_name, parent_result.get("directories", []))
                            
                            return {
                                "error": f"路径 '{path}' 不存在",
                                "auto_fallback": True,
                                "fallback_count": fallback_count + 1,
                                "parent_path": parent_path,
                                "parent_contents": parent_result,
                                "similar_directories": similar_dirs,
                                "exploration_history": exploration_history,
                                "suggestions": self._generate_fallback_suggestions(path, parent_path, similar_dirs, fallback_count + 1)
                            }
                        else:
                            return parent_result
                    else:
                        return {"error": f"探索路径时出错: {str(e)}"}
            
            result = explore_path(target_path)
            
            # 添加探索建议
            if result.get("success") and result.get("type") == "directory":
                result["exploration_suggestions"] = [
                    "可以继续探索的子目录:",
                    *[f"  - {d['name']} ({d['path']})" for d in result.get("directories", [])]
                ]
            
            return result
            
        except Exception as e:
            return {"error": f"智能路径探索失败: {str(e)}"}
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算字符串相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 简单的Jaccard相似度
        set1 = set(str1.lower())
        set2 = set(str2.lower())
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union) if union else 0.0

    async def intelligent_file_finder(self, repo_url: str, file_pattern: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """智能文件查找 - 基于模式匹配查找文件"""
        try:
            owner, repo_name = self._parse_repo_url(repo_url)
            repo = self.github.get_repo(f"{owner}/{repo_name}")
            
            if not branch:
                branch = repo.default_branch
            
            # 使用GitHub搜索API查找文件
            found_files = []
            
            # 尝试不同的搜索策略
            search_strategies = [
                f"filename:{file_pattern}",
                f"path:{file_pattern}",
                f"{file_pattern} in:file",
                f"{file_pattern}"
            ]
            
            for strategy in search_strategies:
                try:
                    query = f"{strategy} repo:{owner}/{repo_name}"
                    search_results = self.github.search_code(query)
                    
                    for result in search_results[:10]:  # 限制结果数量
                        found_files.append({
                            "name": result.name,
                            "path": result.path,
                            "score": result.score,
                            "search_strategy": strategy
                        })
                        
                    if found_files:
                        break  # 找到结果就停止
                        
                except Exception as e:
                    print(f"搜索策略 '{strategy}' 失败: {e}")
                    continue
            
            return {
                "success": True,
                "pattern": file_pattern,
                "found_files": found_files,
                "total_found": len(found_files),
                "suggestions": [
                    "使用 get_file_content 获取具体文件内容",
                    "使用 check_file_exists 验证路径是否正确"
                ] if found_files else [
                    "未找到匹配的文件",
                    "尝试使用 get_repository_structure 查看项目结构",
                    "或使用更宽泛的搜索模式"
                ]
            }
            
        except Exception as e:
            return {"error": f"智能文件查找失败: {str(e)}"}

    async def suggest_exploration_path(self, repo_url: str, current_path: str, target_concept: str, branch: Optional[str] = None) -> Dict[str, Any]:
        """基于目标概念建议探索路径"""
        try:
            # 定义常见的Java项目路径模式
            path_patterns = {
                "filter": ["filter", "filters", "web/filter", "security/filter", "config/filter"],
                "controller": ["controller", "controllers", "web/controller", "api", "rest"],
                "service": ["service", "services", "business", "biz"],
                "config": ["config", "configuration", "settings"],
                "security": ["security", "auth", "authentication", "authorization"],
                "util": ["util", "utils", "common", "helper"],
                "entity": ["entity", "entities", "model", "domain", "pojo"],
                "dao": ["dao", "repository", "mapper", "persistence"],
                "exception": ["exception", "exceptions", "error", "errors"]
            }
            
            # 根据目标概念生成建议路径
            suggested_paths = []
            base_path = current_path.rstrip("/")
            
            concept_lower = target_concept.lower()
            for concept, patterns in path_patterns.items():
                if concept in concept_lower or concept_lower in concept:
                    for pattern in patterns:
                        if base_path:
                            suggested_paths.append(f"{base_path}/{pattern}")
                        else:
                            suggested_paths.append(pattern)
            
            # 如果没有找到特定模式，生成通用建议
            if not suggested_paths:
                common_java_paths = [
                    f"{base_path}/src/main/java" if not "src/main/java" in base_path else "",
                    f"{base_path}/web",
                    f"{base_path}/common",
                    f"{base_path}/core"
                ]
                suggested_paths = [p for p in common_java_paths if p]
            
            # 验证建议的路径
            verified_paths = []
            for path in suggested_paths[:5]:  # 只验证前5个
                try:
                    exists_result = await self.check_file_exists(repo_url, path, branch)
                    if exists_result.get("exists"):
                        verified_paths.append({
                            "path": path,
                            "type": exists_result.get("type"),
                            "verified": True
                        })
                except:
                    verified_paths.append({
                        "path": path,
                        "verified": False
                    })
            
            return {
                "success": True,
                "target_concept": target_concept,
                "current_path": current_path,
                "suggested_paths": verified_paths,
                "recommendations": [
                    "先尝试已验证存在的路径",
                    "使用 smart_path_explorer 进行智能探索",
                    "如果都不存在，使用 get_repository_structure 查看完整结构"
                ]
            }
            
        except Exception as e:
            return {"error": f"路径建议失败: {str(e)}"}
