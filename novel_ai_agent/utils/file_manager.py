"""
文件管理工具
负责小说、大纲、角色设定的文件读写

目录结构（每部小说独立一个目录）：
  output/
    <novel_id>/
      novels/          # JSON 存档 + 章节 MD + 完整版 MD
      outlines/        # 大纲 MD
      characters/      # 角色 MD
"""
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..models.novel import Novel
from ..models.outline import Outline
from ..models.character import Character
from ..models.chapter import Chapter
from ..config.settings import get_settings


class FileManager:
    """文件管理器"""

    def __init__(self):
        self.settings = get_settings()
        # 确保根输出目录存在
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)

    # ── 路径辅助 ────────────────────────────────────────────────

    def _novel_dirs(self, novel_id: str) -> dict:
        """
        返回某部小说的三个子目录路径，并自动创建。

        结构：
          output/<novel_id>/novels/
          output/<novel_id>/outlines/
          output/<novel_id>/characters/
        """
        base = Path(self.settings.output_dir) / novel_id
        dirs = {
            "base":       base,
            "novels":     base / "novels",
            "outlines":   base / "outlines",
            "characters": base / "characters",
        }
        for p in dirs.values():
            p.mkdir(parents=True, exist_ok=True)
        return dirs

    # ── 小说 JSON 存档 ───────────────────────────────────────────

    def save_novel_json(self, novel: Novel) -> str:
        """保存小说为 JSON 文件（数据持久化）"""
        dirs = self._novel_dirs(novel.id)
        filepath = dirs["novels"] / f"{novel.id}.json"
        filepath.write_text(
            novel.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return str(filepath)

    def load_novel_json(self, novel_id: str) -> Optional[Novel]:
        """从 JSON 文件加载小说，不存在则返回 None"""
        filepath = Path(self.settings.output_dir) / novel_id / "novels" / f"{novel_id}.json"
        if not filepath.exists():
            # 兼容旧路径：novel_ai_agent/output/novels/<novel_id>.json
            legacy = Path("novel_ai_agent/output/novels") / f"{novel_id}.json"
            if legacy.exists():
                filepath = legacy
            else:
                return None
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return Novel(**data)

    # ── Markdown 导出 ────────────────────────────────────────────

    def save_novel_markdown(self, novel: Novel, include_metadata: bool = True) -> str:
        """保存完整小说为 Markdown"""
        dirs = self._novel_dirs(novel.id)
        raw_name = f"{novel.id}_{novel.title}.md"
        filename = "".join(c for c in raw_name if c.isalnum() or c in (" ", "_", "-", ".")).strip()
        filepath = dirs["novels"] / filename
        filepath.write_text(novel.to_markdown(include_metadata=include_metadata), encoding="utf-8")
        return str(filepath)

    def save_outline_markdown(self, outline: Outline, novel_id: str) -> str:
        """保存大纲为 Markdown"""
        dirs = self._novel_dirs(novel_id)
        filepath = dirs["outlines"] / f"{novel_id}_outline_v{outline.version}.md"
        filepath.write_text(outline.to_markdown(), encoding="utf-8")
        return str(filepath)

    def save_characters_markdown(self, characters: list[Character], novel_id: str) -> str:
        """保存角色设定为 Markdown"""
        dirs = self._novel_dirs(novel_id)
        filepath = dirs["characters"] / f"{novel_id}_characters.md"

        md = "# 角色设定\n\n"
        md += f"**更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += "---\n\n"
        for character in characters:
            md += character.to_markdown()
            md += "---\n\n"

        filepath.write_text(md, encoding="utf-8")
        return str(filepath)

    def save_chapter_markdown(self, chapter: Chapter, novel_id: str) -> str:
        """保存单个章节为 Markdown"""
        dirs = self._novel_dirs(novel_id)
        filepath = dirs["novels"] / f"{novel_id}_chapter_{chapter.number:03d}.md"
        filepath.write_text(chapter.to_markdown(include_metadata=True), encoding="utf-8")
        return str(filepath)

    def sync_chapter_markdown_to_json(self, novel_id: str, chapter_number: int) -> bool:
        """
        读取用户手动修改过的 Markdown 章节文件，同步回 novel.json。
        
        Args:
            novel_id: 小说 ID
            chapter_number: 章节号
            
        Returns:
            bool: 同步是否成功
        """
        try:
            novel = self.load_novel_json(novel_id)
            if not novel:
                print(f"找不到小说 {novel_id}")
                return False
                
            dirs = self._novel_dirs(novel_id)
            md_path = dirs["novels"] / f"{novel_id}_chapter_{chapter_number:03d}.md"
            
            if not md_path.exists():
                print(f"找不到 markdown 文件: {md_path}")
                return False
                
            content = md_path.read_text(encoding="utf-8")
            
            # 解析 md 内容：去掉由 to_markdown(include_metadata=True) 生成的头部
            # 格式大致是：
            # ## 第X章 标题\n\n
            # > **状态**... \n\n
            # ---\n\n
            # (正文开始)
            parts = content.split("---\n\n", 1)
            if len(parts) == 2:
                # 存在分隔符，取下半部分作为纯正文
                pure_content = parts[1].strip()
            else:
                # 如果用户把分隔符删了，做兼容处理：尝试去掉以 ## 章节开头的行
                lines = content.split('\n')
                body_lines = []
                in_header = True
                for line in lines:
                    if in_header and (line.startswith('##') or line.startswith('>')):
                        continue
                    in_header = False
                    body_lines.append(line)
                pure_content = '\n'.join(body_lines).strip()
                
            # 更新 novel 对象
            chapter_found = False
            for ch in (novel.chapters or []):
                if ch.number == chapter_number:
                    # 如果内容没变，直接返回成功可省写磁盘
                    if ch.content.strip() == pure_content:
                        return True
                    ch.content = pure_content
                    ch.update_word_count()
                    ch.updated_at = datetime.now()
                    ch.version += 1
                    chapter_found = True
                    break
                    
            if not chapter_found:
                print(f"在 JSON 中未找到第 {chapter_number} 章")
                return False
                
            # 保存更新后的 JSON
            self.save_novel_json(novel)
            # 同步更新整个小说聚合的 markdown
            self.save_novel_markdown(novel)
            return True
        except Exception as e:
            print(f"同步章节 markdown 到 JSON 时出错: {e}")
            return False

    def export_novel_with_version(self, novel: Novel) -> str:
        """导出带时间戳版本的小说备份"""
        dirs = self._novel_dirs(novel.id)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_name = f"{novel.id}_{novel.title}_backup_{timestamp}.md"
        filename = "".join(c for c in raw_name if c.isalnum() or c in (" ", "_", "-", ".")).strip()
        filepath = dirs["novels"] / filename
        filepath.write_text(novel.to_markdown(include_metadata=True), encoding="utf-8")
        return str(filepath)

    # ── 小说列表 ─────────────────────────────────────────────────

    def list_novels(self) -> list[str]:
        """列出所有小说 ID（根据 output/ 下的子目录）"""
        root = Path(self.settings.output_dir)
        if not root.exists():
            return []

        novel_ids = []
        for entry in root.iterdir():
            if entry.is_dir():
                json_path = entry / "novels" / f"{entry.name}.json"
                if json_path.exists():
                    novel_ids.append(entry.name)

        # 兼容旧 flat 目录（novel_ai_agent/output/novels/*.json）
        legacy_dir = Path("novel_ai_agent/output/novels")
        if legacy_dir.exists():
            for f in legacy_dir.glob("*.json"):
                if f.stem not in novel_ids:
                    novel_ids.append(f.stem)

        return novel_ids

    # ── 删除 ─────────────────────────────────────────────────────

    def delete_novel(self, novel_id: str) -> bool:
        """删除小说的整个目录"""
        import shutil
        try:
            novel_dir = Path(self.settings.output_dir) / novel_id
            if novel_dir.exists():
                shutil.rmtree(novel_dir)
            return True
        except Exception as e:
            print(f"删除小说 {novel_id} 时出错: {e}")
            return False


# 全局文件管理器实例
file_manager = FileManager()
