# Android：USB、ADB 与 scrcpy 实机镜像

采用真实手机，通过 ADB 安装和核对开发包，通过 scrcpy 显示手机画面。已有可用镜像优先复用；工具路径、设备序列号和包名每轮重新识别，不固定某台设备。无 scrcpy 时，也可使用当前 Computer 工具明确支持的其他镜像。

## 连接与开发包

1. 检查 `adb`、`scrcpy` 是否存在，执行 `adb devices -l`。多台设备时明确目标，后续命令均用 `adb -s SERIAL`，scrcpy 用 `--serial SERIAL`。
2. `unauthorized` 时请用户解锁手机，在手机上允许 USB 调试；无弹窗可重新插线。无设备时检查线缆是否支持数据与 USB 调试。首次启用开发选项或安装工具，说明用途并按已有授权推进；不擅自更改其他手机设置。
3. 用 `adb -s SERIAL shell getprop ro.product.model` 和 `adb -s SERIAL shell getprop ro.build.version.release` 记录设备与 Android 版本。
4. 需要安装时，使用用户指定的 APK，路径需 shell 引号保护：`adb -s SERIAL install -r '/absolute/path/app.apk'`。以 `Success` 确认安装；签名冲突或降级失败时保留错误，不自动卸载、清数据或强制降级。
5. 从 APK 元数据工具或安装结果核对包名；必要时列出候选包，再用 `adb -s SERIAL shell dumpsys package PACKAGE` 核对版本和更新时间。不能只凭相同版本号判断选对包，beta 与正式版可能包名不同、同时存在。用 `adb -s SERIAL shell cmd package resolve-activity --brief PACKAGE` 获取真实入口，再用 `adb -s SERIAL shell am start -n COMPONENT` 启动，不能猜入口。
6. 启动 `scrcpy --serial SERIAL --window-title 'Android 走查' --no-audio`，保留进程供后续操作。若 macOS 报无法初始化 SDL 显示、没有显示器，检查是否受执行沙箱限制；通过工具支持的授权方式在可访问桌面的环境重试。以实际窗口画面确认连接，不以进程启动日志代替可见画面。

## 操作与校准

按 Computer 工具初始化要求选择镜像窗口，读取工具文档。采用观察 → 定位 → 操作 → 再观察；坐标来自当前画面，滚动在手机内容区域内进行。可使用已授权的 ADB 输入作为等效入口，但必须检查真实结果；普通 `adb shell input text` 不保证中文输入正确，中文优先使用镜像与当前输入法。

首次短校准检查点击、纵向滚动、文本输入、系统返回、应用返回和截图保存。选择可逆、不会提交业务修改的入口；不为校准发送消息、购买、删除或改变设备配置。每项记录通过、失败或未验证及原因，未验证项不能宣称可用。ADB 系统返回可用 `adb -s SERIAL shell input keyevent KEYCODE_BACK`；应用内返回需定位应用自己的按钮。区分 Android 系统权限、键盘和返回行为与设计定义的自定义组件。

设备锁定和凭据由用户处理；新权限按当前任务需要及已有授权决定。断连或超时先查看真实状态，操作可能已生效；保存当前用例与 next_action，恢复后再继续。连接和控制故障不直接记为产品问题。

## 截图与证据

优先直接保存手机整屏原图：`adb -s SERIAL exec-out screencap -p > '/absolute/run/evidence/raw-android.png'`。检查命令成功、图像可打开且为当前状态；每个状态用独立文件，避免覆盖证据。整屏截图无需裁掉状态栏或导航栏。

若使用镜像窗口截图，保存工具返回的原生文件并记录手机内容边界；桌面和窗口边框不当作产品界面。确需提取手机区域时保留窗口原图，另存完整手机区域图，并记录两者关系，不把问题局部裁图当作整屏证据。

按 [取证与复核](evidence-and-review.md) 配对实际整屏与 Figma 依据。`render-evidence.py` 不发现问题，也不自动判断框坐标：模型核对设计后填写 annotations.json。实际红框、设计蓝框，主图保留完整 source；crop 仅生成补充细节图。打开生成图确认状态和框位置。

## 已验证范围与每轮记录

2026-10-21 在 macOS + OnePlus MT2110 / Android 14 上已验证：USB 授权、ADB 安装 APK、读取包名/版本、启动应用、scrcpy 5.0.1 镜像可见（用户确认）。当次 beta 包为 `com.tplink.tpm5.trial`，正式包为 `com.tplink.tpm5`，仅作区分渠道的实例。

这次接入尚未校准点击、滚动、输入、返回和截图，不能视为整轮走查已验证。新任务仍须完成所需控制校准，将真实设备、版本、包名、镜像/输入/截图方式、校准结果和限制写入 run.json 的 environment 与 LOG.md；不保存凭据。
