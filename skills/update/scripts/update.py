#!/usr/bin/env python3
"""查资料更新到第几集，落后就把正文装上。

用法：
    python3 update.py --check          # 只报状态：本地第几集、最新第几集、要不要更新
    python3 update.py --apply          # 落后就装（写临时文件再原子替换）
    python3 update.py --json           # 机器可读输出（给助手用）
    python3 update.py --source <路径或网址>   # 换一个来源（本机自测用）

退出码：0 已经是最新 · 10 有新版（--check 时报出，--apply 时已装好）· 20 查不到远端

三个来源按顺序试，任何一个通了就停：
    1. 最新的 release 包（一次拿到「最新第几集」和要装的内容）
    2. 仓里的 SOURCES.md（只看，1 KB 出头）
    3. GitHub API 的最新 release 标签（只有版本号，没有集号）

只动本插件自己的 `skills/ask/knowledge/`，不碰用户的课程仓、不碰硬件。
写文件一律「临时文件 + os.replace」：插件的文件在 pnpm 那边可能是硬链接，
原地写会连带改掉共享 store 里那一份。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

REPO = "https://github.com/Yanshi-Robotics/yanshifu-plugin-cn"
RAW = "https://raw.githubusercontent.com/Yanshi-Robotics/yanshifu-plugin-cn/main"
TARBALL_ASSET = "yanshifu-plugin-cn.tgz"          # 资产名不带版本号，latest/download 永远有效
KNOWLEDGE_REL = Path("skills/ask/knowledge")      # 相对插件根
SKILLS_REL = Path("skills")
KNOWLEDGE_FILES = ("SOURCES.md", "INDEX.md", "so101-guide.md", "pc-checkup.md",
                   "github-signup.md", "dsh-install.md")
HTTP_TIMEOUT = 30                                  # 秒
MAX_TARBALL = 32 * 1024 * 1024                     # 包只有几十 KB，超过就当中毒

EXIT_LATEST, EXIT_UPDATED, EXIT_UNKNOWN = 0, 10, 20


def plugin_root() -> Path:
    """本文件在 <插件根>/skills/update/scripts/update.py。"""
    return Path(__file__).resolve().parents[3]


def read_frontmatter(path: Path) -> dict:
    """读 --- 包起来的头部；没有就返回空字典。"""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            out[key.strip()] = value.strip()
    return out


def as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def version_key(value: str | None):
    """把版本串变成可排序的键：(数字段, 是否正式版)。没有版本号返回 None。

    只在拿不到集号时用来兜底比较，所以不追求完整 semver：
    `0.4.0` > `0.4.0-rc.1` > `0.3.0`。
    """
    if not value:
        return None
    head, _, tail = value.lstrip("v").partition("-")
    nums = tuple(int(x) for x in re.findall(r"\d+", head)) or (0,)
    return (nums, 0 if tail else 1)


def http_get(url: str, timeout: int = HTTP_TIMEOUT) -> bytes:
    """先试标准库，再退回系统的 curl。

    2026-10-09 实测：同一个网址 curl 0.3 秒拿到，urllib 读 60 秒超时（国内网络下这条很常见）。
    所以 curl 存在时它是可靠得多的那条路；两个都失败才认输。
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "yanshifu-update"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read(MAX_TARBALL + 1)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError):
        data = _curl_get(url, timeout)
    if len(data) > MAX_TARBALL:
        raise ValueError(f"下载内容超过 {MAX_TARBALL} 字节，不像这个插件")
    return data


def _curl_get(url: str, timeout: int) -> bytes:
    curl = shutil.which("curl")
    if not curl:
        raise OSError("标准库取不到，机器上也没有 curl")
    result = subprocess.run(
        [curl, "-fsSL", "--max-time", str(timeout), url],
        capture_output=True,
        timeout=timeout + 10,
    )
    if result.returncode != 0:
        raise OSError(f"curl 失败（{result.returncode}）：{result.stderr.decode('utf-8', 'replace').strip()[:120]}")
    return result.stdout


def fetch_tarball(source: str | None) -> bytes | None:
    url = source or f"{REPO}/releases/latest/download/{TARBALL_ASSET}"
    if not url.startswith(("http://", "https://")):
        try:
            return Path(url).read_bytes()
        except OSError:
            return None
    try:
        return http_get(url)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError):
        return None


def open_tarball(blob: bytes) -> tarfile.TarFile | None:
    try:
        tar = tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz")
    except tarfile.TarError:
        return None
    # npm 打的包所有文件都在 package/ 下；GitHub 的源码包是 <repo>-<ref>/
    prefixes = {member.name.split("/", 1)[0] for member in tar.getmembers() if "/" in member.name}
    for prefix in sorted(prefixes, key=len):
        if any(m.name.startswith(f"{prefix}/{SKILLS_REL}/") for m in tar.getmembers()):
            tar.prefix = prefix  # type: ignore[attr-defined]
            return tar
    return None


