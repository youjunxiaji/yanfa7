---
name: yanfa7-release
description: "给研发七部工具包（yanfa7）打包、发版或排查安装包问题时使用：两步打包（Nuitka 把后端打成 sidecar、Tauri 出 NSIS 安装包）、版本号、CI 发版、工具链，以及装机后后端起不来怎么查。"
---

# yanfa7 打包与发版

安装包 = Tauri 外壳 + 后端 sidecar：`backend/build_backend.py` 用 Nuitka 把 FastAPI 后端打成单个 exe，
Tauri 当 `externalBin` 收进 NSIS 安装包。装完安装目录里是两个 exe，外壳启动时拉起后端、退出时结束它
（外壳一侧见 Tauri Skill「后端进程」）。只出 Windows 安装包。

## 两步，顺序不能反

```bash
cd backend
uv run python build_backend.py      # 问一次版本、写进三处 → Nuitka 打 sidecar
cd ../frontend
npm run tauri:build                 # Tauri 收进安装包 → 仓库根目录 output/
```

- Windows 上直接跑仓库根目录的 `build.cmd`，双击也行：依次执行这两步，参数原样传给 `build_backend.py`
  （`build.cmd --version 2.1.0`）；前端没装过依赖时先 `npm install`，哪一步失败就停在那里。双击运行时结束前会停住，
  方便看输出。
- `build.cmd` 只看 `frontend/node_modules` 在不在，不比对 `package.json`：拉到改了依赖的提交、或 `node_modules`
  是别的分支装的旧版时，要自己在 `frontend/` 跑一次 `npm install`，否则第二步报找不到 `@electron-toolkit/tsconfig` 这类包。
- `build.cmd` 全文只能是 ASCII：注释和提示写英文，也不要在里面 `chcp`。cmd 按字符数而不是字节数推算下一行的起点，
  文件里有 UTF-8 中文时读指针会比真实位置多跳 2 字节/字，落进 `rem` 注释行的中间，剩下半行被当命令执行
  （报 `'y：' 不是内部或外部命令`；注释里的 `cmd --keep-version` 还会拉起一个停在提示符上的嵌套交互式 cmd，
  看着像脚本结束了）。`chcp 65001` 救不了：这个 cmd.exe 进程已经在中文代码页（936）下启动，只有切换之后新起的
  cmd 才读得对，所以症状是「第一次失败，在嵌套提示符里重敲一次反而成功」。换行必须是 CRLF（`.gitattributes` 已经设好），
  LF 换行时 cmd 可能找不到 goto 的标签。
- 第二步只拿 `frontend/src-tauri/binaries/` 里现成的 sidecar，不会重打后端：改了后端却只跑第二步，装出来的还是上一版后端。
- 产物是 `output/yanfa7-toolkit-<版本>-setup.exe`，由 `frontend/scripts/collect-output.mjs` 从
  `src-tauri/target/release/bundle/nsis/` 拷出来改名：Tauri 按 productName 起的中文文件名，传到 GitHub Release 会被改掉。
- Windows 上 `tauri:dev` 也要先跑过一次第一步：`tauri.windows.conf.json` 的 externalBin 不分 dev / build 都校验文件存在。

## 版本号

- 只经 `build_backend.py` 改。它先列出三处当前版本、标出和其他不一致的，问一次，再统一写进：

  | 落点 | 用在哪 |
  |---|---|
  | `frontend/package.json` | 首页显示的版本（渲染层的 `__APP_VERSION__`） |
  | `frontend/src-tauri/tauri.conf.json` | 安装包文件名、应用版本 |
  | `frontend/src-tauri/Cargo.toml` | 外壳 crate 版本 |

- 匹配三处的正则在脚本的 `VERSION_SITES`；哪个文件里版本号的写法变了要跟着改，匹配不上会直接报错退出。
- 非交互用 `--version X.Y.Z` 或 `--keep-version`（三处必须已经一致）。版本只认 `主.次.修订`。
- 发版顺序：本地跑脚本定版本 → 提交 → 推 `v<版本>` tag。CI 会按 tag 再写一遍，tag 和仓库里的版本对不上时以 tag 为准。

## 后端打包（Nuitka）

参数都在 `build_backend.py` 的 `nuitka_args()`，改之前先看那里的注释：

- **onefile**：externalBin 收的是一个文件。解包目录固定为 `{CACHE_DIR}/yanfa7/backend`（Windows 上是
  `%LOCALAPPDATA%\yanfa7\backend`），不带版本号：第一次启动和版本更新后要解包几百 MB，之后每次启动只核对校验和。
  默认的随机临时目录每次启动都要整个解包，进程被外壳结束时还删不掉。固定目录时是两个进程：
  安装目录里的 sidecar 只负责解包和看守，解包目录里的那个 exe 才跑 Python。
