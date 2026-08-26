# Job Search Toolkit Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

Goal: Build a standalone, open-source-ready skill repository containing job-tracker and resume-registry, a shared Obsidian contract, deterministic Markdown index tooling, and no dependency on personal data.

Architecture: The repository is a skills monorepo. Each skill has its own SKILL.md, agents/openai.yaml, references, and templates so it can be discovered independently. job-tracker owns application records, events, source mappings, pending items, and the generated overview. resume-registry owns uploaded resume versions and links confirmed versions into application notes. User data stays in a separately configured private Obsidian vault or private data repository.

Tech Stack: Markdown skill instructions with YAML frontmatter, Python 3 standard library, browser interaction through the available agent-browser skill at runtime, and unittest for deterministic local tests. No network service, database, third-party Python dependency, credential store, or live website fixture is required for the first release.

---

## Repository Map

All implementation files belong under /Users/aitejiu/resume/job-search-toolkit. The parent /Users/aitejiu/resume repository remains the private resume/design repository and must not be used as the public skill repository.

    job-search-toolkit/
      .gitignore
      README.md
      skills/
        job-tracker/
          SKILL.md
          agents/openai.yaml
          references/
            data-contract.md
            source-adapters.md
            workflows.md
          templates/
            application.md
            pending-item.md
            status-config.md
        resume-registry/
          SKILL.md
          agents/openai.yaml
          references/
            resume-contract.md
          templates/
            resume-version.md
      tests/
        __init__.py
        fixtures/vault/求职/
          投递/
          配置/来源/
          投递总览.md
        test_markdown_records.py
        test_update_index.py
        test_package_hygiene.py
      skills/job-tracker/scripts/
        __init__.py
        markdown_records.py
        update_index.py
      docs/superpowers/plans/2026-08-27-job-search-toolkit.md

Personal resumes, real company names, real URLs, real interview transcripts, .obsidian, credentials, cookies, tokens, and the user's vault are not allowed anywhere under this tree.

### Task 1: Bootstrap the Public Skill Repository

Files:
- Modify: /Users/aitejiu/resume/.gitignore
- Create: .gitignore
- Create: README.md
- Create: skills/job-tracker/SKILL.md
- Create: skills/job-tracker/agents/openai.yaml
- Create: skills/job-tracker/references/
- Create: skills/resume-registry/SKILL.md
- Create: skills/resume-registry/agents/openai.yaml
- Create: skills/resume-registry/references/

- [ ] Step 1: Confirm the independent repository root

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit rev-parse --show-toplevel

Expected output:

    /Users/aitejiu/resume/job-search-toolkit

If the command fails, run git -C /Users/aitejiu/resume/job-search-toolkit init. Do not initialize or change the parent private repository.

- [ ] Step 2: Generate both skill skeletons with the bundled initializer

Run:

    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/init_skill.py job-tracker --path /Users/aitejiu/resume/job-search-toolkit/skills --resources references
    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/init_skill.py resume-registry --path /Users/aitejiu/resume/job-search-toolkit/skills --resources references

Do not pass --examples. Keep the generated agents/openai.yaml files, then replace the generated body and frontmatter with the task-specific content in Tasks 4 and 5.

- [ ] Step 3: Keep the public repository out of the private parent repository

Use apply_patch in the parent private repository to create or update /Users/aitejiu/resume/.gitignore with this line:

    /job-search-toolkit/

Do not add the parent .gitignore to the public repository. Commit the parent change separately:

    git -C /Users/aitejiu/resume add .gitignore
    git -C /Users/aitejiu/resume commit -m "chore: keep public toolkit repository separate"

- [ ] Step 4: Add the public-repository ignore policy

Write .gitignore with these exact categories:

    __pycache__/
    *.py[cod]
    .pytest_cache/
    .mypy_cache/
    .DS_Store

    # Private Obsidian vault and personal source material
    .obsidian/
    /求职/
    *.pdf
    *.doc
    *.docx
    *.rtf
    *.txt
    *.log

    # Local credentials and browser state
    .env
    .env.*
    *.cookie
    cookies.json
    tokens.json

The synthetic fixtures under tests/fixtures use Markdown and example.invalid URLs, so they remain tracked.

- [ ] Step 5: Add the repository README

