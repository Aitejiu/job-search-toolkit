import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).parents[1]
URL_PATTERN = re.compile(r"https?://[^\s)>\"']+")


class PackageHygieneTests(unittest.TestCase):
    def test_fixtures_have_no_private_document_extensions(self):
        fixture_files = [
            path
            for path in (ROOT / "tests" / "fixtures").rglob("*")
            if path.is_file()
        ]
        forbidden = {".pdf", ".doc", ".docx", ".rtf"}
        self.assertTrue(all(path.suffix.lower() not in forbidden for path in fixture_files))

    def test_repository_has_no_obsidian_directory_or_credential_file(self):
        repository_paths = list(ROOT.rglob("*"))
        forbidden_names = {".obsidian", ".env", "cookies.json", "tokens.json"}
        self.assertFalse(
            any(path.name in forbidden_names for path in repository_paths)
        )

    def test_fixture_urls_use_example_invalid(self):
        fixture_files = [
            path
            for path in (ROOT / "tests" / "fixtures").rglob("*")
            if path.is_file() and path.suffix == ".md"
        ]
        urls = [
            url
            for path in fixture_files
            for url in URL_PATTERN.findall(path.read_text(encoding="utf-8"))
        ]
        self.assertTrue(urls)
        self.assertTrue(all("example.invalid" in url for url in urls))

    def test_skill_directory_names_are_lowercase_hyphenated(self):
        skill_directories = [
            path
            for path in (ROOT / "skills").iterdir()
            if path.is_dir() and not path.name.startswith("_")
        ]
        self.assertEqual(
            {path.name for path in skill_directories},
            {
                "job-tracker",
                "resume-registry",
                "resume-ats-optimizer",
                "resume-bullet-writer",
                "tech-resume-optimizer",
            },
        )
        for skill_directory in skill_directories:
            self.assertRegex(skill_directory.name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


if __name__ == "__main__":
    unittest.main()
