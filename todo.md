# yanfa7 待办

## 载荷简化迁移

simple_load v1.3.1 搬进了 `backend/app_simpleLoad/`，页面是 `SimpleLoadView.vue`。下面每步一个提交，
每步跑一遍 `uv run pytest`：算法用例和 `tests/test_real_baseline.py`（真实算例对拍）只许改 import，不许改断言。

- **分布图在最大值正好是 100 的整数倍时出错**：`savePic` 按最值往外取整到 100 的倍数划格，最大值正好落在最上面那条边上时，
  `np.digitize` 把它分到格子外面，`_weighted_hist` 里两个数组长度对不上，加载直接失败；一个分量全是 0 也一样。
  网页版的「划分区间」也有这个问题。修法是落在最上边的值算进最后一格，simple_load 冻结期间两边一起改。
- **删区间表按位置对齐的兼容分支**：新接口总按分量名发区间表，这个分支走不到了。算法用例的 `table_data()` 还在用它造数，
  删分支要连这些用例一起改成带分量名的写法，超出「只改 import」，先定下来再动。
- **历史配置存本机**：路径、列对应、单位换算、坐标映射、缩减参数和区间表按项目存进 Tauri store，怎么存、怎么找到时再定。
- **打包验证，下次发版前必须做**：sidecar 启动就导入 polars，漏收模块会连边缘应力、Pmax 一起起不来。
  在 Windows 上先在 `backend/` 跑一遍 `uv run pytest`（这套测试还没在 Windows 上跑过），再用 `build.cmd` 打包，
  装上确认应用能打开，边缘应力、Pmax 照常可用，载荷简化能加载、缩减；sidecar 新带了 httpx，再确认能登录、能查历史记录。
- **文档**：`yanfa7-ref` 加「载荷简化」参考（取 simple_load 的 README 算法公式、CLAUDE.md 约定、测试 skill）。
- **下线旧软件**：simple_load 停止发版、GitHub 仓库归档；`tmb_web_v1` 删载荷简化页面、路由和
  `useSimpleLoadSocket.ts`，`shanghai_yanfa7` 的载荷简化历史接口和模型留着，这边的「历史记录」靠它回填；
  删掉项目规则「项目边界」里载荷简化那条。

## 载荷简化降内存

下面的 X 指载荷 txt 的总大小。量法：把 GW-V16 的 txt 用符号链接复制 6 份（3.1 GB、2716 万行），逐步记进程内存峰值（Mac）。
现在各步的峰值：加载数据时读文件 0.75X、统计最值 1.0X、算分布 0.75X，缩减 1.25X；改区间再缩减会涨到 1.4X 左右后不再涨。
剩下能压的，按能省多少排：

- **打标签**：numpy 的 `digitize`、`clip` 生成 int64 临时数组，缩减时多占约 0.9 GB（3 GB 数据，下同）；
  再次缩减时旧的标签列还在，又多占一份。改成按工况分块算、直接写进 int16，算新标签前先丢掉旧的。
- **统计最值**：加载数据的最后一步用 `describe()` 统计六个分量，它会排序算分位数，多占约 0.8 GB，
  其实只用到最小值、最大值，改成直接取 min / max。
- **加载**：读完后进程占的内存约是数据本身的两倍，逐个文件「pandas 读 → 转 polars → 单位换算」的临时数组释放后
  没有还给系统，要少几次整列复制。txt 如果都是单个 tab 分隔（GW-V16 就是），可以改用 polars 直接读，
  先确认有没有用多个空格对齐的文件。
- **文件名列**：每行存一份字符串，占 282 MB，是一列 float32 的近三倍，换成整数编号或枚举。
- **Time 列**：加载时算完仿真时间、采样间隔就用不上了，还占 104 MB，加载时丢掉。
- **以上都做完还不够时**：读进来就写成临时 parquet，后面每一步从文件流式读、边读边算，内存不再随数据量涨；
  代价是每一步多读一遍磁盘，还要管临时文件的清理。

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

- 渲染层的 ts、vue 都按 prettier 排过了；`npm run format`（`prettier --write .`）还会扫到 `src-tauri/target` 的构建产物、
  两个入口 HTML 和 Electron 旧外壳，先补 `.prettierignore`，再整仓跑一次单独提交，
  之后把项目规则验证命令里的 prettier 一行换成 `npm run format`。
- 存量代码按全局代码风格收敛：
  - `shims/tauri-bridge.ts` 里 4 处 `function` 声明改成 `const` 箭头函数；箭头函数不提升，模块级的先确认没有在定义之前调用。
  - `backend/app_edgeStress/module/` 下 `dataset.py`、`processor.py`、`reporter.py`、`cache.py` 的 NumPy 风格 docstring
    改成 Google 风格。
  - 还是 2 空格缩进的文件改成 4 空格：`frontend/eslint.config.mjs`、`frontend/tsconfig.node.json`、
    `frontend/.vscode/extensions.json`、`frontend/.vscode/settings.json`（Electron 旧外壳那几个随删除处理）。
- 没有调用方的代码，确认不要后删掉：`EdgeStressReporter.export_processed_excel`；
  `app_pmax/module/chart.py` 导入时的 `print(TEMP_DIR)`。
