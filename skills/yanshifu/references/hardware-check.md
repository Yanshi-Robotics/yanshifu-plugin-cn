# 电脑配置诊断

给「我这台电脑够不够」这类问题用。⭐ 做法是**读本机真实硬件，再对照资料里的判据**，⛔ 不是把要求表念一遍。

判据出处在《落地指南》第四节「电脑配置要求」与第五节「四个模型各要什么硬件」；正文在 `../knowledge/so101-guide.md`，本文件是给动手用的速查。

## 一、先问一句

要分清对方想做哪件事，答案不一样：

- 只想**在本机跑推理**（跟着节目做到哪算哪）；
- 想**在本机训练** ACT / SmolVLA；
- 只是想知道**要不要换电脑**。

没问清就先按「推理 + 以后可能训练」给，并说明训练可以放云端。

## 二、只读探测（三个系统各一套）

全部是只读命令：⛔ 不装驱动、⛔ 不改系统设置、⛔ 不下载模型、⛔ 不动机械臂。

**Linux**

| 查什么 | 命令 |
|---|---|
| 系统版本 | `cat /etc/os-release \| head -3` |
| CPU | `lscpu \| grep -m1 'Model name'` · 核数 `nproc` |
| 内存 | `free -h \| awk '/^Mem:/{print $2}'` |
| 硬盘空余 | `df -h "$HOME" \| tail -1` |
| 显卡与显存 | `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader` |
| 没装 NVIDIA 驱动时 | `lspci \| grep -Ei 'vga\|3d'` |

**macOS**

| 查什么 | 命令 |
|---|---|
| 系统版本 | `sw_vers -productVersion` |
| 芯片 | `sysctl -n machdep.cpu.brand_string`（Apple Silicon 会打出 `Apple M…`）· 核数 `sysctl -n hw.ncpu` |
| 内存 | `sysctl -n hw.memsize`（字节，除 1073741824 得 GB） |
| 硬盘空余 | `df -h "$HOME" \| tail -1` |
| 显卡 | `system_profiler SPDisplaysDataType \| grep -E 'Chipset\|VRAM\|Metal'` |

**Windows（PowerShell）**

| 查什么 | 命令 |
|---|---|
| 系统版本 | `(Get-CimInstance Win32_OperatingSystem).Caption` |
| CPU | `(Get-CimInstance Win32_Processor).Name` · 核数同一条取 `.NumberOfCores` |
| 内存 | `[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)` |
| 硬盘空余 | `Get-PSDrive C \| Select-Object @{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}}` |
| 显卡 | 有 NVIDIA 驱动就用 `nvidia-smi --query-gpu=name,memory.total --format=csv,noheader`；没有就 `Get-CimInstance Win32_VideoController \| Select-Object Name`，⚠️ 它的 `AdapterRAM` 对 4 GB 以上的卡会报错值，⛔ 别拿它当显存依据 |

命令的用法受本机环境限制，逐条跑、跑不了就跳过；**测不到的项目写「没测到」并说明原因，⛔ 不猜、不按型号推断。**

## 三、判据（照《落地指南》抄，别自己改数）

四档的硬指标：

| | 最低 | 标准 | 高级 | 顶级 |
|---|---|---|---|---|
| 能推理 | ACT | ACT、SmolVLA | ACT、SmolVLA、π₀、π₀.₅ | 同高级 |
| 本地训练 | 不支持 | 不支持 | ACT、SmolVLA | 四个都能 |
| 独立显卡 | 不需要 | NVIDIA 8 GB（Apple Silicon 不需要） | NVIDIA 16 GB | NVIDIA 40 GB |
| CPU | 4 核 | 8 核 | 8 核 | 12 核 |
| 内存 | 8 GB | 16 GB | 32 GB | 64 GB |
| 硬盘空余 | 30 GB | 40 GB | 100 GB | 100 GB |
| 系统 | Windows 10/11；macOS（Intel / AS）；Ubuntu 20.04+ | Windows 11；macOS 14+（AS）；Ubuntu 22.04 / 24.04 | Ubuntu 22.04 / 24.04；Windows 11 | Ubuntu 22.04 / 24.04 |

模型这一层（权重多大、推理要什么、训练要什么）：

| 模型 | 权重 | 全量推理 | 本地训练 |
|---|---|---|---|
| ACT | 0.2 GiB | CPU 即可（含 Apple Silicon）；NVIDIA GTX 1650 及以上 | Apple Silicon 6–14 小时；NVIDIA 6 GB |
| SmolVLA | 865 MiB（本身 BF16） | Apple Silicon 16 GB（能跑但不流畅）；NVIDIA 8 GB | NVIDIA 16 GB |
| π₀ | 13.0 GiB | NVIDIA 16 GB；Apple Silicon 32 GB（能跑，速度未知） | NVIDIA 40 GB |
| π₀.₅ | 13.5 GiB | 同 π₀ | 官方配方 NVIDIA 80 GB |

几条容易漏的硬约束：

- 课程环境的 PyTorch **只支持 GTX 16 系、RTX 20 系及更新的显卡**；GTX 10 系及更老的卡装不上。
- 训练显存按批大小 8：ACT 2–6 GB，SmolVLA 10–16 GB，π₀ 与 π₀.₅ 24–40 GB。
- 课程环境本身占 6.6 GB 硬盘，模型权重和数据集另算，所以硬盘要按「空余」算，不是总容量。
- **Windows**：pip 默认装的 PyTorch 不带 CUDA，装完要从 PyTorch 官方索引再装一次；EP8 的笛卡尔控制与 EP9 的手柄控制在 Windows 上装不了（求解器没有 Windows 安装文件），要用 WSL 2 或云主机，或者这两集跳过。
- **Apple Silicon** 走 MPS，要 macOS 14 起；Intel 的 Mac 没有 GPU 加速。Apple Silicon 看的是**统一内存**，不单独看显存。
- 四档都要有桌面和浏览器；EP9 另需一只 Xbox 键位的 USB 或蓝牙手柄。
- 8 GB 显存参考型号：台式 RTX 3060 Ti / 4060 / 5060，笔记本 RTX 3070 / 4060 / 5060 Laptop；16 GB：台式 RTX 4080 / 5070 Ti / 5080，笔记本 RTX 4090 / 5080 Laptop。

## 四、结论怎么写

四块，缺一块都算没答完：

1. **本机实际配置**：一张小表（系统 / CPU / 内存 / 硬盘空余 / 显卡与显存），标出哪几项没测到。
2. **落在哪一档**：按上表对，写成「够最低档，差标准档的显存」这种一句话结论。
3. **能做什么、不能做什么**：能跑哪几个模型、训练放本地还是云端、哪几集在你这台机器上要跳过或上云。
4. **下一步**：具体动作，比如「训练 ACT 的命令照抄，但放到租来的云端机器上跑，命令不变」；想真验一遍环境就指《电脑体检指南》，让它跑 `lerobot-doctor`。

⛔ 不替用户下单、不推荐买哪台电脑（资料里只给了显卡参考型号，没给整机推荐）。
