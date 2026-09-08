# Job Search Toolkit

面向个人求职者的 Codex skill 工具集。它用私有 Obsidian vault 记录投递、简历版本和求职过程，用可复用的 skill 处理采集、整理、优化和同步。

本仓库只保存公开的 skill、脚本、模板、数据契约和合成测试数据。真实简历、投递记录、面试转写、浏览器会话、凭据和飞书资源地址都放在独立的私有目录中。

## 先看这里

从仓库根目录打开 Codex，并在请求中明确指定 skill：

```text
请读取并使用 ./skills/job-tracker/SKILL.md。
我的私有 Obsidian vault 是：
/Users/你的用户名/obsidian/job-search

请处理下面的投递信息。先展示抽取结果、去重结果和拟写入内容，
等我确认后再修改 vault。
```

使用规则：

1. 需要处理投递、简历或同步时，先指定对应的 `SKILL.md`。
2. 涉及写入私有数据时，要求 skill 先给预览；没有确认就不写入。
3. 仓库中的 skill、脚本和模板可以提交远程仓库；真实数据只能写入私有 vault。
4. 需要浏览招聘网站时，只扫描用户明确指定的页面和来源，不保存密码、Cookie 或登录状态。

## Skill 总览

| Skill | 什么时候使用 | 默认写入位置 |
| --- | --- | --- |
| `job-tracker` | 处理投递链接、粘贴文本、招聘网站投递状态、去重和投递总览 | 私有 Obsidian vault |
| `resume-registry` | 上传或登记一份简历，检查重复版本，关联到投递 | 私有 Obsidian vault |
| `resume-ats-optimizer` | 检查 ATS 兼容性和职位描述关键词匹配 | 先输出建议，不覆盖原简历 |
| `resume-bullet-writer` | 将职责描述改写为成果型简历 bullet | 先输出候选文案 |
| `tech-resume-optimizer` | 面向 Agent、软件工程、基础架构等技术岗位优化简历 | 先输出结构和修改建议 |
| `feishu-job-sync` | 将已确认投递同步到飞书多维表格 Base | 飞书 Base，不回写 Obsidian |

这些 skill 都位于 `skills/` 下。当前仓库不包含面试录音整理和面试复盘 skill，后续可以单独增加。

## 一次配置

### 准备私有 vault

推荐目录结构：

```text
/Users/你的用户名/obsidian/job-search/
└── 求职/
    ├── 投递/                  # 已确认的投递记录
    ├── 收件箱/                # 待确认项、未知状态和失败记录
    ├── 配置/
    │   ├── 状态.md            # 标准状态 ID 和显示名称
    │   ├── 字段别名.md        # 可选：来源字段别名
    │   ├── 规则.md            # 可选：个人规则
    │   └── 来源/              # 各招聘网站的状态映射
    └── 投递总览.md            # 脚本生成的总览
```

初始化状态文件：

```bash
mkdir -p /Users/你的用户名/obsidian/job-search/求职/配置
cp skills/job-tracker/templates/status-config.md \
  /Users/你的用户名/obsidian/job-search/求职/配置/状态.md
```

`状态.md` 中的 `id` 是稳定的内部值，例如 `applied`、`screening`、`interviewing`；投递 note 保存状态 ID，显示名称可以自行调整。

### 配置飞书 CLI（可选）

只有需要同步飞书时才需要配置：

```bash
lark-cli auth status --json --verify
```

确认用户身份可用后再执行 `feishu-job-sync`。Base URL、Base token 和表格 ID 只保存在私有配置或环境变量中。

## 投递跟踪：job-tracker

### 处理一个链接

链接可能是公开职位详情页，也可能是登录后的投递状态页。两者不能混为一谈。使用下面的请求，让 skill 先识别页面类型并预览：

```text
请使用 ./skills/job-tracker/SKILL.md。
vault: /Users/你的用户名/obsidian/job-search

处理这个链接：
https://example.invalid/application/123

请先判断它是职位详情页还是投递状态页，抽取公司、部门、职位、原始状态、事件时间、来源和证据。
按公司、部门、职位去重，只展示拟执行操作，不要写入。
```

确认写入时逐条授权：

```text
确认第 1 条，按预览内容写入；其他记录不要处理。
```

如果要改字段，先明确修改后重新预览：

```text
把第 1 条的部门改为算法平台部，职位保持不变，重新展示预览。
```

### 粘贴投递文本

适用于邮件、招聘系统通知和手动复制的页面文本：

```text
请使用 ./skills/job-tracker/SKILL.md。
vault: /Users/你的用户名/obsidian/job-search

下面是投递结果文本。请拆分出每一条记录，保留原文证据，
按公司、部门、职位去重，并逐条展示需要确认的字段；不要直接写入。

<粘贴文本>
```

