#!/usr/bin/env python3
"""把本包的技能装进各宿主的技能目录。三个宿主（DSH / Codex / Kimi）用的是同一套技能文件。

用法：
    python3 scripts/install.py --list-targets         # 看看准备装到哪、哪些宿主在这台机器上
    python3 scripts/install.py --host all --dry-run   # 演练，不写盘
    python3 scripts/install.py --host dsh             # 装给 DSH
    python3 scripts/install.py --host all             # 三个宿主都装
    python3 scripts/install.py --host dsh --link      # 软链（DSH 与 Kimi 支持；Codex 跳过软链，永远复制）
    python3 scripts/install.py --host codex --force   # 覆盖已存在的（旧的先备份成 .bak-<时间戳>）

DSH 用户一般不需要这个脚本：`dsh plugin --profile web add ...` 装插件更省事，还能跟着版本走。
这个脚本是给另外两个宿主、以及不想装成插件的人用的。
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_SRC = REPO_ROOT / "skills"
SKILL_NAMES = ("yanshifu", "ask", "update")

# 宿主 → 技能根。环境变量优先，其次各自的默认家目录。
HOSTS = {
    "dsh": ("DSH_HOME", ".dsh", False),
    "codex": ("CODEX_HOME", ".codex", True),      # 第三项 True = 永远复制：Codex 的扫描跳过符号链接
    "kimi": ("KIMI_CODE_HOME", ".kimi-code", False),
    "agents": (None, ".agents", False),           # 共享根：DSH 与 Kimi 都读它
}
HOST_NOTES = {
    "dsh": "DSH 读 ~/.dsh/skills/ 与 ~/.agents/skills/，改完即时生效，不用重启",
    "codex": "Codex 只读 ~/.codex/skills/**/SKILL.md，且要先把 skills 特性打开、改完要重启",
    "kimi": "Kimi 读 ~/.kimi-code/skills/ 与 ~/.agents/skills/，新会话里用 /skill:<名字> 调",
    "agents": "共享根：DSH 与 Kimi 都读，装这里一次顶两个（Codex 不读它）",
}


def host_home(host: str) -> Path:
    """宿主的配置根（`~/.dsh`、`~/.codex`…）。"""
    env, default, _ = HOSTS[host]
    base = os.environ.get(env) if env else None
    return Path(base).expanduser() if base else Path.home() / default


def host_root(host: str) -> Path:
    """宿主的技能根 —— 技能一律装在它下面的 `<名字>/SKILL.md`。"""
    return host_home(host) / "skills"


def codex_skills_enabled(root: Path) -> bool | None:
    """读 Codex 的 config.toml 判断 skills 特性开没开；读不到就返回 None。"""
    config = root.parent / "config.toml"
    try:
        text = config.read_text(encoding="utf-8")
    except OSError:
        return None
    in_features = False
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("["):
            in_features = stripped == "[features]"
            continue
        if in_features and stripped.replace(" ", "").startswith("skills="):
            return stripped.replace(" ", "").split("=", 1)[1].strip().strip('"') == "true"
    return False


def enable_codex_skills(root: Path) -> None:
    """给 config.toml 的 [features] 加一行 skills = true；先备份。"""
    config = root.parent / "config.toml"
    backup = config.with_suffix(f".toml.bak-{time.strftime('%Y%m%d-%H%M%S')}")
    text = config.read_text(encoding="utf-8") if config.exists() else ""
    shutil.copy2(config, backup) if config.exists() else None
    lines, out, inserted = text.split("\n"), [], False
    for line in lines:
        out.append(line)
        if line.strip() == "[features]":
            out.append("skills = true")
            inserted = True
    if not inserted:
        out += ["", "[features]", "skills = true"]
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
    print(f"   已开启：{config}（备份 {backup.name}）")


def install_skill(name: str, dest_root: Path, link: bool, force: bool, dry_run: bool) -> str:
    source = SKILLS_SRC / name
    target = dest_root / name
    if not source.is_dir():
        return f"⛔ 源里没有 {name}"
    if target.exists() or target.is_symlink():
        same = target.is_symlink() and target.resolve() == source.resolve()
        if same:
            return f"·  {name}：已是指向本仓的软链"
        if not force:
            return f"·  {name}：已存在（没动；要覆盖加 --force）"
    if dry_run:
        return f"→  {name}：{'软链' if link else '复制'}到 {target}"
    dest_root.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        backup = target.with_name(f"{name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        target.rename(backup)
    if link:
        target.symlink_to(source, target_is_directory=True)
        return f"✅ {name}：软链 → {source}"
    shutil.copytree(source, target)
    return f"✅ {name}：复制 → {target}"


def main() -> int:
    parser = argparse.ArgumentParser(description="把技能装进各宿主的技能目录")
    parser.add_argument("--host", default=None, help=f"{'|'.join(HOSTS)}|all")
    parser.add_argument("--link", action="store_true", help="用软链（Codex 会退回复制）")
    parser.add_argument("--force", action="store_true", help="覆盖已存在的（旧的先备份）")
    parser.add_argument("--dry-run", action="store_true", help="只打印要做什么")
    parser.add_argument("--list-targets", action="store_true", help="列出目标后退出")
    parser.add_argument("--enable-codex-skills", action="store_true", help="顺手把 Codex 的 skills 特性打开（改 config.toml 前会备份）")
    args = parser.parse_args()

    if not args.host and not args.list_targets:
        parser.print_help()
        return 1

    hosts = list(HOSTS) if args.host == "all" else ([args.host] if args.host else [])
    for host in hosts:
        if host not in HOSTS:
            print(f"⛔ 不认识的宿主：{host}（可选 {'|'.join(HOSTS)}|all）")
            return 1

    if args.list_targets:
        for host in hosts or list(HOSTS):
            root = host_root(host)
            state = "存在" if root.parent.exists() else "这台机器上没有"
            print(f"{host:7} {root}   （{state}；{HOST_NOTES[host]}）")
        print(f"\n要装的技能：{'、'.join(SKILL_NAMES)}（源：{SKILLS_SRC}）")
        return 0

    for host in hosts:
        root = host_root(host)
        link = args.link and not HOSTS[host][2]
        print(f"\n[{host}] {root}" + ("（Codex 跳过软链，改为复制）" if args.link and HOSTS[host][2] else ""))
        if not host_home(host).exists():
            print(f"   ⚠️ {host_home(host)} 不存在 —— 这个宿主这台机器上可能没装；继续装也可以，以后装上就能用")
        for name in SKILL_NAMES:
            print("  " + install_skill(name, root, link, args.force, args.dry_run))
        if host == "codex":
            enabled = codex_skills_enabled(root)
            if enabled is False:
                print(f"   ⚠️ Codex 的 skills 特性还没开。在 {root.parent / 'config.toml'} 的 [features] 下加一行：")
                print("        skills = true")
                print("      然后重启 Codex；或者这次加 --enable-codex-skills 让我改（改前备份）。")
                if args.enable_codex_skills and not args.dry_run:
                    enable_codex_skills(root)
            elif enabled is None:
                print("   ℹ️ 没找到 Codex 的 config.toml，装完记得确认 skills 特性是开的。")

    if args.dry_run:
        print("\n（--dry-run，没有写盘）")
    else:
        print("\n装完各自生效方式：DSH 即时；Codex 重启后；Kimi 新会话里用 /skill:<名字>。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
