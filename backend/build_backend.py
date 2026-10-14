"""把后端打成 Tauri 外壳能收的 sidecar，顺带管住发版版本号。

    cd backend
    uv run python build_backend.py                  # 问一次版本，再打包
    uv run python build_backend.py --version 2.1.0  # 直接给版本，不问（CI 用）
    uv run python build_backend.py --keep-version   # 沿用当前版本，不问

产物落到 `../frontend/src-tauri/binaries/yanfa7-backend-<target-triple>.exe`，接着在 `frontend/`
跑 `npm run tauri:build` 才会把它收进安装包。

版本号散在三个文件里（见 `VERSION_SITES`），首页显示的版本、安装包文件名和 exe 属性都从这里来。
发版从这个脚本起步，版本在这里定一次、三处一起写，不手改其中某一处。

Nuitka 用 onefile：Tauri 的 `externalBin` 收的是一个文件，standalone 出的是一整个目录。
解包目录固定在用户缓存目录（见 `nuitka_args()`），只有第一次启动和版本更新后要解包，之后每次启动
只核对校验和、改过的文件才重写。Python 代码编译成 C，安装包里没有明文源码。
"""

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# 这里是 backend/。nuitka 的入口按相对路径给，必须在本目录跑，build() 里已经指定 cwd。
HERE = Path(__file__).resolve().parent
FRONTEND = HERE.parent / "frontend"

# sidecar 名和 `frontend/src-tauri/src/backend.rs` 的 SIDECAR、`tauri.windows.conf.json` 的
# externalBin 绑死，改名三处一起改。
SIDECAR_NAME = "yanfa7-backend"

# Tauri 按 `<名字>-<target-triple>[.exe]` 找 sidecar，放在 src-tauri/ 下的这个目录。
OUTPUT_DIR = FRONTEND / "src-tauri" / "binaries"

# 版本号的三个落点：(文件, 正则, 这处版本用在哪)。
# 正则留三个组：前缀、版本、后缀，替换时只换中间那个，文件其余部分不动。
# 都锚定行首：package.json、tauri.conf.json 顶层的 version 只缩进一级；Cargo.toml 依赖里的版本是
# 内联表（`tauri = { version = "2" }`），锚定行首才不会误伤。
VERSION_SITES: list[tuple[Path, str, str]] = [
    (
        FRONTEND / "package.json",
        r'(?m)^(    "version": ")([^"]+)(")',
        "首页显示的版本（渲染层的 __APP_VERSION__）",
    ),
    (
        FRONTEND / "src-tauri" / "tauri.conf.json",
        r'(?m)^(    "version": ")([^"]+)(")',
        "安装包文件名、应用版本",
    ),
    (
        FRONTEND / "src-tauri" / "Cargo.toml",
        r'(?m)^(version = ")([^"]+)(")',
        "外壳 crate 版本",
    ),
]

# 只认 主.次.修订：Tauri 要求 semver，将来出 msi 时 WiX 也只认这种形态。
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def read_versions() -> dict[Path, str]:
    """读出三处的当前版本。

    Returns:
        文件路径到版本号的映射。

    Raises:
        SystemExit: 某处的写法和 `VERSION_SITES` 的正则对不上。直接报错，不静默跳过。
    """
    found: dict[Path, str] = {}
    for path, pattern, what in VERSION_SITES:
        match = re.search(pattern, path.read_text(encoding="utf-8"))
        if not match:
            raise SystemExit(
                f"在 {path} 里没找到版本号（{what}）。那里的写法改了的话，本脚本的 VERSION_SITES 也要跟着改。"
            )
        found[path] = match.group(2)
    return found


def write_versions(version: str) -> None:
    """把版本写进三处。

    Args:
        version: 要写入的版本号。

    Raises:
        SystemExit: 某处没能替换。
    """
    for path, pattern, _what in VERSION_SITES:
        text = path.read_text(encoding="utf-8")
        new_text, count = re.subn(pattern, lambda m: m[1] + version + m[3], text, count=1)
        if count != 1:
            raise SystemExit(f"写版本号失败：{path}")
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")


def resolve_version(args: argparse.Namespace) -> str:
    """定下这次要打的版本：命令行给了就用给的，否则问一次。

    Args:
        args: 命令行参数，看 `version` 和 `keep_version`。

    Returns:
        这次要打的版本号，三处已经统一成它。

    Raises:
        SystemExit: 版本号不合规，或者没法确定版本。
    """
    current = read_versions()
    counts = Counter(current.values())
    majority = max(counts.values())

    print("当前版本：")
    for path, _pattern, what in VERSION_SITES:
        # 只标少数派：上次发版漏改的多半就是它
        flag = "  <- 与其他不同" if len(counts) > 1 and counts[current[path]] < majority else ""
        print(f"  {current[path]:<10} {path.relative_to(HERE.parent)}{flag}")
        print(f"  {'':<10} {what}")

    if len(counts) > 1:
        # 不替人猜哪个对：不一致本身说明上次漏改了一处，由人看着定
        print("\n注意：三处版本不一致，这次打包会把它们统一成你给的版本。")

    if args.version:
        chosen = args.version
    elif args.keep_version:
        if len(counts) > 1:
            raise SystemExit("三处版本不一致，--keep-version 沿用不了，请显式给 --version")
        chosen = next(iter(counts))
    elif not sys.stdin.isatty():
        # 非交互环境（CI、被别的脚本调）不能停在这儿等输入
        raise SystemExit("非交互环境下必须给 --version 或 --keep-version")
    else:
        default = next(iter(counts)) if len(counts) == 1 else ""
        hint = f"[回车沿用 {default}]" if default else "[必填]"
        chosen = input(f"\n这次打哪个版本？{hint} ").strip() or default
        if not chosen:
            raise SystemExit("没给版本号，中止")

    if not VERSION_RE.match(chosen):
        raise SystemExit(f"版本号得是 主.次.修订（如 2.1.0），拿到的是 {chosen!r}")

    if any(v != chosen for v in current.values()):
        write_versions(chosen)
        print(f"已把三处版本统一为 {chosen}")
    return chosen


