# 投递状态配置

The `id` values are stable internal IDs. Skills store IDs in application frontmatter; labels are for display and may be changed by the user.

| id | label |
| --- | --- |
| ready_to_apply | 待投递 |
| applied | 已投递 |
| screening | 筛选中 |
| assessment | 测评中 |
| interviewing | 面试中 |
| offer | Offer |
| accepted | 已接受 |
| rejected | 拒绝 |
| withdrawn | 撤回 |
| closed | 无回应/关闭 |

## Default Overview Groups

The deterministic overview uses these groups unless a future configuration extends the contract:

| group | status IDs |
| --- | --- |
| 进行中 | `ready_to_apply`, `applied`, `screening`, `assessment` |
| 待跟进 | `offer`, `accepted` |
| 面试中 | `interviewing` |
| 已结束 | `rejected`, `withdrawn`, `closed` |

Source mappings are kept separately by source name. An unknown raw status must not be guessed or silently mapped; it leaves the current canonical status unchanged and sends only the affected record to the pending inbox.
