# 本地数据契约

prepare-run.py 创建初始记录和 LOG.md。JSON 用 UTF-8，路径相对运行目录或绝对路径；脚本不解释 shell 内容。每次批量更新先保存完整 JSON，再执行校验。

## run.json

schema_version=1；phase 为 scope / decode / walkthrough / review / writeback / complete。design_url、target_url、platforms、environment 记录真实入口和环境。pages 为有序对象数组，每项 id/name/status（pending / active / done）、scope_note、requirements。requirements 每项含 id、summary、figma_url、case_ids；不适用要求用 excluded_reason 说明。要求必须关联当前 Page 的用例，多平台每个平台都应有用例（不适用时也写带理由的用例）。module_order 是按功能接近程度排列的模块名数组，所有用例/问题的 module 都须出现其中；cases 数组同组按操作路径排序。当前页 current_page、当前用例 active_case、已执行步骤数 current_step、最近观察 last_observation、批次 batch、下一步 next_action。environment 按平台记录设备、系统、包/版本、镜像工具和必要账号条件，不保存密码或令牌。

## cases.json

数组。每项必需：id、page_id、module、platform、preconditions（数组）、steps（数组）、expected、figma_url、status（pending / pass / issue / blocked / not_applicable）。可选 finding_ids、evidence（文件路径数组）、reason、actual。module 按页面功能组织；同一交互的两平台各建独立用例。not_applicable 和 blocked 必须有 reason；issue 必须链接存在的 finding_ids。记录版本变化时标明观察环境。

## findings.json

数组。每项必需：id、case_ids（可为空，仅供用户补充暂存；最终校验需关联用例）、module、platform、kind、title、actual、expected、feedback、figma_url、review（pending / confirmed / rejected）、review_note、publish（布尔）。

kind：implementation（有依据的实现偏差）、needs_confirmation（缺明确规则）、design_change（用户明确提出的新规则）、coverage_request（需补测条件）。issue_type 为目标 profile 允许的标签，仅在线交付时需要。severity 可按项目约定添加，不由公司状态标签推断。related_ids 可关联其他平台同类问题。一个问题只写一个 platform，并与关联用例平台相同。

正式本地交付时填写 problem_image、design_image，指向标注后的产物；problem_source、design_source 指原始截图。取证未完成时可以先保存不完整条目；批次校验允许暂缺这些字段，--final 会阻止缺图交付。sources 还可记录准确 Figma node、捕获方式和时间；motion_evidence 可记录录屏/时刻。对 coverage_request，图是上下文参考，文字说明未覆盖；对 design_change，注明旧稿仅用于定位，并写出用户确认的新规则。

修正点独立的 UI 和交互问题分成两条，case_ids 可共享。稳定 ID 不随排序改变；module + 用例顺序组织，避免依据编号字母误排。rejected 留在本地历史中，publish=false；pending 不进入确认交付。

## annotations.json

对象含 items 数组。每项 id、problem、design；后两者含 source、crop（可省略）、boxes（可省略）。主图始终保留完整 source 范围；crop 只指定补充放大图，必须包含全部标注框。crop 和 boxes 为原图坐标归一化的 [x,y,width,height]，所有矩形在原图范围内。可选 extra_problems 数组，元素与 problem 相同，适合同一问题的多个必要证据；其原图以完整范围拼入主图。

render-evidence.py --help 查看参数。渲染成功后读取 evidence/render-manifest.json，按 id 把 problem_image/design_image 写回 findings.json，并从 annotations.json 写回原图 source 字段；脚本不自动改问题事实。主产物 evidence/<id>-problem.png、<id>-design.png、<id>-comparison.png；manifest 的 context_mode 为 full。非全图 crop 另生成 <id>-problem-detail.png / <id>-design-detail.png，映射到 problem_detail_image / design_detail_image，只作补充，不能替代主图字段。原图保持原样。标注配置是坐标依据，模型仍需打开生成图核验位置。

## 写入恢复与结果

attachments.json：本地 SHA256 到目标附件 file_id / collection / filename 的映射。仅存永久标识和元数据，短期上传地址及令牌不落盘。

writeback.json：rows 数组，每项 id 和已回读到的 issue_status、issue_type、platform、module、author、date、problem_width、design_width、media_count、figma_url；同时记录目标标识、服务器版本/快照标识、separator_count、visual_verified 和 snapshot_file。这些值必须来自目标回读，不从拟写入 payload 复制。目标返回 ADF 或其他格式时先适配解析，再校验。

validate-delivery.py 的本地模式检查数据、链接与证据；--writeback 检查在线回读映射。该脚本验证已输入的事实，不替代真实 UI 操作、设计判断和服务器回读。