Write README.md with these sections:

    # Job Search Toolkit

    An open-source Codex skill toolkit for maintaining a job seeker's private Obsidian records.

    ## Skills

    - job-tracker: capture application text or links, scan user-selected pages on demand, map source statuses, deduplicate applications, manage confirmations, and rebuild the overview.
    - resume-registry: register uploaded resume files as versioned private assets and link confirmed versions to applications.

    The repository will later host separate interview-organizer and job-review skills. They are not part of the first release.

    ## Data Boundary

    The toolkit repository contains reusable instructions, templates, synthetic fixtures, and tests. It never contains a real resume, private Obsidian vault, application history, interview transcript, credential, browser session, or token.

    At runtime, configure the skills with a path to a private Obsidian vault or private data repository. The toolkit repository and the private data repository are versioned and published independently.

    ## Validation

    Run python -m unittest discover -s tests -v for deterministic tests. Run the bundled skill validator against each skill directory before publishing.

- [ ] Step 6: Validate the generated skeletons

Run:

    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/job-tracker
    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/resume-registry

Expected result for each command: successful validation of frontmatter and skill naming. Generated scaffold text is not acceptable in the committed files.

- [ ] Step 7: Commit the public repository bootstrap

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add .gitignore README.md skills/job-tracker skills/resume-registry docs/superpowers/plans/2026-08-27-job-search-toolkit.md
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "chore: bootstrap job search skills"

### Task 2: Define the Shared Obsidian Contract and Templates

Files:
- Create: skills/job-tracker/references/data-contract.md
- Create: skills/job-tracker/references/source-adapters.md
- Create: skills/job-tracker/references/workflows.md
- Create: skills/job-tracker/templates/application.md
- Create: skills/job-tracker/templates/pending-item.md
- Create: skills/job-tracker/templates/status-config.md
- Create: skills/resume-registry/references/resume-contract.md
- Create: skills/resume-registry/templates/resume-version.md

- [ ] Step 1: Define the application frontmatter and timeline

Make application.md use this exact shape:

    ---
    type: application
    company: 示例公司
    department: 数据平台部
    position: 产品分析师
    status: applied
    first_applied_at: 2026-08-27
    last_updated_at: 2026-08-27
    next_action: 等待反馈
    next_action_due: 2026-09-03
    resume_version: "[[求职/简历/版本/简历-产品分析-2026-08-27]]"
    source_urls: ["https://example.invalid/application/123"]
    ---

    # 示例公司 / 数据平台部 / 产品分析师

    ## Timeline

    ### 2026-08-27 14:30 | application_created
    - status: applied
    - raw_status: 已投递
    - source: manual-text
    - source_url: https://example.invalid/application/123
    - evidence: 用户确认已提交申请
    - event_fingerprint: 由系统根据来源和事件字段生成

Document that status uses the configured internal ID, display labels come from 求职/配置/状态.md, and the deduplication key is the normalized company, department, and position. Define event_fingerprint as a SHA-256 value over source name, normalized source URL, event type, event time, raw status, and deduplication key.

- [ ] Step 2: Define standard statuses and source mappings

Write status-config.md with the default IDs and labels:

    | id | label |
    | --- | --- |
    | ready_to_apply | 待投递 |
    | applied | 已投递 |
    | screening | 筛选中 |
    | assessment | 测评中 |
    | interviewing | 面试中 |
    | offer | Offer |
    | accepted | 已接受 |
    | rejected | 拒绝 |
    | withdrawn | 撤回 |
    | closed | 无回应/关闭 |

Document that mappings are isolated by source name, unknown raw states leave the existing canonical status unchanged, and only the affected record enters the pending inbox.

- [ ] Step 3: Define the source adapter contract

Write source-adapters.md so each adapter returns a list of snapshots with these fields:

    source_name
    source_url
    page_type
    company
    department
    position
    external_id
    raw_status
    displayed_at
    observed_at
    evidence

The reference must support one page containing multiple applications, distinguish a public job detail page from an authenticated application-status page, and state that an absent row is not rejection or closure. Source configuration fields are enabled, entry_url, page_type, status_mapping, and field_aliases.

- [ ] Step 4: Define pending items and confirmations

Write pending-item.md and workflows.md with these reasons:

    new_application
    missing_field
    unknown_status
    ambiguous_match
    possible_duplicate
    unreachable_source
    manual_conflict

Each manual text or link confirmation must show company, department, position, event time, source, raw status, canonical status, target operation, evidence, and missing fields. Multiple records may be displayed together, but each record has an independent confirm, edit, reject, merge, split, or ignore result.

- [ ] Step 5: Define the resume-version contract

Write resume-version.md with this exact shape:

    ---
    type: resume_version
    name: 产品分析方向简历 2026-08-27
    language: zh-CN
    created_at: 2026-08-27
    target_direction: 产品分析
    file_path: "求职/简历/文件/resume-cn.pdf"
    source_path: "/private/path/resume-cn.pdf"
    content_sha256: 由系统计算
    ---

    # 产品分析方向简历 2026-08-27

    ## Extracted Summary

    用户确认后的简历文本摘要。

