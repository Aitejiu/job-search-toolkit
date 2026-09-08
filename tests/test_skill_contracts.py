import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class JobTrackerSkillContractTests(unittest.TestCase):
    def test_job_tracker_skill_states_capture_and_scan_guards(self):
        content = (ROOT / "skills" / "job-tracker" / "SKILL.md").read_text(encoding="utf-8")
        required_fragments = (
            "Use when",
            "manual text",
            "user-triggered",
            "agent-browser",
            "company",
            "department",
            "position",
            "event time",
            "raw status",
            "canonical status",
            "target operation",
            "evidence",
            "missing fields",
            "absent row",
            "event_fingerprint",
            "update_index.py",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, content)
        self.assertNotIn("TODO", content)

    def test_job_tracker_skill_allows_confirmed_records_with_empty_fields(self):
        content = (ROOT / "skills" / "job-tracker" / "SKILL.md").read_text(encoding="utf-8")
        for fragment in (
            "confirmed application",
            "explicit empty fields",
            "overview",
            "automatic deduplication",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, content)


class ResumeRegistrySkillContractTests(unittest.TestCase):
    def test_resume_registry_skill_states_private_version_guards(self):
        content = (ROOT / "skills" / "resume-registry" / "SKILL.md").read_text(encoding="utf-8")
        required_fragments = (
            "Use when",
            "receive file",
            "PDF",
            "Word",
            "content hash",
            "duplicate",
            "confirm",
            "original file",
            "private",
            "application",
            "never silently overwrite",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, content)
        self.assertNotIn("TODO", content)


class FeishuJobSyncSkillContractTests(unittest.TestCase):
    def test_feishu_job_sync_skill_describes_safe_repeatable_sync(self):
        skill_path = ROOT / "skills" / "feishu-job-sync" / "SKILL.md"
        self.assertTrue(skill_path.exists(), "feishu-job-sync skill has not been implemented")
        content = skill_path.read_text(encoding="utf-8")
        required_fragments = (
            "Use when",
            "Feishu",
            "Obsidian",
            "--vault",
            "--base-url",
            "--base-token",
            "--create",
            "--dry-run",
            "唯一事实源",
            "多维表格",
            "base +record-list",
            "base +record-batch-create",
            "base +record-batch-update",
            "同步键",
            "token",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, content)
        self.assertNotIn("--spreadsheet-url", content)
        self.assertNotIn("table-put", content)
        self.assertNotIn("TODO", content)


if __name__ == "__main__":
    unittest.main()
