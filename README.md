# yanshifu

[![DeepSeek Harness bundle](https://img.shields.io/badge/dsh-plugin-bundle-blue)](#quick-start)
[![Node](https://img.shields.io/badge/node-%3E%3D20-lightgrey)](package.json)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

English · [简体中文](docs/i18n/zh/README.md)

A DeepSeek Harness plugin that adds **偃师傅八号**, an assistant that answers from four Yanshi Robotics handbooks: the SO-101 build guide, the PC checkup guide, the GitHub signup guide, and the DeepSeek Harness install guide.

## Quick Install Prompt

Paste this into a DeepSeek Harness session and let the agent do it:

```text
安装 yanshifu 插件，插件位于 github: Yanshi-Robotics/yanshifu-plugin-cn 中，参照要求直接安装。

如果 github 拉不动，改装 release tarball：
https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz

装完确认技能列表里出现 /yanshifu，并让它回答「SO-101 的 BOM 是什么」。
```

In English: install the yanshifu plugin from `github: Yanshi-Robotics/yanshifu-plugin-cn`, following this repository's instructions; if GitHub will not fetch it, install the release tarball instead; then check that `/yanshifu` shows up in the skill list and can answer a bill-of-materials question.

The last line is the part worth keeping. The failure this flow actually hits is a plugin that reports a successful install and then never appears in the skill list, so the prompt asks the agent to prove the skill answers before calling it done.

Under the hood it is one command — `dsh plugin --profile web add <source>` — which installs the package and selects it as a bundle. Nothing has to be edited by hand, and no restart is needed for this plugin. Prefer to drive it yourself? See [Quick start](#quick-start).

## Overview

People following the *Let's Build Robots* Season 1 series keep asking the same questions: what exactly do I have to buy, is my laptop enough, which motor goes on which arm, why does the calibration step fail. The answers exist, but they are spread across four PDFs that are painful to search.

This plugin packages those four handbooks into a skill, so the assistant answers from the text instead of from memory. It also reads the machine it runs on, which is what makes the hardware question worth asking: "is my computer enough" gets answered against your actual CPU, RAM, disk and GPU, not against a generic table.

Answers are in Chinese, because the handbooks and the audience are Chinese. The plugin adds no host code: it registers a skill directory and nothing else.

## Quick start

Install it yourself from the **Plugins** page in the Web sidebar — **Add plugin**, paste the repository, install, enable — or from a terminal:

```bash
dsh plugin --profile web add github:Yanshi-Robotics/yanshifu-plugin-cn
```

`git` has to be on the machine, because the package is fetched from the repository. Letting the agent do it works too, but plugin-management tools are only switched on in the Creator preset, so an ordinary session runs this same command through the shell.

If GitHub is slow or unreachable where you are, install the release tarball instead. It is 68 kB rather than a full repository clone, and it comes from GitHub's own release hosting:

```bash
dsh plugin --profile web add https://github.com/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest/download/yanshifu-plugin-cn.tgz
```

Prefer that over a third-party GitHub proxy site. A proxy sits in the middle of your download and can hand you different content; the tarball above comes from GitHub itself, and its checksum is published with the release.

**The repository name carries the language.** This one ends in `-cn` and answers in Chinese. An English edition would be published as `yanshifu-plugin-en`, so a user installs the one they want and never both.

Then ask, with or without the slash:

```text
/yanshifu 机械臂要买什么？
/yanshifu 我这台电脑够不够跑 π₀.₅
/yanshifu EP10 讲了什么
```

The skill is also model-invocable: asking "偃师傅，BOM 是什么" without naming the skill triggers it, because the description covers that ground. Writing `@yanshifu` works too — `@` is reserved for file references in the composer, so it will not autocomplete, but the name in the message is enough for the assistant to load the skill.

## What it answers

- **Bill of materials** — every line of the SO-101 BOM with October 2026 reference prices, which of the three motor suffixes goes on which arm, and what to buy first if you already own some of it.
- **Whether your computer is enough** — reads the local machine (CPU, RAM, free disk, GPU and VRAM), places it in one of the guide's four tiers, and says which policies you can run, whether training fits locally or belongs in the cloud, and which episodes to skip on your platform.
- **Build, print and software steps** — assembly order, wiring, motor configuration, calibration, teleoperation, Cartesian control, gamepad control, slicing settings.
- **Model selection** — ACT, SmolVLA, π₀ and π₀.₅ weights, inference memory and training memory.
- **Progress** — how far the bundled handbooks go, plus a reminder that the video platform may already be ahead.

It declines the rest. Cost and profit accounting, suppliers and purchasing, marketplace operations, Season 2 and later, other robots, and general programming questions are outside these four handbooks, and the assistant says so rather than guessing.

## How it is put together

```text
skills/yanshifu/
├── SKILL.md                  persona, scope, routing, wording rules
├── references/
│   └── hardware-check.md     read-only probes per OS + the four-tier criteria
└── knowledge/                the four handbooks, plus a generated index
    ├── INDEX.md
    ├── SOURCES.md
    └── so101-guide.md · pc-checkup.md · github-signup.md · dsh-install.md
```

`cordis.patch.yml` mounts `@deepseek-ai/dsh-skill-filesystem` with `bundledSkillDir` pointing at the packaged `skills/` directory, so the whole plugin is a skill provider with no host logic.

## Maintaining the knowledge

The handbooks live in a private archive that only the maintainer has, and they grow every episode. The bundled copies are therefore a snapshot, and `SOURCES.md` records when it was taken and how far the guide goes.

Refresh the snapshot from a checkout that sits next to the archive:

```bash
npm run sync
```

Point it somewhere else with the environment variable:

```bash
YANSHIFU_SOURCE_DIR=/path/to/源文件 npm run sync
```

Verify that the packaged copies still match the source, for example in CI:

```bash
npm run sync:check
```

Source files are only ever read. The script normalizes images into `〔配图：file.jpg〕` placeholders and drops layout `<div>` wrappers, because the 5.6 MB of images stay out of the package; the prose itself is copied verbatim.

## Limits

- The knowledge is a snapshot, so a fresh episode needs a fresh release. That is deliberate: the assistant says which episode its own copy ends at instead of pretending to be live.
- Images and the printable PDFs are not bundled. Answers that depend on a picture say so and point at the guide.
- Answers are in Chinese only.
- The plugin answers from these four handbooks. It is not a general robotics assistant and will not pretend to be one.

## License

MIT — see [LICENSE](LICENSE).
