#!/usr/bin/env python3
"""
GitHub API服务器
提供GitHub代码阅读和分析功能的HTTP API接口
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
import sys

from simple_github_client import SimpleGitHubClient

# 加载环境变量
load_dotenv()

# 配置日志
logger.add(sys.stderr, level="INFO")

# 创建FastAPI应用
app = FastAPI(
    title="GitHub MCP API",
    description="GitHub代码阅读和分析API",
    version="1.0.0"
)

# 全局GitHub客户端
github_client: Optional[SimpleGitHubClient] = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化GitHub客户端"""
    global github_client
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("未找到GITHUB_TOKEN环境变量")
        raise Exception("GitHub Token is required")
    
    github_client = SimpleGitHubClient(token)
    logger.info("GitHub API服务器启动成功")

# API模型定义
class RepoRequest(BaseModel):
    repo_url: str

class FileRequest(BaseModel):
    repo_url: str
    file_path: str
    branch: Optional[str] = None

class DirectoryRequest(BaseModel):
    repo_url: str
    directory_path: Optional[str] = ""
    branch: Optional[str] = None

class SearchRequest(BaseModel):
    repo_url: str
    query: str
    file_extension: Optional[str] = None
    path_filter: Optional[str] = None

class StructureRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    max_depth: Optional[int] = 3

class CommitsRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = None
    limit: Optional[int] = 10

# API端点
@app.get("/")
async def root():
    """根端点，返回API信息"""
    return {
        "name": "GitHub MCP API",
        "version": "1.0.0",
        "description": "GitHub代码阅读和分析API",
        "endpoints": {
            "repository_info": "/repo/info",
            "file_content": "/repo/file",
            "directory_list": "/repo/directory",
            "search_code": "/repo/search",
            "repository_structure": "/repo/structure",
            "branches": "/repo/branches",
            "commits": "/repo/commits"
        }
    }

@app.post("/repo/info")
async def get_repository_info(request: RepoRequest):
    """获取仓库基本信息"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.get_repository_info(request.repo_url)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取仓库信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/file")
async def get_file_content(request: FileRequest):
    """获取文件内容"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.get_file_content(
            request.repo_url, 
            request.file_path, 
            request.branch
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取文件内容失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/directory")
async def list_directory(request: DirectoryRequest):
    """列出目录内容"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.list_directory(
            request.repo_url, 
            request.directory_path, 
            request.branch
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"列出目录内容失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/search")
async def search_code(request: SearchRequest):
    """搜索代码"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.search_code(
            request.repo_url,
            request.query,
            request.file_extension,
            request.path_filter
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"搜索代码失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/structure")
async def get_repository_structure(request: StructureRequest):
    """获取仓库结构"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.get_repository_structure(
            request.repo_url,
            request.branch,
            request.max_depth
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取仓库结构失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/branches")
async def get_branches(request: RepoRequest):
    """获取分支列表"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.get_branches(request.repo_url)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取分支列表失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/repo/commits")
async def get_commits(request: CommitsRequest):
    """获取提交历史"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        result = await github_client.get_commits(
            request.repo_url,
            request.branch,
            request.limit
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取提交历史失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# 简单的GET端点用于快速测试
@app.get("/repo/info/{owner}/{repo}")
async def get_repo_info_get(owner: str, repo: str):
    """GET方式获取仓库信息（用于快速测试）"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        repo_url = f"{owner}/{repo}"
        result = await github_client.get_repository_info(repo_url)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取仓库信息失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/repo/file/{owner}/{repo}")
async def get_file_get(owner: str, repo: str, file_path: str = Query(...), branch: str = Query(None)):
    """GET方式获取文件内容（用于快速测试）"""
    try:
        if not github_client:
            raise HTTPException(status_code=500, detail="GitHub客户端未初始化")
        
        repo_url = f"{owner}/{repo}"
        result = await github_client.get_file_content(repo_url, file_path, branch)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取文件内容失败: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # 检查GitHub Token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("未找到GITHUB_TOKEN环境变量，请设置GitHub Personal Access Token")
        sys.exit(1)
    
    logger.info("启动GitHub API服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 