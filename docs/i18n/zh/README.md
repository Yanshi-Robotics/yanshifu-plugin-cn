# yanshifu

[![DeepSeek Harness 插件包](https://img.shields.io/badge/dsh-plugin-bundle-blue)](#快速开始)
[![Node](https://img.shields.io/badge/node-%5E22.19%20%7C%7C%20%3E%3D24-lightgrey)](../../../package.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](../../../LICENSE)

[English](../../../README.md) · 简体中文

一个 DeepSeek Harness 插件，装上就多一个**偃师傅八号**：只答四份资料里的事，就是《偃师傅的 SO-101 落地指南》《偃师傅的电脑体检指南》《GitHub 注册指南》《DeepSeek Harness 安装指南》。

## Quick Install Prompt · 安装用的提示词

把下面这段发给 DeepSeek Harness 里的助手，剩下的它做：

```text
安装 yanshifu 插件，插件位于 github: Yanshi-Robotics/yanshifu-plugin-cn 中，参照要求直接安装。

如果 github 拉不动，改装 release tarball：
https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz

装完确认技能列表里出现 /yanshifu，并让它回答「SO-101 的 BOM 是什么」。
```

最后那句别删。这套流程真正会翻车的地方，是插件报「装好了」但技能列表里根本没有它；最后那句就是让助手先证明技能答得出来，再说装完了。

它背后就一条命令 `dsh plugin --profile web add <来源>`：装包、同时把这个包选成 bundle，不用手工改任何配置文件，这个插件也不需要重启。想自己动手就看下面的「快速开始」。

## 这是什么

跟着《一起手搓机器人》第一季做 SO-101 的股东，问来问去就那几个问题：到底要买什么、我这台电脑够不够、这个舵机装哪条臂、校准那一步为什么过不去。答案都有，只是散在四份 PDF 里，翻起来费劲。

这个插件把四份资料收进一个技能，让助手照着资料答，而不是照着印象答。它还会读一遍你正在用的这台电脑。「我这配置够不够」这个问题因此值得问：答案对着你真实的 CPU、内存、硬盘和显卡给，不是对着通用表格给。

答案用中文，因为资料和读者都是中文的。插件本身不含宿主代码，只挂一个技能目录。

## 快速开始

自己装：Web 侧栏 **Plugins** 页里 **Add plugin**，把仓库填进去，装完启用；或者命令行：

```bash
dsh plugin --profile web add github:Yanshi-Robotics/yanshifu-plugin-cn
```

机器上要有 `git`，包是直接从仓库拉的。让助手代劳也行，但管插件的工具默认只在 Creator 预设里打开，普通会话里它就是替你跑上面这条命令。

**GitHub 慢或者连不上的话**，改装 release 里的 tarball：68 kB，不用克隆整个仓库，而且是从 GitHub 自己的 release 托管上取的：

```bash
dsh plugin --profile web add https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz
```

优先用这条，别用第三方的 GitHub 加速站：加速站夹在你和 GitHub 中间，能给你换成别的内容；上面这个包直接从 GitHub 取，校验和随 release 一起公布。

**仓名带语言。** 这个仓以 `-cn` 结尾，答中文；英文版会是 `yanshifu-plugin-en`。各装各的，不用装两个。

然后直接问，带不带斜杠都行：

```text
/yanshifu 机械臂要买什么？
/yanshifu 我这台电脑够不够跑 π₀.₅
/yanshifu EP10 讲了什么
```

技能也会自己触发：直接问「偃师傅，BOM 是什么」，不用点名也会加载，因为触发条件写在技能说明里。写 `@yanshifu` 也能用：`@` 在输入框里是引文件用的，不会补全出这个技能，但消息里有这个名字，助手就会去加载它。

## 它答什么

- **物料清单**：SO-101 全套 BOM，2026 年 10 月的参考价，三种舵机后缀各装哪条臂；手上已经有几样时先买什么。
- **电脑够不够**：读本机配置（CPU、内存、硬盘空余、显卡与显存），对上资料里的四档，说清能跑哪几个模型、训练放本地还是云端、哪几集在你这台机器上要跳过。
- **装配、打印与软件步骤**：装配顺序、接线、电机配置、校准、遥操、笛卡尔控制、手柄控制、切片设置。
- **模型选型**：ACT、SmolVLA、π₀、π₀.₅ 的权重、推理显存与训练显存。
- **更新进度**：包里资料到第几集，并提醒视频平台可能已经更新。

范围之外的它会直说：成本与利润、供应商与采购、橱窗运营、Season 2 及以后、别的机器人、通用编程问题，都不在这四份资料里，它不会硬答。

## 里面是什么

```text
skills/yanshifu/
├── SKILL.md                  人设、边界、章节路由、叫法
├── references/
│   └── hardware-check.md     三个系统的只读探测命令 + 四档判据
└── knowledge/                四份资料正文，加一份生成的索引
    ├── INDEX.md
    ├── SOURCES.md
    └── so101-guide.md · pc-checkup.md · github-signup.md · dsh-install.md
```

`cordis.patch.yml` 挂的是 `@deepseek-ai/dsh-skill-filesystem`，把 `bundledSkillDir` 指向包内的 `skills/`，所以整个插件就是一个技能提供方，没有宿主逻辑。

## 资料怎么更新

四份资料的正本在维护者手上的资料库里，每播一集就补一点。包里的正文是**快照**，`SOURCES.md` 记着同步时间和资料的最后一集。

从挨着资料库的克隆里重新同步：

```bash
npm run sync
```

资料在别处时用环境变量指过去：

```bash
YANSHIFU_SOURCE_DIR=/path/to/源文件 npm run sync
```

校验包里的正文是否还和源一致（可以放进 CI）：

```bash
npm run sync:check
```

脚本对源文件只读。图片换成 `〔配图：文件名.jpg〕` 占位、排版用的 `<div>` 只留内容，因为 5.6 MB 素材不进包；文字本身逐字照抄。

## 已知限制

- 知识是快照，出新一集要重新发一版。这是有意的：助手会说自己这份资料到第几集，不装作是实时的。
- 不打包图片和 PDF。答案要配图时会说明，并指向资料里对应的那一节。
- 只答中文。
- 只答这四份资料里的事，不是通用机器人助手，也不会假装是。

## 许可证

MIT，见 [LICENSE](../../../LICENSE)。
