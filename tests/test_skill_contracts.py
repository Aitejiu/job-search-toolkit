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


if __name__ == "__main__":
    unittest.main()
