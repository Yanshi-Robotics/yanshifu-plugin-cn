DSH 与 AI Agent 协作指南 · 偃师造物 · 桌面版优先 · 2026-10-17 更新

<!-- 官方入口与行为依据，2026-10-17 核对，不进入 PDF：
  桌面下载：https://deepseek.com/harness/
  工作区与首次提问：https://deepseek-harness.github.io/deepseek-harness/guide/quickstart
  模型配置：https://deepseek-harness.github.io/deepseek-harness/guide/providers
  账号、API Key 与开发用途：https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-settings-account/README.zh.md
  桌面运行时：https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/desktop/README.zh.md
  Web 启动与 Node 要求：https://github.com/deepseek-ai/deepseek-harness
  API 价格：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
  本轮只核对文档，不代表已执行安装、模型调用或硬件测试。
-->

# DSH 与 AI Agent 协作指南

## 用 AI Agent 协作开发

机器人开发同时涉及代码、环境配置、日志和真实硬件。AI Agent 可以读取我们选定的项目文件，结合报错查找原因，修改代码并运行软件检查；机械臂的装配、接线、上电和现场观察仍由我们完成。本章使用 DeepSeek Harness（简称 DSH），并为它安装偃师傅插件，方便查询第一季课程资料。

普通问答需要我们逐段粘贴代码，AI Agent 则能在授权的工作区内查找相关文件。因此，开始时先告诉它当前期数、目标和项目位置，让它读取实际文件后再提出修改。报错消失只说明对应的软件问题得到处理，抓取是否成功还要按课程要求在现场验证。

## 安装 DSH 桌面客户端

打开 [DSH 官方下载页](https://deepseek.com/harness/)，选择与电脑匹配的安装包。当前官网提供 Windows 64 位和 Apple 芯片 Mac 的桌面客户端。桌面版从官方安装包开始，无需照旧版教程先安装 Node.js。

1. 安装并打开 DSH，按欢迎页提示登录 DeepSeek 账号；桌面客户端会通过系统浏览器完成授权。也可以按界面提供的方式配置 API 密钥：在 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 创建自己的密钥，再到“设置 → 模型”填入。
2. 若首次引导询问用途，选择“开发”。若已跳过引导，或配置密钥后仍无法读取项目文件、使用终端，到设置中检查代码工作工具是否开启。
3. 账号登录与 API 密钥是两种接入方式，额度、权益和计费分别按对应页面说明查看。使用 API 时先查看开放平台的余额和 [当前价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)，不要沿用旧截图中的报价。
4. 添加并选中第一季开源仓库在本机的文件夹作为工作区。这个文件夹应包含仓库的 README 和课程代码；GitHub 网页地址不能代替本地工作区。
5. 在模型选择器中选一个当前可用的模型。需要审批的文件修改和命令执行，先阅读操作内容，再决定是否允许。

密钥只填入设置页，不粘贴进对话、日志或代码仓库。交给模型处理的代码和日志会发送到相应模型服务，提交前先去掉密钥和私人资料。

### 没有对应桌面安装包时

Linux 等官网尚未列出桌面包的平台，可以使用 Web 版。先安装符合官方要求的 Node.js：本版核对的要求为 22.19.0 及以上的 22 系版本，或 24 及以上版本。然后在终端运行：

```sh
npx @deepseek-ai/dsh web
```

启动后使用终端打印的完整网址打开页面，保留可能附带的访问令牌。保持该终端运行，再按上面的步骤配置模型和工作区。桌面版与 Web 版的界面可能随更新调整，入口以 [官方使用指南](https://deepseek-harness.github.io/deepseek-harness/guide/quickstart) 为准。

## 先读项目，再解决问题

第一次打开课程项目时，我们先让 DSH 读取 README、环境说明和已有日志，核对当前做到哪一步。可以把下面这段发给它，按实际情况补充期数和目标：

```text
我正在学习《一起手搓机器人》第一季，当前做到 EP〔填写期数〕。
当前目标是〔填写本次目标〕，工作区已选择我的课程代码仓库。

请先读取 README、相关配置和已有日志，说明项目当前状态，
指出完成这个目标还缺什么。暂时只读，不修改文件、不安装软件。
需要补充信息时列出具体问题，不要根据目录名称推断测试已经通过。
涉及相机、串口、电机、上电或运动的操作，只准备步骤，由我执行。
```

处理问题时，一次给出一个明确目标，并按下面的顺序推进：

1. 提供现场信息：说明操作系统、课程期数、刚执行的命令、完整报错，以及相关日志的位置。接线和电机标签等信息由我们检查后补充。
2. 查找原因：让 DSH 读取对应配置、代码和日志，说明哪些信息支持判断，缺少什么信息；不要直接要求它重装整个环境。
3. 确认修改：看清它准备改哪些文件、运行什么命令，再允许必要操作。修改后让它列出实际改动和软件检查结果。
4. 现场执行并反馈：相机、串口、电机配置、校准和运动命令由我们按课程步骤执行，再把输出和观察结果交回 DSH。训练任务也先核对数据路径、显卡和预计资源，再自行启动。

AI 可以帮我们整理测试表、分析已有结果，但不能把尚未执行的测试写成通过。EP14 的成功率、重试和安全中止记录，都以实际执行结果为准。
