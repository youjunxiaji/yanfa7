@echo off

REM 切换到 UTF-8 编码
chcp 65001

REM 设置版本号环境变量
set "APP_VERSION=4.0.4"
echo 当前版本号: %APP_VERSION%

REM 获取当前批处理文件所在的目录
set "current_dir=%~dp0"

REM 创建输出目录（如果不存在）
if not exist "%current_dir%output" mkdir "%current_dir%output"

REM 执行PyInstaller命令
pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --distpath "%current_dir%output" ^
    --name "yanfa7-%APP_VERSION%" ^
    --icon "%current_dir%main_window/static/icon/配置数据处理.ico" ^
    --add-data "%current_dir%app_dutyRatio;app_dutyRatio/" ^
    --add-data "%current_dir%app_edgeStress;app_edgeStress/" ^
    --add-data "%current_dir%app_enercon;app_enercon/" ^
    --add-data "%current_dir%app_gearBox;app_gearBox/" ^
    --add-data "%current_dir%app_pmax;app_pmax/" ^
    --add-data "%current_dir%app_simpleLoad;app_simpleLoad/" ^
    --add-data "%current_dir%main_showLog;main_showLog/" ^
    --add-data "%current_dir%main_window;main_window/" ^
    "%current_dir%main.py"

REM 删除 build 文件夹和 .spec 文件
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /f /q "*.spec"

if %errorlevel% neq 0 (
    echo PyInstaller 执行失败，退出脚本
    goto :EOF
)



REM 加密代码
py2pyd -f "%current_dir%output" -d

if %errorlevel% neq 0 (
    echo 代码加密失败，退出脚本
    goto :EOF
)

REM 打包成安装文件
"D:\Inno Setup 6\ISCC.exe" "%current_dir%inno_setup.iss"

if %errorlevel% neq 0 (
    echo Inno Setup 打包失败，退出脚本
    goto :EOF
)
