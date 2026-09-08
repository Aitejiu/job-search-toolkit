---
name: job-tracker
description: Use when maintaining a user's private Obsidian job-application records from pasted text, pasted links, or user-triggered browser scans; use when capturing application outcomes, mapping recruiting-site statuses, deduplicating applications, or processing pending confirmations.
metadata:
  short-description: Track job applications in Obsidian
---

# Job Tracker

Maintain application records in the configured private Obsidian vault. The `job-search-toolkit` repository is code and documentation only; never use it as the user's data root.

## Scope and Routing

Handle only four workflows: manual text/link capture, a user-triggered scan of selected recruiting sources, pending-inbox decisions, and rebuilding the generated overview. Read the relevant [data contract](references/data-contract.md), [source adapter contract](references/source-adapters.md), and [workflow reference](references/workflows.md) before changing data.

**REQUIRED SUB-SKILL:** Before interacting with a website, read the available `agent-browser` skill instructions at runtime and use the authorized browser session. Never schedule background scans, store credentials/cookies/tokens, bypass CAPTCHA, or use the public toolkit as a vault.

## Manual Capture

For every manual text or link:

1. Classify it as application evidence, a public job detail page, or an application-status page, then extract every possible record separately.
2. Keep the source URL and field-level evidence. A public job detail page proves only that a job exists; create a candidate or `new_application` pending item, never a formal application.
3. Normalize and deduplicate by the exact `(company, department, position)` normalized tuple. Show the proposed target operation before writing.
4. Require independent confirmation for each record of: company, department, position, event time, source, raw status, canonical status, target operation, evidence, and missing fields. A batch preview does not authorize a batch write.
5. After confirmation, create/update the note, append a timeline event only if its `event_fingerprint` is new, then run `update_index.py`. A confirmed application may use explicit empty fields when metadata is unknown; the overview renders the empty cells, while automatic deduplication waits until the identity tuple is complete.

## User-Triggered Scans

Require an explicit scan request and selected enabled sources. A page may contain multiple applications; process each row/card as an independent snapshot. Use only that source's confirmed status mapping. A new source requires interactive confirmation of each raw-to-canonical mapping before reuse.

Known mapping plus a unique same-source three-field match may update an existing application. New unconfirmed records, unknown raw states, ambiguous matches, and cross-source matches become pending items. After the user confirms an application with missing metadata, write it as an application note with explicit empty fields; it appears in the overview but is not eligible for automatic deduplication until its identity tuple is complete. Unknown status leaves the existing canonical status untouched. An absent row is never rejection, withdrawal, or closure.

Same-source exact matches append only new events. Cross-source matches are user-confirmed merge/split suggestions; after a merge retain every source link. If the user identifies a reapplication, create a separate note only after confirming the split.

## Pending and Failure Handling

Use `confirm`, `edit`, `merge`, `split`, `ignore`, or `retry` decisions; an explicit `reject` may discard a candidate. Pending reasons include `new_application`, `missing_field`, `unknown_status`, `ambiguous_match`, `possible_duplicate`, `unreachable_source`, and `manual_conflict`.

Login failures, CAPTCHA, inaccessible pages, structural changes, malformed links, and still-unconfirmed observations go under `求职/收件箱/` with the reason and evidence. They must not modify an existing application. After every scan, report automatic updates, unchanged records, new pending records, unknown statuses, possible duplicates, and failures.

## Overview Invariant

Run the bundled `skills/job-tracker/scripts/update_index.py --vault <private-vault>` after confirmed writes. It scans only `求职/投递/*.md`, renders explicit empty fields as blank cells, ignores still-pending items, validates before writing, and replaces only the generated marker block in `求职/投递总览.md`. Preserve all user-authored content outside those markers.

Route only these workflows: capture pasted text or links, scan a user-selected recruiting page, process pending confirmations, and rebuild the generated application overview. Read the relevant files in `references/` before changing behavior.
