---
name: yanfa7-tauri
description: "修改研发七部工具包（yanfa7）的 Tauri 外壳或原生能力时使用：兼容垫片 tauri-bridge、Rust command、预览窗口等多窗口、本地文件显示与破缓存、插件与 capability 权限、主题切换与设置持久化、后端 sidecar 的启动与结束、开发端口与 CSP、应用图标。"
---

# yanfa7 Tauri 外壳与原生能力

渲染层不直接依赖 Tauri：组件写 `window.electronAPI.*` / `window.electron.*` / `window.previewAPI.*`，
由兼容垫片 `src/renderer/src/shims/tauri-bridge.ts` 翻译成 Tauri 调用。组件只认这几个全局对象，不依赖具体外壳；
原生实现只在 bridge 和 `src-tauri/` 里。下文路径相对 `frontend/`。

## 兼容垫片

- 入口 `initTauriBridge()`。`main.ts`、`preview.ts` 在挂载前调用它，全局对象和持久化的主题在首屏前就位；
  它失败时应用照样挂载（`.finally`），所以 `npm run dev:renderer` 在纯浏览器里也能开界面，只是原生能力不可用。
- 它无条件挂上三个全局：`window.electron`（`process.platform` 由 plugin-os 得到，`macos` 转成 `darwin`；
  `process.versions` 是应用和 Tauri 版本）、`window.electronAPI`（下表）、`window.previewAPI`（`getSearchParams()`，
  预览窗口读 URL query）。
- 这些全局的类型在 `src/preload/index.d.ts`（`CustomElectronAPI`，经 `tsconfig.web.json` include），改接口时同步。

| `window.electronAPI` | Tauri 实现 |
|---|---|
| `openFileDialog` / `openDir` / `openDirectoryDialog` | `@tauri-apps/plugin-dialog` 的 `open()` |
| `scanDir` | `invoke('scan_dir')`（Rust） |
| `openPreviewWindow` | `WebviewWindow`（见多窗口） |
| `onConfirmQuit` / `confirmQuit` | `getCurrentWindow().onCloseRequested` / `destroy()` |
| `theme.set` / `theme.get` | plugin-store + `setTheme` + `.dark` class |
| `account.load` / `account.save` | plugin-store 的 `account.json`（见主题与设置） |
| `openLogDir` | `invoke('backend_log_path')` 拿这次运行的日志，再用 `@tauri-apps/plugin-opener` 的 `revealItemInDir` 选中它 |
| `startDrag` | `@crabnebula/tauri-plugin-drag` |

## 新增原生能力

1. 前端插件 API 能做的，直接在 bridge 的 `electronAPIShim` 加方法；组件只调 `window.electronAPI.xxx`，
   不直接 import `@tauri-apps/*`（显示本地文件的 `convertFileSrc` 例外）。
2. 要 Rust 实现的：在 `src-tauri/src/lib.rs` 写 `#[tauri::command]`，加进 `generate_handler![...]`；bridge 里
   `invoke('<command 名>', { ... })`，参数键用 camelCase，对应 Rust 的 snake_case 参数。
3. 新插件：`src-tauri/Cargo.toml` 加依赖，`lib.rs` 里 `.plugin(...)` 注册，前端装对应的 `@tauri-apps/plugin-*`。
4. 权限加在 `src-tauri/capabilities/default.json`（作用于 `windows: ["main", "preview"]`），不是 `tauri.conf.json`。
5. 在 `src/preload/index.d.ts` 的 `CustomElectronAPI` 补签名。

现有两个 command：
- `scan_dir(root_dir, extensions)` → `{ filePaths, fileSizes }`：递归扫描，扩展名不分大小写，默认 `["htm"]`，结果按路径排序。
- `backend_log_path()` → 这次运行的后端日志路径，开发版不拉起后端，是 `null`（见后端进程）。

业务数据（解析、计算、出图）不走 Tauri IPC，走后端 HTTP / WS，见项目规则。

## 多窗口

- `tauri.conf.json` 只声明主窗口 `main`。预览窗口由 bridge 的 `openPreviewWindow` 用 `WebviewWindow` 动态创建，
  label 固定为 `preview`，加载 `preview.html?<query>`。
