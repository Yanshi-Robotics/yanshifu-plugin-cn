#!/usr/bin/env node
/**
 * 把资料群共享的四份正文同步进技能包，并重新生成索引与出处记录。
 *
 * 为什么要同步而不是让技能去读原文件：插件是发到别人电脑上的，
 * 别人的机器上没有 `资料群共享/`。所以正文必须随包走。
 *
 * 用法：
 *   node scripts/sync-knowledge.mjs            # 同步（拷正文 + 重写 INDEX.md / SOURCES.md）
 *   node scripts/sync-knowledge.mjs --check     # 只校验：包里内容与索引是否和源一致，不一致就非零退出
 *
 * 源目录：sync.config.json 的 sourceRoot（相对本仓根），环境变量 YANSHIFU_SOURCE_DIR 可覆盖。
 *
 * ⚠️ 只读源文件，一个字都不改 —— `资料群共享/` 是「只增不改」的，改了就是事故。
 */
import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { dirname, isAbsolute, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const REPO_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const CHECK_ONLY = process.argv.includes('--check')

/** 配图在包里是缺的（5.6 MB 素材不进 npm 包），换算成一行占位说明，免得正文里挂着断链。 */
function normalizeForModel(text, srcName) {
  const stats = { img: 0, div: 0, label: 0 }
  const lines = text.split('\n').map((line) => {
    let out = line

    // <p class="os-label">Linux · Ubuntu 24.04 · 终端</p> → **Linux · Ubuntu 24.04 · 终端**
    out = out.replace(/<p class="os-label">(.*?)<\/p>/g, (_m, label) => {
      stats.label += 1
      return `**${label.trim()}**`
    })

    // HTML 配图 → 占位
    out = out.replace(/<img\b[^>]*src="([^"]+)"[^>]*>/g, (_m, src) => {
      stats.img += 1
      return `〔配图：${src.split('/').pop()}〕`
    })

    // 排版用的 div（os-box / os 分栏）只留内容
    if (/^\s*<\/?div\b/.test(out)) {
      stats.div += 1
      return ''
    }

    // Markdown 配图 → 占位
    out = out.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_m, alt, src) => {
      stats.img += 1
      return `〔配图：${alt.trim() || src.split('/').pop()}〕`
    })

    return out
  })

  // 占位行会留下多余空行，压一压；正文本身不用动
  const collapsed = lines.filter((line, i, all) => !(line === '' && all[i - 1] === ''))
  if (stats.img || stats.div || stats.label) {
    process.stdout.write(
      `   归一化 ${srcName}：配图 ${stats.img}、div ${stats.div}、系统标签 ${stats.label}\n`,
    )
  }
  return collapsed.join('\n')
}

