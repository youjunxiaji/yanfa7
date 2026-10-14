# yanfa7 待办

## 载荷简化迁移

simple_load v1.3.1 搬进了 `backend/app_simpleLoad/`，目录已按项目规则排好，测试在它的 `tests/` 里。下面每步一个提交，
每步跑一遍 `uv run pytest`：算法用例和 `tests/test_real_baseline.py`（真实算例对拍）只许改 import，不许改断言。

- **重计算挪出事件循环**：划分区间、缩减的 polars 计算还直接跑在 async 函数里，缩减期间整个后端没响应，
  改用 `asyncio.to_thread`。
- **去掉 pyarrow**：只有 `cal_simpleLoad.py` 的两处 `to_pandas()` 要它，改写掉。
- **代码风格**：`typing` 的 `List` / `Dict` 换成内置类型，docstring 换成 Google 风格。
- **接口协议随前端移植一起改**：报错改 400 + `detail`，WebSocket 改成边缘应力那样每步一条，理顺报文字段名，
  路径加 `/api/simple-load/`、`/ws/simple-load/` 前缀；删 `main.py` 里只对载荷简化生效的校验处理器、
  区间表按位置对齐的旧前端兼容分支、加载前等前端重连 10 秒。
- **前端 `SimpleLoadView.vue`**：Naive UI，原生选文件夹 / 文件，Plotly 直方图和框选求占比，Pinia store，
  历史配置存本机（Tauri store）。列映射的拖拽排序、「加载 → 划分 → 缩减」三个按钮怎么摆，先出方案。
- **打包验证，下次发版前必须做**：sidecar 启动就导入 polars，漏收模块会连边缘应力、Pmax 一起起不来。
  在 Actions 手动触发一次构建（不打 tag 不发版），查编译报告确认 polars、pyarrow 收进去了，装机能起来。
  发版 CI 在打 sidecar 前加一步 `uv run pytest`。
- **文档**：`yanfa7-ref` 加「载荷简化」参考（取 simple_load 的 README 算法公式、CLAUDE.md 约定、测试 skill），
  `README.md` 加使用说明，删掉项目规则「项目边界」里载荷简化那条。
- **下线旧软件**：simple_load 停止发版、GitHub 仓库归档；`tmb_web_v1` 删载荷简化页面、路由和
  `useSimpleLoadSocket.ts`；服务器上的历史配置要不要导入，到时再定。

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
