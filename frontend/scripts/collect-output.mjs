/**
 * 把 tauri build 出的安装包收到仓库根目录的 `output/`，改名成 `yanfa7-toolkit-<版本>-setup.exe`。
 *
 * Tauri 把安装包放在 `src-tauri/target/release/bundle/nsis/`，层级深，和 cargo 的中间产物混在一起；
 * 发版要拿的就一个文件，让它落在显眼的地方。Tauri 按 productName 起的中文文件名传到 GitHub Release
 * 会被改掉，所以沿用以前的 ASCII 文件名。由 `package.json` 的 `tauri:build` 串在 `tauri build` 后面，
 * 构建成功才执行。
 *
 * 不清空 output/：不同版本各是一个文件，同版本重打则覆盖。要清理自己删。
 */

import { copyFile, mkdir, readdir, readFile, stat } from 'node:fs/promises'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const FRONTEND = join(dirname(fileURLToPath(import.meta.url)), '..')
const NSIS_DIR = join(FRONTEND, 'src-tauri', 'target', 'release', 'bundle', 'nsis')
const OUTPUT = join(FRONTEND, '..', 'output')

// 安装包文件名里带版本：按 tauri.conf.json 的版本挑出这次打的，不拿目录里以前版本的
const config = JSON.parse(await readFile(join(FRONTEND, 'src-tauri', 'tauri.conf.json'), 'utf8'))
const version = config.version

let names
try {
    names = await readdir(NSIS_DIR)
} catch {
    throw new Error(`找不到安装包目录：${NSIS_DIR}`)
}
const installer = names.find((name) => name.includes(`_${version}_`) && name.endsWith('-setup.exe'))
if (!installer) {
    throw new Error(`${NSIS_DIR} 下没有 ${version} 版的安装包`)
}

await mkdir(OUTPUT, { recursive: true })
const dest = join(OUTPUT, `yanfa7-toolkit-${version}-setup.exe`)
await copyFile(join(NSIS_DIR, installer), dest)
const { size } = await stat(dest)
console.log(`安装包 -> ${dest}（${(size / 1024 / 1024).toFixed(1)} MB）`)