The contract must state that the original file stays in the private data repository or user-selected local path, the registration note is separate from application notes, identical content is offered for reuse rather than silently duplicated, and the toolkit repository never receives the file.

- [ ] Step 6: Commit the contracts and templates

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add skills/job-tracker/references skills/job-tracker/templates skills/resume-registry/references skills/resume-registry/templates
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "docs: define Obsidian job search contracts"

### Task 3: Build and Test Deterministic Markdown Record Tools

Files:
- Create: skills/job-tracker/scripts/__init__.py
- Create: skills/job-tracker/scripts/markdown_records.py
- Create: skills/job-tracker/scripts/update_index.py
- Create: tests/__init__.py
- Create: tests/test_markdown_records.py
- Create: tests/test_update_index.py
- Create: tests/fixtures/vault/求职/投递/示例公司-数据平台部-产品分析师.md
- Create: tests/fixtures/vault/求职/投递/第二示例公司-研发部-数据分析师.md
- Create: tests/fixtures/vault/求职/投递总览.md

- [ ] Step 1: Write failing normalization and frontmatter tests

Create tests/test_markdown_records.py with this executable test body:

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

Run:

    python -m unittest tests.test_markdown_records -v

Expected result before implementation: the test module fails because markdown_records.py is empty or does not expose the four functions.

- [ ] Step 2: Implement the record parser and identity functions

Implement these public functions in markdown_records.py:

    parse_frontmatter(markdown: str) -> dict[str, object]
    normalize_component(value: str) -> str
    build_dedupe_key(company: str, department: str, position: str) -> tuple[str, str, str] | None
    event_fingerprint(source: str, source_url: str, event_type: str, occurred_at: str, raw_status: str, dedupe_key: tuple[str, str, str]) -> str

Use only the standard library. parse_frontmatter accepts one opening and one closing frontmatter fence, scalar strings, empty values, and JSON-compatible inline arrays. It raises ValueError for duplicate keys and unterminated frontmatter. normalize_component applies Unicode NFKC, trims and collapses whitespace, casefolds Latin text, and removes punctuation while preserving Chinese characters. build_dedupe_key returns None when any component is empty. event_fingerprint joins the normalized inputs with a unit-separator, hashes them with SHA-256, and returns sha256 followed by 64 lowercase hexadecimal characters.

- [ ] Step 3: Run the record tests

Run:

    python -m unittest tests.test_markdown_records -v

Expected result: all four tests pass.

- [ ] Step 4: Write failing index-generation tests

Create tests/test_update_index.py with this executable test class. The helper methods are part of the test file and must not be omitted:

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


    if __name__ == "__main__":
        unittest.main()

The failing-test run must invoke the CLI through sys.executable and assert that malformed records leave the overview byte-for-byte unchanged.

- [ ] Step 5: Implement index generation

Implement update_index.py with this CLI:

    python skills/job-tracker/scripts/update_index.py --vault /absolute/path/to/vault