function outline(markdown) {
  const rows = []
  let inFence = false
  markdown.split('\n').forEach((line, i) => {
    if (/^\s*```/.test(line)) inFence = !inFence
    if (inFence) return
    const m = /^(#{2,5})\s+(.*)$/.exec(line)
    if (!m) return
    rows.push({ level: m[1].length, title: m[2].trim(), line: i + 1 })
  })
  return rows
}

function sha256(text) {
  return createHash('sha256').update(text).digest('hex')
}

async function main() {
  const config = JSON.parse(await readFile(join(REPO_ROOT, 'sync.config.json'), 'utf8'))
  const sourceRoot = isAbsolute(process.env.YANSHIFU_SOURCE_DIR ?? '')
    ? process.env.YANSHIFU_SOURCE_DIR
    : resolve(REPO_ROOT, process.env.YANSHIFU_SOURCE_DIR || config.sourceRoot)
  const knowledgeDir = join(REPO_ROOT, config.knowledgeDir)

  const entries = []
  for (const item of config.sources) {
    const raw = await readFile(join(sourceRoot, item.src), 'utf8')
    const body = normalizeForModel(raw, item.src)
    entries.push({ ...item, body, rawBytes: Buffer.byteLength(raw), bytes: Buffer.byteLength(body) })
  }

  const syncedAt = new Date().toISOString()
  const previous = CHECK_ONLY
    ? null
    : await readFile(join(knowledgeDir, 'SOURCES.md'), 'utf8').catch(() => null)

  if (CHECK_ONLY) {
    const stale = []
    for (const entry of entries) {
      const onDisk = await readFile(join(knowledgeDir, entry.dest), 'utf8').catch(() => null)
      if (onDisk !== entry.body) stale.push(entry.dest)
    }
    const onDiskIndex = await readFile(join(knowledgeDir, 'INDEX.md'), 'utf8').catch(() => null)
    if (!onDiskIndex || !onDiskIndex.includes('## ')) stale.push('INDEX.md')
    if (stale.length) {
      console.error(`⛔ 包内知识与源不一致：${stale.join('、')} —— 跑 node scripts/sync-knowledge.mjs 重新同步`)
      process.exit(1)
    }
    console.log('✅ 包内知识与源一致')
    return
  }

  await mkdir(knowledgeDir, { recursive: true })

  const index = [
    '# 知识库索引',
    '',
    '四份资料的正文都在本目录，随包分发。**这份索引由 `scripts/sync-knowledge.mjs` 生成，行号与正文同一次生成，可直接跳。**',
    '',
    '读法：先在下表找到那一节，再 `Read` 对应文件、按行号区间取那一段。⛔ 不要把整份文件从头读到尾。',
    '',
  ]
  // 附录 EP Review 里最后一节就是资料库看到的最新一集；答进度类问题要用它
  const guide = entries.find((entry) => entry.dest === 'so101-guide.md')
  const episodes = guide ? [...guide.body.matchAll(/^###\s+EP(\d+)\b/gm)].map((m) => Number(m[1])) : []
  const latestEpisode = episodes.length ? Math.max(...episodes) : null

  const sourcesLog = [
    '# 出处与版本',
    '',
    `同步时间：${syncedAt}`,
    `源目录：维护者本机的资料库（路径配在 \`sync.config.json\`，不随包分发）`,
    latestEpisode === null
      ? '最新一集：没能从正文里认出来'
      : `最新一集：EP${latestEpisode}（取自《落地指南》附录 EP Review 的最后一节）`,
    '',
    '答「更新到第几集」时：说这里的一集，再补一句抖音那边可能已经有新的更新、以抖音为准。',
    '',
    '⛔ 本目录是**拷贝**，正本在维护者手上的资料库里。资料只增不改，插件要重新发版才带得上新内容。',
    '',
    '为便于阅读，同步时做了三处等价归一：HTML 配图与 Markdown 配图换成 `〔配图：文件名〕`、排版用的 `<div>` 分栏只留内容、`<p class="os-label">` 换成加粗的系统名。文字本身一个字没动。',
    '',
    '| 文件 | 标题 | 源文件 | 源字节 | 包内字节 | 源 sha256（前 12 位） |',
    '|---|---|---|---:|---:|---|',
  ]

  for (const entry of entries) {
    await writeFile(join(knowledgeDir, entry.dest), entry.body, 'utf8')
    sourcesLog.push(
      `| \`${entry.dest}\` | ${entry.title} | \`${entry.src}\` | ${entry.rawBytes} | ${entry.bytes} | \`${sha256(entry.body).slice(0, 12)}\` |`,
    )
    index.push(`## ${entry.title}（\`${entry.dest}\`）`, '', entry.scope, '')
    for (const row of outline(entry.body)) {
      index.push(`${'  '.repeat(row.level - 2)}- ${row.title} · 第 ${row.line} 行`)
    }
    index.push('')
  }

  index.push(
    '## 资料里没有的时候',
    '',
    '- Season 1 之外的内容（Season 2 起、其他机器人、成本与利润、供应商与采购、橱窗上架运营）不在本知识库范围内。',
    '- 命令报错、环境装不上，先看《电脑体检指南》，再指到课程代码仓与官方文档。',
    '',
  )

  await writeFile(join(knowledgeDir, 'INDEX.md'), `${index.join('\n')}\n`, 'utf8')
  await writeFile(join(knowledgeDir, 'SOURCES.md'), `${sourcesLog.join('\n')}\n`, 'utf8')

  if (previous && !previous.includes(syncedAt.slice(0, 10))) {
    console.log('（上次同步是别的日期，SOURCES.md 已更新）')
  }
  console.log(`✅ 已同步 ${entries.length} 份正文 → ${relative(REPO_ROOT, knowledgeDir)}`)
  for (const entry of entries) console.log(`   ${entry.src} → ${entry.dest}（${entry.bytes} B）`)
}

await main()