- **无控制台**（`--windows-console-mode=disable`）：Tauri 拉起时 stdio 是管道，照常可用；直接双击运行时
  stdout 是 None，uvicorn 起不来。手动排查要重定向输出：`yanfa7-backend.exe > out.txt 2>&1`。
- **lxml、openpyxl、polars 显式带上**：pandas 读 HTM、读写 Excel 时按名字导入 lxml、openpyxl；
  polars 沿用 simple_load 打包时的整包包含。Nuitka 静态分析不一定跟得到。新增依赖凡是运行时按名字导入的，同样加在这里。
- **编译时 `MPLBACKEND=Agg`**：matplotlib 插件把编译时探测到的后端写进随包配置，装了 Tk 的机器上探测到的是 TkAgg。
- **编译时 `CL=/utf-8`**（仅 Windows）：`--product-name` 这类参数里的中文，Nuitka 以 UTF-8 写进 `build_definitions.h`，
  而中文 Windows 上 MSVC 默认按 GBK 读，字符串常量被截坏，C 编译阶段报 `error C2001: 常量中有换行符`，
  接着 `scons: *** [...obj] Error 2`。`build()` 给 Nuitka 的环境带上 `CL=/utf-8`，让 cl 统一按 UTF-8 读；
  打包参数里有中文就靠它，别去掉。
- **编译报告** `backend/build/compilation-report.xml`：装机后缺模块、缺数据文件时，先查这里有没有收进去。
- Python 代码编译成 C，安装包里没有明文源码。

Nuitka 不设 `sys.frozen`（那是 PyInstaller 的），`backend/main.py` 用 `"__compiled__" in globals()` 判断是否打包：
打包后固定监听 `127.0.0.1:8000`，只听本机，不弹 Windows 防火墙提示。

## 安装包

- `bundle.targets` 只有 `nsis`。`bundle.windows.nsis`：简体中文向导、不显示语言选择、`installMode: currentUser`
  （装进 `%LOCALAPPDATA%`，不要管理员权限，和以前的 Electron 版一样按用户装）。
- 安装包没有签名，装的时候 SmartScreen 会拦，点「仍要运行」。
- v2.0.6 及以前是 Electron 版，和现在的安装包互不认识，不会被覆盖：先在「设置 → 应用」里卸载旧版再装新版，
  不然两版并存，同名的开始菜单、桌面快捷方式互相覆盖。

## CI

`.github/workflows/build.yml`：推 `v*` tag 或手动触发，在 `windows-latest` 上先跑后端测试（`uv run pytest`，不通过就停），
再跑同样的两步（tag 触发时 `--version` 取 tag，手动触发用 `--keep-version`），上传 `output/*.exe`；
tag 触发时建 GitHub Release，自动生成 release notes。

## 工具链（Windows）

| 工具 | 用途 |
|---|---|
| Visual Studio Build Tools，勾选「使用 C++ 的桌面开发」 | Nuitka 编译 C 代码、Rust 链接 |
| Rust（rustup，MSVC 工具链） | 编译外壳；`build_backend.py` 问 `rustc` 要 target triple，不自己拼 |
| uv | 后端依赖和 Python 3.12，Nuitka 在 dev 依赖组里 |
| Node 20+ | 渲染层和 Tauri CLI |
| NSIS | 不用装，Tauri 打包时自己下载 |

## 装机后后端起不来

- 后端的输出在 `%LOCALAPPDATA%\com.rd7.yanfa7\logs\`，每次运行一个文件，按启动时间命名（如 `backend-20261015-103152.log`），
  留 7 天；外壳自己的报错也以 `[外壳]` 开头写在这里。后端起来了的话，应用里的「日志」页也能看这次运行的。
- 安装或更新后第一次启动要解包，系统还要扫描新解出的文件，后端要几十秒才能应答（Mac 上实测 24–60 秒）；之后每次一两秒。
  前端第一次请求前最多等 2 分钟（`api/backend.ts` 的 `waitBackend`），等不到就报「后端服务没有启动」。
- 8000 端口被别的程序占着时后端绑不上端口，日志里能看到。

## 关键文件路径

```text
build.cmd                                   # Windows 上一键跑完两步
backend/build_backend.py                    # 定版本 + 调 Nuitka，产物放到 src-tauri/binaries/
backend/main.py                             # 打包后的分支：127.0.0.1:8000，--sidecar 时 stdin 关了就退出
backend/pyproject.toml                      # nuitka 在 dev 依赖组
frontend/src-tauri/tauri.windows.conf.json  # 只有 bundle.externalBin
frontend/src-tauri/tauri.conf.json          # 版本、bundle.targets、bundle.windows.nsis
frontend/src-tauri/src/backend.rs           # 拉起、记日志、退出时结束 sidecar
frontend/scripts/collect-output.mjs         # 安装包收到 output/ 并改名
.github/workflows/build.yml                 # CI 发版
```
