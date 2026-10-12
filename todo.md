# yanfa7 待办

## Tauri 迁移收尾

下次发版之前要做完 1、2，现状见发版 Skill。

1. **Tauri 打包带上后端**：`tauri.conf.json` 的 `bundle` 打进 PyInstaller 后端（`resources` 或 `externalBin`），
   Rust 外壳在打包后启动后端、等 `http://localhost:8000/docs` 就绪、退出时结束进程，做法对照 Electron 主进程
   `src/main/index.ts`。
2. **CI 改用 `npm run tauri:build`**：`.github/workflows/build.yml` 的前端步骤换掉 `electron-builder`，
   上传 Tauri 的 NSIS 产物。
3. **Tauri 退出时清理 Pmax 临时目录** `<系统临时目录>/yanfa7_pmax`（现在只靠每次生成前的 `cleanup_temp_files()`）。
4. **删 Electron 旧外壳**（1、2 做完之后）：
   - 先把 `src/preload/index.d.ts` 里 `window.electron*` 的全局类型搬到渲染层，`tsconfig.web.json` 去掉对 `src/preload` 的 include。
   - 删 `src/main`、`src/preload`、`electron.vite.config.ts`、`electron-builder.yml`、`build/`、`.vscode/launch.json`
     的 Electron 调试配置。
   - `package.json` 删 `electron`、`electron-vite`、`electron-builder`、`electron-store`、`@electron-toolkit/preload`、
     `@electron-toolkit/utils` 依赖，和 `dev`、`start`、`build`、`build:*`、`postinstall` 脚本。
   - `tsconfig.node.json` 改为检查 `vite.renderer.config.ts`，`typecheck` 脚本跟着调整。
   - `@electron-toolkit/tsconfig`、`@electron-toolkit/eslint-config-*` 是 tsconfig 和 ESLint 的基础配置，保留或换成等价配置，不跟着删。
   - 同步项目规则「项目边界」和发版 Skill。

## 发版

- CI 用 tag 的版本号，或校验 tag 与 `package.json` 的 `version` 一致：workflow 解析出的 `APP_VERSION` 没用上，
  v2.0.5、v2.0.6 两个 Release 的安装包名和应用内版本都还是 2.0.4。

## 界面存量

UI Skill 的规则管新代码，下面是还没收敛的旧写法：

- Element Plus 主色覆盖成 `#0071e3`（在 `main.ts` 设 `--el-color-primary` 一组变量），去掉 `ReportPreviewView.vue` 里硬编码的 `#409eff`。
- 抽 `:root` / `html.dark` 设计变量，替换各处裸 hex；设置页的 `--settings-*` 可作样板。
- 次级灰统一成 `#86868b`，现在还混着 `#909399`、`#6e6e73`。
- `.empty-state` 抽到 `main.css` 通用段，现在 `EdgeStressView.vue`、`PmaxView.vue`、`ReportPreviewView.vue` 各一份。
- `<kbd>` 样式统一，现在首页、Pmax 页、命令面板各写各的。

## 代码清理

- `src/renderer/src/shims/tauri-bridge.ts:31` 的类型错误：`@tauri-apps/plugin-store` 的 `StoreOptions` 要求 `defaults`，
  `npm run typecheck:web` 因此不过，CI 里的 `npm run build` 也会卡在这一步。
- 渲染层 14 个文件还没按 prettier 排过版（`npx prettier --check 'src/renderer/src/**/*.{ts,vue}'` 列出），
  整仓跑一次 `npm run format` 单独提交，之后把项目规则验证命令里的 prettier 一行换成 `npm run format`。
- 存量代码按全局代码风格收敛：
  - 渲染层 12 个文件里 35 处 `function` 声明改成 `const` 箭头函数；箭头函数不提升，模块级的先确认没有在定义之前调用。
  - `backend/app_edgeStress/module/` 下 `dataset.py`、`processor.py`、`reporter.py`、`cache.py` 的 NumPy 风格 docstring
    改成 Google 风格。
  - 还是 2 空格缩进的文件改成 4 空格：`.github/workflows/build.yml`、`frontend/eslint.config.mjs`、
    `frontend/tsconfig.node.json`、`frontend/.vscode/extensions.json`、`frontend/.vscode/settings.json`
    （Electron 旧外壳那几个随删除处理）。
- 没有调用方的代码，确认不要后删掉：`components/FilePreviewDialog.vue`、`components/Versions.vue`、
  `EdgeStressReporter.export_processed_excel`；`app_pmax/module/chart.py` 导入时的 `print(TEMP_DIR)`。