每条记录都要单独确认公司、部门、职位、事件时间、来源、原始状态、标准状态、证据、缺失字段和拟执行操作。字段缺失可以在确认后保留为空，但不能靠猜测补全。

### 扫描招聘网站

扫描必须由用户主动触发，并指定来源和页面：

涉及网页交互时，必须先读取并使用 `agent-browser` skill。优先复用用户当前已经登录并授权的浏览器会话，不要自行打开空白浏览器或另起未登录实例；如果现有会话不可用，应先报告访问问题，不要猜测页面状态。

```text
请使用 ./skills/job-tracker/SKILL.md 扫描招聘页面。
vault: /Users/你的用户名/obsidian/job-search
来源: example-career-site
页面: https://example.invalid/account/applications

使用我当前授权的浏览器会话，处理页面上的全部投递卡片。
先展示扫描结果、状态映射和拟更新项，等待确认后再写入。
```

新招聘网站第一次出现时，先确认原始状态如何映射：

```text
页面原始状态       标准状态
简历筛选中         screening
在线测评           assessment
一面               interviewing
```

一个来源的状态映射不能自动套用到另一个来源。页面中的多个职位必须作为独立快照处理；未知状态、字段不足、疑似重复和页面访问失败都进入 `求职/收件箱/`，不修改已有记录。

### 处理待确认项

```text
请使用 ./skills/job-tracker/SKILL.md。
vault: /Users/你的用户名/obsidian/job-search

读取求职/收件箱/中的待确认项，逐条展示，不要批量写入。
```

可用决策包括：`确认`、`编辑`、`合并`、`拆分`、`忽略`、`重试`。只有明确确认后，pending item 才会变成正式投递记录。

### 重建投递总览

`求职/投递总览.md` 是生成视图，不是第二份事实来源。确认写入投递后，可以手动重建：

```bash
python3 skills/job-tracker/scripts/update_index.py \
  --vault "/Users/你的用户名/obsidian/job-search"
```

脚本只读取 `求职/投递/*.md`，保留总览文件中生成标记之外的内容，校验通过后才替换生成区域。

## 简历版本登记：resume-registry

登记简历文件时使用：

```text
请使用 ./skills/resume-registry/SKILL.md。
vault: /Users/你的用户名/obsidian/job-search

登记这份简历：/Users/你的用户名/resume/resume-cn.pdf
请提取文件信息和文本摘要，计算内容 hash，展示拟使用的版本名、方向、日期、保存路径和重复候选。
先不要写入，等我确认。
```

确认时需要明确：版本名、语言、更新时间、目标方向、私有存储路径，以及是否允许关联后续投递。原始文件不会被覆盖；相同 hash 的文件会先提示复用或创建新版本。

确认后，版本 note 默认放在：

```text
求职/简历/版本/
```

投递 note 只保存 Obsidian 链接，不复制整份简历正文。

## 简历优化

这些 skill 默认只生成分析和候选文案，不会静默覆盖原始 `.tex`、`.pdf` 或文本文件。建议先登记版本，再进行优化。

### ATS 检查

```text
请使用 ./skills/resume-ats-optimizer/SKILL.md。

简历文件：/Users/你的用户名/resume/resume-cn.pdf
目标职位描述：<粘贴职位描述>

请分析 ATS 可读性、关键词覆盖、缺失关键词和格式风险，给出修改建议，不要覆盖原文件。
```

### Bullet 改写

```text
请使用 ./skills/resume-bullet-writer/SKILL.md。

把下面的经历改写成适合技术简历的成果型 bullet，保留事实，不虚构指标。
原文：<粘贴经历>
目标方向：Agent 平台 / 基础架构研发工程师
```

### 技术简历优化

```text
请使用 ./skills/tech-resume-optimizer/SKILL.md。

基于这份已确认的简历版本和目标岗位，审查技术技能、项目、工作经历和排序。
先输出问题清单、建议结构和可替换文案，不要直接覆盖原文件。
```

## 飞书同步：feishu-job-sync

`feishu-job-sync` 的目标是飞书多维表格 Base，不是电子表格。Obsidian 是唯一事实源，飞书只是用于查看、筛选和统计的副本。

### 第一次使用：先预览

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --dry-run
```

`--dry-run` 只读取私有 vault，不访问飞书。确认记录数、字段和数据后再创建资源。

### 创建 Base 和数据表

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --create \
  --title 求职投递跟踪 \
  --table-name 投递记录
```

脚本会创建一个 Base 和名为 `投递记录` 的数据表，然后批量写入已确认的投递记录。创建结果中的 Base URL 只保存到私有 vault 配置，例如：

