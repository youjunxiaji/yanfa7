---
name: yanfa7-ui-style
description: "实现、修改或审查研发七部工具包（yanfa7）的 Vue 界面时使用，涵盖工具页骨架、配色、间距与字号、Element Plus 用法、可复用交互模式和暗色样式。新增工具页必读。"
---

# yanfa7 UI 风格

本 Skill 管外观与交互；模块行为查 `yanfa7-ref`，主题切换、拖拽、本地图片等原生能力查 `yanfa7-tauri`。
技术栈沿用项目规则：Element Plus + `<style scoped>`，暗色覆盖写在 `assets/main.css`。细则见[界面标准](references/界面标准.md)。

## 共用选择规则

- 工具页（设参数 → 出结果）套界面标准第一节的骨架，复用 `main.css`「工具页通用样式」段的全局类：
  `.page-card`、`.card-header`、`.config-form` / `.config-section`、`.action-bar`；页面只写差异，不另写卡片外壳。
- 阅读型页面（首页、设置、文档）居中定宽，不套 bento 骨架。
- 不写媒体查询：最小窗口 1100×700，靠 flex、`el-row` / `el-col :span`、`min-height: 0` 适配；高度不够时收紧间距，不加滚动条。
- 品牌蓝 `#0071e3`，次级灰 `#86868b`；不硬编码 `#409eff`、`#909399`。
- 主按钮不可用时用 `--inactive` 态并在下方写明缺什么，不只灰掉。
- 优先复用界面标准第六节的交互模式（可点击空状态、进度三态、缺前置提示等），不重造。
- 图标只用 `@element-plus/icons-vue`。

## 实现与验证

1. 先读与当前场景最近的基准页：工具页看 `EdgeStressView.vue`、`PmaxView.vue`，阅读型页面看 `SettingsView.vue`；
   在现有结构里改，保留业务逻辑、校验和异常处理。
2. 写了硬编码颜色就同步在 `main.css` 补 `html.dark` 覆盖。
3. 按界面标准末尾的检查清单逐项核对代码：空数据、处理中、出错、禁用、长文件名和长路径、窗口缩到最小时的布局。