def target_triple() -> str:
    """问 rustc 要 target triple，Tauri 按它给 sidecar 命名。

    不按 `platform.machine()` 自己拼：Tauri 认的是 rustc 那套写法（`x86_64-pc-windows-msvc`），
    拼错了 `tauri build` 会报找不到 sidecar。

    Returns:
        rustc 的 host triple。

    Raises:
        SystemExit: rustc 没装，或者输出里没有 host 行。
    """
    try:
        out = subprocess.run(["rustc", "-vV"], capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"取 target triple 失败，rustc 装了吗：{exc}") from exc

    for line in out.splitlines():
        if line.startswith("host:"):
            return line.split(":", 1)[1].strip()
    raise SystemExit(f"rustc -vV 里没有 host 行：\n{out}")


def nuitka_args(version: str, output_name: str) -> list[str]:
    """拼 nuitka 的命令行。

    Args:
        version: 写进 exe 属性的版本号。
        output_name: onefile 产物的文件名。

    Returns:
        完整的命令行参数列表。
    """
    return [
        sys.executable, "-m", "nuitka",
        "--mode=onefile",
        "--assume-yes-for-downloads",
        # 后端没有界面，不要控制台窗口。Tauri 拉起它时 stdio 是管道，照常可用；
        # 直接双击运行时 stdout / stderr 是 None，uvicorn 起不来，排查时要重定向输出。
        "--windows-console-mode=disable",
        # 解包目录固定、不带版本号：每次启动只核对校验和，改过的文件才重写；默认的随机临时目录每次都要
        # 整个解包，进程被外壳结束时还删不掉。目录在 %LOCALAPPDATA%\yanfa7\backend。
        "--onefile-tempdir-spec={CACHE_DIR}/yanfa7/backend",
        # pandas 读 HTM 用 lxml、读写 Excel 用 openpyxl，都是运行时按名字导入的，显式带上
        "--include-module=lxml.etree",
        "--include-module=lxml.html",
        "--include-package=openpyxl",
        # 载荷简化沿用 simple_load 打包时的显式包含，polars 整包带上
        "--include-package=polars",
        f"--product-version={version}",
        f"--file-version={version}",
        "--product-name=研发七部工具包",
        "--file-description=研发七部工具包后端服务",
        f"--windows-icon-from-ico={FRONTEND / 'src-tauri' / 'icons' / 'icon.ico'}",
        f"--output-dir={HERE / 'build'}",
        f"--output-filename={output_name}",
        # 模块、数据文件的清单，装机后缺东西时先看这里
        f"--report={HERE / 'build' / 'compilation-report.xml'}",
        "main.py",
    ]


def build(version: str) -> Path:
    """调 nuitka 打包，把产物放到 Tauri 找 sidecar 的位置。

    Args:
        version: 这次打的版本号。

    Returns:
        sidecar 的最终路径。

    Raises:
        SystemExit: nuitka 没产出预期的文件。
        subprocess.CalledProcessError: nuitka 执行失败。
    """
    suffix = ".exe" if sys.platform == "win32" else ""
    final = OUTPUT_DIR / f"{SIDECAR_NAME}-{target_triple()}{suffix}"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n打包 {SIDECAR_NAME} {version} → {final}")
    # matplotlib 插件把编译时探测到的后端写进随包的配置；机器上装了 Tk 时探测到的是 TkAgg，
    # 会把 tkinter 牵进来。main.py 运行时用的是 Agg，编译时也定成 Agg。
    env = {**os.environ, "MPLBACKEND": "Agg"}
    if sys.platform == "win32":
        # nuitka_args() 里的产品名等中文，Nuitka 以 UTF-8 写进 build_definitions.h；中文 Windows 上
        # MSVC 默认按 GBK（代码页 936）读源文件，字符串常量被截坏，报 C2001。CL 环境变量里的选项
        # cl 每次调用都会带上，用它让 cl 统一按 UTF-8 读。
        env["CL"] = f"{env.get('CL', '')} /utf-8".strip()
    subprocess.run(nuitka_args(version, final.name), cwd=HERE, env=env, check=True)

    built = HERE / "build" / final.name
    if not built.is_file():
        raise SystemExit(f"nuitka 没有产出预期的文件：{built}")
    shutil.copy2(built, final)

    print(f"\n完成：{final}（{final.stat().st_size / 1024 / 1024:.1f} MB）")
    print("接着在 frontend/ 跑 `npm run tauri:build` 出安装包。")
    return final


def main() -> None:
    # 输出里有中文。Windows 上 stdout 被重定向（`> build.log`、CI 捕获）时退回系统编码，
    # 遇到编码不了的字符会 UnicodeEncodeError，把打包中断在版本那一步，统一成 UTF-8。
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="把后端打成 Tauri sidecar，并统一三处版本号")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--version", metavar="X.Y.Z", help="这次要打的版本，写进三处")
    group.add_argument("--keep-version", action="store_true", help="沿用当前版本，不询问（三处必须已经一致）")
    args = parser.parse_args()

    build(resolve_version(args))


if __name__ == "__main__":
    main()
