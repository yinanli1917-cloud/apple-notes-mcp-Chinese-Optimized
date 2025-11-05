#!/usr/bin/env python3
"""
备忘录索引脚本
功能：读取 SQLite 中的备忘录，使用 BGE-M3 生成向量并存入 ChromaDB
"""

import sqlite3
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents
import os
import sys
from datetime import datetime
from typing import List

# 导入 BGE-M3 模型
from FlagEmbedding import FlagModel

# ============ 配置 ============
NOTES_DB = os.path.expanduser("~/notes.db")
CHROMA_DB = os.path.expanduser("~/Documents/apple-notes-mcp/chroma_db")
LAST_SYNC_FILE = os.path.expanduser("~/Documents/apple-notes-mcp/.last_sync")

# ============ BGE-M3 嵌入函数 ============
class BGEEmbeddingFunction(EmbeddingFunction):
    """
    BGE-M3 嵌入函数
    使用 BAAI/bge-m3 模型生成 1024 维向量
    - 模型: BAAI/bge-m3
    - 维度: 1024
    - 特点: 优化中英文混合搜索，支持 100+ 语言
    """
    def __init__(self):
        print("🚀 加载 BGE-M3 模型（首次加载会下载约2GB模型文件）...")
        self.model = FlagModel(
            'BAAI/bge-m3',
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章：",
            use_fp16=True  # 使用半精度浮点数加速，M2 MAX 支持
        )
        print("✅ BGE-M3 模型加载完成")

    def __call__(self, input: Documents) -> List[List[float]]:
        """
        将文本转换为向量
        Args:
            input: 文本列表
        Returns:
            向量列表（每个向量 1024 维）
        """
        embeddings = self.model.encode(input)
        return embeddings.tolist()

# ============ 初始化 ChromaDB ============
print("📂 初始化 ChromaDB...")
client = chromadb.PersistentClient(path=CHROMA_DB)

# 使用 BGE-M3 嵌入函数
bge_ef = BGEEmbeddingFunction()

collection = client.get_or_create_collection(
    name="apple_notes",
    embedding_function=bge_ef,
    metadata={"description": "Apple Notes 语义搜索 (BGE-M3, 1024维)"}
)

