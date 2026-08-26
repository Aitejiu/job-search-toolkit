---
name: resume-registry
description: Use when a user uploads a resume, wants to catalog a resume version, checks for duplicate resume content, or asks to link a confirmed version to an Obsidian job application.
metadata:
  short-description: Register resume versions in Obsidian
---

# Resume Registry

Register resume files as private, versioned assets in the configured Obsidian vault. The `job-search-toolkit` repository contains no personal source files or extracted resume text. Do not rewrite, optimize, or automatically associate a resume with an application.

## Workflow

1. `receive file`: identify the local path, file name, format, and whether the user wants registration, reuse, or application linking.
2. Extract available text and metadata using tools available at runtime. Support PDF, Word, plain text, RTF, and other locally extractable formats; do not claim successful extraction without evidence.
3. Compute a content hash, stored as `content_sha256`, from the original file bytes when accessible. Use it first, then normalized version metadata and filename, as a duplicate hint.
4. Show the proposed version note, storage path or file link, extraction result, hash, and any duplicate candidates. Preserve the original file and never silently overwrite an existing version.
5. Require confirmation of every version's name, language, created or updated date, target direction, storage path or file link, and whether it may be associated with future applications.
6. After confirmation, create a separate note under the private `求职/简历/版本/` path using [resume-contract.md](references/resume-contract.md) and [resume-version.md](templates/resume-version.md). Keep the original file at the confirmed private path.
7. Offer application links only after the version note is confirmed. Each application association is a separate confirmable action and stores an Obsidian link instead of copying the resume body.

## Extraction and Failure Rules

If extraction fails or a format is unsupported, retain the original file reference, record the failure reason in the private version note, and let the user provide a label and summary manually. Do not block registration merely because text extraction failed, but do not invent extracted content.

For an identical hash, present `reuse existing` and `create new version` choices. A new target direction or materially different metadata is still a user decision, not an automatic duplicate override. Never put the uploaded file, private text, credentials, cookies, or tokens in this public repository.

## Application Links

Link confirmed versions from application notes through `resume_version`. Keep version notes independent so interview notes and application timelines can reference the same asset without duplicating its contents. If the requested application is ambiguous, create a pending decision instead of guessing.
