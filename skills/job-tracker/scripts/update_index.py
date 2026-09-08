"""Rebuild the generated application overview in a private Obsidian vault."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

try:
    from markdown_records import parse_frontmatter, normalize_component
except ImportError:  # pragma: no cover - supports package-style imports too
    from .markdown_records import parse_frontmatter, normalize_component


START_MARKER = "<!-- job-tracker:generated:start -->"
END_MARKER = "<!-- job-tracker:generated:end -->"
GROUP_ORDER = ("进行中", "待跟进", "面试中", "已结束")
DEFAULT_STATUS_ROWS = (
    ("ready_to_apply", "待投递"),
    ("applied", "已投递"),
    ("screening", "筛选中"),
    ("assessment", "测评中"),
    ("interviewing", "面试中"),
    ("offer", "Offer"),
    ("accepted", "已接受"),
    ("rejected", "拒绝"),
    ("withdrawn", "撤回"),
    ("closed", "无回应/关闭"),
)
DEFAULT_STATUS_GROUPS = {
    "ready_to_apply": "进行中",
    "applied": "进行中",
    "screening": "进行中",
    "assessment": "进行中",
    "interviewing": "面试中",
    "offer": "待跟进",
    "accepted": "待跟进",
    "rejected": "已结束",
    "withdrawn": "已结束",
    "closed": "已结束",
}
REQUIRED_FIELDS = ("company", "department", "position", "status", "last_updated_at")
NON_EMPTY_REQUIRED_FIELDS = ("company", "position", "status", "last_updated_at")
TABLE_COLUMNS = (
    "公司",
    "部门",
    "职位",
    "当前状态",
    "最近更新时间",
    "下一步行动",
    "截止日期",
    "简历版本",
    "来源链接",
)


def load_status_config(path: Path) -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
    """Load status labels/order and optional groups from a Markdown table."""

    if not path.exists():
        rows = list(DEFAULT_STATUS_ROWS)
        return rows, dict(DEFAULT_STATUS_GROUPS)

    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = None
    headers: List[str] = []
    for index, line in enumerate(lines):
        cells = _table_cells(line)
        normalized_headers = [cell.casefold() for cell in cells]
        if cells and "id" in normalized_headers and "label" in normalized_headers:
            header_index = index
            headers = cells
            break
    if header_index is None:
        raise ValueError(f"status config has no id/label table: {path}")

    normalized_headers = [cell.casefold() for cell in headers]
    id_index = normalized_headers.index("id")
    label_index = normalized_headers.index("label")
    group_index = normalized_headers.index("group") if "group" in normalized_headers else None
    rows: List[Tuple[str, str]] = []
    groups = dict(DEFAULT_STATUS_GROUPS)
    seen = set()
    for line in lines[header_index + 1 :]:
        cells = _table_cells(line)
        if not cells:
            if line.strip():
                break
            continue
        if _is_table_separator(cells):
            continue
        if max(id_index, label_index) >= len(cells):
            raise ValueError(f"status config row has too few columns: {line}")
        status_id = cells[id_index].strip()
        label = cells[label_index].strip()
        if not status_id or not label:
            raise ValueError(f"status config row has an empty id or label: {line}")
        if status_id in seen:
            raise ValueError(f"duplicate status id in config: {status_id}")
        seen.add(status_id)
        rows.append((status_id, label))
        if group_index is not None and group_index < len(cells) and cells[group_index].strip():
            group = cells[group_index].strip()
            groups[status_id] = group if group in GROUP_ORDER else "进行中"

    if not rows:
        raise ValueError(f"status config has no status rows: {path}")
    return rows, groups


def _table_cells(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or "|" not in stripped[1:]:
        return []
    content = stripped[1:-1] if stripped.endswith("|") else stripped[1:]
    return [cell.strip() for cell in content.split("|")]


def _is_table_separator(cells: Iterable[str]) -> bool:
    return all(cell and set(cell) <= {"-", ":", " "} for cell in cells)


def collect_applications(
    application_dir: Path,
) -> Tuple[List[dict], int, List[str]]:
    """Read application notes and return valid rows plus validation errors."""

    records: List[dict] = []
    errors: List[str] = []
    scanned = 0
    if not application_dir.exists():
        return records, scanned, errors

    for path in sorted(application_dir.glob("*.md")):
        if not path.is_file():
            continue
        scanned += 1
        try:
            fields = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        if fields.get("type") != "application":
            continue
        missing = [
            field
            for field in REQUIRED_FIELDS
            if not isinstance(fields.get(field), str)
        ]
        if missing:
            errors.append(f"{path.name}: missing required fields: {', '.join(missing)}")
            continue
        empty = [
            field
            for field in NON_EMPTY_REQUIRED_FIELDS
            if not fields[field].strip()
        ]
        if empty:
            errors.append(f"{path.name}: empty required fields: {', '.join(empty)}")
            continue
        fields["_path"] = path
        records.append(fields)
    return records, scanned, errors


def render_generated_block(
    records: List[dict],
    status_rows: List[Tuple[str, str]],
    status_groups: Dict[str, str],
) -> str:
    labels = dict(status_rows)
    status_order = {status_id: index for index, (status_id, _label) in enumerate(status_rows)}
    grouped: Dict[str, List[dict]] = {group: [] for group in GROUP_ORDER}
    for record in records:
        status = str(record["status"])
        group = status_groups.get(status, "进行中")
        if group not in grouped:
            group = "进行中"
        grouped[group].append(record)

    for group_records in grouped.values():
        group_records.sort(
            key=lambda record: (
                status_order.get(str(record["status"]), len(status_order)),
                normalize_component(str(record["company"])),
                normalize_component(str(record["department"])),
                normalize_component(str(record["position"])),
                str(record.get("_path", "")),
            )
        )

    lines = [START_MARKER]
    for group in GROUP_ORDER:
        lines.extend((f"## {group}", "", _render_table(grouped[group], labels), ""))
    lines.append(END_MARKER)
    return "\n".join(lines)


def _render_table(records: List[dict], labels: Dict[str, str]) -> str:
    header = "| " + " | ".join(TABLE_COLUMNS) + " |"
    separator = "| " + " | ".join("---" for _column in TABLE_COLUMNS) + " |"
    lines = [header, separator]
    if not records:
        return "\n".join(lines)
    for record in records:
        status = str(record["status"])
        values = (
            record["company"],
            record["department"],
            record["position"],
            labels.get(status, status),
            record["last_updated_at"],
            record.get("next_action", ""),
            record.get("next_action_due", ""),
            record.get("resume_version", ""),
            _format_source_urls(record.get("source_urls", [])),
        )
        lines.append("| " + " | ".join(_escape_cell(value) for value in values) + " |")
    return "\n".join(lines)


def _format_source_urls(value: object) -> str:
    if isinstance(value, list):
        return "<br>".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


def _escape_cell(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")


def replace_generated_block(existing: str, generated: str) -> str:
    """Replace only the generated marker block, preserving all other text."""

    start = existing.find(START_MARKER)
    end = existing.find(END_MARKER)
    if (start == -1) != (end == -1):
        raise ValueError("overview has only one generated marker")
    if start != -1:
        if end < start:
            raise ValueError("overview generated markers are out of order")
        return existing[:start] + generated + existing[end + len(END_MARKER) :]

    prefix = existing
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix:
        prefix += "\n"
    return prefix + generated + "\n"


def write_overview(overview: Path, content: str) -> None:
    """Atomically replace the overview after validation has completed."""

    overview.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=overview.parent,
            prefix=f".{overview.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, overview)
        temporary_name = None
    finally:
        if temporary_name:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def rebuild(vault: Path) -> Tuple[int, int, List[str]]:
    application_dir = vault / "求职" / "投递"
    overview = vault / "求职" / "投递总览.md"
    status_config = vault / "求职" / "配置" / "状态.md"
    status_rows, status_groups = load_status_config(status_config)
    records, scanned, errors = collect_applications(application_dir)
    if errors:
        return scanned, 0, errors

    existing = overview.read_text(encoding="utf-8") if overview.exists() else "# 投递总览\n"
    generated = render_generated_block(records, status_rows, status_groups)
    updated = replace_generated_block(existing, generated)
    write_overview(overview, updated)
    return scanned, len(records), []


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path, help="absolute path to the private Obsidian vault")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        scanned, rendered, errors = rebuild(args.vault)
    except (OSError, UnicodeError, ValueError) as exc:
        print("records=0 records_scanned=0 rows_rendered=0 validation_errors=1", flush=True)
        print(f"validation error: {exc}", file=os.sys.stderr, flush=True)
        return 1

    print(
        f"records={scanned} records_scanned={scanned} rows_rendered={rendered} validation_errors={len(errors)}",
        flush=True,
    )
    if errors:
        for error in errors:
            print(f"validation error: {error}", file=os.sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
