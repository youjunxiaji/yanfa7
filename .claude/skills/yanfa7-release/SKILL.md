---
name: yanfa7-release
description: "给研发七部工具包（yanfa7）打包、发版或排查安装包问题时使用：CI 发版流程、后端 PyInstaller 打包与 py2pyd 加密、版本号、本地手动打包，以及 Tauri 打包还缺什么。"
---

# yanfa7 打包与发版

## 现状

- **现在的 CI 打不出能用的安装包。** `.github/workflows/build.yml` 仍按 Electron 旧外壳打包，但渲染层已经依赖 Tauri：
  兼容垫片调的是 Tauri 插件和 command，组件用 Tauri 的 `convertFileSrc` 显示本地图片，这些在 Electron 里都跑不起来。
  已发布的最新版 v2.0.6 是 Electron 外壳打的包，用户手里的是这一版。
- **Tauri 打包还不带后端。** `npm run tauri:build` 能出 NSIS 安装包，但 `tauri.conf.json` 的 `bundle` 没把后端打进去，
  Rust 外壳也不启动后端：装上后界面和选文件正常，解析、计算、出图这些要后端的功能都用不了。
- 所以下次发版之前要先做完 `todo.md`「Tauri 迁移收尾」里的打包两项；推 `v*` tag 之前确认这一点。

## 后端打包（两种外壳通用）

- PyInstaller onedir 打 `backend/main.py`，产物在 `backend/dist/main/`（入口 `main.exe` + `_internal/`）。
- `--add-data` 把 `app_edgeStress` 源码目录带进 `_internal/`，再用 py2pyd 把它编成 `.pyd`，不让安装包里留明文源码；
  `app_pmax` 只走 PyInstaller 常规打包。
- 打包后的后端走 `backend/main.py` 的 `sys.frozen` 分支：直接传 app 对象、固定监听 8000、不热重载。
- 外壳要负责后端的生命周期，Electron 主进程（`frontend/src/main/index.ts`）的做法：只在打包后启动 `resources/backend/main.exe`，
  轮询 `http://localhost:8000/docs` 等它就绪（最长 30 秒），窗口全部关闭或退出时结束进程（Windows 上 `taskkill /f /t`），
  顺带删掉 Pmax 临时目录。Tauri 外壳接后端时照这套做。

## CI 流程

推 `v*` tag 或手动触发，在 `windows-latest` 上：

1. `uv sync` → PyInstaller 打后端 → 删 `build/` 和 `.spec` → `ilammy/msvc-dev-cmd` 准备 MSVC → py2pyd 加密 `app_edgeStress`
2. 后端产物复制到 `frontend/resources/backend/`
3. `npm install` → `npm run build`（`typecheck` + `electron-vite build`）→ `electron-builder --win --publish never`
4. 上传 `frontend/dist/*.exe`；由 tag 触发时建 GitHub Release，自动生成 release notes

## 版本号

- 安装包名 `yanfa7-toolkit-${version}-setup.exe` 和应用内显示的版本都取 `frontend/package.json` 的 `version`；
  workflow 从 tag 解析出的 `APP_VERSION` 没有被用到。
- 发版前先把版本号改成要打的 tag，`frontend/package.json`、`frontend/src-tauri/tauri.conf.json`、
  `frontend/src-tauri/Cargo.toml` 三处保持一致，提交后再打 tag。

## 本地手动打包（Windows）

```bat
cd backend
uv run pyinstaller --noconfirm --onedir --console --add-data "app_edgeStress;app_edgeStress/" main.py
uv run py2pyd -r -d --no-confirm dist/main/_internal/app_edgeStress
xcopy /E /I /Y dist\main\* ..\frontend\resources\backend\
```

- `--add-data` 里的 `;` 是 Windows 写法；py2pyd 要在有 MSVC 的命令行里跑（VS 开发者命令提示符）。
- `frontend/resources/backend/` 已在 `frontend/.gitignore`，不提交。
- 前端那一步按当前要用的外壳执行：Electron 是 `npm run build && npx electron-builder --win --publish never`，
  产物在 `frontend/dist/`；Tauri 是 `npm run tauri:build`。

## 关键文件路径

```text
.github/workflows/build.yml          # CI 发版
backend/main.py                      # 打包分支：固定 8000、不热重载
backend/pyproject.toml               # 后端依赖（含 pyinstaller、gl-py2pyd）
frontend/package.json                # 版本号、打包脚本
frontend/electron-builder.yml        # Electron 安装包：extraResources 带上 resources/backend，NSIS 选项
frontend/build/installer.nsh         # NSIS 自定义：安装 / 卸载时显示详情
frontend/src/main/index.ts           # Electron 主进程：后端启动、等待、结束
frontend/src-tauri/tauri.conf.json   # Tauri 打包配置（bundle，NSIS）
```