def remote_from_tarball(blob: bytes) -> dict | None:
    tar = open_tarball(blob)
    if tar is None:
        return None
    prefix = tar.prefix  # type: ignore[attr-defined]

    # package.json 一定能给出包版本；SOURCES.md 的头部给集号（老版本没有这个头部）
    version = None
    try:
        pkg = tar.extractfile(f"{prefix}/package.json")
        if pkg is not None:
            version = json.loads(pkg.read().decode("utf-8", "replace")).get("version")
    except (KeyError, json.JSONDecodeError):
        version = None

    fields = {}
    try:
        member = tar.extractfile(f"{prefix}/{KNOWLEDGE_REL}/SOURCES.md")
    except KeyError:
        member = None
    if member is not None:
        m = re.search(r"^---\n(.*?)\n---\n", member.read().decode("utf-8", "replace"), re.S)
        if m:
            for line in m.group(1).split("\n"):
                if ":" in line:
                    key, _, value = line.partition(":")
                    fields[key.strip()] = value.strip()
    return {
        "source": "release 包",
        "version": fields.get("bundle_version") or version,
        "latest_ep": as_int(fields.get("latest_ep")),
        "synced_at": fields.get("synced_at"),
        "tarball": blob,
    }


def remote_from_sources(source: str | None) -> dict | None:
    url = source or f"https://raw.githubusercontent.com/Yanshi-Robotics/yanshifu-plugin-cn/main/{KNOWLEDGE_REL}/SOURCES.md"
    if not url.startswith(("http://", "https://")):
        return None
    try:
        text = http_get(url).decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError):
        return None
    m = re.search(r"^---\n(.*?)\n---\n", text, re.S)
    fields = {}
    if m:
        for line in m.group(1).split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                fields[key.strip()] = value.strip()
    if not fields:
        return None
    return {"source": "仓里的 SOURCES.md", "version": fields.get("bundle_version"),
            "latest_ep": as_int(fields.get("latest_ep")), "synced_at": fields.get("synced_at")}


