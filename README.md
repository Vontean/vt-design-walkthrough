# vt-design-walkthrough

给设计师验收开发版本用的 Codex Skill。提供 Figma 交互稿和测试版本入口，agent 会按 Page 整理验收用例，在真实设备上检查交互与界面，留下实际截图、设计依据和定位框。

整轮走查完成后，你集中复核问题，也可以补充自己的截图。确认需要反馈的条目，再按授权写入 Confluence。进度和证据分批保存在项目目录，中断后可以接着做。

## 执行环境

运行在 Codex harness 中，需要 Computer Use 能力、Figma 访问和本地文件读写；写入 Confluence 时还需要 Atlassian 连接器及目标页面权限。

iOS 使用 iPhone Mirroring。Android 优先实机镜像，具体连接与控制路径仍待实机验证。图像脚本使用 Python 3 和 Pillow。

## 安装

克隆到 Codex 的技能目录：

```bash
git clone https://github.com/Vontean/vt-design-walkthrough.git ~/.codex/skills/vt-design-walkthrough
python3 -m pip install -r ~/.codex/skills/vt-design-walkthrough/requirements.txt
```

若配置了 `CODEX_HOME`，将安装位置改为该目录下的 `skills/vt-design-walkthrough`。也可以把仓库保留在项目中，在对话里提供 `SKILL.md` 路径让 agent 读取。

## 使用

```text
使用 $vt-design-walkthrough，设置 goal，走查这个 Figma 文件对应的 iOS 测试版本：
设计链接：…
开发版本入口：…
本地输出目录：…
先交付完整问题表供我复核，确认后再写入 Confluence。
```

`profiles/user-profile.json` 管理署名和图片尺寸，`profiles/confluence.json` 管理标签与表格结构。在线交付前，在自己的配置副本里填写姓名并核对目标模板。设备操作路径见 `references/`，本地截图标注、表格生成和校验脚本在 `scripts/`。
