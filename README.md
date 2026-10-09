# yanshifu

[![DeepSeek Harness 插件包](https://img.shields.io/badge/dsh-plugin-bundle-blue)](#快速开始)
[![Node](https://img.shields.io/badge/node-%5E22.19%20%7C%7C%20%3E%3D24-lightgrey)](package.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

> **English** — This repository is the Chinese edition, written for Chinese-speaking users; the plugin answers in Chinese. The English edition is `Yanshi-Robotics/yanshifu-plugin`. It is coming soon and is not open yet.

一个 DeepSeek Harness 插件，装上多**三个技能**：`/yanshifu` 是陪你把这季 SO-101 做出来的开发搭子，`/yanshifu ask`（或 `/ask`）只查资料，`/yanshifu update`（或 `/update`）把资料更新到最新一集。

## 这是什么

跟着《一起手搓机器人》第一季做 SO-101，卡点很少是「不知道那句话怎么念」，多半是「我这台机器现在这一步过不去」。所以这个插件分三块：

**`yanshifu` · 机器人开发增强。** 加载后先做三件事：问清你的课程仓 clone 在哪个目录（确认过的路径记在 `~/.yanshifu/project.json`，下次直接拿出来问你是不是还在那儿）；用只读探针扫一遍你的项目，看环境、校准、遥操日志、相机配置、数据集、训练产物，判断你做到哪一步；然后报一句「你现在到 EP<N>，下一步是这个，要不要现在做」。之后它按你实际卡住的地方干活：读你的代码与日志、跑不碰硬件的离线程序（仓里的 `tests/`、`ACT-1-Pick/offline_eval.py` 这类）、把要跑的命令写清楚交给你。碰真实硬件的命令（开相机、占串口、给电机上电）它只写不跑，那是你的手。

**`ask` · 资料速查。** 只从四份资料里找答案：BOM 与参考价、三种舵机后缀怎么分、电脑够不够跑某个模型、装配接线、切片设置、模型选型、更新到第几集。这一块不看你的项目，就是查得快、答得准、编不出来就说没有。

**`update` · 资料更新。** 查最新一集是第几集、你手上这份到第几集：一样就说已经是最新，落后就把正文装上，查不到就说查不到。

```text
/yanshifu                  看你做到哪一步，下一步做什么
/yanshifu ask BOM 是什么    查四份资料（等价于 /ask BOM 是什么）
/yanshifu update           把资料更新到最新一集（等价于 /update）
```

它手边有三个来源：**你的项目**、**偃师傅的公开仓**（课程仓 `Lets-Build-Robots-S1-SO101`、`lerobot-doctor`、`lerobot-remote-inference`）、以及**四份速查资料**。资料是手边的参考书，不是边界。

答案用中文，因为资料和读者都是中文的。插件本身不含宿主代码，只挂技能目录。

## Quick Install Prompt · 安装用的提示词

把下面这段发给 DeepSeek Harness 里的助手，剩下的它做：

```text
安装 yanshifu 插件，插件位于 github: Yanshi-Robotics/yanshifu-plugin-cn 中，参照要求直接安装。

如果 github 拉不动，改装 release tarball：
https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz

装完确认技能列表里出现 yanshifu、ask、update 三个技能，然后发一句 /yanshifu：
它应该先问你课程仓在哪个目录，报出你做到第几步，再问下一步要不要现在做。
```

最后那句别删。这套流程真正会翻车的地方，是插件报「装好了」但技能列表里根本没有它；最后那句就是让助手先证明技能答得出来，再说装完了。

它背后就一条命令 `dsh plugin --profile web add <来源>`：装包、同时把这个包选成 bundle，不用手工改任何配置文件，这个插件也不需要重启。想自己动手就看下面的「快速开始」。

## 在别的宿主上用

同一套技能文件（`skills/` 下那三个目录）在三个宿主上都能装，不需要改内容：

| 宿主 | 装法 | 叫起来 |
|---|---|---|
| **DSH** | `dsh plugin --profile web add github:Yanshi-Robotics/yanshifu-plugin-cn`，或本节的提示词 | `/yanshifu`、`/ask`、`/update` |
| **Codex** | 让它用自带的 skill-installer 从这个仓装：`scripts/install-skill-from-github.py --repo Yanshi-Robotics/yanshifu-plugin-cn --path skills/yanshifu skills/ask skills/update`；或克隆本仓后跑 `python3 scripts/install.py --host codex` | `$yanshifu`、`$ask`、`$update` |
| **Kimi** | 克隆本仓后跑 `python3 scripts/install.py --host kimi`（或 `--host agents`，那个根 DSH 与 Kimi 都读） | `/skill:yanshifu`、`/skill:ask`、`/skill:update` |

两个宿主的额外条件，装之前先知道：

- **Codex 的 skills 是实验特性，默认关着**。要在 `~/.codex/config.toml` 的 `[features]` 下加 `skills = true` 再重启；`install.py --host codex --enable-codex-skills` 可以替你改（改前备份 `config.toml`）。它还**跳过符号链接**，所以给它装的时候一律是复制，不是软链。
- **Codex 只读 `~/.codex/skills/`**，不读 `~/.agents/skills/`；**Kimi 与 DSH 两个根都读**，所以 `--host agents` 一次能顶两个。

`install.py` 的别开关：`--list-targets` 看准备装到哪、`--dry-run` 演练、`--force` 覆盖已存在的（旧的先备份成 `.bak-<时间戳>`）、`--link` 用软链（Codex 会退回复制）。

> ⚠️ 精度说明：这里只有 DSH 这条路是作者实测过的（本机 DSH 跑通）；Codex 与 Kimi 的装法与叫法照各自的官方文档写，作者还没在真机上验过。谁先验了谁改这一行。

## 快速开始

自己装：Web 侧栏 **Plugins** 页里 **Add plugin**，把仓库填进去，装完启用；或者命令行：

```bash
dsh plugin --profile web add github:Yanshi-Robotics/yanshifu-plugin-cn
```

机器上要有 `git`，包是直接从仓库拉的。让助手代劳也行，但管插件的工具默认只在 Creator 预设里打开，普通会话里它就是替你跑上面这条命令。

**GitHub 慢或者连不上的话**，改装 release 里的 tarball：69 kB，不用克隆整个仓库，而且是从 GitHub 自己的 release 托管上取的：

```bash
dsh plugin --profile web add https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz
```

优先用这条，别用第三方的 GitHub 加速站：加速站夹在你和 GitHub 中间，能给你换成别的内容；上面这个包直接从 GitHub 取，校验和随 release 一起公布。

**仓名带语言。** 这个仓以 `-cn` 结尾，专门给中文用户；英文版是 `yanshifu-plugin`，还没开放。各装各的，不用装两个。

然后直接用，带不带斜杠都行：

```text
/yanshifu                      看项目、报进度、给下一步
/yanshifu ask BOM 是什么        查四份资料
/ask 我这台电脑够不够跑 π₀.₅     同上，直接进资料速查
```

技能也会自己触发：直接问「偃师傅，我这步过不去」，不用点名也会加载，因为触发条件写在技能说明里。写 `@yanshifu` 也能用：`@` 在输入框里是引文件用的，不会补全出这个技能，但消息里有这个名字，助手就会去加载它。

## 它能干什么

**`yanshifu`（开发增强）**

- **你现在该做什么**：扫你的项目产物说清你到哪一步、下一步是什么，这是它默认开场。
- **报错怎么查**：先读你仓里最新的日志和报错原文、看现场（设备、版本），再下结论，不猜。
- **数据集与训练产物体检**：读 `datasets/<名字>/meta/info.json`、数回合与帧、看 `outputs/train/*/checkpoints/`，把事实列出来。
- **训练完上真机之前**：先跑 `ACT-1-Pick/offline_eval.py` 离线评估（不碰硬件），再谈真机测试。
- **要跑的命令**：写清哪个程序、哪个模式、在哪个目录、先激活环境、预期看到什么。
- **相机那一集**：怎么列相机、稳定路径怎么看、取景与旋转怎么定，这部分来自公开的课程代码仓 `Cameras/`。
- **环境与显卡**：指 `lerobot-doctor` 一键体检；显卡不够要上云指 `lerobot-remote-inference`。

**`ask`（资料速查）**

- **物料清单**：SO-101 全套 BOM，2026 年 10 月的参考价，三种舵机后缀各装哪条臂；手上已经有几样时先买什么。
- **电脑够不够**：读本机配置（CPU、内存、硬盘空余、显卡与显存），对上资料里的四档，说清能跑哪几个模型、训练放本地还是云端、哪几集在你这台机器上要跳过。
- **装配、打印与软件步骤**：装配顺序、接线、电机配置、校准、遥操、笛卡尔控制、手柄控制、切片设置。
- **模型选型**：ACT、SmolVLA、π₀、π₀.₅ 的权重、推理显存与训练显存。
- **节目更新到第几集**：包里资料到第几集，并提醒视频平台可能已经更新。
- **把资料更新到最新**（`update`）：比对本地与最新已发布版本，落后就把正文装上；只动技能自己的目录，不碰你的项目。

**两半都守的规矩**：资料里没写的，去公开的课程代码仓 `Yanshi-Robotics/Lets-Build-Robots-S1-SO101` 找（每集的程序按目录分：`Cameras/`、`Teleop/`、`Bringup/`、`Cartesian/` 等），答案里标明这条来自代码仓、不是资料。碰真实硬件的命令只写出来交给你跑，自己不代跑。

范围之外的它会直说：成本与利润、供应商与采购、橱窗运营、Season 2 及以后、别的机器人、通用编程问题，都不在范围内，它不会硬答。

## 项目进度怎么读的

`skills/yanshifu/scripts/project-scan.py` 只看文件状态——不开设备、不碰串口与相机、不执行你仓里的程序。它认这些产物（含义见课程仓 README）：

| 产物 | 说明你做到了 |
|---|---|
| `.venv/` | EP3：环境装好了 |
| `calibration/follower` 与 `calibration/leader` | EP6：两条臂校准过 |
| `Teleop/logs/` 里有日志 | EP7：跑过遥操与诊断 |
| `models/so101/` | 笛卡尔控制要用的臂模型下好了 |
| `Cartesian/gamepad_map.json` | EP9：手柄配过 |
| `cameras.json` | EP11：两台相机配好、方向定过 |
| `datasets/`（或 Hugging Face 缓存里的数据集） | EP12：录过数据 |
| `outputs/train/*/checkpoints/` | EP13：训练跑过 |
| `ACT-1-Pick/` | 第 12–15 课那个任务的工装 |

数据集只按 `meta/info.json` 认。LeRobot 缓存里还有 `calibration`、`videos` 这些它自己的目录，拿「有子目录」当数据集会把没录过数据的人判成已经录完了。

## 里面是什么

```text
skills/
├── yanshifu/                    机器人开发增强（/yanshifu）
│   ├── SKILL.md                 开工三步、能做什么、来源与边界、进度判据
│   └── scripts/
│       └── project-scan.py      找项目目录 / 扫进度 / 记住路径（只读文件，不碰硬件）
├── ask/                         资料速查（/yanshifu ask、/ask）
│   ├── SKILL.md                 人设、知识边界、章节路由、BOM 与橱窗、口吻
│   ├── knowledge/               四份资料正文，加一份生成的索引
│   │   ├── INDEX.md
│   │   ├── SOURCES.md           头部三个可机读字段：随包版本 / 同步时间 / 最新一集
│   │   └── so101-guide.md · pc-checkup.md · github-signup.md · dsh-install.md
│   └── references/
│       └── hardware-check.md    三个系统的只读探测命令 + 四档判据
└── update/                      资料更新（/yanshifu update、/update）
    ├── SKILL.md                 查最新一集 → 比对本地 → 落后就装
    └── scripts/
        └── update.py            三源探测 + 逐文件原子替换（只动本技能自己的目录）
```

资料与硬件判据归 `ask`（它才是查资料那一半），探针归 `yanshifu`，更新归 `update`；`yanshifu` 要引用资料里的数字时直接读 `../ask/knowledge/`，要整段问答就把 `ask` 技能加载起来。

`cordis.patch.yml` 挂的是 `@deepseek-ai/dsh-skill-filesystem`，把 `bundledSkillDir` 指向包内的 `skills/`，三个技能一起注册，整个插件没有宿主逻辑。

## 资料怎么更新

包里的四份正文是**快照**。`SOURCES.md` 头部记着三个可机读的值：随包版本、同步时间、资料更新到第几集。

学员侧只有一个动作：

```text
/yanshifu update
```

它会先查最新发布到第几集、再看你手上这份到第几集：一样就说「已经是最新」，落后就把内容装上，查不到就直说查不到。装的时候是逐文件替换（写临时文件再改名），不会动你机器上别的东西。

比它新的那份从哪来：`skills/update/scripts/update.py` 依次试 release 包、`SOURCES.md`、GitHub API，全是同一个公开仓里的东西。装的时候先试 release 包，包取不到就从仓里逐文件取那几份正文；两条都不通会明说「查到有新版但取不到」，不会假装装好了。取数据先走 Python 标准库、失败自动退回系统 `curl`（国内网络下 curl 明显更稳）。

出新的正文由上一条线负责，不在这个仓里：正文正本、出版工装、同步与发版都在发布者侧的私有资料库仓，`/publish` 技能管那一段。这个仓里只有学员要用的东西。

## 已知限制

- 知识是快照，出新一集要重新发一版。这是有意的：助手会说自己这份资料到第几集，不装作是实时的。
- 不打包图片和 PDF。答案要配图时会说明，并指向资料里对应的那一节。
- 只答中文。
- ⚠️ 后两个技能的名字就叫 `ask` 与 `update`，短是短，但别家插件也可能起同名：真撞上了（技能列表里出现两个同名的），用 `/yanshifu ask`、`/yanshifu update` 一定进的是这两个。
- **默认只读**：不改你仓里的文件，要改先问；⛔ 不代跑碰真实硬件的命令（开相机、占串口、上电），只把命令写清楚。
- 进度判断靠 `project-scan.py`，它要机器上有 `python3`（3.10 以上）；扫的是产物，不是结论，报出来会先问你「对不对」。
- 确认过的项目路径记在 `~/.yanshifu/project.json`，只存路径和确认时间；不想要就 `project-scan.py forget`。
- 以这四份资料与偃师傅的公开仓为准；两处都没有的直说没有，不编。
- 不是通用机器人助手，也不会假装是。

## 许可证

MIT，见 [LICENSE](LICENSE)。