def remote_from_api() -> dict | None:
    try:
        payload = json.loads(http_get(f"https://api.github.com/repos/Yanshi-Robotics/yanshifu-plugin-cn/releases/latest"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError, json.JSONDecodeError):
        return None
    return {"source": "GitHub API", "version": (payload.get("tag_name") or "").lstrip("v") or None,
            "latest_ep": None, "synced_at": None}


def apply_from_raw(root: Path) -> tuple[list[str], list[str]]:
    """release 包取不到时的退路：从仓里逐文件取正文。

    只适合「知识库更新」这件事——文件名固定、一共六份、加起来 130 KB 左右。
    ⛔ 不碰技能正文（SKILL.md 与脚本），那些变了要重装插件。
    """
    changed, failures = [], []
    for name in KNOWLEDGE_FILES:
        try:
            data = http_get(f"{RAW}/{KNOWLEDGE_REL.as_posix()}/{name}")
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as error:
            failures.append(f"{name}（{type(error).__name__}）")
            continue
        target = root / KNOWLEDGE_REL / name
        if target.exists() and target.read_bytes() == data:
            continue
        write_atomic(target, data)
        changed.append(str(KNOWLEDGE_REL / name))
    return changed, failures


def safe_members(tar: tarfile.TarFile, rel: Path):
    """只取 skills/ 下的普通文件，且路径不许跑出目标目录。"""
    prefix = f"{tar.prefix}/{SKILLS_REL}/"  # type: ignore[attr-defined]
    for member in tar.getmembers():
        if not member.isfile() or not member.name.startswith(prefix):
            continue
        inner = Path(member.name[len(prefix):])
        if inner.is_absolute() or ".." in inner.parts:
            continue
        yield member, SKILLS_REL / inner


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def apply_tarball(blob: bytes, root: Path) -> tuple[list[str], list[str]]:
    """把包里的 skills/ 覆盖到插件上。返回（更新的知识文件，变了但没动的其他文件）。"""
    tar = open_tarball(blob)
    if tar is None:
        return [], []
    changed_knowledge, changed_other = [], []
    for member, rel in safe_members(tar, Path("skills")):
        handle = tar.extractfile(member)
        if handle is None:
            continue
        data = handle.read()
        target = root / rel
        current = target.read_bytes() if target.exists() else None
        if current == data:
            continue
        if rel.parts[:2] == ("skills", "ask") and rel.parts[2:3] == ("knowledge",):
            write_atomic(target, data)
            changed_knowledge.append(str(rel))
        else:
            changed_other.append(str(rel))
    return changed_knowledge, changed_other


def main() -> int:
    parser = argparse.ArgumentParser(description="查资料更新到第几集，落后就装")
    parser.add_argument("--check", action="store_true", help="只看状态，不写盘")
    parser.add_argument("--apply", action="store_true", help="落后就装")
    parser.add_argument("--json", action="store_true", help="机器可读输出")
    parser.add_argument("--source", help="换一个来源：release 包网址、SOURCES.md 网址，或本机文件路径")
    parser.add_argument("--root", help="插件根目录（默认从本文件位置推）")
    args = parser.parse_args()
    if not args.check and not args.apply:
        args.check = True

    root = Path(args.root).resolve() if args.root else plugin_root()
    local_sources = root / KNOWLEDGE_REL / "SOURCES.md"
    if not local_sources.is_file():
        print(f"⛔ 找不到 {local_sources} —— 这不像装好的插件", file=sys.stderr)
        return EXIT_UNKNOWN
    local = read_frontmatter(local_sources)
    local_ep, local_version = as_int(local.get("latest_ep")), local.get("bundle_version")

    remote = None
    if args.source:
        blob = fetch_tarball(args.source)
        if blob:
            remote = remote_from_tarball(blob) or remote_from_sources(args.source)
    else:
        blob = fetch_tarball(None)
        if blob:
            remote = remote_from_tarball(blob)
        if remote is None:
            remote = remote_from_sources(None)
        if remote is None:
            remote = remote_from_api()

    state, tarball = "unknown", (remote or {}).get("tarball")
    if remote and remote.get("latest_ep") is not None and local_ep is not None:
        if local_ep > remote["latest_ep"]:
            state = "ahead"
        else:
            state = "latest" if local_ep == remote["latest_ep"] else "behind"
    elif remote and remote.get("version") and local_version:
        local_key, remote_key = version_key(local_version), version_key(remote["version"])
        if local_key and remote_key:
            if local_key > remote_key:
                state = "ahead"
            else:
                state = "latest" if local_key == remote_key else "behind"

    applied, other, failures, how = [], [], [], None
    installed_ep = None
    if state == "behind" and args.apply:
        if tarball:
            applied, other = apply_tarball(tarball, root)
            how = "release 包"
        else:
            applied, failures = apply_from_raw(root)
            how = "仓里的正文"
        installed_ep = as_int(read_frontmatter(local_sources).get("latest_ep"))
        if installed_ep is not None:
            state = "latest" if (remote.get("latest_ep") is None or installed_ep >= remote["latest_ep"]) else "behind"

    summary = {
        "state": state,
        "local": {"latest_ep": local_ep, "bundle_version": local_version, "synced_at": local.get("synced_at")},
        "remote": {k: v for k, v in (remote or {}).items() if k != "tarball"},
        "applied": applied,
        "applied_from": how,
        "failed": failures,
        "skill_files_differ": other,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        where = (remote or {}).get("source", "哪儿都没查到")
        print(f"本地：EP{local_ep}（版本 {local_version}，同步于 {local.get('synced_at')}）")
        if remote:
            ep = f"EP{remote['latest_ep']}" if remote.get("latest_ep") is not None else "（这个来源没有集号）"
            print(f"最新：{ep}（版本 {remote.get('version')}，来源：{where}）")
        if applied:
            moved = f"EP{local_ep} → EP{installed_ep}" if local_ep is not None and installed_ep is not None else f"{len(applied)} 个文件"
            print(f"✅ 已更新（{moved}，取自{how}）")
            for name in applied:
                print(f"   {name}")
            if failures:
                print(f"⚠️ 这几份没取到，本地还是旧的：{'、'.join(failures)}")
            if other:
                print(f"⚠️ 技能本体另有 {len(other)} 个文件与最新版不同（本次没动）：{'、'.join(other[:5])}")
                print("   想一并跟上就重装插件，见 README 的安装提示词。")
        elif state == "behind" and args.apply:
            print("⛔ 查到有新版，但两个来源都取不到正文（release 包与仓里的文件都不通），什么都没改。")
            print("   网络恢复后再跑一次，或按 README 的重装命令整包更新。")
        elif state == "latest":
            print("✅ 已经是最新，什么都没改。")
        elif state == "ahead":
            print("ℹ️ 本地这份比线上新（发布者同步过但还没发版），什么都没改。")
        elif state == "behind":
            print("↑ 有新版。跑 `python3 update.py --apply` 装上。")
        else:
            print("⛔ 查不到最新版本（网络不通或来源都不可用），没有猜。")

    if applied:
        return EXIT_UPDATED
    if state == "latest" or state == "ahead":
        return EXIT_LATEST
    if state == "behind" and args.apply:
        return EXIT_UNKNOWN      # 想装但没装上，不能报「有新版」让调用方以为好了
    return EXIT_UPDATED if state == "behind" else EXIT_UNKNOWN


if __name__ == "__main__":
    sys.exit(main())
