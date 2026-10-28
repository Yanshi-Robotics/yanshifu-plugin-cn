GitHub 与国内镜像源 · 偃师造物 · 2026-10-18 更新

<!-- 事实来源，不进入 PDF；2026-10-18 核对：
  清华大学知识工程团队公开组织页：https://github.com/THUDM
  DeepSeek 项目与英文技术报告：https://github.com/deepseek-ai/DeepSeek-V3 与 https://arxiv.org/abs/2412.19437
  Moonshot AI 的 Kimi 项目与英文技术报告：https://github.com/MoonshotAI/Kimi-K2 与 https://arxiv.org/abs/2507.20534
  OpenReview 用途：https://openreview.net/about
  Hugging Face 模型、数据集与演示：https://huggingface.co/docs/hub/index
  GitHub 账号说明：https://docs.github.com/en/account-and-profile/how-tos/account-management/creating-an-account-on-github
  清华 Release 范围：https://mirrors.tuna.tsinghua.edu.cn/help/github-release/
  中科大 Release 范围：https://mirrors.ustc.edu.cn/help/github-release.html
  公开资源加速与 clone 格式：https://gh-proxy.com/docs/github-accelerator
  清华 PyPI 参数：https://mirrors.tuna.tsinghua.edu.cn/help/pypi/
  Git remote set-url：https://git-scm.com/docs/git-remote
  只核对公开项目与服务文档；本轮未执行 clone、安装、训练或硬件测试。
-->

# GitHub与国内镜像源