- Tauri 没有 JS 侧的 `navigate()`，换参数靠销毁重建：`getByLabel` 找到旧窗口 → `destroy()` 并轮询等它消失 → 新建；
  `tauri://created` 后 `maximize()` + `setFocus()`。
- `preview.html` 是独立的 Vite 入口（`vite.renderer.config.ts` 的 `input.preview`），挂 `ReportPreviewView.vue`，
  不建 Router / Pinia。窗口之间只靠 URL query 传参。
- 新建窗口要 `core:webview:allow-create-webview-window`；新增窗口 label 时同时加进 capability 的 `windows`。

## 本地文件与图片

- 后端生成的 PNG 等本地文件用 `convertFileSrc(path)` 转成 asset 协议 URL 显示，组件直接从 `@tauri-apps/api/core` 导入。
- 依赖三处配置：`Cargo.toml` 的 `tauri` 开 `protocol-asset` feature；`tauri.conf.json` 的 `app.security.assetProtocol`
  开启、`scope: ["**"]`；CSP 的 `img-src`、`frame-src` 放行 `asset:` 和 `http(s)://asset.localhost`。
- 路径固定的图片重画后 URL 不变，webview 会用缓存：URL 后拼 `?t=<时间戳>`，只在后端重画成功后更新时间戳
  （`PmaxView.vue`、`ReportPreviewView.vue` 的 `imgCacheBuster`）。弹窗关掉时销毁 DOM 也清不掉这层缓存。

## 后端进程

- release 构建在 `setup` 里拉起后端 sidecar `yanfa7-backend`（`src-tauri/src/backend.rs`，shell 插件的 `sidecar()`），
  `RunEvent::Exit` 时结束它，顺带删掉 Pmax 的临时目录 `<系统临时目录>/yanfa7_pmax`。debug 构建不管后端，
  开发时后端自己 `uv run main.py` 起在 8006。sidecar 怎么打出来见发版 Skill。
- 拉起时带 `--sidecar`：后端读到 stdin 关闭就退出。外壳崩溃或被强杀时管道会断，后端跟着退出，不留孤儿进程占着 8000 端口。
  环境变量 `PYTHONIOENCODING=utf-8`、`PYTHONUNBUFFERED=1`，日志统一 UTF-8、被结束前的输出也能落盘。
