#!/usr/bin/env python3
"""本仓的静态闸：把技能文件里那些「换个宿主就会坏」的问题挡在发布之前。

用法：
    python3 scripts/check-skills.py

查四件事：
  1. frontmatter 能解析，`name` 与目录名一致；Codex 的硬限制（name ≤ 100、description ≤ 500 字符）；
  2. 正文里引用的相对路径真实存在（`scripts/…`、`knowledge/…`、`references/…`、`../…`）；
  3. 正文里不出现宿主专有措辞（换个宿主就说不通的说法）；
  4. 目录里没有多余的 SKILL.md（宿主的扫描规则各不相同，多一份就会有一边读不到）。

退出码 0 = 全过；1 = 有问题（逐条打印）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"

NAME_MAX, DESC_MAX = 100, 500

# 换个宿主就说不通的写法。左边是命中词，右边是该怎么写。
FORBIDDEN = {
    "npm run": "直接写 `node <脚本>`：npm 只是别名，不是所有宿主都有",
    "npx ": "不要依赖 npx",
    "skill 工具": "写成「加载 X 技能（支持嵌套就用宿主机制，否则直接读它的 SKILL.md）」",
    "DSH 插件": "写成「技能包」，它在三个宿主上是同一套文件",
}

REL_PATH = re.compile(r"(?<![\w/.-])((?:\.\./)+(?:[\w\u4e00-\u9fa5.-]+/)*[\w\u4e00-\u9fa5.-]+|(?:scripts|knowledge|references)/[\w\u4e00-\u9fa5./-]+)")


def parse_frontmatter(text: str) -> dict | None:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fields, current = {}, None
    for line in m.group(1).split("\n"):
        if line.startswith((" ", "\t")) and current:      # 续行（YAML 折行）
            fields[current] += " " + line.strip()
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        current = key.strip()
        fields[current] = value.strip().strip("'\"")
    return fields


def main() -> int:
    problems: list[str] = []
    skill_dirs = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())
    if not skill_dirs:
        print(f"⛔ {SKILLS_DIR} 下没有技能目录")
        return 1

    for skill in skill_dirs:
        rel = skill.relative_to(REPO_ROOT)
        files = sorted(skill.rglob("SKILL.md"))
        if not files:
            problems.append(f"{rel}：没有 SKILL.md（宿主的扫描只认这个文件名）")
            continue
        if len(files) > 1:
            problems.append(f"{rel}：有 {len(files)} 个 SKILL.md —— 一个技能只留顶层那一个")
        body = files[0].read_text(encoding="utf-8")
        fields = parse_frontmatter(body)
        if fields is None:
            problems.append(f"{rel}/SKILL.md：没有 frontmatter（--- name/description ---）")
            continue
        name, desc = fields.get("name", ""), fields.get("description", "")
        if not name:
            problems.append(f"{rel}/SKILL.md：缺 name")
        elif name != skill.name:
            problems.append(f"{rel}/SKILL.md：name 是「{name}」，目录叫「{skill.name}」——两边必须一致")
        if len(name) > NAME_MAX:
            problems.append(f"{rel}/SKILL.md：name 长 {len(name)} 字符，超过 Codex 的 {NAME_MAX}")
        if not desc:
            problems.append(f"{rel}/SKILL.md：缺 description")
        elif len(desc) > DESC_MAX:
            problems.append(f"{rel}/SKILL.md：description 长 {len(desc)} 字符，超过 Codex 的 {DESC_MAX}")
        # Codex / Kimi 是按名字触发或按 description 触发的，名字必须出现在 description 里
        if desc and name and name not in desc:
            problems.append(f"{rel}/SKILL.md：description 里没出现技能名「{name}」——别的宿主靠名字和它触发")
        if "\n" in name or "\n" in desc:
            problems.append(f"{rel}/SKILL.md：name/description 里不能有换行")

        for hit, how in FORBIDDEN.items():
            if hit in body:
                problems.append(f"{rel}/SKILL.md：出现宿主专有措辞「{hit}」—— {how}")

        for match in {m.group(1) for m in REL_PATH.finditer(body)}:
            if match.startswith(("http", "www.")):
                continue
            if not (skill / match).exists():
                problems.append(f"{rel}/SKILL.md：引用的路径不存在：{match}")
        print(f"检查 {rel}：name=「{name}」description {len(desc)} 字符，正文 {len(body.splitlines())} 行")

    if problems:
        print()
        for line in problems:
            print("⛔ " + line)
        return 1
    print("\n✅ 全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
