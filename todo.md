# yanfa7 待办

## Tauri 迁移收尾

- **删 Electron 旧外壳**：打包和 CI 都已改走 Tauri，旧外壳没有流程在用。
  - 先把 `src/preload/index.d.ts` 里 `window.electron*` 的全局类型搬到渲染层，`tsconfig.web.json` 去掉对 `src/preload` 的 include。
  - 删 `src/main`、`src/preload`、`electron.vite.config.ts`、`electron-builder.yml`、`build/`、`resources/`、
    `.vscode/launch.json` 的 Electron 调试配置，以及 `frontend/.gitignore` 里的 `out`、`dist`、`resources/backend/`。
  - `package.json` 删 `electron`、`electron-vite`、`electron-builder`、`electron-store`、`@electron-toolkit/preload`、
    `@electron-toolkit/utils` 依赖，和 `dev`、`start`、`build`、`build:*`、`postinstall` 脚本。
  - `tsconfig.node.json` 改为检查 `vite.renderer.config.ts`，`typecheck` 脚本跟着调整。
  - `@electron-toolkit/tsconfig`、`@electron-toolkit/eslint-config-*` 是 tsconfig 和 ESLint 的基础配置，保留或换成等价配置，不跟着删。
  - 同步项目规则「项目边界」。

## 体验问题

- Pmax 页的数据和图表存在组件里，切到别的页面再回来就没了。
- 边缘应力的保存路径和参数不持久化，重启后要重填。
- 生成报告后没有「打开输出目录」；opener 插件已注册，渲染层没用上。
- 雷达图最小值：主页面只能填 ≥0，预览窗只能填 ≤0，范围相反；预览窗打开时也不带主页面填的值。
- 每次关窗口都弹退出确认，没有任务在跑时也弹。
- README 的「技术栈」「开发」两节会在应用内文档页显示给使用者。

## 代码清理

- 渲染层还有 `shims/tauri-bridge.ts` 没按 prettier 排过版
  （`npx prettier --check 'src/renderer/src/**/*.{ts,vue}'` 列出），整仓跑一次 `npm run format` 单独提交，
  之后把项目规则验证命令里的 prettier 一行换成 `npm run format`。
- 存量代码按全局代码风格收敛：
  - `shims/tauri-bridge.ts` 里 4 处 `function` 声明改成 `const` 箭头函数；箭头函数不提升，模块级的先确认没有在定义之前调用。
  - `backend/app_edgeStress/module/` 下 `dataset.py`、`processor.py`、`reporter.py`、`cache.py` 的 NumPy 风格 docstring
    改成 Google 风格。
  - 还是 2 空格缩进的文件改成 4 空格：`frontend/eslint.config.mjs`、`frontend/tsconfig.node.json`、
    `frontend/.vscode/extensions.json`、`frontend/.vscode/settings.json`（Electron 旧外壳那几个随删除处理）。
- 没有调用方的代码，确认不要后删掉：`EdgeStressReporter.export_processed_excel`；
  `app_pmax/module/chart.py` 导入时的 `print(TEMP_DIR)`。
