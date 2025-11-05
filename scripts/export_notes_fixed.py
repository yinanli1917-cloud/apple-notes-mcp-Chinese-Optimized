#!/usr/bin/env python3
"""
修复版的 Apple Notes 导出脚本
原始工具使用 mac_roman 编码，导致中文乱码
这个版本使用正确的 UTF-8 编码
"""

import subprocess
import sqlite3
import secrets
from pathlib import Path

NOTES_DB = Path.home() / "notes.db"

EXTRACT_SCRIPT = """
tell application "Notes"
   repeat with eachNote in every note
      set noteId to the id of eachNote
      set noteTitle to the name of eachNote
      set noteBody to the body of eachNote
      set noteCreatedDate to the creation date of eachNote
      set noteCreated to (noteCreatedDate as «class isot» as string)
      set noteUpdatedDate to the modification date of eachNote
      set noteUpdated to (noteUpdatedDate as «class isot» as string)
      log "{split}-id: " & noteId & "\\n"
      log "{split}-created: " & noteCreated & "\\n"
      log "{split}-updated: " & noteUpdated & "\\n"
      log "{split}-title: " & noteTitle & "\\n\\n"
      log noteBody & "\\n"
      log "{split}{split}" & "\\n"
   end repeat
end tell
""".strip()

def extract_notes():
    """使用 UTF-8 编码导出备忘录"""
    split = secrets.token_hex(8)

    # 运行 AppleScript
    process = subprocess.Popen(
        ["osascript", "-e", EXTRACT_SCRIPT.format(split=split)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    note = {}
    body = []

    for line in process.stdout:
        # 使用 UTF-8 而不是 mac_roman！
        try:
            line = line.decode("utf-8").strip()
        except UnicodeDecodeError:
            # 如果 UTF-8 失败，尝试 UTF-16
            try:
                line = line.decode("utf-16").strip()
            except:
                # 实在不行就跳过这行
                continue

        # 检查是否是笔记分隔符
        if line == f"{split}{split}":
            if note.get("id"):
                note["body"] = "\\n".join(body).strip()
                yield note
            note = {}
            body = []
            continue

        # 解析笔记字段
        found_key = False
        for key in ("id", "title", "created", "updated"):
            if line.startswith(f"{split}-{key}: "):
                note[key] = line[len(f"{split}-{key}: "):]
                found_key = True
                continue

        if not found_key:
            body.append(line)

def main():
    print("=" * 60)
    print("📤 导出 Apple Notes (UTF-8 修复版)")
    print("=" * 60)

    # 创建数据库
    conn = sqlite3.connect(str(NOTES_DB))
    cursor = conn.cursor()

    # 创建表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT,
            body TEXT,
            created TEXT,
            updated TEXT
        )
    """)

    count = 0
    for note in extract_notes():
        # 插入或更新笔记
        cursor.execute("""
            INSERT OR REPLACE INTO notes (id, title, body, created, updated)
            VALUES (?, ?, ?, ?, ?)
        """, (
            note.get("id"),
            note.get("title"),
            note.get("body"),
            note.get("created"),
            note.get("updated")
        ))
        count += 1
        if count % 50 == 0:
            print(f"✓ 已导出 {count} 条笔记...")

    conn.commit()
    conn.close()

    print(f"\\n✅ 导出完成！共 {count} 条笔记")

    # 显示几个笔记标题验证编码
    print("\\n📝 验证编码（前5条标题）:")
    conn = sqlite3.connect(str(NOTES_DB))
    cursor = conn.execute("SELECT title FROM notes WHERE title IS NOT NULL LIMIT 5")
    for i, (title,) in enumerate(cursor.fetchall(), 1):
        print(f"  {i}. {title[:50]}")
    conn.close()

if __name__ == "__main__":
    main()