# ============ 读取上次同步时间 ============
def get_last_sync_time():
    """读取上次同步时间，如果不存在返回 1970-01-01"""
    try:
        with open(LAST_SYNC_FILE, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "1970-01-01 00:00:00"

# ============ 保存同步时间 ============
def save_sync_time():
    """保存当前时间为最后同步时间"""
    with open(LAST_SYNC_FILE, 'w') as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ============ 清理 HTML 标签（简单版）============
def clean_html(text):
    """移除 HTML 标签，保留纯文本"""
    if not text:
        return ""
    import re
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ============ 增量索引 ============
def incremental_index():
    """仅索引新增或修改的备忘录"""
    last_sync = get_last_sync_time()
    print(f"⏰ 上次同步时间: {last_sync}")

    if not os.path.exists(NOTES_DB):
        print(f"❌ 错误：找不到备忘录数据库 {NOTES_DB}")
        print("   请先运行：apple-notes-to-sqlite ~/notes.db")
        return

    # 连接 SQLite
    conn = sqlite3.connect(NOTES_DB)

    # 检查表结构
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 数据库表: {', '.join(tables)}")

    # 查询变更的笔记
    cursor = conn.execute("""
        SELECT id, title, body, created, updated
        FROM notes
        WHERE updated > ?
        ORDER BY updated DESC
    """, (last_sync,))

    # 获取变更的笔记
    changed_notes = cursor.fetchall()
    print(f"🔍 发现 {len(changed_notes)} 条新增或修改的笔记")

    if not changed_notes:
        print("✅ 无需更新")
        conn.close()
        return

    # 批量更新到 ChromaDB
    indexed_count = 0
    for note_id, title, body, created, updated in changed_notes:
        # 清理 HTML 标签
        clean_body = clean_html(body)

        # 合并标题和正文
        if title:
            content = f"{title}\n\n{clean_body}"
        else:
            content = clean_body

        # 跳过空笔记
        if not content.strip():
            continue

        # 准备元数据
        metadata = {
            "title": title or "(无标题)",
            "created": created or "",
            "updated": updated or ""
        }

        try:
            # Upsert（更新或插入）
            collection.upsert(
                ids=[note_id],
                documents=[content],
                metadatas=[metadata]
            )

            # 显示进度
            title_preview = (title[:30] + "...") if title and len(title) > 30 else (title or "(无标题)")
            print(f"  ✓ 索引: {title_preview}")
            indexed_count += 1

        except Exception as e:
            print(f"  ✗ 索引失败: {title or '(无标题)'} - {str(e)}")

    conn.close()
    save_sync_time()
    print(f"\n✅ 索引完成！共处理 {indexed_count} 条笔记")

# ============ 全量索引（首次使用） ============
def full_index():
    """索引所有备忘录（首次运行）"""
    print("🔄 执行全量索引...")

    if not os.path.exists(NOTES_DB):
        print(f"❌ 错误：找不到备忘录数据库 {NOTES_DB}")
        print("   请先运行：apple-notes-to-sqlite ~/notes.db")
        return

    conn = sqlite3.connect(NOTES_DB)
    cursor = conn.execute("SELECT id, title, body, created, updated FROM notes")

    all_notes = cursor.fetchall()
    print(f"📊 总共 {len(all_notes)} 条笔记")

    if len(all_notes) == 0:
        print("⚠️  没有找到笔记，请检查 Apple Notes 中是否有内容")
        conn.close()
        return

    batch_size = 100
    indexed_count = 0

    for i in range(0, len(all_notes), batch_size):
        batch = all_notes[i:i+batch_size]

        ids = []
        documents = []
        metadatas = []

        for note_id, title, body, created, updated in batch:
            # 清理 HTML 标签
            clean_body = clean_html(body)

            # 合并标题和正文
            if title:
                content = f"{title}\n\n{clean_body}"
            else:
                content = clean_body

            # 跳过空笔记
            if not content.strip():
                continue

            ids.append(note_id)
            documents.append(content)
            metadatas.append({
                "title": title or "(无标题)",
                "created": created or "",
                "updated": updated or ""
            })
            indexed_count += 1

        if ids:  # 只有在有数据时才索引
            try:
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                print(f"  进度: {min(i+batch_size, len(all_notes))}/{len(all_notes)} (已索引 {indexed_count} 条)")
            except Exception as e:
                print(f"  ✗ 批量索引失败: {str(e)}")

    conn.close()
    save_sync_time()
    print(f"\n✅ 全量索引完成！共索引 {indexed_count} 条笔记")

# ============ 测试搜索 ============
def test_search(query, limit=5):
    """测试搜索功能"""
    print(f"\n🔍 搜索: {query}")

    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )

        if not results['documents'][0]:
            print("❌ 没有找到相关结果")
            return

        print(f"✅ 找到 {len(results['documents'][0])} 个结果:\n")
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            print(f"--- 结果 {i+1} ---")
            print(f"标题: {metadata['title']}")
            print(f"内容预览: {doc[:200]}...")
            print(f"更新时间: {metadata['updated']}\n")
    except Exception as e:
        print(f"❌ 搜索失败: {str(e)}")

# ============ 显示统计信息 ============
def show_stats():
    """显示索引统计"""
    print("\n📊 索引统计信息")
    print("=" * 50)

    try:
        # ChromaDB 统计
        indexed_count = collection.count()
        print(f"已索引笔记数: {indexed_count}")

        # SQLite 统计
        if os.path.exists(NOTES_DB):
            conn = sqlite3.connect(NOTES_DB)
            cursor = conn.execute("SELECT COUNT(*) FROM notes")
            total_notes = cursor.fetchone()[0]
            conn.close()
            print(f"数据库笔记数: {total_notes}")

            if total_notes > 0:
                coverage = (indexed_count / total_notes) * 100
                print(f"索引覆盖率: {coverage:.1f}%")

        # 文件路径
        print(f"\n📂 文件位置:")
        print(f"  SQLite: {NOTES_DB}")
        print(f"  ChromaDB: {CHROMA_DB}")

        # 上次同步时间
        last_sync = get_last_sync_time()
        print(f"\n⏰ 上次同步: {last_sync}")

    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")

# ============ 主函数 ============
if __name__ == "__main__":
    print("=" * 50)
    print("📝 Apple Notes 索引脚本")
    print("=" * 50)
    print()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "full":
            full_index()
        elif command == "search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "项目"
            test_search(query)
        elif command == "stats":
            show_stats()
        else:
            print("用法:")
            print("  python3 indexer.py           # 增量索引（默认）")
            print("  python3 indexer.py full      # 全量索引（首次运行）")
            print("  python3 indexer.py search <关键词>  # 测试搜索")
            print("  python3 indexer.py stats     # 显示统计信息")
    else:
        # 默认执行增量索引
        incremental_index()