The script scans only <vault>/求职/投递/*.md, accepts type: application, requires company, department, position, status, and last_updated_at, and loads status labels and order from <vault>/求职/配置/状态.md when present. If that file is absent, use the ten defaults in status-config.md. Render the fixed columns 公司, 部门, 职位, 当前状态, 最近更新时间, 下一步行动, 截止日期, 简历版本, 来源链接.

Group rows under 进行中, 待跟进, 面试中, and 已结束 based on status IDs. Pending items are not application rows. Preserve all content outside the generated markers, write through a temporary file and os.replace only after all records validate, print records scanned, rows rendered, and validation errors, and exit nonzero on malformed frontmatter or missing required fields.

The script must not infer rejection from a missing file, mutate application notes, or use the public repository as a data vault by default.

- [ ] Step 6: Run the index tests

Run:

    python -m unittest tests.test_markdown_records tests.test_update_index -v

Expected result: all tests pass, including manual-content preservation and no-write-on-error.

- [ ] Step 7: Commit the deterministic tooling

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add skills/job-tracker/scripts tests
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "feat: add deterministic Obsidian index tooling"

### Task 4: Implement the job-tracker Skill Instructions

Files:
- Modify: skills/job-tracker/SKILL.md
- Modify: skills/job-tracker/agents/openai.yaml

- [ ] Step 1: Write the skill frontmatter and routing rules

Use this frontmatter:

    ---
    name: job-tracker
    description: Maintain a user's private Obsidian job-application records from pasted text, pasted links, and user-triggered browser scans; use when capturing application outcomes, mapping recruiting-site statuses, deduplicating applications, or processing pending confirmations.
    metadata:
      short-description: Track job applications in Obsidian
    ---

The body routes only manual text/link capture, user-triggered source scans, pending-inbox processing, and overview rebuild. It states that the configured private vault is the data root and the job-search-toolkit repository is code only. Link references to data-contract.md, source-adapters.md, and workflows.md.

- [ ] Step 2: Encode the manual input workflow

Write the flow classify, extract, show evidence, normalize and deduplicate, show action, confirm, and write. For every pasted text or link, require independent confirmation of company, department, position, event time, source, raw status, canonical status, target operation, evidence, and missing fields. A public job detail page creates only a candidate or pending item; it cannot prove an application.

After a confirmed write, append a timeline event and call update_index.py. Do not write an application note before the required confirmation.

- [ ] Step 3: Encode manual browser-scan behavior

Read the available agent-browser skill at runtime before interacting with a website. Require a user-triggered scan and selected enabled sources. Do not schedule background scans, store credentials, bypass CAPTCHA, or infer state from an absent row.

Treat each page as a list of snapshots. Known source mapping plus a unique three-field match may update automatically. New records, unknown raw states, missing fields, ambiguous matches, and cross-source possible duplicates become pending items. A new source requires interactive mapping confirmation before reuse.

- [ ] Step 4: Encode deduplication and event idempotency

Use the exact normalized company, department, and position tuple as the first-release deduplication key. Same-source exact matches update one application and append only new events. Cross-source matches are suggestions for user-confirmed merge or split. Store all source links after merge. Use event_fingerprint to skip repeated observations.

When the user says a same-key application is a reapplication, create a separate note only after confirming the split.

- [ ] Step 5: Encode pending inbox and failures

Define actions confirm, edit, merge, split, ignore, and retry. Unknown status leaves the existing canonical status untouched. Login failures, CAPTCHA, inaccessible pages, structural changes, and malformed links record the reason under 求职/收件箱/ and do not modify an existing application.

After every scan, report counts for automatic updates, unchanged records, new pending records, unknown statuses, possible duplicates, and failures. Never overwrite user-authored text outside generated overview markers.

- [ ] Step 6: Set UI metadata and validate

Set agents/openai.yaml interface metadata to:

    display_name: Job Tracker
    short_description: Capture and maintain private Obsidian job applications
    default_prompt: Process this application text or link using the configured private Obsidian vault, confirm key fields, deduplicate by company, department, and position, and update the application timeline.

Preserve generated policy fields. Run:

    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/job-tracker

Expected result: successful validation with no scaffold text.

- [ ] Step 7: Commit the tracker skill

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add skills/job-tracker/SKILL.md skills/job-tracker/agents/openai.yaml
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "feat: add Obsidian job tracker skill"

### Task 5: Implement the resume-registry Skill Instructions

Files:
- Modify: skills/resume-registry/SKILL.md
- Modify: skills/resume-registry/agents/openai.yaml

- [ ] Step 1: Write the skill frontmatter and scope

Use this frontmatter:

    ---
    name: resume-registry
    description: Register uploaded resume files as versioned private assets, extract basic metadata, detect likely duplicate versions, and link confirmed versions to Obsidian job applications; use when a user uploads or wants to catalog a resume.
    metadata:
      short-description: Register private resume versions
    ---

The body excludes public repository storage, automatic resume rewriting, and automatic association with an application.

- [ ] Step 2: Encode the upload and confirmation workflow

Write the flow receive file, identify format, extract available text and metadata, detect likely duplicate, show version fields and storage choice, confirm, create private version note, and offer application links.

Required confirmation fields are version name, language, created or updated date, target direction, storage path or file link, and whether the version may be associated with future applications. Preserve the original file and never silently overwrite an existing version.

Support PDF, Word, plain text, and other locally extractable formats through tools available at runtime. If extraction fails, retain the file reference, record the reason, and let the user provide a label and summary manually. Do not claim successful extraction without evidence.

- [ ] Step 3: Encode duplicate detection and application linking

Use content hash when available, then normalized version metadata and filename as a duplicate hint. Present reuse existing and create new version choices. Link applications to the confirmed note under 求职/简历/版本/ and never copy the resume body into every application note.

- [ ] Step 4: Set UI metadata and validate

Set agents/openai.yaml interface metadata to:

    display_name: Resume Registry
    short_description: Register private resume files and versions
    default_prompt: Register this uploaded resume in the configured private Obsidian vault, confirm its version metadata, preserve the original file, and make it available for linking to applications.

Run:

    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/resume-registry

Expected result: successful validation with no scaffold text.

- [ ] Step 5: Commit the resume registry skill

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add skills/resume-registry/SKILL.md skills/resume-registry/agents/openai.yaml
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "feat: add private resume registry skill"

### Task 6: Add Synthetic Fixtures and Package-Hygiene Tests

Files:
- Create: tests/test_package_hygiene.py
- Create: tests/fixtures/vault/求职/配置/状态.md
- Create: tests/fixtures/vault/求职/配置/来源/示例招聘平台.md
- Modify: tests/fixtures/vault/求职/投递/示例公司-数据平台部-产品分析师.md
- Modify: tests/fixtures/vault/求职/投递/第二示例公司-研发部-数据分析师.md

- [ ] Step 1: Add fictional fixtures

Use fictional Chinese names, example.invalid URLs, synthetic dates, two application statuses, one source mapping, one timeline per application, and one repeated observation that the index must render once.

- [ ] Step 2: Add package-hygiene tests

Create tests/test_package_hygiene.py with this complete test body:

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
            self.assertEqual({path.name for path in skill_directories}, {"job-tracker", "resume-registry"})
            for skill_directory in skill_directories:
                self.assertRegex(skill_directory.name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


    if __name__ == "__main__":
        unittest.main()

The tests must fail if a credential filename, private data directory, or URL outside example.invalid appears in fixtures. The plan's documented local path is not fixture data and is excluded from the URL scan.

- [ ] Step 3: Run all local tests

Run:

    python -m unittest discover -s tests -v

Expected result: all record, index, and package-hygiene tests pass.

- [ ] Step 4: Commit fixtures and hygiene tests

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add tests
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "test: add synthetic vault fixtures"

### Task 7: End-to-End Validation and Release Boundary Check

Files:
- Modify: README.md
- Verify: .gitignore
- Verify: all skill, reference, template, script, and test files

- [ ] Step 1: Run the deterministic suite from the public repository root

Run:

    cd /Users/aitejiu/resume/job-search-toolkit
    python -m unittest discover -s tests -v

Expected result: all tests pass without reading /Users/aitejiu/resume/resume-cn.pdf or any path outside repository fixtures.

- [ ] Step 2: Run both skill validators

Run:

    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/job-tracker
    python /Users/aitejiu/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/aitejiu/resume/job-search-toolkit/skills/resume-registry

Expected result: both skills validate successfully and contain no unfinished scaffold markers.

- [ ] Step 3: Exercise the index tool against the synthetic vault

Run:

    python skills/job-tracker/scripts/update_index.py --vault tests/fixtures/vault

Expected result: the command exits zero, reports the fixture record count, and updates only the generated block in tests/fixtures/vault/求职/投递总览.md.

- [ ] Step 4: Inspect the public diff for private-data leakage

Run:

    git status --short
    git diff --check HEAD~5..HEAD
    rg -n -i 'resume-cn|aitejiu|/Users/|cookie|token|password|secret|boss[.]直聘|linkedin[.]com|zhipin[.]com' --glob '!docs/superpowers/plans/**' .

Expected result: no real personal paths, credentials, or non-synthetic recruiting URLs appear in implementation files or fixtures. The plan may document the local repository path.

- [ ] Step 5: Update README with final validation commands and commit

Keep README limited to reusable toolkit boundaries, validation commands, and data separation. Do not add a personal setup path, real source URL, or example resume content.

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit add README.md
    git -C /Users/aitejiu/resume/job-search-toolkit commit -m "docs: document toolkit validation"

- [ ] Step 6: Record the final repository state

Run:

    git -C /Users/aitejiu/resume/job-search-toolkit status --short
    git -C /Users/aitejiu/resume/job-search-toolkit log --oneline --decorate -8

Expected result: the public skill repository has no unexpected untracked files, and the private parent repository still owns the personal resume files separately.

## Plan Self-Review

- The first phase covers private-vault integration, pasted text/link capture, user-triggered multi-record scans, source-specific status mapping, three-field deduplication, pending confirmations, overview generation, and resume-version registration.
- Interview transcription, reusable knowledge extraction, job review, scheduled scans, Feishu synchronization, credential storage, and resume rewriting remain outside this plan.
- The public repository has no dependency on the private parent repository at runtime; the private vault path is supplied by configuration.
- Every automatic mutation has either a user-confirmation rule or idempotent script behavior; unknown and ambiguous input does not overwrite canonical state.
- Browser interaction is limited to a user-triggered scan of an authorized session through agent-browser.
- All test fixtures use fictional data and example.invalid URLs.
