# Resume Registry Contract

The resume registry records metadata for private resume assets. The original file remains in the user's private data repository or in a user-selected local path; the public toolkit repository never receives it.

## Version Note

Each registered version is a separate Markdown note under the configured private vault, normally `求职/简历/版本/`. It has these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `type` | yes | Must be `resume_version`. |
| `name` | yes | Human-readable version name. |
| `language` | recommended | Language or locale of the resume. |
| `created_at` | yes | Date the version was registered. |
| `target_direction` | recommended | Role or direction this version targets. |
| `file_path` | recommended | Private-vault-relative path to the preserved original. |
| `source_path` | yes | The source path supplied by the user at registration time. |
| `content_sha256` | yes | SHA-256 hash of the original file bytes. |

The registration note is separate from every application note. An application may link to a confirmed version with an Obsidian link in its `resume_version` field.

## Registration Rules

Support common private source files such as PDF, Word, RTF, and plain text when the local environment can read them. Preserve the original bytes and record the content hash before offering a version for linking. Identical hashes are a reuse hint; never silently create a duplicate version note.

Extracted text and a short summary are user-reviewable metadata, not a replacement for the original file. Do not rewrite, optimize, or silently associate a resume with an application. Confirm the version metadata and each requested application link independently.

## Privacy Boundary

Do not place the uploaded file, its extracted private text, credentials, cookies, or tokens under this public repository. The vault path and any source path are runtime inputs. A public fixture may use synthetic names and `example.invalid` URLs only.