## 脚本执行顺序

将 SKILL_DIR 替换为当前技能目录绝对路径，RUN 替换为本轮目录。脚本需要 Python 3；图像生成与交付校验需要 Pillow。先检查所选 Python 能导入 PIL；若不能，使用环境依赖发现工具选择已有解释器，仍缺少时说明并按环境授权规则安装。无需把某台机器的运行时路径写进配置。

```text
python3 SKILL_DIR/scripts/prepare-run.py --run RUN --design-url FIGMA_URL --platform iOS
python3 SKILL_DIR/scripts/render-evidence.py --run RUN
python3 SKILL_DIR/scripts/build-confluence-table.py --run RUN
python3 SKILL_DIR/scripts/validate-delivery.py --run RUN --final
```

在线写入前，在附件映射齐备后调用：

```text
python3 SKILL_DIR/scripts/build-confluence-table.py --run RUN --confluence SKILL_DIR/profiles/confluence.json --user-profile SKILL_DIR/profiles/user-profile.json --date YYYY-MM-DD
```

真实回读结果保存后：

```text
python3 SKILL_DIR/scripts/validate-delivery.py --run RUN --confluence SKILL_DIR/profiles/confluence.json --user-profile SKILL_DIR/profiles/user-profile.json --final --writeback
```

workflow_data.py 是生成器和校验器共用的排序模块，不需要单独执行。排序先按 run.module_order，再按 cases 数组的顺序；同一用例的独立问题保留其记录顺序。

脚本的确认项筛选不代替用户审阅；JSON 的 confirmed 只能依据用户决定填写。初始化已有目录会保留现有数据；启动新任务时使用独立目录，恢复时核对原有目标与平台。

## 最小数据示例

以下展示一个独立用例的结构，实际字段填写当前设计与设备信息；这里的 ID 仅为示例。一个 Page 完成后仍保留其要求与关联，便于最终查漏。

```json
{
  "id": "case-001",
  "page_id": "page-001",
  "module": "账户设置",
  "platform": "iOS",
  "preconditions": ["已进入设置页面"],
  "steps": ["点击通知选项", "关闭弹层"],
  "expected": "展示通知设置；关闭后返回原页面且不改动选项",
  "figma_url": "https://www.figma.com/design/FILE_KEY?node-id=NODE_ID",
  "status": "pending"
}
```

run.pages 当前 Page 的 requirements 对应项：

```json
{"id":"req-001","summary":"通知设置可打开并取消","figma_url":"https://www.figma.com/design/FILE_KEY?node-id=NODE_ID","case_ids":["case-001"]}
```

发现问题后先写 findings.json 的必需字段，review=pending、publish=false；用例 status=issue、finding_ids 包含该问题 ID。pass 用例至少记 actual（必要时附 evidence）；blocked/not_applicable 记 reason。用户接受的问题才改为 review=confirmed；确认不反馈的项保留 review_note 且 publish=false。


单条问题结构（示例值仅用于说明字段；本轮须填入真实观察和依据）：

```json
{
  "id": "issue-001", "case_ids": ["case-001"],
  "module": "账户设置", "platform": "iOS", "kind": "implementation",
  "title": "关闭操作后弹层仍停留",
  "actual": "点击关闭后弹层没有消失", "expected": "关闭弹层并返回原页面",
  "feedback": "路径：设置 → 通知 → 关闭。关闭后弹层仍停留，影响返回原页面；请恢复稿件定义的关闭行为。",
  "figma_url": "https://www.figma.com/design/FILE_KEY?node-id=NODE_ID",
  "review": "pending", "review_note": "", "publish": false,
  "problem_source": "evidence/raw-app.png", "design_source": "evidence/raw-figma.png",
  "problem_image": "evidence/issue-001-problem.png", "design_image": "evidence/issue-001-design.png"
}
```

对应标注配置结构；rect 坐标需根据实际原图计算，以下数字仅说明格式：

```json
{"items":[{"id":"issue-001","problem":{"source":"evidence/raw-app.png","crop":[0,0,1,1],"boxes":[[0.1,0.1,0.2,0.1]]},"design":{"source":"evidence/raw-figma.png","crop":[0,0,1,1],"boxes":[[0.1,0.1,0.2,0.1]]}}]}
```

## 配置边界

profiles/user-profile.json 保存署名、署名颜色和图片预览尺寸；公开版本 author 为空，在线行生成前填写本地副本。profiles/confluence.json 保存列名/角色、原生标签、类型选择规则、分组和保存模式。脚本通过两个显式参数读取配置，本地复核稿不需要个人配置。公开仓库中保留通用默认值，实际个人身份和内部模板调整维护在使用者自己的配置副本中。
