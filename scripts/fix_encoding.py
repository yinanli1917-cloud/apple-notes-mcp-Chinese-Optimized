#!/usr/bin/env python3
"""
修复 apple-notes-to-sqlite 导出的编码问题
问题: apple-notes-to-sqlite 使用 UTF-8 字节但被错误解释为 Latin-1
解决: 将文本编码回 Latin-1 字节，然后正确解码为 UTF-8
"""

import sqlite3
from pathlib import Path

NOTES_DB = Path.home() / "notes.db"

def fix_encoding(text):
    """
    修复编码问题：
    apple-notes-to-sqlite 从 NSAttributedString 读取UTF-8字节，
    但Python将其解释为Latin-1字符。

    修复方法：
    1. 将错误的Unicode字符编码回Latin-1字节
    2. 用UTF-8重新解码这些字节
    """
    if not text:
        return text

    try:
        # 将错误解释的字符编码回原始字节
        # 然后用UTF-8正确解码
        fixed = text.encode('latin-1').decode('utf-8', errors='replace')
        return fixed
    except Exception as e:
        # 如果转换失败，说明可能已经是正确编码或是纯英文
        # 尝试直接返回或使用NFD标准化
        try:
            import unicodedata
            return unicodedata.normalize('NFC', text)
        except:
            return text

def main():
    print("=" * 60)
    print("🔧 修复备忘录编码")
    print("=" * 60)

    if not NOTES_DB.exists():
        print(f"❌ 数据库不存在: {NOTES_DB}")
        return

    conn = sqlite3.connect(str(NOTES_DB))

    # 获取所有笔记
    cursor = conn.execute("SELECT id, title, body FROM notes")
    notes = cursor.fetchall()

    print(f"📊 发现 {len(notes)} 条笔记")

    fixed_count = 0
    for note_id, title, body in notes:
        # 修复标题和内容
        fixed_title = fix_encoding(title) if title else title
        fixed_body = fix_encoding(body) if body else body

        # 如果有变化，更新数据库
        if fixed_title != title or fixed_body != body:
            conn.execute(
                "UPDATE notes SET title = ?, body = ? WHERE id = ?",
                (fixed_title, fixed_body, note_id)
            )
            fixed_count += 1

    conn.commit()
    conn.close()

    print(f"✅ 修复完成！共修复 {fixed_count} 条笔记")

    # 显示几个修复后的标题作为验证
    print("\n📝 修复后的笔记示例:")
    conn = sqlite3.connect(str(NOTES_DB))
    cursor = conn.execute("SELECT title FROM notes WHERE title IS NOT NULL LIMIT 5")
    for i, (title,) in enumerate(cursor.fetchall(), 1):
        print(f"  {i}. {title[:50]}")
    conn.close()

if __name__ == "__main__":
    main()
