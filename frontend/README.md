# Edge Stress 前端

边缘应力分析桌面工具 —— 基于 Electron + Vue 3 构建。

## 技术栈

- **框架**: [Electron](https://www.electronjs.org/) + [Vue 3](https://vuejs.org/)
- **构建工具**: [electron-vite](https://electron-vite.org/)
- **UI 组件**: [Element Plus](https://element-plus.org/)
- **状态管理**: [Pinia](https://pinia.vuejs.org/)
- **路由**: [Vue Router 4](https://router.vuejs.org/)
- **语言**: TypeScript

## 项目结构

```
src/
├── main/                    # Electron 主进程
│   └── index.ts             # 窗口创建、IPC 处理、后端进程管理
├── preload/                 # 预加载脚本
│   ├── index.ts             # 主窗口 preload（暴露 electronAPI）
│   ├── preview.ts           # 预览窗口 preload（暴露 previewAPI）
│   └── index.d.ts           # 类型声明
└── renderer/                # 渲染进程
    ├── index.html           # 主窗口 HTML 入口 (含 CSP 配置)
    ├── preview.html         # 预览窗口 HTML 入口（独立 BrowserWindow）
    └── src/
        ├── main.ts          # 主窗口 Vue 应用入口
        ├── preview.ts       # 预览窗口 Vue 应用入口（轻量，无 Router/Pinia）
        ├── App.vue          # 主窗口根组件（el-container 布局：侧边栏 + 主内容区）
        ├── router/          # 路由配置（仅主窗口使用，带 meta.title/icon）
        ├── views/           # 页面组件
        │   ├── HomeView.vue           # 首页（工具卡片导航 + 版本信息）
        │   ├── EdgeStressView.vue     # 边缘应力分析页面
        │   └── ReportPreviewView.vue  # 报告预览页面（独立窗口）
        ├── stores/          # Pinia 状态管理（仅主窗口使用）
        │   └── edgeStress.ts          # 边缘应力状态
        ├── api/             # 后端 API 接口
        │   └── edgeStress.ts          # 边缘应力 API 调用
        ├── composables/     # Vue Composables
        │   └── usePlotlyDrag.ts         # Plotly 图表数据点拖拽编辑逻辑
        ├── components/      # 通用组件
        │   ├── SideNav.vue          # 侧边栏导航（el-menu，带 TMB logo + 折叠/展开）
        │   ├── FileResultPopover.vue  # 文件结果悬浮弹窗（hover 触发，仅文件名区域）
        │   ├── FilePreviewDialog.vue  # 文件预览对话框（已废弃，保留备用）
        │   └── Versions.vue
        └── assets/          # 静态资源
            ├── logo.png               # TMB® 品牌 logo（侧边栏顶部）
            └── drag.svg               # 拖拽编辑图标（Plotly 工具栏自定义按钮）
scripts/
└── afterPack.cjs            # electron-builder 打包钩子 (macOS 后端签名)
resources/
├── icon.png                 # 默认图标
├── app_icon.ico             # Windows 图标
├── 滚珠轴承.png              # macOS 图标
└── backend/                 # Python 后端打包产物 (不提交到 git)
```

## 开发

```bash
# 安装依赖
cnpm install

# 启动开发服务器
npm run dev

# 类型检查
npm run typecheck

# 代码格式化
npm run format
```

## 构建

### CI 自动打包（推荐）

项目使用 GitHub Actions 自动打包，推送 `v*` 格式的 tag 即可触发：

```bash
git tag v1.0.0
git push origin main --tags
```

工作流（`.github/workflows/build.yml`）自动完成：
1. PyInstaller 打包 Python 后端
2. py2pyd 加密业务代码
3. 复制后端产物到 `frontend/resources/backend/`
4. electron-builder 打包 Windows NSIS 安装包
5. 创建 GitHub Release 并上传 .exe

也支持在 GitHub Actions 页面手动触发（workflow_dispatch）。

### 本地手动打包

```bash
# 1. 打包后端（使用 auto-py-to-exe 或 PyInstaller 命令行）
cd backend
pyinstaller --noconfirm --onedir --console --add-data "app_edgeStress;app_edgeStress/" main.py

# 2. 复制后端产物
xcopy /E /I /Y dist\main\* ..\frontend\resources\backend\

# 3. 打包 Electron (Windows)
cd ../frontend
npm run build && npx electron-builder --win --publish never
```

### 后端自动启动

打包后 Electron 主进程会在启动时自动 spawn 后端进程（`resources/backend/main.exe`），并轮询等待端口 8000 就绪（30 秒超时）。关闭应用时自动终止后端进程树。

开发环境下不会自动启动后端，需手动运行 `uv run main.py`。

### 注意事项

- Windows：无需代码签名即可正常运行
- `resources/backend/` 已在 `.gitignore` 中排除，不会提交到仓库
- NSIS 安装程序支持自定义安装路径（非一键安装模式）
- 安装包命名格式：`研发七部工具包-x.x.x-setup.exe`

## 功能概述

- **首页**: 启动后默认展示首页，包含欢迎区域（logo + 标题 + 描述）、工具卡片网格（点击跳转至对应功能页面）、底部版本号（从 package.json 自动注入）
- **侧边栏导航**: el-menu 侧边栏，顶部 TMB® logo + "研发七部工具包"标题，侧边栏右侧边缘中间的圆形按钮控制折叠/展开（双箭头图标），自动读取路由 meta 信息生成菜单项，底部固定「文档」「设置」占位，所有动画统一 0.3s ease-in-out 与 el-menu 同步
- **数据文件管理**: 支持选择文件夹递归扫描 HTM 文件（多次追加去重）、一键清空（带确认），文件悬浮显示详情
- **参数配置**: 峰值阈值、图片尺寸
- **一键解析**: 点击"开始解析"即完成解析 + 去峰 + 全部报告生成
- **进度显示**: 解析进度条 + 完成后显示生成文件数
- **退出确认**: 关闭窗口时弹出确认对话框，防止误操作退出；macOS 下关闭窗口后彻底退出应用
- **预览窗口复用**: 点击预览按钮复用已有窗口而非创建新窗口；主窗口关闭时自动销毁预览窗口
- **Cmd+Q 行为**: macOS 下 Cmd+Q 不直接关闭预览窗口，统一走主窗口确认退出流程；预览窗口仅响应 Cmd+W 关闭自身
- **DevTools 快捷键**: 打包后可通过 Ctrl+Shift+I (macOS: Cmd+Shift+I) 打开开发者工具，方便调试
- **Plotly 工具栏定制**: 隐藏了 Zoom/ZoomIn/ZoomOut/Select/Lasso 按钮；去峰后数据图表添加"拖拽编辑"自定义按钮，启用后可按住数据点上下拖拽修改 Y 值；拖拽逻辑封装在 `usePlotlyDrag` composable 中
- **拖拽数据同步**: 拖拽编辑数据点松手后自动同步到后端缓存（`POST /api/update-stress-point`），后端先验证 xlsx 可写性，再更新缓存数据并重新生成应力曲线 PNG、应力雷达图 PNG、最大应力汇总.xlsx，前端通过 cache busting 自动刷新图片
- **雷达图最小值调整**: 预览窗口顶部可设置载荷最小值和应力最小值，修改后自动调用 `POST /api/regenerate-polar` 重新生成雷达图 PNG（600ms 防抖）

## 前后端通信

- 通信方式: WebSocket (`ws://localhost:8000`) + HTTP REST API
- CSP 策略:
  - `index.html` — 允许 `ws://localhost:8000`（主窗口 WebSocket）
  - `preview.html` — 允许 `http://localhost:8000`（预览窗口 REST API）
- 接口:
  - `WS /ws/parse` — 解析文件并实时推送进度，完成后返回全部报告路径
  - `GET /api/chart-data` — 获取 Plotly 图表数据（预览窗口按需调用）
  - `POST /api/update-stress-point` — 修改单个应力数据点，更新缓存并重新生成 PNG + xlsx
  - `POST /api/regenerate-polar` — 使用自定义最小值重新生成雷达图 PNG

## 组件说明

| 组件 | 说明 |
|------|------|
| `SideNav.vue` | 侧边栏导航：el-menu + vue-router，顶部 TMB® logo 区域（展开时 logo + 标题，折叠时仅缩小 logo），自动从路由 meta（title/icon）生成菜单项，底部固定「文档」「设置」占位。折叠按钮位于 App.vue 侧边栏边缘 |
| `HomeView.vue` | 首页：欢迎区域 + 工具卡片网格导航（可扩展）+ 底部版本号 |
| `EdgeStressView.vue` | 边缘应力分析页面：文件管理 + 参数配置 + 解析触发 |
| `FileResultPopover.vue` | 鼠标悬浮文件名时显示详情弹窗（多列图片横向排列，仅文件名区域触发） |
| `ReportPreviewView.vue` | 报告预览独立窗口（Electron BrowserWindow），三栏布局：Plotly 交互式图表（通过 HTTP API 获取数据，去峰图表支持拖拽编辑数据点并同步后端）+ 应力曲线 PNG + 雷达图 PNG，顶部卡片式工具栏（文件名 + 列号选择 + segmented control 滚道切换 + 雷达图最小值设置） |
| `FilePreviewDialog.vue` | 已废弃，保留备用。原为 el-dialog 形式的报告预览，已被独立窗口方案替代 |
