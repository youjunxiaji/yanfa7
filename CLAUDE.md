# yanfa7 项目规则

研发七部工具包：轴承数据分析桌面应用。Tauri v2 外壳 + Vue 3 / TypeScript / Naive UI / Pinia 渲染层，
Python FastAPI 后端作为独立进程，经 HTTP / WebSocket 提供解析、计算和出图。
全局协作约定见 `~/.claude/CLAUDE.md`；本文件和各 Skill 只写本项目特有的工程约束，全局已有的不重复，两边冲突时以全局为准。

## 资料分工

| 内容 | 维护位置 |
|---|---|
| 技术栈、架构边界、命名和接口约束 | 本文件 |
| 任务适用范围、资料路由、工作流程 | 各 Skill 的 `SKILL.md` |
| 模块背景、行为契约、设计原因和操作细节 | 对应 Skill 的 `references/` |
| 字段、默认值、样式数值、版本和配置值 | 代码与配置 |
| 功能说明、使用步骤、快捷键（面向使用者） | 根目录 `README.md`，应用内「文档」页直接渲染它 |
| 还没做的事 | `todo.md` |

同一约定只在一处完整维护，其他位置简述并链接。代码说明当前行为，规则约束本次开发；两者不一致时如实指出：
参考落后于代码就直接改参考，代码偏离规则就按规则改或向用户说明，不把旧实现当规范。
修改影响参考文档描述的接口、数据流、输出文件、原生能力或打包流程时，同步对应参考；
改到使用者能看到的功能、步骤或快捷键时，同步 `README.md`。

| 任务 | 先读 |
|---|---|
| 理解、排查或修改边缘应力、Pmax 等工具模块，或新增工具模块 | [yanfa7-ref](.claude/skills/yanfa7-ref/SKILL.md)：相关模块参考，再核对源码 |
| 实现、修改或审查界面 | [yanfa7-ui-style](.claude/skills/yanfa7-ui-style/SKILL.md)：先读界面标准 |
| 改 Tauri 外壳或原生能力：兼容垫片、Rust command、窗口、本地文件、插件权限、主题、端口与 CSP、图标 | [yanfa7-tauri](.claude/skills/yanfa7-tauri/SKILL.md) |
| 打包、发版、CI | [yanfa7-release](.claude/skills/yanfa7-release/SKILL.md) |

## 项目边界

- `frontend/` 是 Tauri 工程：`src-tauri/` 为 Rust 外壳，`src/renderer/` 为 Vue 渲染层，主窗口 `index.html`、
  预览窗口 `preview.html` 两个入口。`backend/` 是 FastAPI 后端。
- 应用只走 Tauri。`frontend/src/main`、`src/preload`、`electron.vite.config.ts`、`electron-builder.yml`、`build/`，
  以及 `package.json` 里的 `electron`、`electron-vite`、`electron-builder`、`electron-store`、`@electron-toolkit/preload`、
  `@electron-toolkit/utils` 依赖和 `dev`、`start`、`build`、`build:*`、`postinstall` 脚本是 Electron 旧外壳：
  新功能不写进去，也不照着它改渲染层。CI 仍用它打安装包，但渲染层已经依赖 Tauri，这条流水线打不出能用的包，
  见发版 Skill；删除排在 Tauri 打包接上后端之后，见 `todo.md`。`@electron-toolkit/tsconfig` 和
  `@electron-toolkit/eslint-config-*` 是现用的 tsconfig、ESLint 基础配置，不属于旧外壳。
- 例外：`src/preload/index.d.ts` 仍提供 `window.electron*` 的全局类型（`tsconfig.web.json` include），
  改兼容垫片的接口时同步它。
- 开发端口：渲染层 Vite 5179，后端 8006；打包后的后端固定 8000。改端口要同步的位置见 Tauri Skill。

## 架构约束

- 业务数据只走后端：渲染层经 HTTP / WebSocket 调 FastAPI，后端地址一律从 `src/renderer/src/api/backend.ts`
  取 `API_BASE` / `WS_BASE`（按 `import.meta.env.DEV` 选 8006 或 8000），不在别处写死；
  后端在 `backend/main.py` 按是否打包选端口，两边一起改。
- 原生能力只走兼容垫片：组件调 `window.electronAPI.*` / `window.electron.*`，由
  `src/renderer/src/shims/tauri-bridge.ts` 翻译成 Tauri 调用。组件不直接用 `@tauri-apps/*`，
  唯一例外是显示本地文件的 `convertFileSrc`。新增能力的步骤见 Tauri Skill。
- 后端生成的本地图片用 `convertFileSrc` 显示；路径固定、内容会重画的图片在 URL 后拼 `?t=<时间戳>`，
  重画成功后再更新时间戳，否则 webview 显示的还是旧图。
- 窗口之间经 URL query 传参，不共享 Pinia 状态。

## 前端

- 组件用 `<script setup lang="ts">`。UI 只用 Naive UI（`components/AppProviders.vue` 统一配主题和中文 locale），
  图标只用 `@lucide/vue`。
- Pinia store 用 Options API 写法（避开 Vue 3.5 的类型兼容问题），放 `stores/`；只属于单个页面的状态留在组件里（如 Pmax 页）。
- 渲染层模块用 `@renderer/...` 导入（映射 `src/renderer/src/`）；`@root` 映射仓库根目录，用来导入 `README.md`。
  没有 `@/` 别名。
- 前后端共用的枚举两边取值一致：前端放 `src/renderer/src/constants/`，后端放 `backend/common/constants.py`（如 `Language`）。
- 静态资源放 `src/renderer/src/assets/`；`frontend/resources/` 只放打包用的后端产物（`resources/backend/`，不入库）。
- 颜色和阴影只用 `assets/tokens.css` 里的设计变量（`:root` 浅色、`html.dark` 暗色），组件里不写 hex，也不写暗色覆盖；
  配色、骨架和交互模式见 UI Skill。

## 后端

- Python ≥ 3.12，依赖和命令走 `uv`（`uv sync`、`uv add`、`uv run`）；`uv run main.py` 起开发服务（8006，热重载）。
- 每个工具一个 `app_<模块名>/`：`urls.py` 建 `APIRouter` 注册路由，`views.py` 写接口，`serializers.py`
  放 Pydantic 请求 / 响应模型，`module/` 放解析、计算、出图；在 `main.py` 里 `include_router`。
- 业务错误抛 `HTTPException(status_code=400, detail=...)`，`detail` 用中文写清哪里不对，前端读 `detail` 展示；
  WebSocket 推 `{"type": "error", "message": ...}`。
- 出图用 matplotlib 的 Agg 后端（`main.py` 入口设置），只写文件不弹窗，返回给前端的是文件绝对路径。

## 验证命令

按改动涉及的部分执行；纯文档修改核对链接、规则一致性及 Skill 格式即可。

前端（`frontend/`）：

```bash
npm run typecheck:web              # vue-tsc
npx prettier --write <改动的文件>    # 只排改动的文件，整仓还有存量没排过，见 todo.md
npx eslint <改动的文件>
npm run build:renderer             # 渲染层打包
cd src-tauri && cargo check        # 改了 Rust 时
```

后端（`backend/`）没有自动化测试，改完至少确认能导入：

```bash
uv run python -c "import main"
```
