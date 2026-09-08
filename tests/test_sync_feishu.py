import importlib.util
import json
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).parents[1]
MODULE_PATH = ROOT / "skills" / "job-tracker" / "scripts" / "sync_feishu.py"


class FeishuSyncTests(unittest.TestCase):
    def load_module(self):
        self.assertTrue(MODULE_PATH.exists(), "sync_feishu.py has not been implemented")
        spec = importlib.util.spec_from_file_location("sync_feishu", MODULE_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.vault = pathlib.Path(self.tempdir.name)
        self.app_dir = self.vault / "求职" / "投递"
        self.app_dir.mkdir(parents=True)
        config_dir = self.vault / "求职" / "配置"
        config_dir.mkdir(parents=True)
        (config_dir / "状态.md").write_text(
            "# 状态\n\n"
            "| id | label | group |\n"
            "| --- | --- | --- |\n"
            "| applied | 已投递 | 进行中 |\n"
            "| screening | 筛选中 | 进行中 |\n",
            encoding="utf-8",
        )

    def write_application(self):
        (self.app_dir / "示例公司-产品分析师.md").write_text(
            "---\n"
            "type: application\n"
            "company: 示例公司\n"
            "department: 数据平台部\n"
            "position: 产品分析师\n"
            "status: applied\n"
            "first_applied_at: 2026-08-27\n"
            "last_updated_at: 2026-09-08\n"
            "source_urls: [\"https://example.invalid/application/1\"]\n"
            "missing_fields: []\n"
            "location: 北京\n"
            "program: 秋招\n"
            "---\n\n"
            "# 示例公司 / 产品分析师\n\n"
            "## Timeline\n\n"
            "### 2026-09-08 | status_observed\n"
            "- status: applied\n"
            "- raw_status: 网申成功\n"
            "- source: example-site\n"
            "- source_url: https://example.invalid/application/1\n"
            "- evidence: 页面显示网申成功\n"
            "- event_fingerprint: sha256:0000000000000000000000000000000000000000000000000000000000000000\n",
            encoding="utf-8",
        )

    def test_collect_rows_uses_latest_event_and_record_fields(self):
        module = self.load_module()
        self.write_application()

        rows = module.collect_application_rows(self.vault)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["公司"], "示例公司")
        self.assertEqual(rows[0]["当前状态"], "已投递")
        self.assertEqual(rows[0]["原始状态"], "网申成功")
        self.assertEqual(rows[0]["来源"], "example-site")
        self.assertEqual(rows[0]["Obsidian记录"], "求职/投递/示例公司-产品分析师.md")

    def test_build_base_schema_and_record_payload(self):
        module = self.load_module()
        self.write_application()
        rows = module.collect_application_rows(self.vault)

        fields = module.build_base_fields(["已投递", "筛选中"])
        fields_by_name = {field["name"]: field for field in fields}
        records = module.build_base_records(rows)
        record = records[0]

        self.assertEqual(fields[0], {"name": "记录标题", "type": "text"})
        self.assertEqual(fields_by_name["当前状态"]["type"], "select")
        self.assertEqual(fields_by_name["当前状态"]["multiple"], False)
        self.assertEqual(
            fields_by_name["当前状态"]["options"],
            [{"name": "已投递"}, {"name": "筛选中"}],
        )
        self.assertEqual(
            fields_by_name["首次投递日期"]["style"],
            {"format": "yyyy-MM-dd"},
        )
        self.assertEqual(record["记录标题"], "示例公司 / 数据平台部 / 产品分析师")
        self.assertEqual(record["公司"], "示例公司")
        self.assertEqual(record["部门"], "数据平台部")
        self.assertEqual(record["职位"], "产品分析师")
        self.assertEqual(record["当前状态"], ["已投递"])
        self.assertEqual(record["首次投递日期"], "2026-08-27 00:00")
        self.assertEqual(record["最近更新时间"], "2026-09-08 00:00")
        self.assertEqual(
            record["同步键"],
            module.build_sync_key("示例公司", "数据平台部", "产品分析师"),
        )

    def test_plan_record_sync_updates_existing_and_creates_new(self):
        module = self.load_module()
        self.write_application()
        rows = module.collect_application_rows(self.vault)
        existing = [
            {
                "record_id": "rec_existing",
                "fields": {"同步键": module.build_sync_key("示例公司", "数据平台部", "产品分析师")},
            }
        ]

        new_row = dict(rows[0])
        new_row["公司"] = "另一公司"
        plan = module.plan_record_sync(rows + [new_row], existing)

        self.assertEqual(len(plan["create_records"]), 1)
        self.assertEqual(plan["create_records"][0]["公司"], "另一公司")
        self.assertEqual(list(plan["update_records"]), ["rec_existing"])
        self.assertEqual(
            plan["update_records"]["rec_existing"]["同步键"],
            module.build_sync_key("示例公司", "数据平台部", "产品分析师"),
        )

    def test_extract_field_names_accepts_base_field_ids(self):
        module = self.load_module()

        response = {
            "ok": True,
            "data": {
                "fields": [
                    {"id": "fld_company", "name": "公司"},
                    {"id": "fld_key", "name": "同步键"},
                ]
            },
        }

        self.assertEqual(module._extract_field_names(response), {"公司", "同步键"})

    def test_record_list_uses_json_limit_supported_by_cli(self):
        module = self.load_module()
        commands = []
        original_run_cli = module._run_cli
        module._run_cli = lambda command: commands.append(command) or {"ok": True, "data": {"items": []}}
        self.addCleanup(lambda: setattr(module, "_run_cli", original_run_cli))

        module._record_list("base_token", "table_id")

        limit_index = commands[0].index("--limit")
        self.assertEqual(commands[0][limit_index + 1], "200")

    def test_extract_records_converts_base_matrix_response(self):
        module = self.load_module()

        response = {
            "ok": True,
            "data": {
                "data": [["company | department | position"], ["another |  | role"]],
                "fields": ["同步键"],
                "record_id_list": ["rec_one", "rec_two"],
            },
        }

        self.assertEqual(
            module._extract_records(response),
            [
                {
                    "record_id": "rec_one",
                    "fields": {"同步键": "company | department | position"},
                },
                {
                    "record_id": "rec_two",
                    "fields": {"同步键": "another |  | role"},
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
