"""
一致性检查工具
检查角色、情节等的前后一致性
"""
from typing import List, Dict, Tuple
from ..models.novel import Novel
from ..models.character import Character


class ConsistencyChecker:
    """一致性检查器"""

    def __init__(self, novel: Novel):
        self.novel = novel

    def check_character_consistency(self) -> List[Dict]:
        """
        检查角色一致性

        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []

        # 检查大纲中提到的角色是否都有设定
        if self.novel.outline and self.novel.outline.chapters_plan:
            mentioned_characters = set()
            for chapter_plan in self.novel.outline.chapters_plan:
                mentioned_characters.update(chapter_plan.characters_involved)

            defined_characters = {char.name for char in self.novel.characters}

            missing_characters = mentioned_characters - defined_characters
            if missing_characters:
                issues.append({
                    "type": "missing_character_definition",
                    "severity": "warning",
                    "message": f"以下角色在大纲中提到但未设定: {', '.join(missing_characters)}"
                })

        # 检查角色关系的对称性
        for char in self.novel.characters:
            for related_name, relation in char.relationships.items():
                related_char = self.novel.get_character(related_name)
                if not related_char:
                    issues.append({
                        "type": "undefined_related_character",
                        "severity": "error",
                        "character": char.name,
                        "message": f"角色'{char.name}'的关系中提到'{related_name}',但该角色未定义"
                    })
                elif char.name not in related_char.relationships:
                    issues.append({
                        "type": "asymmetric_relationship",
                        "severity": "info",
                        "character": char.name,
                        "message": f"角色'{char.name}'与'{related_name}'的关系不对称"
                    })

        return issues

    def check_chapter_sequence(self) -> List[Dict]:
        """
        检查章节顺序和完整性

        Returns:
            List[Dict]: 发现的问题列表
        """
        issues = []

        if not self.novel.chapters:
            return issues

        chapter_numbers = sorted([ch.number for ch in self.novel.chapters])

        # 检查章节编号是否连续
        expected_numbers = list(range(1, chapter_numbers[-1] + 1))
        missing_numbers = set(expected_numbers) - set(chapter_numbers)

        if missing_numbers:
            issues.append({
                "type": "missing_chapters",
                "severity": "warning",
                "message": f"缺失章节: {sorted(missing_numbers)}"
            })

        # 检查章节编号是否从1开始
        if chapter_numbers and chapter_numbers[0] != 1:
            issues.append({
                "type": "invalid_start_chapter",
                "severity": "warning",
                "message": f"章节编号应从1开始,当前从{chapter_numbers[0]}开始"
            })

        return issues

    def check_word_count(self) -> Dict:
        """
        检查字数统计

        Returns:
            Dict: 字数统计信息
        """
        total_words = self.novel.get_total_words()
        target_words = self.novel.outline.target_words if self.novel.outline else None

        result = {
            "total_words": total_words,
            "target_words": target_words,
            "chapter_count": len(self.novel.chapters),
            "average_words_per_chapter": total_words // len(self.novel.chapters) if self.novel.chapters else 0
        }

        if target_words:
            result["progress"] = (total_words / target_words) * 100
            result["remaining_words"] = target_words - total_words

        return result

    def check_all(self) -> Tuple[List[Dict], Dict]:
        """
        执行所有检查

        Returns:
            Tuple[List[Dict], Dict]: (问题列表, 字数统计)
        """
        all_issues = []

        all_issues.extend(self.check_character_consistency())
        all_issues.extend(self.check_chapter_sequence())
        word_count_info = self.check_word_count()

        return all_issues, word_count_info

    def generate_report(self) -> str:
        """
        生成检查报告

        Returns:
            str: Markdown格式的检查报告
        """
        issues, word_count = self.check_all()

        report = "# 一致性检查报告\n\n"

        # 字数统计
        report += "## 字数统计\n\n"
        report += f"- **当前总字数**: {word_count['total_words']:,}\n"
        if word_count.get('target_words'):
            report += f"- **目标字数**: {word_count['target_words']:,}\n"
            report += f"- **完成进度**: {word_count['progress']:.1f}%\n"
            report += f"- **剩余字数**: {word_count['remaining_words']:,}\n"
        report += f"- **章节数**: {word_count['chapter_count']}\n"
        if word_count['average_words_per_chapter']:
            report += f"- **平均每章字数**: {word_count['average_words_per_chapter']:,}\n"
        report += "\n"

        # 问题列表
        if issues:
            report += "## 发现的问题\n\n"

            error_issues = [i for i in issues if i.get('severity') == 'error']
            warning_issues = [i for i in issues if i.get('severity') == 'warning']
            info_issues = [i for i in issues if i.get('severity') == 'info']

            if error_issues:
                report += "### 错误 (需要修复)\n\n"
                for issue in error_issues:
                    report += f"- {issue['message']}\n"
                report += "\n"

            if warning_issues:
                report += "### 警告 (建议处理)\n\n"
                for issue in warning_issues:
                    report += f"- {issue['message']}\n"
                report += "\n"

            if info_issues:
                report += "### 提示\n\n"
                for issue in info_issues:
                    report += f"- {issue['message']}\n"
                report += "\n"
        else:
            report += "## 检查结果\n\n"
            report += "未发现问题,一切正常!\n\n"

        return report
