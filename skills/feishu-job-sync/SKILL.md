---
name: feishu-job-sync
description: Use when synchronizing confirmed Obsidian job-application records to a Feishu Base (Bitable), creating the initial Base, or repeating an idempotent record upsert.
metadata:
  short-description: Sync private Obsidian applications to a Feishu Base
---

# Feishu Job Sync

把私有 Obsidian vault 中 `求职/投递/*.md` 的已确认投递记录同步到飞书多维表格（Base）。Obsidian 是唯一事实源，飞书 Base 是用于查看、筛选和统计的副本；不要从 `求职/投递总览.md` 反向解析，也不要将 Base URL、token 或其他凭据提交到公开仓库。

## 使用前提

- 已安装并配置 `lark-cli`，用户身份可用：`lark-cli auth status --json --verify`。
- 已读取本项目的 `skills/job-tracker/SKILL.md`，并由用户明确提供私有 vault 路径。
- 只同步 `求职/投递/*.md`；`求职/收件箱/` 中的 pending items 不同步。
- 只使用 `--as user`，不要把真实 Base token 写入仓库、测试或日志。

## 首次创建

先只读取本地数据预览：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --dry-run
```

确认记录数和字段后创建 Base 及首个数据表：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --create \
  --title 求职投递跟踪 \
  --table-name 投递记录
```

脚本使用 `lark-cli base +base-create` 创建 Base，再用 `lark-cli base +record-batch-create` 写入记录。输出的 Base URL 只能保存到私有 vault 配置，例如 `求职/配置/飞书同步.md`，不要提交到本仓库。

## 重复同步

使用 Base URL：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --base-url "$FEISHU_JOB_BASE_URL" \
  --table-name 投递记录
```

也可以使用私有的 Base token；如果 Base 中有多个数据表，同时传入真实的 `--table-id`：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --base-token "$FEISHU_JOB_BASE_TOKEN" \
  --table-id tblxxxxxxxx
```

重复同步会先调用 `lark-cli base +field-list` 校验字段，再调用 `lark-cli base +record-list` 读取同步键，最后按需调用 `lark-cli base +record-batch-create` 和 `lark-cli base +record-batch-update`。已有记录更新，新增记录插入，不会重复追加；不会自动删除 Base 中的历史记录，也不会把飞书编辑回写 Obsidian。

## 去重与字段

同步键是规范化后的 `公司 + 部门 + 职位` 三元组，保存在 `同步键` 字段中。规范化沿用 job-tracker 的 Unicode NFKC、空白和大小写规则。记录标题由三项拼成，便于在 Base 中阅读。

数据表包含：记录标题、公司、部门、职位、状态 ID、当前状态、首次投递日期、最近更新时间、下一步行动、截止日期、简历版本、工作地点、职位类别、用工类型、招聘项目、投递渠道、志愿顺序、原始状态、来源、来源链接、缺失字段、Obsidian 记录和同步键。`当前状态` 是单选字段，日期是日期时间字段，其他信息按文本保留。

## 安全边界

- `--dry-run` 只读取 vault，不访问飞书。
- 写入前必须检查 Base 与数据表身份、字段 schema 和目标表名。
- 单批最多 200 条记录；脚本会串行分批写入。
- 不使用电子表格接口，只操作 Base、数据表、字段和记录。
- 写入失败时不执行删除；先保留现状并检查命令错误，再重试和回读。
