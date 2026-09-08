import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[1]
SCRIPT = ROOT / "skills" / "job-tracker" / "scripts" / "update_index.py"


class UpdateIndexTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.vault = pathlib.Path(self.tempdir.name)
        self.app_dir = self.vault / "求职" / "投递"
        self.app_dir.mkdir(parents=True)
        self.overview = self.vault / "求职" / "投递总览.md"
        self.overview.write_text("# 投递总览\n", encoding="utf-8")

    def run_update_index(self):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--vault", str(self.vault)],
            capture_output=True,
            text=True,
            check=False,
        )

    def write_overview(self, content):
        self.overview.write_text(content, encoding="utf-8")

    def write_application(self, filename, company, department, position, status):
        content = (
            "---\n"
            "type: application\n"
            f"company: {company}\n"
            f"department: {department}\n"
            f"position: {position}\n"
            f"status: {status}\n"
            "last_updated_at: 2026-08-27\n"
            "next_action: 等待反馈\n"
            "next_action_due: 2026-09-03\n"
            "resume_version: ''\n"
            'source_urls: ["https://example.invalid/application/1"]\n'
            "---\n"
        )
        (self.app_dir / filename).write_text(content, encoding="utf-8")

    def write_invalid_application(self):
        (self.app_dir / "坏记录.md").write_text(
            "---\ntype: application\ncompany: 缺少字段\n---\n",
            encoding="utf-8",
        )

    def test_update_index_preserves_user_text_outside_generated_block(self):
        self.write_application("示例.md", "示例公司", "数据平台部", "产品分析师", "applied")
        self.write_overview(
            "## My Notes\n\n手写内容保留。\n\n"
            "<!-- job-tracker:generated:start -->\n旧内容\n"
            "<!-- job-tracker:generated:end -->\n\n"
            "## Review Notes\n\n手写复盘保留。\n"
        )
        result = self.run_update_index()
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = self.overview.read_text(encoding="utf-8")
        self.assertIn("手写内容保留。", updated)
        self.assertIn("手写复盘保留。", updated)
        self.assertNotIn("旧内容", updated)

    def test_update_index_groups_records_by_status_order(self):
        self.write_application("已投递.md", "示例公司", "数据平台部", "产品分析师", "applied")
        self.write_application("面试.md", "第二示例公司", "研发部", "数据分析师", "interviewing")
        result = self.run_update_index()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.overview.read_text(encoding="utf-8")
        self.assertLess(content.index("进行中"), content.index("面试中"))
        self.assertIn("示例公司", content)
        self.assertIn("数据分析师", content)

    def test_update_index_does_not_write_when_frontmatter_is_invalid(self):
        original = self.overview.read_text(encoding="utf-8")
        self.write_invalid_application()
        result = self.run_update_index()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(original, self.overview.read_text(encoding="utf-8"))

    def test_update_index_reports_zero_records_for_empty_directory(self):
        result = self.run_update_index()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("records=0", result.stdout)

    def test_update_index_renders_confirmed_application_with_empty_department(self):
        self.write_application("待补部门.md", "腾讯", "", "Agent 开发工程师", "screening")
        result = self.run_update_index()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.overview.read_text(encoding="utf-8")
        self.assertIn("| 腾讯 |  | Agent 开发工程师 | 筛选中 |", content)

    def test_update_index_stops_status_table_before_later_markdown_tables(self):
        config = self.vault / "求职" / "配置" / "状态.md"
        config.parent.mkdir(parents=True)
        config.write_text(
            "# 投递状态配置\n\n"
            "| id | label |\n"
            "| --- | --- |\n"
            "| applied | 已投递 |\n\n"
            "## Default Overview Groups\n\n"
            "| group | status IDs |\n"
            "| --- | --- |\n"
            "| 进行中 | `applied` |\n",
            encoding="utf-8",
        )
        self.write_application("自定义状态.md", "示例公司", "数据平台部", "产品分析师", "进行中")
        result = self.run_update_index()
        self.assertEqual(result.returncode, 0, result.stderr)
        content = self.overview.read_text(encoding="utf-8")
        self.assertIn("| 示例公司 | 数据平台部 | 产品分析师 | 进行中 |", content)


if __name__ == "__main__":
    unittest.main()
