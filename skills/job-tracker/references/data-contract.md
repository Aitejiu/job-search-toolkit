# Job Tracker Data Contract

This contract describes the Markdown records stored in the user's configured private Obsidian vault. The public toolkit repository is never the data root.

## Vault Layout

The first-release paths are:

```text
求职/
  投递/
  收件箱/
  配置/
    状态.md
    字段别名.md
    规则.md
    来源/
  投递总览.md
```

The vault path is supplied at runtime. A skill must not assume that the current code repository is the vault.

## Application Record

Every application note has YAML frontmatter with these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | yes | Must be `application`. |
| `company` | yes | Company name as confirmed by the user. |
| `department` | yes | Department or team; use an explicit empty value only while the record is pending. |
| `position` | yes | Position title as confirmed by the user. |
| `status` | yes | Canonical internal status ID. |
| `first_applied_at` | recommended | Date of the first confirmed submission. |
| `last_updated_at` | yes | Date of the latest confirmed state change or observation. |
| `next_action` | recommended | The next action for the candidate. |
| `next_action_due` | optional | Due date for the next action. |
| `resume_version` | optional | Obsidian link to a registered resume version. |
| `source_urls` | recommended | JSON-compatible inline list of source URLs. |

The note title is a readable rendering of `company / department / position`; the normalized triple, not the title, is the first-release identity key.

`status` stores the configured internal ID. Display labels and ordering come from `求职/配置/状态.md`; do not replace an ID with a translated label in frontmatter.

## Deduplication Identity

The first-release deduplication key is:

```text
(normalize(company), normalize(department), normalize(position))
```

Normalization applies Unicode NFKC, trims and collapses whitespace, case-folds Latin text, and removes punctuation while preserving Chinese characters. If any component is empty, the key is unavailable and the record must be pending instead of silently merged.

A same-source observation with the same key updates the existing note and appends only a new event when its event fingerprint is new. A cross-source match is only a possible duplicate until the user chooses merge or split. A confirmed reapplication can create a separate note after the user confirms the split.

## Timeline Events

The `## Timeline` section is append-only from the skill's perspective. Each event records at least:

```text
occurred_at
event_type
status
raw_status
source
source_url
evidence
event_fingerprint
```

The canonical `status` on the frontmatter is a convenience projection of the latest confirmed event. The timeline remains the source of historical truth. Do not infer rejection, closure, or a status transition merely because a source row disappeared.

`event_fingerprint` is a string in the form `sha256:<64 lowercase hexadecimal characters>`. It is the SHA-256 digest of the following normalized values joined with a unit-separator character:

```text
source name, normalized source URL, event type, event time, raw status, deduplication key
```

Repeated observations with the same fingerprint must not append duplicate timeline events.

## Generated Overview

`求职/投递总览.md` is a generated view, not a second source of truth. The generator owns only the content between:

```text
<!-- job-tracker:generated:start -->
<!-- job-tracker:generated:end -->
```

It must preserve all user-authored content outside those markers and must validate all application records before replacing the file.
