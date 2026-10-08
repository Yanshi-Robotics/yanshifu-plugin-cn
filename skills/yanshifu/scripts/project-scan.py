#!/usr/bin/env python3
"""看一眼 SO-101 学员的项目，判断他做到哪一步了。

只读文件状态，不开任何设备、不碰串口与相机、不执行仓里的程序。
跨平台，只用标准库。

    python project-scan.py scan [--repo DIR] [--json]   看状态并推阶段（默认动作）
    python project-scan.py find [--root DIR ...]        找课程仓在哪（默认从当前目录找）
    python project-scan.py remember DIR                 记住这次确认过的目录
    python project-scan.py status                       打印记住的目录
    python project-scan.py forget                       清掉记住的目录

记住的目录存在 $YANSHIFU_HOME/project.json（默认 ~/.yanshifu/project.json），
就一个路径加确认时间，别的不存。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_DIR_NAME = "Lets-Build-Robots-S1-SO101"
# 课程仓里一定有的四个目录，用来认它（见课程仓 README 的 "What's in the repository"）
REPO_MARKERS = ("Bringup", "Cameras", "Teleop", "Cartesian")
FIND_MAX_DEPTH = 3


def yanshifu_home() -> Path:
    return Path(os.environ.get("YANSHIFU_HOME") or (Path.home() / ".yanshifu"))


def memory_file() -> Path:
    return yanshifu_home() / "project.json"


def read_memory() -> dict:
    try:
        return json.loads(memory_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_memory(repo: str) -> Path:
    path = memory_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"repo": repo, "confirmed_at": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def count_files(path: Path, limit: int = 5000) -> int:
    n = 0
    for root, dirs, files in os.walk(path):
        n += len(files)
        if n > limit:
            return limit
        dirs[:] = [d for d in dirs if d != "__pycache__"]
    return n


def newest_mtime(path: Path) -> str | None:
    latest = None
    for entry in path.rglob("*"):
        try:
            if entry.is_file():
                m = entry.stat().st_mtime
                latest = m if latest is None else max(latest, m)
        except OSError:
            continue
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M") if latest else None


def looks_like_repo(path: Path) -> bool:
    if not path.is_dir():
        return False
    if all((path / marker).is_dir() for marker in REPO_MARKERS):
        return True
    readme = path / "README.md"
    try:
        head = readme.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        return False
    return "Let's Build Robots" in head and "SO-101" in head


def find_repos(roots: list[Path]) -> list[Path]:
    found: list[Path] = []
    skip = {".git", "node_modules", ".venv", "__pycache__", "历史文件备份-不需要备份-agent忽视本文件夹"}
    for root in roots:
        root = root.expanduser().resolve()
        if not root.is_dir():
            continue
        if root.name == REPO_DIR_NAME and looks_like_repo(root):
            found.append(root)
        base_depth = len(root.parts)
        for dirpath, dirs, _files in os.walk(root):
            here = Path(dirpath)
            # ⚠️ 先认名字再剪深度：仓恰好落在最后一层时，先剪就永远看不见它
            if here.name == REPO_DIR_NAME and looks_like_repo(here):
                found.append(here)
                dirs[:] = []
                continue
            if len(here.parts) - base_depth >= FIND_MAX_DEPTH:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in skip]
    # 去重，浅的排前面
    return sorted({p for p in found}, key=lambda p: (len(p.parts), str(p)))


def is_lerobot_dataset(path: Path) -> bool:
    """LeRobot 0.6.1 的数据集目录长这样：<root>/<repo_id>/{meta,data,videos}，认 meta/info.json。"""
    return (path / "meta" / "info.json").is_file()


def find_datasets(candidates: list[Path]) -> list[dict]:
    """在候选根下找数据集。⛔ 不能只看「有子目录」——~/.cache/huggingface/lerobot 里有
    calibration、videos 这些 LeRobot 自己的缓存目录，那样会把没录过数据的人判成「已经录完了」。"""
    found: list[dict] = []
    seen: set[str] = set()
    for base in candidates:
        if not base.is_dir():
            continue
        hits: list[Path] = []
        if is_lerobot_dataset(base):
            hits.append(base)
        for child in sorted(p for p in base.iterdir() if p.is_dir()):
            if is_lerobot_dataset(child):
                hits.append(child)
                continue
            # 缓存目录常见的是两级：<user>/<dataset>
            for grandchild in sorted(p for p in child.iterdir() if p.is_dir()):
                if is_lerobot_dataset(grandchild):
                    hits.append(grandchild)
        names = [f"{p.parent.name}/{p.name}" if p.parent != base else p.name for p in hits]
        names = [n for n in names if n not in seen]
        if names:
            seen.update(names)
            found.append({"where": str(base), "names": names[:20]})
    return found


def scan(repo: Path) -> dict:
    repo = repo.expanduser().resolve()
    out: dict = {"repo": str(repo), "exists": repo.is_dir(), "evidence": [], "missing": []}

    if not out["exists"]:
        return out

    out["is_course_repo"] = looks_like_repo(repo)
    out["markers"] = {m: (repo / m).is_dir() for m in REPO_MARKERS}

    head = repo / ".git" / "HEAD"
    if head.is_file():
        try:
            ref = head.read_text(encoding="utf-8").strip()
            out["git_branch"] = ref.split("refs/heads/")[-1] if "refs/heads/" in ref else ref
        except OSError:
            pass

    venv = repo / ".venv"
    out["venv"] = venv.is_dir()

    calibration = {}
    for arm in ("follower", "leader"):
        arm_dir = repo / "calibration" / arm
        calibration[arm] = count_files(arm_dir) if arm_dir.is_dir() else 0
    out["calibration"] = calibration

    model_dir = repo / "models" / "so101"
    out["arm_model_files"] = count_files(model_dir) if model_dir.is_dir() else 0

    cameras = repo / "cameras.json"
    if cameras.is_file():
        try:
            data = json.loads(cameras.read_text(encoding="utf-8"))
            out["cameras"] = {
                key: {"path": str(value.get("index_or_path", "")), "rotation": value.get("rotation", 0)}
                for key, value in data.items()
                if isinstance(value, dict)
            }
        except (OSError, ValueError):
            out["cameras"] = {"error": "cameras.json 读不动或不是合法 JSON"}
    else:
        out["cameras"] = None

    out["gamepad_map"] = (repo / "Cartesian" / "gamepad_map.json").is_file()

    logs = repo / "Teleop" / "logs"
    if logs.is_dir():
        files = [p for p in logs.iterdir() if p.is_file()]
        out["teleop_logs"] = {"count": len(files), "newest": newest_mtime(logs)}
    else:
        out["teleop_logs"] = {"count": 0, "newest": None}

    out["datasets"] = find_datasets(
        [repo / "datasets", repo / "data", Path.home() / ".cache" / "huggingface" / "lerobot"]
    )

    train_root = repo / "outputs" / "train"
    runs = []
    if train_root.is_dir():
        for run in sorted(p for p in train_root.iterdir() if p.is_dir()):
            ckpts = run / "checkpoints"
            runs.append({"run": run.name, "checkpoints": sorted(p.name for p in ckpts.iterdir()) if ckpts.is_dir() else []})
    out["training_runs"] = runs

    out["act_task_tooling"] = (repo / "ACT-1-Pick").is_dir()

    # 阶段推断：每条都带证据，判断权交回给模型和用户
    if not out["is_course_repo"]:
        out["stage"] = {"label": "这不像课程仓", "evidence": ["没找到 Bringup/ Cameras/ Teleop/ Cartesian/，README 里也没有课程字样"]}
        return out

    if not out["venv"]:
        stage = ("EP3 之前：环境还没建", ".venv/ 不在")
    elif not (calibration["follower"] and calibration["leader"]):
        stage = ("EP4–5：装配与接线，校准还没做", f"calibration/ 里 follower {calibration['follower']} 个文件、leader {calibration['leader']} 个文件")
    elif not out["teleop_logs"]["count"]:
        stage = ("EP6 过了，EP7 遥操还没跑过", "Teleop/logs/ 是空的")
    elif not out["arm_model_files"]:
        stage = ("EP8 之前：臂模型还没下", "models/so101/ 不在或为空")
    elif not out["gamepad_map"]:
        stage = ("EP8 左右：笛卡尔控制，手柄还没配", "Cartesian/gamepad_map.json 不在")
    elif not out["cameras"]:
        stage = ("EP10–11：相机还没配", "cameras.json 不在")
    elif not out["datasets"]:
        stage = ("EP12：录制数据集", "cameras.json 有了，但没找到数据集目录")
    elif not out["training_runs"]:
        stage = ("EP13：开始训练", f"有数据集（{out['datasets'][0]['names'][:3]}），outputs/train/ 还是空的")
    else:
        stage = ("训练跑过了：下一步是离线评估与真机验收", f"outputs/train/ 里有 {[r['run'] for r in out['training_runs']]}")
    out["stage"] = {"label": stage[0], "evidence": [stage[1]]}
    return out


def render(state: dict) -> str:
    if not state["exists"]:
        return f"⛔ 目录不存在：{state['repo']}"
    lines = [f"项目目录：{state['repo']}"]
    if "git_branch" in state:
        lines.append(f"分支：{state['git_branch']}")
    lines.append(f"像不像课程仓：{'是' if state.get('is_course_repo') else '不是'}")

    def mark(flag: bool) -> str:
        return "✓" if flag else "✗"

    if state.get("is_course_repo"):
        lines.append(f"环境 .venv/：{mark(state['venv'])}")
        cal = state["calibration"]
        lines.append(f"校准 calibration/：follower {mark(bool(cal['follower']))}（{cal['follower']} 个文件）· leader {mark(bool(cal['leader']))}（{cal['leader']} 个文件）")
        lines.append(f"臂模型 models/so101/：{state['arm_model_files']} 个文件")
        cams = state["cameras"]
        if cams and "error" not in cams:
            pairs = " · ".join(f"{k} rotation={v['rotation']}" for k, v in cams.items())
            lines.append(f"相机 cameras.json：{pairs}")
        else:
            lines.append("相机 cameras.json：✗")
        lines.append(f"手柄映射：{mark(state['gamepad_map'])}")
        logs = state["teleop_logs"]
        lines.append(f"Teleop 日志：{logs['count']} 个" + (f"，最新 {logs['newest']}" if logs["newest"] else ""))
    else:
        lines.append("（不是课程仓，按用户自己的项目看）")

    if state["datasets"]:
        for d in state["datasets"]:
            lines.append(f"数据集：{d['where']} → {', '.join(d['names'][:6])}")
    else:
        lines.append("数据集：✗")
    if state["training_runs"]:
        for r in state["training_runs"]:
            lines.append(f"训练输出：{r['run']}（检查点 {', '.join(r['checkpoints']) or '无'}）")
    else:
        lines.append("训练输出 outputs/train/：✗")
    lines.append(f"ACT-1-Pick 工装：{mark(state['act_task_tooling'])}")
    lines.append("")
    lines.append(f"推断阶段：{state['stage']['label']}")
    for ev in state["stage"]["evidence"]:
        lines.append(f"  依据：{ev}")
    lines.append("（这是按产物推的，⛔ 拿去问用户对不对，别当成结论）")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="看一眼 SO-101 学员的项目做到哪一步了（只读，不碰硬件）")
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="看状态并推阶段")
    scan_p.add_argument("--repo", help="项目目录；不给就用记住的那个，再不给就用当前目录")
    scan_p.add_argument("--json", action="store_true")

    find_p = sub.add_parser("find", help="找课程仓在哪")
    find_p.add_argument("--root", action="append", default=[], help="从哪个目录找，可给多次；默认当前目录")

    remember_p = sub.add_parser("remember", help="记住确认过的目录")
    remember_p.add_argument("repo")

    sub.add_parser("forget", help="清掉记住的目录")
    sub.add_parser("status", help="打印记住的目录")

    args = parser.parse_args(sys.argv[1:] if len(sys.argv) > 1 else ["scan"])
    if args.command in (None, "scan"):
        repo = getattr(args, "repo", None) or read_memory().get("repo") or os.getcwd()
        state = scan(Path(repo))
        print(json.dumps(state, ensure_ascii=False, indent=2) if getattr(args, "json", False) else render(state))
        return 0
    if args.command == "find":
        roots = [Path(r) for r in args.root] or [Path.cwd()]
        hits = find_repos(roots)
        if not hits:
            print("没找到课程仓（找的是目录名 Lets-Build-Robots-S1-SO101）。问用户它 clone 在哪。")
            return 1
        print("找到这些，让用户确认是哪一个：")
        for hit in hits:
            print(f"  {hit}")
        return 0
    if args.command == "remember":
        repo = Path(args.repo).expanduser().resolve()
        if not repo.is_dir():
            print(f"⛔ 目录不存在：{repo}")
            return 1
        print(f"已记住：{repo}\n（写在 {write_memory(str(repo))}）")
        return 0
    if args.command == "forget":
        path = memory_file()
        if path.exists():
            path.unlink()
            print(f"已清掉 {path}")
        else:
            print("本来就没记住什么。")
        return 0
    if args.command == "status":
        memory = read_memory()
        print(json.dumps(memory, ensure_ascii=False, indent=2) if memory else "还没记住任何目录。")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