- 正常退出时结束的是 Nuitka onefile 的引导进程，真正跑 Python 的子进程每秒查一次父进程，发现没了自己退出。
- sidecar 的 stdout / stderr 要一直读走：shell 插件的事件通道容量是 1，没人读，后端就卡在写输出上。现在写进
  `<应用日志目录>`（Windows 上是 `%LOCALAPPDATA%\com.rd7.yanfa7\logs\`）：每次运行一个文件，按启动时间命名，启动时删掉
  7 天前的，单个文件写到 10 MB 停写。路径存在 `Backend` 状态里，command `backend_log_path` 给「日志」页的「打开日志目录」。
  应用里的「日志」页见 yanfa7-ref 的日志参考。
- externalBin 只写在 `tauri.windows.conf.json`：Tauri 的构建脚本不分 dev / build 都校验它指的文件存在，写进
  `tauri.conf.json` 的话 macOS 上连 `tauri:dev` 都起不来。Tauri 按 RFC 7396 合并平台配置，数组整体替换，
  以后加第二个 sidecar 要把整个数组重写。不要改用 `tauri build --config` 绕：直接敲 `tauri build` 就会静默打出不带后端的包。
- 只在 Rust 侧用 shell 插件，capability 里不加 `shell:*` 权限，前端调不到。
- 后端刚启动时还没开始监听：渲染层请求前先 `await waitBackend()`（`api/backend.ts`，轮询 `/docs`，最多 2 分钟）。

## 主题与设置

- 设置存在 `@tauri-apps/plugin-store` 的 `settings.json`（`autoSave`），bridge 里懒加载单例；外观模式在 `appearance` 键。
- TMB 账号的登录状态（令牌、用户信息、上次登录的工号，不存密码）单放 `account.json` 的 `account` 键。bridge 只管存取，
  内容和校验在 `stores/account.ts`，见 yanfa7-ref 的 TMB 账号参考。
- `applyTheme(mode)` 调 `getCurrentWindow().setTheme(mode === 'system' ? null : mode)`，原生窗口和 webview 的
  `prefers-color-scheme` 跟着变，同时切 `<html>` 的 `.dark` class；启动时 `initTauriBridge()` 读出来应用。
- `system` 模式靠 `matchMedia('(prefers-color-scheme: dark)')`：`App.vue`、`preview.ts` 各挂一个监听切 `.dark`。
- 要有 `core:window:allow-set-theme` 权限。暗色样式的写法见 UI Skill。

## 插件

`lib.rs` 注册，前端用对应的 `@tauri-apps/plugin-*`，权限在 `capabilities/default.json`：

| 插件 | 用途 |
|---|---|
| `window-state` | 记忆窗口位置、尺寸和最大化状态 |
| `dialog` | 选文件、选目录 |
| `store` | 设置持久化 |
| `os` | 读平台 |
| `drag`（`@crabnebula/tauri-plugin-drag`） | 把图表 PNG 拖到 Word 等外部应用（webview 里的 `<img>` 自己拖不出去，只带 asset 链接）。插件按原尺寸显示跟手的预览图，垫片的 `makeDragIcon` 先用 canvas 缩成 200 宽（asset 协议带 `Access-Control-Allow-Origin`，`crossOrigin` 加载不污染画布），缩不了用原图 |
| `opener` | 「日志」页的「打开日志目录」（`revealItemInDir`）；`opener:default` 里就有这个权限，路径不受 scope 限制，但文件要存在 |
| `shell` | 拉起后端 sidecar，只在 Rust 侧用（见后端进程） |

## 开发端口与 CSP

- 渲染层 Vite 固定 5179（`vite.renderer.config.ts` 的 `server.port` + `strictPort`），`tauri.conf.json` 的 `build.devUrl` 与它一致。
- CSP 只在 `tauri.conf.json` 的 `app.security.csp`（两个 HTML 入口里没有）。`connect-src` 放行 Vite 的 5179（HMR）、
  后端的 8006（开发）和 8000（打包后）。
- 改端口时这些一起改：`vite.renderer.config.ts`、`devUrl`、CSP；后端端口还有 `backend/main.py` 和
  `src/renderer/src/api/backend.ts`。

## 命令

- `npm run tauri:dev`：`beforeDevCommand` 先起渲染层 Vite，再编译运行 Rust 外壳；后端要先 `uv run main.py` 起在 8006。
- `npm run dev:renderer`：只起渲染层 Vite，不启动 Tauri 外壳，原生能力不可用。
- `npm run tauri:build`：打包，要先有 `backend/build_backend.py` 打好的 sidecar；`beforeBuildCommand` 跑 `build:renderer`，
  打完由 `scripts/collect-output.mjs` 把安装包收到仓库根目录 `output/`，见发版 Skill。
- 只改了 Rust 时可以先在 `src-tauri/` 里 `cargo check`。`backend.rs` 的日志文件命名、保留、大小上限有单元测试，`cargo test --lib`。
- 应用图标源在 `src-tauri/icons/`（`bundle.icon` 引用）。开发时的 Dock 图标在编译期用 `include_bytes!` 嵌进 `icon.icns`，
  改图标后要 `cargo clean -p yanfa7` 再 `tauri:dev` 才会更新。

## 关键文件路径

```text
src/renderer/src/shims/tauri-bridge.ts     # 兼容垫片：三个全局、主题、设置 store
src/preload/index.d.ts                     # window.electron* 的全局类型
src-tauri/src/lib.rs                       # 插件注册、Rust command、退出时的收尾
src-tauri/src/backend.rs                   # 后端 sidecar 的拉起、日志、结束
src-tauri/capabilities/default.json        # 窗口权限
src-tauri/tauri.conf.json                  # 主窗口、devUrl、CSP、asset 协议、打包
src-tauri/tauri.windows.conf.json          # 只有 bundle.externalBin（后端 sidecar）
src-tauri/Cargo.toml                       # Rust 依赖与 feature
vite.renderer.config.ts                    # 渲染层 Vite：两个入口、别名、端口
src/renderer/src/main.ts / preview.ts      # 两个窗口的挂载入口
```