```yaml
---
type: feishu_job_sync
base_url: "https://example.feishu.cn/base/your_base_token"
table_name: 投递记录
last_sync_at: 2026-09-08
last_sync_count: 25
---
```

示例中的地址只是格式示意，真实地址不能提交到本仓库。

### 后续重复同步

推荐使用 Base URL：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --base-url "$FEISHU_JOB_BASE_URL" \
  --table-name 投递记录
```

也可以使用私有 Base token；一个 Base 有多张数据表时同时指定 `--table-id`：

```bash
python3 skills/job-tracker/scripts/sync_feishu.py \
  --vault /Users/你的用户名/obsidian/job-search \
  --base-token "$FEISHU_JOB_BASE_TOKEN" \
  --table-id tblxxxxxxxx \
  --table-name 投递记录
```

同步过程会：

1. 从 `求职/投递/*.md` 读取已确认记录。
2. 校验目标 Base 的字段 schema。
3. 读取已有记录的 `同步键`。
4. 按规范化后的“公司 + 部门 + 职位”三元组匹配。
5. 新记录调用批量新增，已有记录调用批量更新。

它不会删除 Base 中的历史记录，不会把飞书编辑回写 Obsidian，也不会自动同步 `求职/投递总览.md`。

### Base 字段和去重规则

数据表包括：

```text
记录标题、公司、部门、职位、状态ID、当前状态、首次投递日期、最近更新时间、
下一步行动、截止日期、简历版本、工作地点、职位类别、用工类型、招聘项目、
投递渠道、志愿顺序、原始状态、来源、来源链接、缺失字段、Obsidian记录、同步键
```

`当前状态` 是单选字段，日期是日期时间字段，`同步键` 是文本字段。同步键使用 job-tracker 的 Unicode NFKC、空白、大小写和标点归一化规则。

当前版本只支持 Base 记录的新增和更新。已经存在的错误电子表格不会自动迁移、删除或继续使用；需要迁移时单独提出任务。

## 数据契约

### 投递 note

已确认的投递记录位于 `求职/投递/*.md`，基本 frontmatter：

```yaml
---
type: application
company: 示例公司
department: 数据平台部
position: 产品分析师
status: applied
first_applied_at: 2026-08-27
last_updated_at: 2026-08-27
next_action: 等待反馈
next_action_due: 2026-09-03
resume_version: "[[求职/简历/版本/简历-产品分析-2026-08-27]]"
source_urls: ["https://example.invalid/application/123"]
---
```

`status` 保存标准 ID，不直接保存显示名称。字段暂时未知时可以保存空字符串；未经确认的内容不要进入正式投递目录。

### Timeline

投递 note 的 `## Timeline` 保存状态观察历史。事件至少包含发生时间、事件类型、标准状态、原始状态、来源、来源链接、证据和 `event_fingerprint`。重复扫描遇到相同指纹时不重复追加事件。

## 安全边界

本工具集明确不做：

- 后台定时轮询招聘网站；
- 未经用户主动请求的浏览器扫描；
- 绕过登录、验证码或访问控制；
- 保存密码、Cookie、Token 或浏览器会话；
- 把公开职位详情直接当成已投递；
- 根据页面中消失的记录推断拒绝、撤回或关闭；
- 未经确认批量写入私有 vault 或飞书 Base；
- 将真实简历、投递历史、面试文本或真实招聘链接提交到公开仓库。

遇到登录失败、验证码、页面结构变化、未知状态或字段冲突，应保留证据并进入待确认流程，不修改已有投递记录。

## 开发与验证

仓库根目录执行：

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile skills/job-tracker/scripts/sync_feishu.py
git diff --check
```

测试只使用 `tests/fixtures/` 中的合成数据，不能用真实 vault 路径运行测试并把结果写回仓库。修改 skill、脚本或数据契约后，至少运行一次完整测试套件。

## 目录索引

```text
skills/
├── job-tracker/           # 投递采集、状态映射、去重、总览
├── feishu-job-sync/       # Obsidian 到飞书 Base 的同步
├── resume-registry/       # 私有简历版本登记
├── resume-ats-optimizer/  # ATS 检查
├── resume-bullet-writer/  # bullet 改写
└── tech-resume-optimizer/ # 技术简历优化
```

详细的数据格式和来源适配规则见：

- [投递跟踪 Skill](skills/job-tracker/SKILL.md)
- [数据契约](skills/job-tracker/references/data-contract.md)
- [来源适配器契约](skills/job-tracker/references/source-adapters.md)
- [工作流说明](skills/job-tracker/references/workflows.md)
- [飞书同步 Skill](skills/feishu-job-sync/SKILL.md)
- [投递记录模板](skills/job-tracker/templates/application.md)
- [状态配置模板](skills/job-tracker/templates/status-config.md)
