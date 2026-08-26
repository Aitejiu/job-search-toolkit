import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]
MODULE_PATH = ROOT / "skills" / "job-tracker" / "scripts" / "markdown_records.py"
SPEC = importlib.util.spec_from_file_location("markdown_records", MODULE_PATH)
markdown_records = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(markdown_records)


class MarkdownRecordTests(unittest.TestCase):
    def test_normalize_component_collapses_space_case_and_punctuation(self):
        self.assertEqual(
            markdown_records.normalize_component(" 示例公司， Data  Platform "),
            "示例公司 data platform",
        )

    def test_build_dedupe_key_requires_all_three_identity_fields(self):
        self.assertEqual(
            markdown_records.build_dedupe_key("示例公司", "数据平台部", "产品分析师"),
            ("示例公司", "数据平台部", "产品分析师"),
        )
        self.assertIsNone(
            markdown_records.build_dedupe_key("示例公司", "", "产品分析师")
        )

    def test_event_fingerprint_is_stable_and_sha256_prefixed(self):
        args = (
            "example-site",
            "https://example.invalid/a",
            "status_changed",
            "2026-08-27 14:30",
            "screening",
            ("示例公司", "数据平台部", "产品分析师"),
        )
        first = markdown_records.event_fingerprint(*args)
        second = markdown_records.event_fingerprint(*args)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^sha256:[0-9a-f]{64}$")

    def test_parse_frontmatter_reads_scalars_and_inline_lists(self):
        fields = markdown_records.parse_frontmatter(
            '---\ntype: application\nsource_urls: ["https://example.invalid/a"]\n---\nbody'
        )
        self.assertEqual(fields["type"], "application")
        self.assertEqual(fields["source_urls"], ["https://example.invalid/a"])


if __name__ == "__main__":
    unittest.main()
