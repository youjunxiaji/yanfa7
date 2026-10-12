@echo off
setlocal
for /f "tokens=2 delims=:." %%c in ('chcp') do set "ORIGINAL_CP=%%c"
chcp 65001 >nul

rem 上面几行只能是英文：先切到 UTF-8 代码页，后面的中文才不会乱码、不会吞掉换行；结束时切回原来的代码页。
rem
rem 一键出安装包（Windows）：先用 Nuitka 把后端打成 sidecar，再用 Tauri 打安装包，顺序不能反，见发版 Skill。
rem 参数原样传给 backend\build_backend.py：
rem   build.cmd                    问一次版本
rem   build.cmd --version 2.1.0    直接定版本
rem   build.cmd --keep-version     沿用当前版本
rem 安装包在 output\yanfa7-toolkit-<版本>-setup.exe。

for %%t in (uv rustc npm) do (
    where %%t >nul 2>nul || (
        echo 没找到 %%t，先把打包要的工具装好，见发版 Skill 的「工具链」一节
        goto :fail
    )
)

pushd "%~dp0backend"
call uv run python build_backend.py %*
if errorlevel 1 goto :fail_popd
popd

pushd "%~dp0frontend"
rem 新机器上第一次打包时先装前端依赖
if not exist node_modules (
    call npm install
    if errorlevel 1 goto :fail_popd
)
call npm run tauri:build
if errorlevel 1 goto :fail_popd
popd

echo.
echo 打包完成，安装包在 %~dp0output
set "EXIT_CODE=0"
goto :end

:fail_popd
popd
:fail
echo.
echo 打包失败，原因见上面的输出
set "EXIT_CODE=1"

:end
rem 双击运行时窗口一结束就关，停一下好看输出；在已经打开的命令行里运行时不停
echo %cmdcmdline% | findstr /i /c:"%~nx0" >nul && pause
chcp %ORIGINAL_CP% >nul
exit /b %EXIT_CODE%
