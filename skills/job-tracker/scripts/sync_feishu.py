#!/usr/bin/env python3
"""Synchronize Obsidian application notes to a Feishu Base table."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from markdown_records import normalize_component  # noqa: E402
from update_index import collect_applications, load_status_config  # noqa: E402


BASE_COLUMNS = (
    "记录标题",
    "公司",
    "部门",
    "职位",
    "状态ID",
    "当前状态",
    "首次投递日期",
    "最近更新时间",
    "下一步行动",
    "截止日期",
    "简历版本",
    "工作地点",
    "职位类别",
    "用工类型",
    "招聘项目",
    "投递渠道",
    "志愿顺序",
    "原始状态",
    "来源",
    "来源链接",
    "缺失字段",
    "Obsidian记录",
    "同步键",
)
DATE_COLUMNS = {"首次投递日期", "最近更新时间", "截止日期"}
DEFAULT_STATUS_LABELS = (
    "待投递",
    "已投递",
    "筛选中",
    "测评中",
    "面试中",
    "Offer",
    "已接受",
    "拒绝",
    "撤回",
    "无回应/关闭",
)
LAST_EVENT_HEADING = re.compile(r"^###\s+(.+?)\s+\|\s+(.+?)\s*$")
EVENT_FIELD = re.compile(r"^-\s+([a-z_]+):\s?(.*)$")
DATE_PREFIX = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def _date_value(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    match = DATE_PREFIX.match(text)
    return match.group(1) if match else text


def _base_datetime(value: object) -> str | None:
    date = _date_value(value)
    if not date:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        return f"{date} 00:00"
    return date


def _urls(value: object) -> str:
    if isinstance(value, list):
        return "；".join(str(item).strip() for item in value if str(item).strip())
    return _text(value)


def _timeline_events(markdown: str) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    in_timeline = False
    current: dict[str, str] | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped == "## Timeline":
            in_timeline = True
            continue
        if in_timeline and stripped.startswith("## ") and not stripped.startswith("### "):
            break
        if not in_timeline:
            continue

        heading = LAST_EVENT_HEADING.match(stripped)
        if heading:
            if current is not None:
                events.append(current)
            current = {
                "occurred_at": heading.group(1).strip(),
                "event_type": heading.group(2).strip(),
            }
            continue
        if current is None:
            continue
        field = EVENT_FIELD.match(stripped)
        if field:
            current[field.group(1)] = field.group(2).strip()
    if current is not None:
        events.append(current)
    return events


def _latest_event(path: Path) -> dict[str, str]:
    events = _timeline_events(path.read_text(encoding="utf-8"))
    return events[-1] if events else {}


def _status_labels(vault: Path) -> tuple[dict[str, str], dict[str, int]]:
    rows, _groups = load_status_config(vault / "求职" / "配置" / "状态.md")
    return dict(rows), {status_id: index for index, (status_id, _label) in enumerate(rows)}


def collect_application_rows(vault: Path) -> list[dict[str, str]]:
    """Load confirmed applications and flatten them into Base record fields."""

    application_dir = vault / "求职" / "投递"
    records, _scanned, errors = collect_applications(application_dir)
    if errors:
        raise ValueError("cannot sync invalid application notes: " + "; ".join(errors))

    labels, status_order = _status_labels(vault)
    records.sort(
        key=lambda record: (
            status_order.get(str(record.get("status", "")), len(status_order)),
            normalize_component(str(record.get("company", ""))),
            normalize_component(str(record.get("department", ""))),
            normalize_component(str(record.get("position", ""))),
            str(record.get("_path", "")),
        )
    )

    rows: list[dict[str, str]] = []
    for record in records:
        path = Path(record["_path"])
        event = _latest_event(path)
        missing = record.get("missing_fields", [])
        if not isinstance(missing, list):
            missing = [missing]
        rows.append(
            {
                "公司": _text(record.get("company")),
                "部门": _text(record.get("department")),
                "职位": _text(record.get("position")),
                "状态ID": _text(record.get("status")),
                "当前状态": labels.get(_text(record.get("status")), _text(record.get("status"))),
                "首次投递日期": _text(record.get("first_applied_at")),
                "最近更新时间": _text(record.get("last_updated_at")),
                "下一步行动": _text(record.get("next_action")),
                "截止日期": _text(record.get("next_action_due")),
                "简历版本": _text(record.get("resume_version")),
                "工作地点": _text(record.get("location")),
                "职位类别": _text(record.get("job_category")),
                "用工类型": _text(record.get("employment_type")),
                "招聘项目": _text(record.get("program")),
                "投递渠道": _text(record.get("application_channel")),
                "志愿顺序": _text(record.get("preference_order")),
                "原始状态": _text(event.get("raw_status")),
                "来源": _text(event.get("source")),
                "来源链接": _urls(record.get("source_urls")),
                "缺失字段": "；".join(str(item).strip() for item in missing if str(item).strip()),
                "Obsidian记录": path.relative_to(vault).as_posix(),
            }
        )
    return rows


def build_sync_key(company: object, department: object, position: object) -> str:
    """Build the stable company/department/position identity used by Base upserts."""

    parts = (
        normalize_component(_text(company)),
        normalize_component(_text(department)),
        normalize_component(_text(position)),
    )
    return " | ".join(parts)


def _record_title(row: dict[str, str]) -> str:
    parts = [row.get("公司", ""), row.get("部门", ""), row.get("职位", "")]
    title = " / ".join(part.strip() for part in parts if part and part.strip())
    return title or "未命名投递"


def build_base_fields(status_labels: Iterable[str] | None = None) -> list[dict[str, Any]]:
    labels: list[str] = []
    for value in status_labels or DEFAULT_STATUS_LABELS:
        label = _text(value)
        if label and label not in labels:
            labels.append(label)

    text_fields = {
        "记录标题",
        "公司",
        "部门",
        "职位",
        "状态ID",
        "下一步行动",
        "简历版本",
        "工作地点",
        "职位类别",
        "用工类型",
        "招聘项目",
        "投递渠道",
        "志愿顺序",
        "原始状态",
        "来源",
        "来源链接",
        "缺失字段",
        "Obsidian记录",
        "同步键",
    }
    fields: list[dict[str, Any]] = []
    for name in BASE_COLUMNS:
        if name in text_fields:
            fields.append({"name": name, "type": "text"})
        elif name == "当前状态":
            fields.append(
                {
                    "name": name,
                    "type": "select",
                    "multiple": False,
                    "options": [{"name": label} for label in labels],
                }
            )
        elif name in DATE_COLUMNS:
            fields.append(
                {
                    "name": name,
                    "type": "datetime",
                    "style": {"format": "yyyy-MM-dd"},
                }
            )
        else:
            raise ValueError(f"unsupported Base field: {name}")
    return fields


def build_base_record(row: dict[str, str]) -> dict[str, Any]:
    record: dict[str, Any] = {}
    for column in BASE_COLUMNS:
        if column == "记录标题":
            record[column] = _record_title(row)
        elif column == "同步键":
            record[column] = build_sync_key(row.get("公司"), row.get("部门"), row.get("职位"))
        elif column == "当前状态":
            value = _text(row.get(column))
            record[column] = [value] if value else []
        elif column in DATE_COLUMNS:
            record[column] = _base_datetime(row.get(column))
        else:
            value = _text(row.get(column))
            record[column] = value or None
    return record


def build_base_records(rows: Iterable[dict[str, str]]) -> list[dict[str, Any]]:
    return [build_base_record(row) for row in rows]


def _ensure_unique_sync_keys(records: Iterable[dict[str, Any]]) -> None:
    seen: set[str] = set()
    for record in records:
        key = _text(record.get("同步键"))
        if key in seen:
            raise ValueError(f"duplicate application identity in Obsidian records: {key}")
        seen.add(key)


def _field_value(record: dict[str, Any], name: str) -> Any:
    fields = record.get("fields")
    if isinstance(fields, dict):
        return fields.get(name)
    return record.get(name)


def _cell_text(value: Any) -> str:
    if isinstance(value, list):
        values = []
        for item in value:
            if isinstance(item, dict):
                values.append(_text(item.get("text") or item.get("value") or item.get("name")))
            else:
                values.append(_text(item))
        return "；".join(value for value in values if value)
    if isinstance(value, dict):
        return _text(value.get("text") or value.get("value") or value.get("name"))
    return _text(value)


def _record_id(record: dict[str, Any]) -> str:
    for key in ("record_id", "recordId"):
        value = record.get(key)
        if isinstance(value, str) and value:
            return value
    value = record.get("id")
    return value if isinstance(value, str) and value.startswith("rec") else ""


def plan_record_sync(
    rows: Iterable[dict[str, str]], existing_records: Iterable[dict[str, Any]]
) -> dict[str, Any]:
    desired = build_base_records(rows)
    _ensure_unique_sync_keys(desired)

    existing_by_key: dict[str, str] = {}
    for record in existing_records:
        record_id = _record_id(record)
        sync_key = _cell_text(_field_value(record, "同步键"))
        if not record_id or not sync_key:
            continue
        if sync_key in existing_by_key and existing_by_key[sync_key] != record_id:
            raise ValueError(f"duplicate sync key already exists in Feishu Base: {sync_key}")
        existing_by_key[sync_key] = record_id

    creates: list[dict[str, Any]] = []
    updates: dict[str, dict[str, Any]] = {}
    for record in desired:
        sync_key = _text(record["同步键"])
        record_id = existing_by_key.get(sync_key)
        if record_id:
            updates[record_id] = record
        else:
            creates.append(record)
    return {"create_records": creates, "update_records": updates}


def _run_cli(command: list[str]) -> dict[str, Any]:
    environment = {
        "LARKSUITE_CLI_NO_UPDATE_NOTIFIER": "1",
        "LARKSUITE_CLI_NO_SKILLS_NOTIFIER": "1",
    }
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env={**os.environ, **environment},
        check=False,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise RuntimeError(f"lark-cli failed ({process.returncode}): {detail[:1000]}")
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"lark-cli returned non-JSON output: {process.stdout[:500]}") from exc
    if not isinstance(result, dict):
        raise RuntimeError("lark-cli returned a non-object JSON response")
    if result.get("ok") is False:
        raise RuntimeError("lark-cli returned an error")
    return result


def _find_first(value: Any, keys: set[str]) -> str:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str) and item:
                return item
        for item in value.values():
            found = _find_first(item, keys)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_first(item, keys)
            if found:
                return found
    return ""


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)


def _extract_records(value: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in _walk_dicts(value):
        matrix = item.get("data")
        field_names = item.get("fields")
        record_ids = item.get("record_id_list")
        if (
            isinstance(matrix, list)
            and isinstance(field_names, list)
            and isinstance(record_ids, list)
            and all(isinstance(name, str) for name in field_names)
        ):
            for index, record_id in enumerate(record_ids):
                if not isinstance(record_id, str) or not record_id or record_id in seen:
                    continue
                row = matrix[index] if index < len(matrix) and isinstance(matrix[index], list) else []
                records.append(
                    {
                        "record_id": record_id,
                        "fields": {
                            name: row[column_index] if column_index < len(row) else None
                            for column_index, name in enumerate(field_names)
                        },
                    }
                )
                seen.add(record_id)
            continue
        if not (_record_id(item) or isinstance(item.get("fields"), dict)):
            continue
        record_id = _record_id(item)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        records.append(item)
    return records


def _extract_tables(value: Any) -> list[dict[str, Any]]:
    tables: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in _walk_dicts(value):
        table_id = _find_first(item, {"table_id", "tableId"})
        if not table_id:
            candidate = item.get("id")
            table_id = candidate if isinstance(candidate, str) and candidate.startswith("tbl") else ""
        if not table_id or table_id in seen:
            continue
        seen.add(table_id)
        tables.append(item | {"_table_id": table_id})
    return tables


def _extract_field_names(value: Any) -> set[str]:
    names: set[str] = set()
    for item in _walk_dicts(value):
        field_id = _find_first(item, {"field_id", "fieldId"})
        if not field_id:
            candidate = item.get("id")
            field_id = candidate if isinstance(candidate, str) and candidate.startswith("fld") else ""
        name = item.get("name") or item.get("field_name") or item.get("fieldName")
        if field_id and isinstance(name, str) and name:
            names.add(name)
    return names


def _resolve_table(
    *,
    base_url: str | None,
    base_token: str | None,
    table_id: str | None,
    table_name: str,
) -> tuple[str, str, str | None]:
    resolved_url = base_url
    if base_url:
        resolved = _run_cli(
            [
                "lark-cli",
                "base",
                "+url-resolve",
                "--as",
                "user",
                "--format",
                "json",
                "--url",
                base_url,
            ]
        )
        base_token = base_token or _find_first(resolved, {"base_token", "baseToken"})
        table_id = table_id or _find_first(resolved, {"table_id", "tableId"})
        resolved_url = _find_first(resolved, {"url", "base_url", "baseUrl"}) or resolved_url

    if not base_token:
        raise ValueError("provide --base-url or --base-token")

    if not table_id:
        listed = _run_cli(
            [
                "lark-cli",
                "base",
                "+table-list",
                "--as",
                "user",
                "--format",
                "json",
                "--base-token",
                base_token,
            ]
        )
        tables = _extract_tables(listed)
        matches = [
            table
            for table in tables
            if _text(table.get("name") or table.get("table_name") or table.get("tableName")) == table_name
        ]
        if len(matches) != 1:
            raise ValueError(f"expected exactly one Feishu Base table named {table_name!r}")
        table_id = matches[0]["_table_id"]

    return base_token, table_id, resolved_url


def _validate_table_fields(base_token: str, table_id: str, required_fields: Iterable[str]) -> None:
    response = _run_cli(
        [
            "lark-cli",
            "base",
            "+field-list",
            "--as",
            "user",
            "--format",
            "json",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
        ]
    )
    available = _extract_field_names(response)
    missing = [name for name in required_fields if name not in available]
    if missing:
        raise ValueError("Feishu Base is missing required fields: " + ", ".join(missing))


def _record_list(base_token: str, table_id: str) -> list[dict[str, Any]]:
    response = _run_cli(
        [
            "lark-cli",
            "base",
            "+record-list",
            "--as",
            "user",
            "--format",
            "json",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--field-id",
            "同步键",
            "--limit",
            "200",
        ]
    )
    return _extract_records(response)


def _chunks(values: list[Any], size: int = 200) -> Iterable[list[Any]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _create_records(base_token: str, table_id: str, records: list[dict[str, Any]]) -> int:
    created = 0
    for batch in _chunks(records):
        _run_cli(
            [
                "lark-cli",
                "base",
                "+record-batch-create",
                "--as",
                "user",
                "--format",
                "json",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps({"create_records": batch}, ensure_ascii=False),
            ]
        )
        created += len(batch)
    return created


def _update_records(base_token: str, table_id: str, records: dict[str, dict[str, Any]]) -> int:
    updated = 0
    items = list(records.items())
    for batch in _chunks(items):
        _run_cli(
            [
                "lark-cli",
                "base",
                "+record-batch-update",
                "--as",
                "user",
                "--format",
                "json",
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps({"update_records": dict(batch)}, ensure_ascii=False),
            ]
        )
        updated += len(batch)
    return updated


def _base_create(title: str, table_name: str, fields: list[dict[str, Any]]) -> dict[str, Any]:
    return _run_cli(
        [
            "lark-cli",
            "base",
            "+base-create",
            "--as",
            "user",
            "--format",
            "json",
            "--name",
            title,
            "--table-name",
            table_name,
            "--time-zone",
            "Asia/Shanghai",
            "--fields",
            json.dumps(fields, ensure_ascii=False),
        ]
    )


def _created_table(response: dict[str, Any], base_token: str, table_name: str) -> tuple[str, str | None]:
    table_id = _find_first(response, {"table_id", "tableId"})
    base_url = _find_first(response, {"url", "base_url", "baseUrl"}) or None
    if table_id:
        return table_id, base_url
    listed = _run_cli(
        [
            "lark-cli",
            "base",
            "+table-list",
            "--as",
            "user",
            "--format",
            "json",
            "--base-token",
            base_token,
        ]
    )
    tables = _extract_tables(listed)
    matches = [
        table
        for table in tables
        if _text(table.get("name") or table.get("table_name") or table.get("tableName")) == table_name
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one newly created table named {table_name!r}")
    return matches[0]["_table_id"], base_url


def sync_to_feishu(
    vault: Path,
    *,
    base_url: str | None = None,
    base_token: str | None = None,
    table_id: str | None = None,
    create: bool = False,
    title: str = "求职投递跟踪",
    table_name: str = "投递记录",
    dry_run: bool = False,
) -> dict[str, Any]:
    rows = collect_application_rows(vault)
    labels, _status_order = _status_labels(vault)
    status_labels = list(labels.values())
    status_labels.extend(row["当前状态"] for row in rows)
    fields = build_base_fields(status_labels)
    records = build_base_records(rows)
    _ensure_unique_sync_keys(records)

    if dry_run:
        return {
            "operation": "dry-run",
            "record_count": len(records),
            "field_count": len(fields),
            "fields": fields,
            "records": records,
        }

    if create:
        if base_url or base_token or table_id:
            raise ValueError("--create cannot be combined with an existing Base locator")
        created = _base_create(title, table_name, fields)
        created_base_token = _find_first(created, {"base_token", "baseToken"})
        if not created_base_token:
            raise RuntimeError("Feishu Base creation did not return a base token")
        created_table_id, created_url = _created_table(created, created_base_token, table_name)
        _validate_table_fields(created_base_token, created_table_id, BASE_COLUMNS)
        created_count = _create_records(created_base_token, created_table_id, records)
        return {
            "operation": "created",
            "record_count": len(records),
            "created_count": created_count,
            "base_url": created_url,
            "table_name": table_name,
        }

    if base_url and base_token:
        raise ValueError("provide only one of --base-url or --base-token")
    resolved_base_token, resolved_table_id, resolved_url = _resolve_table(
        base_url=base_url,
        base_token=base_token,
        table_id=table_id,
        table_name=table_name,
    )
    _validate_table_fields(resolved_base_token, resolved_table_id, BASE_COLUMNS)
    existing_records = _record_list(resolved_base_token, resolved_table_id)
    plan = plan_record_sync(rows, existing_records)
    created_count = _create_records(
        resolved_base_token,
        resolved_table_id,
        plan["create_records"],
    )
    updated_count = _update_records(
        resolved_base_token,
        resolved_table_id,
        plan["update_records"],
    )
    return {
        "operation": "updated",
        "record_count": len(records),
        "existing_count": len(existing_records),
        "created_count": created_count,
        "updated_count": updated_count,
        "base_url": resolved_url,
        "table_name": table_name,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", type=Path, required=True)
    locator = parser.add_mutually_exclusive_group()
    locator.add_argument("--base-url")
    locator.add_argument("--base-token")
    parser.add_argument("--table-id")
    parser.add_argument("--create", action="store_true")
    parser.add_argument("--title", default="求职投递跟踪")
    parser.add_argument("--table-name", default="投递记录")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = sync_to_feishu(
            args.vault,
            base_url=args.base_url,
            base_token=args.base_token,
            table_id=args.table_id,
            create=args.create,
            title=args.title,
            table_name=args.table_name,
            dry_run=args.dry_run,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
