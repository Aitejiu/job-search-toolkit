# Job Search Toolkit

An open-source Codex skill toolkit for maintaining a job seeker's private Obsidian records.

## Skills

- `job-tracker`: capture application text or links, scan user-selected pages on demand, map source statuses, deduplicate applications, manage confirmations, and rebuild the overview.
- `resume-registry`: register uploaded resume files as versioned private assets and link confirmed versions to applications.
- `resume-ats-optimizer`: audit ATS compatibility and job-description keyword coverage.
- `resume-bullet-writer`: turn weak resume bullets into achievement-focused statements.
- `tech-resume-optimizer`: improve resumes for software, product, and other technical roles.

The three resume optimization skills above are imported from [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills).

The repository will later host separate `interview-organizer` and `job-review` skills. They are not part of the first release.

## Data Boundary

The toolkit repository contains reusable instructions, templates, synthetic fixtures, and tests. It never contains a real resume, private Obsidian vault, application history, interview transcript, credential, browser session, or token.

At runtime, configure the skills with a path to a private Obsidian vault or private data repository. The toolkit repository and the private data repository are versioned and published independently.

## Validation

From the repository root, run:

```bash
python3 -m unittest discover -s tests -v
python3 /path/to/quick_validate.py skills/job-tracker
python3 /path/to/quick_validate.py skills/resume-registry
python3 skills/job-tracker/scripts/update_index.py --vault tests/fixtures/vault
```

The validator path is supplied by the local Codex installation. The final command exercises the generated overview against synthetic data only.
