"""
边缘应力报告生成器

负责生成 matplotlib 图表、Plotly HTML 报告和 Excel 导出。
无 UI 依赖，纯文件输出。

Author: gu lei
Date: 2026-02-11
"""
from pathlib import Path

import matplotlib.pyplot as plt
from loguru import logger
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

from app_edgeStress.module.dataset import (
    EdgeStressDataset,
    ReportConfig,
    RollerColumn,
    StressPosition,
)

plt.rcParams['font.sans-serif'] = ['SimHei']

# 图表样式常量
MARKERS = ["s-", "^-", "D-", "d-", "|-", "-", "|-", "d-", "H-", "o-", "X-", "^-"] * 100
COLORS = [
    "#fe0000", "#0000ff", "#636efa", "#ef553b", "#00cc96", "#ab63fa",
    "#ffa15a", "#19d3f3", "#ff6692", "#b6e880", "#ff97ff", "#fecb52",
] * 100

# 英文标题映射
TITLE_EN = {
    StressPosition.INNER: "Contact Stress Distribution of Inner Ring",
    StressPosition.OUTER: "Contact Stress Distribution of Outer Ring",
}


LEGEND_ENTRY_HEIGHT = 0.2  # 单条图例条目的近似高度（英寸）


def calc_legend_ncol(n_entries: int, canvas_height: float) -> int:
    """
    根据图例条目数和画布高度自动计算图例列数。

    Parameters
    ----------
    n_entries : int
        图例中的条目数量。
    canvas_height : float
        画布高度（英寸）。

    Returns
    -------
    int
        图例列数（至少为 1）。
    """
    if n_entries <= 0:
        return 1
    max_rows = max(1, int(canvas_height / LEGEND_ENTRY_HEIGHT))
    return max(1, -(-n_entries // max_rows))  # ceil division


class EdgeStressReporter:
    """
    边缘应力报告生成器。

    负责基于处理后的 RollerColumn 数据生成：
    - Matplotlib 应力分布曲线图（中/英文）
    - Matplotlib 雷达图（载荷分布、应力分布）
    - Plotly 交互式 HTML 报告
    - 去峰后数据 Excel 导出
    """

    def __init__(self, config: ReportConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ============================================================
    # 应力分布曲线图 (matplotlib)
    # ============================================================

    def generate_stress_chart(
        self,
        col: RollerColumn,
        position: StressPosition,
        is_cn: bool = True,
    ) -> Path:
        """
        生成应力分布曲线图。

        Parameters
        ----------
        col : RollerColumn
            滚子列数据。
        position : StressPosition
            内圈 / 外圈。
        is_cn : bool
            True = 中文标题, False = 英文标题。

        Returns
        -------
        Path
            保存的 PNG 文件路径。
        """
        stress = col.get_stress(position)
        df = stress.processed if stress.processed is not None else stress.origin
        df = df.copy()

        # 角度偏移 +180°
        new_level_0 = ((df.index.levels[0].astype(float) + 180) % 360).round(3)  # type: ignore[union-attr]
        df.index = df.index.set_levels(new_level_0, level=0)  # type: ignore[union-attr]
        df = df.sort_index()
        level_unique = df.index.get_level_values(0).unique()

        fig, ax = plt.subplots(
            figsize=(self.config.pic_width, self.config.pic_height),
            constrained_layout=True,
        )

        # 绘制每个角度的曲线
        for i, angle in enumerate(level_unique):
            values = df.loc[angle, "接触应力 (MPa)"]
            if (values == 0).all():  # type: ignore[union-attr]
                continue
            ax.plot(values, MARKERS[i], c=COLORS[i], label=angle)

        # 坐标轴样式
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

        x_ticks = plt.xticks()[0]
        y_ticks = plt.yticks()[0]
        interval_x = x_ticks[1] - x_ticks[0] if len(x_ticks) > 1 else 1
        interval_y = y_ticks[1] - y_ticks[0] if len(y_ticks) > 1 else 1

        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(interval_x))
        ax.xaxis.set_minor_locator(ticker.MultipleLocator(interval_x / 2))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(interval_y))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(interval_y / 2))

        # 标题和标签
        if is_cn:
            ax.set_title(f"{position.value}\n", fontsize=20, fontweight="bold")
            ax.set_xlabel("沿滚子的距离(mm)")
            ax.set_ylabel("接触应力(MPa)")
        else:
            ax.set_title(f"{TITLE_EN[position]}\n", fontsize=20, fontweight="bold")
            ax.set_xlabel("Along the Roller Length(mm)")
            ax.set_ylabel("Contact Stress (MPa)")

        n_entries = len(ax.get_legend_handles_labels()[1])
        ncol = calc_legend_ncol(n_entries, self.config.pic_height)
        ax.legend(
            loc="center left", bbox_to_anchor=(1, 0.5),
            ncol=ncol, frameon=False,
        )
        ax.grid(ls="dotted", lw=1.5, alpha=0.6, c="black")

        # 保存
        lang_tag = "中" if is_cn else "英"
        png_file = (
            self.output_dir
            / f"{col.filename}-{position.value}-第{col.col_index}列-{lang_tag}.png"
        )
        fig.savefig(str(png_file), bbox_inches="tight")
        plt.close(fig)
        return png_file

    # ============================================================
    # 雷达图 (matplotlib)
    # ============================================================

    def generate_polar_chart(
        self,
        col: RollerColumn,
        dataset: EdgeStressDataset | None = None,
        is_load: bool = True,
    ) -> Path | None:
        """
        生成雷达图。

        Parameters
        ----------
        col : RollerColumn
            滚子列数据。
        dataset : EdgeStressDataset | None
            数据集（用于获取应力雷达图的 max 数据）。
        is_load : bool
            True = 载荷分布雷达图, False = 应力分布雷达图。

        Returns
        -------
        Path | None
            PNG 文件路径，数据不足时返回 None。
        """
        if is_load:
            # 载荷分布雷达图
            if col.load_distribution is None:
                return None
            df = col.load_distribution.copy()
        else:
            # 应力分布雷达图（内外圈最大值）
            inner = col.inner_stress.processed if col.inner_stress.processed is not None else col.inner_stress.origin
            outer = col.outer_stress.processed if col.outer_stress.processed is not None else col.outer_stress.origin
            df = pd.concat([
                outer.groupby(level=0).max(),
                inner.groupby(level=0).max(),
            ], axis=1)

        # 首尾相连形成闭合图形
        df = pd.concat([df, df.iloc[[0]]], axis=0)
        df.index = np.radians(df.index.astype(float))  # type: ignore[assignment]

        fig = plt.figure(figsize=(self.config.pic_width, self.config.pic_height))
        ax = fig.add_subplot(111, polar=True)

        # r 轴范围
        user_r_min = self.config.load_polar_min if is_load else self.config.press_polar_min
        r_max = df.max().max()

        if user_r_min != 0:
            r_min = user_r_min
        elif (df.values == 0).any():
            r_min = -(r_max / 2)
        else:
            r_min = 0

        ax.set_rlim(r_min, r_max)  # type: ignore[attr-defined]

        # 网格
        ax.grid(c="gray", linestyle=":", alpha=1, which="major", zorder=1)

        # 遮罩负值区域
        theta = np.linspace(0, 2 * np.pi, 100)
        ax.fill_between(theta, r_min, 0, color="white", zorder=2)
        ax.plot(theta, np.zeros_like(theta), color="#aaaaaa", linewidth=0.5, zorder=3)

        # 角度刻度
        ax.set_theta_direction(-1)  # type: ignore[attr-defined]
        ax.xaxis.set_major_locator(ticker.MultipleLocator(np.pi / 6))
        plt.xticks(
            [i * 30 / 180 * np.pi for i in range(12)],
            [
                "180°", "210°", "240°", "270°", "300°", "330°",
                "Y 0°\n(GL-hub)", "30°", "60°", "Z 90°\n(GL-hub)", "120°", "150°",
            ],
            size=20,
        )

        # 径向刻度
        yticks = plt.yticks()[0]
        ylabels = ["" if y < 0 else f"{float(f'{y:.3g}'):g}" for y in yticks]
        plt.yticks(yticks, ylabels, size=13)
        ax.set_rlabel_position(90)  # type: ignore[attr-defined]
        ax.tick_params(axis="x", pad=28)
        ax.text(np.pi / 2, 0, "0.0", ha="left", va="bottom", size=13)

        # 绘制数据
        ax.plot(df.iloc[:, 1], "rs", linewidth=1, linestyle="solid", label="IR raceway", zorder=4)
        ax.plot(df.iloc[:, 0], "b^", linewidth=1, linestyle="solid", label="OR raceway", zorder=4)
        plt.legend(bbox_to_anchor=(0.5, -0.4), loc=8, fontsize=25, frameon=False)

        # 标题
        title_list = ["Load Distribution [kN]", "Max. Contact Pressure Distribution [MPa]"]
        chart_type = "载荷雷达图" if is_load else "应力雷达图"
        plt.title(title_list[0 if is_load else 1], fontsize=25, pad=20)

        png_file = self.output_dir / f"{col.filename}-第{col.col_index}列-{chart_type}.png"
        fig.savefig(str(png_file), bbox_inches="tight")
        plt.close(fig)
        return png_file

    # ============================================================
    # Plotly 图表数据
    # ============================================================

    @staticmethod
    def build_chart_data(
        col: RollerColumn,
        position: StressPosition,
    ) -> list[dict]:
        """
        构建 Plotly 图表数据，供前端 Plotly.newPlot() 直接消费。

        返回包含原始数据和去峰后数据两组图表配置的列表，不涉及文件 I/O。

        Parameters
        ----------
        col : RollerColumn
            滚子列数据。
        position : StressPosition
            内圈 / 外圈。

        Returns
        -------
        list[dict]
            图表数据列表，每项包含 label / traces / layout。
        """
        stress = col.get_stress(position)
        charts: list[dict] = []

        for label, df in [("原始数据", stress.origin), ("去峰后数据", stress.processed)]:
            if df is None:
                continue
            df = df.copy()
            if label == "去峰后数据":
                new_level_0 = ((df.index.levels[0].astype(float) + 180) % 360).round(3)
                df.index = df.index.set_levels(new_level_0, level=0)
                df = df.sort_index()

            level_unique = df.index.get_level_values(0).unique()
            traces = []
            for angle in level_unique:
                values = df.loc[angle, "接触应力 (MPa)"]
                if (values == 0).all():
                    continue
                traces.append({
                    "x": values.index.tolist(),
                    "y": values.values.tolist(),
                    "mode": "lines+markers",
                    "name": str(angle),
                })

            charts.append({
                "label": label,
                "traces": traces,
                "layout": {
                    "xaxis_title": "沿滚子距离(mm)",
                    "yaxis_title": "接触应力(MPa)",
                    "height": 600,
                },
            })

        return charts

    # ============================================================
    # Excel 导出
    # ============================================================

    def export_processed_excel(self, col: RollerColumn) -> Path:
        """
        导出去峰后的内外圈数据合并 Excel。

        Parameters
        ----------
        col : RollerColumn
            滚子列数据。

        Returns
        -------
        Path
            Excel 文件路径。
        """
        inner_df = col.inner_stress.processed if col.inner_stress.processed is not None else col.inner_stress.origin
        outer_df = col.outer_stress.processed if col.outer_stress.processed is not None else col.outer_stress.origin

        df = (
            outer_df.rename(columns={"接触应力 (MPa)": "外滚道接触应力"})
            .merge(
                inner_df.rename(columns={"接触应力 (MPa)": "内滚道接触应力"}),
                left_index=True, right_index=True, how="outer",
            )
        )

        excel_file = self.output_dir / f"{col.filename}-第{col.col_index}列.xlsx"
        df.to_excel(str(excel_file))
        return excel_file

    # ============================================================
    # 批量生成
    # ============================================================

    def generate_for_column(self, col: RollerColumn) -> list[Path]:
        """为单个 RollerColumn 生成全部报告文件。"""
        files: list[Path] = []

        for position in StressPosition:
            for is_cn in [True, False]:
                files.append(self.generate_stress_chart(col, position, is_cn))

        polar_load = self.generate_polar_chart(col, is_load=True)
        if polar_load:
            files.append(polar_load)
        polar_stress = self.generate_polar_chart(col, is_load=False)
        if polar_stress:
            files.append(polar_stress)

        return files

    def generate_all(
        self,
        dataset: EdgeStressDataset,
        on_progress=None,
    ) -> list[Path]:
        """
        批量生成所有报告。

        每个 RollerColumn 生成：
        - 应力分布曲线图（内圈中/英 + 外圈中/英 = 4 张 PNG）
        - 雷达图（载荷 + 应力 = 2 张 PNG）

        Parameters
        ----------
        dataset : EdgeStressDataset
            数据集。
        on_progress : callable
            进度回调 (current, total)。

        Returns
        -------
        list[Path]
            所有生成的文件路径列表。
        """
        files: list[Path] = []
        total = len(dataset.columns)

        for i, col in enumerate(dataset.columns):
            files.extend(self.generate_for_column(col))

            if on_progress:
                on_progress(i + 1, total)

        return files
