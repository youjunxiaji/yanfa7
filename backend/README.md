# Edge Stress 后端

轴承边缘应力数据处理与分析后端服务 —— 基于 FastAPI 构建。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python >= 3.12 | 运行时 |
| [FastAPI](https://fastapi.tiangolo.com/) | WebSocket 服务框架 |
| [uvicorn](https://www.uvicorn.org/) | ASGI 服务器 |
| pandas / numpy | 数据处理 |
| scipy | 峰值检测与去除 |
| matplotlib / Plotly | 图表生成 |
| BeautifulSoup | HTM 文件解析 |
| openpyxl | Excel 读写 |
| Jinja2 | 报告模板 |

## 项目结构

```
backend/
├── main.py                  # FastAPI 入口 (app 初始化 + uvicorn 启动)
├── pyproject.toml           # 项目配置 & 依赖
├── uv.lock                  # uv 锁文件
├── app_edgeStress/          # 核心边缘应力模块 (Django 风格命名)
│   ├── urls.py              # WebSocket 路由定义
│   ├── views.py             # 视图函数 (业务逻辑)
│   ├── serializers.py       # Pydantic 请求/响应模型
│   ├── module/
│   │   ├── dataset.py       # 数据模型 (枚举 + dataclass)
│   │   ├── processor.py     # 数据加载器 + 去峰处理器
│   │   ├── reporter.py      # 报告生成器 (PNG/Plotly 数据)
│   │   └── cache.py         # DatasetCache 内存缓存管理器
```

## 开发

```bash
cd backend

# 安装依赖
uv sync

# 启动 FastAPI 服务 (端口 8000, 热重载)
uv run main.py
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## 接口

### GET /api/chart-data

REST API，返回指定滚子列的 Plotly 图表数据（原始 + 去峰后），供前端 Plotly.newPlot() 消费。

**请求参数（Query）:**

| 参数 | 类型 | 说明 |
|------|------|------|
| file_stem | string | 文件名 stem（不含扩展名） |
| col_index | int | 列号（从 1 开始） |
| position | string | `inner` 或 `outer` |

**响应:** JSON 数组，每项包含 `label` / `traces` / `layout`。

**前置条件:** 需先通过 WebSocket 解析文件（触发 DatasetCache 缓存），否则返回 400 并提示"缓存数据不存在，请重新解析文件后再预览"。

### POST /api/update-stress-point

REST API，修改去峰后数据中的单个应力值，更新内存缓存并重新生成相关 PNG。

**请求体（JSON）:**

| 参数 | 类型 | 说明 |
|------|------|------|
| file_stem | string | 文件名 stem（不含扩展名） |
| col_index | int | 列号（从 1 开始） |
| position | string | `inner` 或 `outer` |
| trace_index | int | 前端图表中的曲线索引（对应偏移+排序+跳零后的角度） |
| point_index | int | 曲线中的数据点索引 |
| new_value | float | 新的应力值 |

**响应:**

```json
{ "ok": true, "regenerated": ["/path/to/中.png", "/path/to/英.png", "/path/to/雷达图.png"] }
```

**副作用:** 先验证 xlsx 可写性（文件被占用时返回 400），再修改缓存、重新生成最大应力汇总.xlsx、应力曲线 PNG（中/英文）和应力雷达图 PNG。

### POST /api/regenerate-polar

REST API，使用自定义最小值重新生成雷达图 PNG。

**请求体（JSON）:**

| 参数 | 类型 | 说明 |
|------|------|------|
| file_stem | string | 文件名 stem（不含扩展名） |
| col_index | int | 列号（从 1 开始） |
| load_polar_min | float | 载荷雷达图径向最小值 |
| press_polar_min | float | 应力雷达图径向最小值 |

**响应:**

```json
{ "ok": true, "regenerated": ["/path/to/载荷雷达图.png", "/path/to/应力雷达图.png"] }
```

**副作用:** 使用传入的最小值创建临时 ReportConfig，重新生成对应列的载荷雷达图和应力雷达图 PNG。

### WS /ws/parse

WebSocket 接口。连接后发送 JSON 请求，服务端逐文件处理并实时推送进度，最终返回结果。

**客户端发送:**

```json
{
  "filePaths": ["/path/to/file1.htm", "/path/to/file2.htm"],
  "fileType": "htm",
  "peakThreshold": 0.00001,
  "outputDir": "/path/to/output",
  "reportConfig": {
    "picWidth": 10,
    "picHeight": 8,
    "loadPolarMin": 0,
    "pressPolarMin": 0
  }
}
```

**服务端推送 — 进度:**

```json
{ "type": "progress", "current": 0, "total": 3, "filename": "file1.htm" }
```

**服务端推送 — 完成:**

```json
{
  "type": "done",
  "fileNames": ["滚动轴承 1 (1.Extreme Tilt)", "..."],
  "columns": { "滚动轴承 1 (1.Extreme Tilt)": [1, 2] },
  "generatedFiles": ["/path/to/output/res-output/xxx.png", "..."],
  "previewMap": {
    "滚动轴承 1 (1.Extreme Tilt)": [
      { "colIndex": 1, "path": "/abs/path/to/...内滚道接触应力-第1列-中.png" },
      { "colIndex": 2, "path": "/abs/path/to/...内滚道接触应力-第2列-中.png" }
    ]
  }
}
```

> `previewMap` 以源文件 stem 为 key，值为该文件每个滚子列的内圈中文应力曲线 PNG 绝对路径（仅作为缩略图预览用）。前端可根据文件命名规则推导出其余 7 个文件的路径。

**服务端推送 — 错误:**

```json
{ "type": "error", "message": "错误信息" }
```

**自动生成的文件 (保存到 `outputDir/res-output/`):**

文件按组名创建子目录：`outputDir/res-output/{组名}/`。组名由文件名中第一个 `(` 之前的部分确定（去末尾空格），例如文件名 `滚动轴承 1 (1.Extreme Tilt)` 的组名为 `滚动轴承 1`。

| 文件类型 | 数量 (每列) | 说明 |
|----------|-------------|------|
| 应力曲线 PNG (中文) | 2 (内/外圈) | matplotlib 静态图 |
| 应力曲线 PNG (英文) | 2 (内/外圈) | matplotlib 静态图 |
| 雷达图 PNG | 2 (载荷/应力) | matplotlib 极坐标图 |
| 最大应力汇总.xlsx | 1 (全局) | 所有文件所有列的最大应力值 |

> Plotly 交互式图表不再生成文件，改为通过 REST API `/api/chart-data` 按需返回数据，由前端直接渲染。

**文件命名规则 (每个 RollerColumn 生成 6 个文件):**

```
{组名}/
├── {文件名}-内滚道接触应力-第{N}列-中.png    # 内圈应力曲线 (中文)
├── {文件名}-内滚道接触应力-第{N}列-英.png    # 内圈应力曲线 (英文)
├── {文件名}-外滚道接触应力-第{N}列-中.png    # 外圈应力曲线 (中文)
├── {文件名}-外滚道接触应力-第{N}列-英.png    # 外圈应力曲线 (英文)
├── {文件名}-第{N}列-载荷雷达图.png           # 载荷分布雷达图
└── {文件名}-第{N}列-应力雷达图.png           # 应力分布雷达图
```

其中 `{文件名}` 为源文件去扩展名后的 stem（如 `滚动轴承 1 (1.Extreme Tilt)`），`{N}` 为列号（从 1 开始）。

## 打包

### CI 自动打包（推荐）

推送 `v*` tag 后由 GitHub Actions 自动完成（`.github/workflows/build.yml`）：
1. PyInstaller `--onedir` 打包
2. py2pyd 加密 `app_edgeStress` 模块（需要 MSVC 编译器）
3. 复制产物到前端 `resources/backend/` 并打包为 Windows 安装包

### 本地手动打包

```bash
cd backend

# PyInstaller 打包
pyinstaller --noconfirm --onedir --console --add-data "app_edgeStress;app_edgeStress/" main.py

# py2pyd 加密（需要 MSVC）
py2pyd -r -d --no-confirm dist/main/_internal/app_edgeStress

# 复制到前端 resources
xcopy /E /I /Y dist\main\* ..\frontend\resources\backend\
```

也可使用 auto-py-to-exe GUI 打包。

### `main.py` 打包兼容

`main.py` 中 uvicorn 启动逻辑区分了开发/打包环境：
- **打包环境** (`sys.frozen=True`)：直接传 app 对象
- **开发环境**：使用 import 字符串 + 热重载

注意事项：
- 打包后首次运行会建 matplotlib 字体缓存（`~/.edge_stress_mpl/`），之后启动正常
- 打包环境需要：PyInstaller、gl-py2pyd（`uv add pyinstaller gl-py2pyd`）

## 核心模块说明

### dataset.py — 数据模型

- `FileType` / `StressPosition`: 枚举
- `StressData`: 原始 + 去峰后的应力 DataFrame
- `RollerColumn`: 单列滚子完整数据
- `ProcessConfig` / `ReportConfig` / `InputConfig`: 配置类
- `EdgeStressDataset`: 数据集容器 + 查询/汇总接口

### processor.py — 数据处理

- `EdgeStressLoader`: HTM / Excel 文件解析，生成 RollerColumn 列表
- `EdgeStressProcessor`: 使用 scipy.signal.find_peaks 去除异常峰值

### reporter.py — 报告生成

- `calc_legend_ncol()`: 根据图例条目数和画布高度自动计算图例列数
- `EdgeStressReporter.generate_stress_chart()`: 应力分布曲线 PNG（图例列数自动计算）
- `EdgeStressReporter.generate_polar_chart()`: 雷达图 PNG
- `EdgeStressReporter.build_chart_data()`: 构建 Plotly 图表数据（静态方法，不写文件）
- `EdgeStressReporter.export_processed_excel()`: 去峰数据 Excel（当前已注释）
- `EdgeStressReporter.generate_all()`: 批量生成所有报告

### cache.py — 数据缓存

- `DatasetCache.save()`: 保存 dataset 到内存缓存
- `DatasetCache.load()`: 读取缓存的 dataset
- `DatasetCache.get_column()`: 获取指定 RollerColumn
- `DatasetCache.update()`: 替换指定 RollerColumn（为后续数据编辑预留）
