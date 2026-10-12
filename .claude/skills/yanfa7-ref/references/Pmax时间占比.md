# Pmax 时间占比

## 业务背景

分析轴承最大接触应力（Pmax）在各应力区间上的时间占比：用户从 Excel 粘贴工况持续时间和前、后轴承的 Pmax，
按自定义区间分箱，统计每个区间的累计时长占总时长的百分比，前、后轴承各出一张柱状图，可以直接拖进 Word。

## 数据流

```text
「粘贴数据」→ 弹窗里 ⌘/Ctrl+V 粘贴 Excel 的 4 列 → 确认导入（页面只显示行数，不渲染表格）
→ 左卡设分箱（前 / 后轴承各一组 Min、Max、Step）、字号、图形尺寸、图表语言
→ 「生成图表」→ POST /api/pmax/analyze
→ 后端分箱、按区间汇总时长、算统计摘要，matplotlib 出 PNG 到临时目录，返回路径和统计
→ 右卡「图表预览」：统计摘要表 + 前 / 后轴承 PNG，图片可拖到 Word
```

## 业务约定

### 输入

- 4 列依次是持续时间 [h]、Pmax 前、持续时间 [h]、Pmax 后：列 0、1 归前轴承，列 2、3 归后轴承，两组各算各的。
- 后端把每格转成数字，转不了的当空值（表头行、空格子都会被跳过），前、后两组分别去掉空行；两组都没有有效数值时
  返回 400「未找到有效的数值数据」。

### 分箱

- 区间边界是 `Min, Min+Step, …`（不超过 Max），两头再补 −∞ 和 +∞。`pd.cut` 默认右闭，所以每个区间都是左开右闭。
- 标签和实际区间：`<Min` 实际是 `(−∞, Min]`，中间是 `(a, b]`，`>最后一条边界` 是 `(最后一条边界, +∞)`。
  Pmax 恰好等于 Min 的点算进 `<Min` 这一格。
- 占比 = 区间内持续时间之和 ÷ 总时长 × 100。实现在 `module/calculator.py`。
- 分箱、字号、尺寸的默认值见 `PmaxView.vue` 的 `binConfig` / `chartConfig`，后端 `serializers.py` 的 `ChartConfig` 有同一套默认值。

### 图表语言

前端 `Language`（`constants/language.ts`）和后端 `Language`（`backend/common/constants.py`）的取值都是 `中文` / `English`，
作为请求字段原样传过去，两边必须一致；图表标题和坐标轴文字按它切换。

### 临时文件

- PNG 写到 `<系统临时目录>/yanfa7_pmax/`，文件名固定为 `front.png` / `rear.png`；每次生成前先清空这个目录，
  只保留最近一次的图。
- 路径固定，前端靠 `imgCacheBuster` 时间戳破缓存，生成成功后才更新（做法见 Tauri Skill 的本地文件一节）。
- Tauri 外壳退出时不清理这个目录（见 `todo.md`），残留的图在下次生成前被清掉。

### 拖到 Word

webview 里的 `<img>` 拖不到外部应用，要走原生文件拖拽：图片 `dragstart` 时调 `window.electronAPI.startDrag(路径)`，
由兼容垫片转给 `@crabnebula/tauri-plugin-drag`。

## 接口与页面

`POST /api/pmax/analyze`：请求带表格数据（`string[][]`，每行 4 格）、`binConfig`（前 / 后各一组 `min`、`max`、`step`）、
`chartConfig`（字号和尺寸）、`language`；响应按 `front` / `rear` 各给 `chartPath`、`bins`（标签和占比）、
`stats`（时长和 Pmax 的最小 / 最大值）。模型见 `serializers.py` 与 `api/pmax.ts`。

页面 `PmaxView.vue`，没有 Pinia store，状态都在组件里，统计摘要取自后端响应：

- **左卡「参数配置」**（`:span=10`）：分箱参数、字体参数、图形比例、图表语言四个分区；底部「生成图表」和「清空数据」并排。
- **右卡「图表预览」**（`:span=14`）：卡头「粘贴数据」按钮带行数；空状态整块可点（没数据时打开粘贴弹窗，
  有数据没出图时直接生成）；出图后上面是统计摘要表，下面前、后轴承 PNG 纵向排列。

## 关键文件路径

### 后端

```text
backend/app_pmax/urls.py                 # 路由
backend/app_pmax/views.py                # analyze：转数字、分组、调用分箱和出图
backend/app_pmax/serializers.py          # Pydantic 请求 / 响应模型，ChartConfig 默认值
backend/app_pmax/module/calculator.py    # 分箱与时间占比
backend/app_pmax/module/chart.py         # 柱状图 PNG，临时目录与清理
backend/common/constants.py              # Language 枚举（前后端共用）
```

### 前端

```text
frontend/src/renderer/src/views/PmaxView.vue          # 页面，状态自管理
frontend/src/renderer/src/api/pmax.ts                 # 接口封装与类型
frontend/src/renderer/src/constants/language.ts       # Language 枚举（跨模块复用）
```
