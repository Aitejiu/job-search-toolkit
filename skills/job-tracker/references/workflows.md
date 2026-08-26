# Job Tracker Workflows

All workflows operate against the configured private vault and keep uncertainty visible until the user resolves it.

## Manual Text or Link Capture

1. Classify the input as pasted application text, a public job detail link, or an application-status link.
2. Extract each possible record independently. Keep the source URL and evidence for every extracted field.
3. Show a confirmation block for every record containing company, department, position, event time, source, raw status, canonical status, target operation, evidence, and missing fields.
4. Normalize the company, department, and position and check the first-release deduplication key.
5. Show the proposed operation: create, update, append an event, create pending, or suggest a duplicate.
6. Require an independent confirm, edit, reject, merge, split, or ignore decision for each record. A batch display never turns into a batch write without per-record decisions.
7. After confirmation, write the application note or pending item, append a new timeline event when its fingerprint is new, and rebuild `求职/投递总览.md`.

A public job detail page proves only that a job exists. It creates a candidate or `new_application` pending item; it cannot prove that the user submitted an application. A pasted link must not be written as an application until the key fields and target operation are confirmed.

## User-Triggered Source Scan

1. Confirm that the user asked for a scan and selected the enabled sources. Never schedule a background scan in the first release.
2. Read the available `agent-browser` skill instructions immediately before website interaction, then use only the user's authorized browser session.
3. Read each configured source adapter and collect a list of snapshots. Process every row or card on a multi-application page independently.
4. Apply the source-specific raw-status mapping. If no mapping exists, pause only the affected snapshot as `unknown_status` and preserve the existing canonical status.
5. Match a snapshot by the normalized company, department, and position triple. A unique same-source match may update automatically; new or ambiguous records become pending.
6. Append a timeline event only when the event fingerprint is new. Do not infer rejection, withdrawal, or closure from an absent row.
7. Rebuild the overview and report automatic updates, unchanged records, new pending records, unknown statuses, possible duplicates, and failures.

An enabled source is not reusable until its first observed raw statuses have interactive mapping confirmation. Login failures, CAPTCHA, inaccessible pages, structural changes, and malformed links produce a failure pending item and do not modify existing application notes.

## Pending Inbox

Pending items live under `求职/收件箱/` and use one of these reasons:

```text
new_application
missing_field
unknown_status
ambiguous_match
possible_duplicate
unreachable_source
manual_conflict
```

The available decisions are `confirm`, `edit`, `merge`, `split`, `ignore`, and `retry`; `reject` is an explicit user decision for a candidate that should not enter the tracker. A merge stores all source links in the surviving application. A split creates a separate note only after the user confirms that two otherwise identical keys represent different applications.

## Overview Rebuild

The deterministic index script scans only `求职/投递/*.md`, validates records before writing, groups rows by configured status order, and replaces only the generated marker block. It must leave user-authored overview text and application timeline text untouched.
