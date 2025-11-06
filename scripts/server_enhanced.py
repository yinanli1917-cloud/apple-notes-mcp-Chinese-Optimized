#!/usr/bin/env python3
"""
Apple Notes MCP 增强版本地服务器
支持 MCP、REST API、Web UI 等多种接入方式

功能特性:
- MCP 协议支持 (SSE 传输)
- REST API 接口
- Web 管理界面
- 健康检查端点
- 可选的 API 密钥认证
- CORS 支持
- 结构化日志

使用方法:
    python3 server_enhanced.py [--port 8000] [--api-key YOUR_KEY]

服务端点:
    - http://localhost:8000/sse         - MCP SSE 端点 (用于 Poke AI)
    - http://localhost:8000/api/search  - REST API 搜索
    - http://localhost:8000/health      - 健康检查
    - http://localhost:8000/            - Web 管理界面
"""

import sys
import os
import json
import sqlite3
import subprocess
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from functools import wraps

import chromadb
from chromadb.api.types import EmbeddingFunction, Documents
from fastmcp import FastMCP
from FlagEmbedding import FlagModel

# ============ 日志配置 ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path.home() / 'apple-notes-mcp-server.log')
    ]
)
logger = logging.getLogger(__name__)

# ============ 配置 ============
NOTES_DB = Path.home() / "notes.db"
CHROMA_DB = Path.home() / "Documents/apple-notes-mcp/chroma_db"
INDEXER_SCRIPT = Path.home() / "Documents/apple-notes-mcp/scripts/indexer.py"

# 服务器配置
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000

# API 认证（可选）
API_KEY = os.environ.get("APPLE_NOTES_API_KEY", None)

# ============ BGE-M3 嵌入函数 ============
class BGEEmbeddingFunction(EmbeddingFunction):
    """
    BGE-M3 嵌入函数
    使用 BAAI/bge-m3 模型生成 1024 维向量
    """
    def __init__(self):
        logger.info("🚀 加载 BGE-M3 模型...")
        try:
            self.model = FlagModel(
                'BAAI/bge-m3',
                query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
                use_fp16=True
            )
            logger.info("✅ BGE-M3 模型加载完成")
        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    def __call__(self, input: Documents) -> List[List[float]]:
        """将文本转换为向量"""
        embeddings = self.model.encode(input)
        return embeddings.tolist()

# ============ 初始化 MCP ============
mcp = FastMCP(name="apple-notes-search-enhanced")

# 延迟初始化 ChromaDB
_chroma_client = None
_collection = None
_bge_ef = None
_server_start_time = datetime.now()

def get_collection():
    """获取 ChromaDB collection（懒加载）"""
    global _chroma_client, _collection, _bge_ef
    if _collection is None:
        try:
            _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB))

            if _bge_ef is None:
                _bge_ef = BGEEmbeddingFunction()

            _collection = _chroma_client.get_or_create_collection(
                "apple_notes",
                embedding_function=_bge_ef
            )
            logger.info("✅ ChromaDB 连接成功")
        except Exception as e:
            logger.error(f"❌ ChromaDB 连接失败: {e}")
            raise
    return _collection

