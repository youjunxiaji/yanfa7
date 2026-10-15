@echo off
setlocal

rem Build the Windows installer in one go. Step 1: Nuitka packs the backend into a sidecar exe.
rem Step 2: Tauri builds the NSIS installer. The order matters (see the yanfa7-release skill).
rem
rem Arguments are passed through to backend\build_backend.py:
rem   build.cmd                    ask for the version once
rem   build.cmd --version 2.1.0    set the version directly
rem   build.cmd --keep-version     keep the current version
rem The installer ends up in output\yanfa7-toolkit-VERSION-setup.exe
rem
rem Keep this file pure ASCII: no Chinese in comments or messages, and no chcp in here.
rem cmd works out where the next line starts by counting characters instead of bytes, so UTF-8
rem text in a running batch file makes it resume in the middle of a line and run the rest of that
rem line as a command. Switching the code page inside the script does not help, cmd.exe is already
rem running. Details are in the yanfa7-release skill.

for %%t in (uv rustc npm) do (
    where %%t >nul 2>nul || (
        echo [build] %%t not found. Install the build toolchain first, see the "Toolchain" section of .claude\skills\yanfa7-release\SKILL.md
        goto :fail
    )
)

pushd "%~dp0backend"
call uv run python build_backend.py %*
if errorlevel 1 goto :fail_popd
popd

pushd "%~dp0frontend"
rem Install the frontend dependencies on the first run on a new machine
if not exist node_modules (
    call npm install
    if errorlevel 1 goto :fail_popd
)
call npm run tauri:build
if errorlevel 1 goto :fail_popd
popd

echo.
echo Build finished. The installer is in %~dp0output
set "EXIT_CODE=0"
goto :end

:fail_popd
popd
:fail
echo.
echo Build FAILED, see the output above.
set "EXIT_CODE=1"

:end
rem Double-clicked: the window closes as soon as the script ends, so pause to read the output.
rem Run from an open prompt: do not pause.
echo %cmdcmdline% | findstr /i /c:"%~nx0" >nul && pause
exit /b %EXIT_CODE%
