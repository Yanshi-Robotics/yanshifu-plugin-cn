偃师傅的电脑体检指南 · 偃师造物 · 工具版本 0.1.6 · 2026-09-20 起生效

# 偃师傅的电脑体检指南

本版对应体检工具 0.1.6，2026-09-20 起生效；群里以最新一版为准。

很多股东问：我这台电脑能不能跑 LeRobot、能不能训练、要不要换显卡。偃师傅做了一个体检工具，粘一行命令，它自己装好 LeRobot 0.6.1，真的跑一遍五个模型，最后在终端里打出一张报告，告诉你能做什么、不能做什么、哪一步得上云。不用会 Python，Windows、macOS、Linux 都行。

## 一、链接

| 名称 | 网址 | 拿它做什么 |
|---|---|---|
| 体检工具仓库 | https://github.com/Yanshi-Robotics/lerobot-doctor | 下面的命令都从这里拉；有问题在这里提 |
| LeRobot 官方仓库 | https://github.com/huggingface/lerobot | 体检装的就是它的 0.6.1 版 |

## 二、怎么跑

打开对应的窗口，把整行粘进去，回车。命令从仓库页面的代码块里复制，那里有复制按钮；从聊天窗口复制有时会带进看不见的字符，命令就找不到了。

命令里不再带版本号：以后工具更新，还是粘这同一条，跑的就是新版。之前用过网址里带 v0.1.3 那条命令的股东，这次重新复制一次。

Windows 10 / 11，开始菜单搜 PowerShell 打开：

```powershell
irm https://raw.githubusercontent.com/Yanshi-Robotics/lerobot-doctor/main/doctor.ps1 | iex
```

macOS，打开「终端」：

```bash
curl -LsSf https://raw.githubusercontent.com/Yanshi-Robotics/lerobot-doctor/main/doctor.sh | bash
```

Linux，打开终端：

```bash
curl -LsSf https://raw.githubusercontent.com/Yanshi-Robotics/lerobot-doctor/main/doctor.sh | bash
```

## 三、跑的时候会发生什么

1. 先读电脑规格，几秒钟。磁盘不到 30 GB、内存不到 8 GB 会在这里停下，告诉你差多少。
2. 问一句要不要继续，回车就开始：建一个独立环境装 LeRobot（约 7 GB），下载样例数据和三个预训练模型（约 13 GB）。有 NVIDIA 显卡的电脑全程 30 到 60 分钟，Apple Silicon 的 Mac 走 MPS 加速，介于两者之间，只有 CPU 的电脑 1 到 2.5 小时。主要时间都在下载，屏幕上一直有进度条。
3. 浏览器会自动弹出一个网页，里面有一条 SO-101 三维模型。每个模型测完推理速度，就在这条臂上跑十秒钟样例任务，你能看到它在动。
4. 五个模型从小到大逐个测：ACT、Diffusion、SmolVLA、X-VLA、WALL-OSS。每个先测推理，再真的训练几步。中途 `Ctrl-C` 可以停，跑完的部分会留着。

## 四、报告怎么看

最后终端里打两张带边框的报告，内容一样，先英文一张，再中文一张，看中文那张就行。下面是偃师傅自己这台电脑跑出来的中文那张，5 分钟跑完五个模型：

〔配图：偃师傅这台电脑的体检报告：Ubuntu 24.04 加一块 RTX 5070 Ti。Mac 和 Windows 上表格长得一样，第一块会换成你自己的系统和显卡〕

这张是 Ubuntu 加一块 RTX 5070 Ti 的结果。Mac 和 Windows 上表格是同一个样子，第一块会换成你自己那台的系统、处理器和显卡；Apple Silicon 的 Mac 那一行写的是 MPS，不是 CUDA。

重点看两处。

各级实测那张表，每个模型两格，推理一格、训练一格，符号只有四种：`✓` 实测通过；`!` 能用但有条件，比如训练要过一夜；`✗` 实测失败或者硬门槛，比如权重比显存还大，旁边写着算式；`–` 这次没测到，下面写着原因。

测的五个模型比课程实际要用的多。课程只教 ACT、SmolVLA 和 π₀.₅ 这三个，体检把 Diffusion、X-VLA、WALL-OSS 也跑一遍，是因为它们的大小正好卡在几条不同的线上，多测这几个才看得出这台电脑的上限在哪。π₀ 没在里面，因为它要先登录 Hugging Face 并同意 Google 的许可。

最下面「SO-101 路线」一句话，是给你这台电脑的结论。常见的三种：全流程本地；本地录数据、上云训练、拿回来本地跑；这台电脑只能做组装、校准、遥操作和录数据，训练和推理要另找机器。

报告的完整数据存在 `~/lerobot-doctor/report-<日期>-<时分>.json`，每跑一次一个文件，最新的一份另存一个 `report-latest.json`（Windows 在 `C:\Users\你的用户名\lerobot-doctor\`）。在群里求助时把这个文件发出来，偃师傅看这个文件就知道你电脑的情况。

只有 CPU、没有 NVIDIA 显卡的电脑，推理那一列常见「接近上限」或「太慢」，训练那一列从第二个模型起多半写「只会更慢 → 上云」。这一格没有出错：工具量过第一个模型的训练速度后，更大的模型就不再白跑了。这类电脑能做的事和上云的办法，偃师傅在群里另说。

## 五、常见问题答疑

下载很慢或者中断：中国大陆的网络访问 Hugging Face 慢，先设一个镜像再跑。Windows 在 PowerShell 里输入 `$env:HF_ENDPOINT="https://hf-mirror.com"`，macOS 和 Linux 输入 `export HF_ENDPOINT=https://hf-mirror.com`，然后再粘上面的命令。下载中断了直接重跑，下好的部分不会重下。

启动器在「准备 Python 3.12」这一步报错：电脑上没有 Python 3.12 时，启动器要从 GitHub 下载一个，中国大陆的网络常拉不到。屏幕上会写「下载 Python 3.12 失败」和一个变量名 `UV_PYTHON_INSTALL_MIRROR`，把它设成一个镜像地址再重跑就行；电脑上本来就有 Python 3.12 的，启动器直接用它，不下载。

为什么没有 π0：π0 系列的模型要先在 Hugging Face 上登录账号、同意 Google 的许可才能下载，体检工具不给股东添这个麻烦。X-VLA 和 WALL-OSS 是同一档次的模型，够用来判断这台电脑的上限。

窗口一闪就没了，或者程序自己报错：0.1.4 起，Windows 的窗口会等你按回车再关，不会自己消失。程序自己出错时，屏幕上会打出错误原因和一个崩溃日志的位置 `~/lerobot-doctor/logs/crash-<时间>.log`（Windows 在 `C:\Users\你的用户名\lerobot-doctor\logs\`）。把这个文件发到群里，有报告文件的话一起发；也可以提到本资料开头链接表里的体检工具仓库，偃师傅照着修。

不想要了怎么删：环境和报告都在 `~/lerobot-doctor` 这一个文件夹里，删掉它就干净了。下载过的模型留在 Hugging Face 的缓存里，以后直接复用，不用重下。