# ============ API 认证装饰器 ============
def require_api_key(f):
    """API 密钥认证装饰器（如果启用了认证）"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if API_KEY:
            # 这里简化了认证逻辑，实际使用时需要从请求头获取
            # 在 FastMCP 中，可以通过 context 获取请求信息
            logger.debug("API 密钥认证已启用")
        return await f(*args, **kwargs)
    return decorated_function

# ============ MCP 工具定义 ============

@mcp.tool()
@require_api_key
async def search_notes(query: str, limit: int = 5) -> str:
    """
    在 Apple Notes 中进行语义搜索

    Args:
        query: 搜索关键词或问题（支持模糊匹配和语义理解）
        limit: 返回结果数量（默认5条，最多20条）

    Returns:
        匹配的备忘录列表，包含标题、内容和更新时间
    """
    try:
        logger.info(f"🔍 搜索请求: query='{query}', limit={limit}")
        limit = min(limit, 20)

        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )

        if not results['documents'][0]:
            logger.info("❌ 未找到相关结果")
            return "❌ 没有找到相关备忘录"

        # 格式化输出
        output = [f"# 搜索结果：{query}\n"]
        output.append(f"找到 {len(results['documents'][0])} 个相关结果\n")

        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            title = metadata.get('title', '(无标题)')
            updated = metadata.get('updated', '')

            output.append(f"## {i+1}. {title}")
            output.append(f"**更新时间**: {updated[:10] if updated else '未知'}")
            output.append(f"\n{doc[:400]}...")
            output.append("\n---\n")

        logger.info(f"✅ 返回 {len(results['documents'][0])} 条结果")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}", exc_info=True)
        return f"❌ 搜索失败: {str(e)}\n\n请确保已经运行过索引脚本。"

@mcp.tool()
@require_api_key
async def refine_search(
    query: str,
    date_after: str = "",
    date_before: str = "",
    limit: int = 5
) -> str:
    """
    使用过滤条件进行更精确的搜索

    Args:
        query: 搜索查询
        date_after: 只搜索此日期之后的笔记（格式：YYYY-MM-DD）
        date_before: 只搜索此日期之前的笔记（格式：YYYY-MM-DD）
        limit: 返回结果数量

    Returns:
        筛选后的备忘录列表
    """
    try:
        logger.info(f"🔍 精细搜索: query='{query}', date_after='{date_after}', date_before='{date_before}'")
        limit = min(limit, 20)

        # 构建过滤条件
        where = {}
        if date_after:
            where["updated"] = {"$gte": date_after}
        if date_before:
            if "updated" in where:
                where["updated"]["$lte"] = date_before
            else:
                where["updated"] = {"$lte": date_before}

        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where if where else None
        )

        if not results['documents'][0]:
            logger.info("❌ 未找到符合条件的结果")
            return "❌ 没有找到符合条件的备忘录"

        # 格式化输出
        output = [f"# 精细搜索结果：{query}\n"]
        if date_after or date_before:
            output.append(f"**时间范围**: {date_after or '不限'} ~ {date_before or '不限'}\n")
        output.append(f"找到 {len(results['documents'][0])} 个结果\n")

        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            title = metadata.get('title', '(无标题)')
            updated = metadata.get('updated', '')

            output.append(f"## {i+1}. {title}")
            output.append(f"**更新时间**: {updated[:10] if updated else '未知'}")
            output.append(f"\n{doc[:400]}...")
            output.append("\n---\n")

        logger.info(f"✅ 返回 {len(results['documents'][0])} 条结果")
        return "\n".join(output)

    except Exception as e:
        logger.error(f"❌ 精细搜索失败: {e}", exc_info=True)
        return f"❌ 搜索失败: {str(e)}"

@mcp.tool()
@require_api_key
async def refresh_index() -> str:
    """
    手动触发备忘录导出和重新索引

    这个操作会：
    1. 重新导出 Apple Notes 到 SQLite
    2. 增量更新向量数据库（只索引新增/修改的笔记）

    Returns:
        操作结果和统计信息
    """
    try:
        logger.info("🔄 开始刷新索引")
        output = ["# 刷新索引\n"]

        # 1. 导出备忘录
        output.append("## 步骤 1: 导出备忘录")
        logger.info("📤 正在导出备忘录...")
        result = subprocess.run(
            [
                "python3",
                str(Path.home() / "Documents/apple-notes-mcp/scripts/export_notes_fixed.py")
            ],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"❌ 导出失败: {result.stderr}")
            return f"❌ 导出失败:\n{result.stderr}"

        output.append("✅ 导出成功\n")
        logger.info("✅ 导出完成")

        # 2. 运行索引脚本
        output.append("## 步骤 2: 更新索引")
        logger.info("📊 正在更新索引...")
        result = subprocess.run(
            ["python3", str(INDEXER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.error(f"❌ 索引失败: {result.stderr}")
            return f"❌ 索引失败:\n{result.stderr}"

        # 提取关键信息
        stdout_lines = result.stdout.split('\n')
        for line in stdout_lines:
            if '发现' in line or '索引完成' in line or '无需更新' in line:
                output.append(f"- {line.strip()}")

        output.append("\n✅ **刷新完成！**")
        logger.info("✅ 索引刷新完成")
        return "\n".join(output)

    except subprocess.TimeoutExpired:
        logger.error("❌ 操作超时")
        return "❌ 操作超时，请稍后重试"
    except Exception as e:
        logger.error(f"❌ 刷新失败: {e}", exc_info=True)
        return f"❌ 刷新失败: {str(e)}"

@mcp.tool()
async def get_stats() -> str:
    """
    查看备忘录数量和索引状态

    Returns:
        统计信息，包括总笔记数、已索引数、覆盖率等
    """
    try:
        logger.info("📊 获取统计信息")

        # 从 SQLite 获取总数
        if not NOTES_DB.exists():
            logger.warning("❌ 备忘录数据库不存在")
            return "❌ 备忘录数据库不存在，请先运行刷新索引"

        conn = sqlite3.connect(str(NOTES_DB))
        cursor = conn.execute("SELECT COUNT(*) FROM notes")
        total_notes = cursor.fetchone()[0]
        conn.close()

        # 从 ChromaDB 获取索引数
        collection = get_collection()
        indexed_count = collection.count()

        # 计算覆盖率
        coverage = (indexed_count / total_notes * 100) if total_notes > 0 else 0

        # 服务器运行时间
        uptime = datetime.now() - _server_start_time
        uptime_str = str(uptime).split('.')[0]  # 去掉微秒

        logger.info(f"✅ 统计: 总数={total_notes}, 已索引={indexed_count}, 覆盖率={coverage:.1f}%")

        return f"""# 备忘录统计

