# Source Adapter Contract

Source adapters translate one user-authorized recruiting site into neutral application snapshots. An adapter may read a page only during a user-triggered scan of an enabled source.

## Snapshot Shape

Each adapter returns a list. One page can therefore produce several independent snapshots.

| Field | Meaning |
| --- | --- |
| `source_name` | Stable configured source name, such as `example-career-site`. |
| `source_url` | URL of the page that supplied the observation. |
| `page_type` | `job_detail` or `application_status`. |
| `company` | Company shown by the source, when available. |
| `department` | Department or team shown by the source, when available. |
| `position` | Position title shown by the source, when available. |
| `external_id` | Source-specific application or posting identifier, when available. |
| `raw_status` | Exact status text shown by the source. |
| `displayed_at` | Timestamp or date displayed by the source, when available. |
| `observed_at` | Timestamp at which the scan read the page. |
| `evidence` | Short quoted or structured description of the visible fields supporting the snapshot. |

The adapter must preserve the raw status and evidence. It must not turn a missing field into a guessed value.

## Page Types

`job_detail` is a public job detail page. It can create a candidate or a `new_application` pending item, but it cannot prove that the user submitted an application.

`application_status` is an authenticated or otherwise user-authorized status page. It may contain many rows/cards at once; each row/card is processed independently. An absent row is not rejection, withdrawal, or closure.

## Source Configuration

Each enabled source is configured under `求职/配置/来源/`. Its configuration exposes these fields:

| Field | Meaning |
| --- | --- |
| `enabled` | Whether the user selected this source for a scan. |
| `entry_url` | User-provided starting URL. |
| `page_type` | Expected page type. |
| `status_mapping` | Raw source statuses mapped to canonical internal IDs. |
| `field_aliases` | Source labels mapped to `company`, `department`, `position`, and other snapshot fields. |

The first time a source is used, show the observed raw statuses and ask the user to confirm each mapping before reusing it. Mappings are isolated by `source_name`; a mapping from one site must never be applied to another site by text similarity alone.

## Scan Outcomes

Known mappings plus a unique normalized company/department/position match may update an existing application. New unconfirmed records, unknown raw statuses, ambiguous matches, and cross-source possible duplicates become pending items. A user-confirmed application may keep a missing field empty and remain visible in the overview, but it is not eligible for automatic deduplication until the identity tuple is complete. An unknown raw status leaves the existing canonical status unchanged.

Report automatic updates, unchanged records, new pending records, unknown statuses, possible duplicates, and failures after every scan.