人工智能与具身智能的研究面向国际社区，论文、开源代码、模型与数据集通过不同平台发布和交流。清华大学的[知识工程团队](https://github.com/THUDM)、[DeepSeek](https://github.com/deepseek-ai/DeepSeek-V3)、Kimi 背后的 [Moonshot AI](https://github.com/MoonshotAI/Kimi-K2) 都在 GitHub 分享项目，也通过论文和模型平台公开研究成果。

英语是国际 AI 研究中常用的交流语言。[DeepSeek-V3](https://arxiv.org/abs/2412.19437) 和 [Kimi K2](https://arxiv.org/abs/2507.20534) 的技术报告都使用英文，方便不同国家的研究者阅读、比较和复现。学习机器人开发，需要熟悉这些团队共同使用的论文与开源平台。

## 一、论文与开源平台

| 平台 | 网址 | 主要用途 |
|---|---|---|
| arXiv | https://arxiv.org | 阅读论文预印本与技术报告，查看作者公开的方法和实验 |
| OpenReview | https://openreview.net | 查看学术会议论文，以及按会议规则公开的评审、回复和讨论 |
| GitHub | https://github.com | 获取项目代码、安装说明与版本更新，向维护者反馈问题 |
| Hugging Face | https://huggingface.co | 获取模型权重、数据集、模型说明和在线演示 |

这些平台分工不同：论文说明方法，GitHub 提供代码，Hugging Face 常用于发布模型和数据集。本课程使用的 LeRobot 也采用这种方式组织资料，项目说明会给出代码、模型、数据和文档的对应入口。

阅读英文页面时，可以用浏览器翻译辅助理解；复制命令、文件名和报错时切回原文，避免改动需要逐字使用的内容。

## 二、GitHub 与课程资料

| 入口与用途 | 网址 |
|---|---|
| GitHub 官网：搜索开源项目，查看代码和 README 说明 | https://github.com |
| GitHub 注册：需要提问题、收藏或订阅更新时，按页面提示创建账号 | https://github.com/signup |

每期程序见[第一季开源代码仓](https://github.com/Yanshi-Robotics/Lets-Build-Robots-S1-SO101)；体检命令、报告与问题反馈见[电脑体检工具仓](https://github.com/Yanshi-Robotics/lerobot-doctor)。

课程仓库是公开的，不注册也能阅读和下载。在仓库页点击 Code，再选 Download ZIP，可以下载源码压缩包；已经安装 Git 的，也可以克隆：

```bash
git clone https://github.com/Yanshi-Robotics/Lets-Build-Robots-S1-SO101.git
```

账号用于参与项目协作：Issues 用来反馈问题，Star 用来收藏，Watch 用来订阅更新。反馈课程程序问题时，附上操作系统、完整命令、报错和已尝试的处理方法即可。LeRobot、SO-101 硬件及其他课程入口见第一章的重要链接。

## 三、国内镜像与下载加速

### 先按下载内容选择入口

国内常说的“GitHub 镜像”包含几种不同服务。高校通常只同步选定项目的文件，第三方加速服务转发公开下载请求，PyPI 镜像则提供 Python 软件包。选择时先看自己要下载什么：

| 入口 | 适合下载什么 | 使用范围 |
|---|---|---|
| 清华 TUNA：[Release](https://mirrors.tuna.tsinghua.edu.cn/github-release/) / [Raw](https://mirrors.tuna.tsinghua.edu.cn/github-raw/) | 已收录项目的发布文件或原始文件 | 仅限目录中列出的项目 |
| 中科大的 [Release 镜像](https://mirrors.ustc.edu.cn/github-release/) | 已收录项目的发布文件 | 先检查目录中是否有目标项目与版本 |
| [GH-Proxy 使用说明](https://gh-proxy.com/docs/github-accelerator) | GitHub 公开仓库克隆、ZIP、Release 与 Raw 文件 | 第三方加速服务，按页面选择当前可用入口 |
| [清华 PyPI 使用说明](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/) | 通过 pip 安装的 Python 软件包 | 只加速软件包下载 |

清华的 GitHub Release 帮助说明，这类镜像通常提供二进制发布文件，未必包含源码；Raw 镜像也只同步目录中列出的内容。下载软件安装包时，可以先查高校目录；下载本课程代码时，不能直接把 github.com 换成高校镜像站的域名。

### 课程代码下载不通时

先使用前面的 GitHub 官方仓库和 Download ZIP。下载失败时，可以打开 GH-Proxy 页面，粘贴原始的公开仓库链接，按页面提供的入口获取分支 ZIP；下载单个文件或 Release 附件时，粘贴对应文件的完整链接。

已经安装 Git、准备第一次获取课程仓库的，也可以按该服务文档使用下面的临时加速入口。repo 保存官方仓库地址，proxy 保存加速前缀；两者拼接后交给 Git。官方克隆和加速克隆选择一种即可。

**Linux / macOS · 终端**

```bash
repo="https://github.com/Yanshi-Robotics/Lets-Build-Robots-S1-SO101.git"
proxy="https://gh-proxy.org/"
git clone "${proxy}${repo}"
```

**Windows · PowerShell**

```powershell
$repo = "https://github.com/Yanshi-Robotics/Lets-Build-Robots-S1-SO101.git"
$proxy = "https://gh-proxy.org/"
git clone "$proxy$repo"
```

通过此地址克隆后，origin 通常会保留加速地址，后续拉取也会经过该服务。网络能够直接访问 GitHub 时，在刚才的同一终端中运行下面的命令，进入课程仓库并恢复官方更新入口；Linux、macOS 和 PowerShell 写法相同。如果已经重开终端，先重新执行上面设置 repo 的那一行。

```sh
cd Lets-Build-Robots-S1-SO101
git remote set-url origin "$repo"
git remote -v
```

只把公开仓库和公开文件交给第三方加速服务，不在加速站输入 GitHub 密码或访问令牌。注册、登录、提 Issue 和订阅更新仍在 GitHub 官方网站完成。加速入口失效时，回到服务说明页查看当前地址，保留课程仓库的官方地址。

### Python 软件包下载不通时

进入 EP3 创建的虚拟环境并激活后，可以给本次 pip 命令加上清华源参数。例如，在当前环境中升级 pip：

```bash
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade pip
```

安装其他 PyPI 软件包时，也可以在原有安装命令中加入同样的 `-i` 地址；课程要求的软件包名称和版本继续按对应节目填写。这种写法只作用于本次命令，不修改默认下载源。

PyPI 镜像不能代替 GitHub 仓库下载，也不会加速模型权重和数据集下载。遇到 `git+https://github.com/` 形式的安装地址，仍要检查 GitHub 的连接。