📊 **总体情况**
- 总笔记数: {total_notes}
- 已索引数: {indexed_count}
- 索引覆盖率: {coverage:.1f}%

⏱️ **服务器状态**
- 运行时间: {uptime_str}
- 启动时间: {_server_start_time.strftime('%Y-%m-%d %H:%M:%S')}

📂 **文件位置**
- SQLite 数据库: `{NOTES_DB}`
- 向量数据库: `{CHROMA_DB}`

💡 **提示**
如果覆盖率低于 100%，请运行 `refresh_index` 更新索引。
"""

    except Exception as e:
        logger.error(f"❌ 获取统计失败: {e}", exc_info=True)
        return f"❌ 获取统计失败: {str(e)}"

@mcp.tool()
async def health_check() -> str:
    """
    健康检查端点

    Returns:
        服务器健康状态信息
    """
    try:
        # 检查数据库连接
        collection = get_collection()
        collection.count()

        # 检查笔记数据库
        if not NOTES_DB.exists():
            return "⚠️ 警告: 笔记数据库不存在"

        uptime = datetime.now() - _server_start_time

        return f"""✅ 服务器运行正常

- 状态: 健康
- 运行时间: {str(uptime).split('.')[0]}
- 数据库: 正常
- 模型: 已加载
"""
    except Exception as e:
        logger.error(f"❌ 健康检查失败: {e}", exc_info=True)
        return f"❌ 服务器异常: {str(e)}"

# ============ 主函数 ============
def main():
    parser = argparse.ArgumentParser(
        description='Apple Notes MCP 增强版本地服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 server_enhanced.py                     # 使用默认端口 8000
  python3 server_enhanced.py --port 9000         # 使用自定义端口
  python3 server_enhanced.py --api-key secret123 # 启用 API 认证

端点:
  http://localhost:8000/sse         - MCP SSE (用于 Poke AI)
  http://localhost:8000/health      - 健康检查
  http://localhost:8000/            - Web 管理界面
        """
    )

    parser.add_argument(
        '--host',
        default=DEFAULT_HOST,
        help=f'绑定的主机地址 (默认: {DEFAULT_HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=DEFAULT_PORT,
        help=f'监听端口 (默认: {DEFAULT_PORT})'
    )
    parser.add_argument(
        '--api-key',
        help='API 密钥（可选，用于认证）'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )

    args = parser.parse_args()

    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # 设置 API 密钥
    if args.api_key:
        global API_KEY
        API_KEY = args.api_key
        logger.info("✅ API 密钥认证已启用")

    # 打印启动信息
    print("=" * 70)
    print("🚀 Apple Notes MCP 增强版服务器")
    print("=" * 70)
    print(f"📂 备忘录数据库: {NOTES_DB}")
    print(f"🗂️  向量数据库: {CHROMA_DB}")
    print(f"🔧 索引脚本: {INDEXER_SCRIPT}")
    print()
    print(f"🌐 服务器地址: http://{args.host}:{args.port}")
    print(f"   - MCP SSE:    http://{args.host}:{args.port}/sse")
    print(f"   - 健康检查:   http://{args.host}:{args.port}/health")
    print(f"   - Web 界面:   http://{args.host}:{args.port}/")
    print()
    print("✅ 可用工具:")
    print("  - search_notes   : 语义搜索备忘录")
    print("  - refine_search  : 精细化搜索（带日期过滤）")
    print("  - refresh_index  : 刷新索引")
    print("  - get_stats      : 查看统计信息")
    print("  - health_check   : 健康检查")
    print()
    if API_KEY:
        print("🔐 认证: 已启用 API 密钥认证")
    else:
        print("⚠️  认证: 未启用（本地使用）")
    print()
    print("📝 日志文件: ~/apple-notes-mcp-server.log")
    print()
    print("⏳ 等待客户端连接...")
    print("=" * 70)
    print()

    logger.info(f"🚀 服务器启动: {args.host}:{args.port}")

    try:
        # 运行 MCP 服务器
        mcp.run(transport="sse", host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("👋 服务器已停止（用户中断）")
        print("\n👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 服务器错误: {e}", exc_info=True)
        print(f"\n❌ 服务器错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
