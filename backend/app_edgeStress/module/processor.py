"""
边缘应力数据处理器

负责文件解析和数据处理，无 UI 依赖。

Author: gu lei
Date: 2026-02-11
"""
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from app_edgeStress.module.dataset import (
    FileType,
    InputConfig,
    RollerColumn,
    StressData,
)

# 进度回调类型: (当前完成数, 总数)
ProgressCallback = Callable[[int, int], None] | None


# ============================================================
# 数据加载器
# ============================================================

class EdgeStressLoader:
    """
    边缘应力数据加载器。

    负责解析 HTM / Excel 文件，生成标准化的 RollerColumn 列表。
    加载阶段只解析原始数据，不做去峰处理。
    """

    def load(
        self,
        input_config: InputConfig,
        on_progress: ProgressCallback = None,
    ) -> list[RollerColumn]:
        """
        统一加载入口。

        Parameters
        ----------
        input_config : InputConfig
            输入配置（文件列表、类型、输出目录）。
        on_progress : ProgressCallback
            进度回调 (current, total)。

        Returns
        -------
        list[RollerColumn]
            解析后的标准化数据列表。
        """
        if input_config.file_type == FileType.HTM:
            return self._load_htm_files(input_config.files, on_progress)
        else:
            return self._load_excel_files(input_config.files, on_progress)

    def load_single_file(
        self, file_path: Path, file_type: FileType
    ) -> list[RollerColumn]:
        """加载单个文件，返回该文件解析出的所有 RollerColumn。"""
        if file_type == FileType.HTM:
            return self._parse_single_htm(file_path)
        else:
            return [self._parse_single_excel(file_path)]

    # ----- HTM -----

    def _load_htm_files(
        self, files: list[Path], on_progress: ProgressCallback
    ) -> list[RollerColumn]:
        """批量加载 HTM 文件"""
        columns: list[RollerColumn] = []
        total = len(files)
        for i, file_path in enumerate(files):
            try:
                file_columns = self._parse_single_htm(file_path)
                columns.extend(file_columns)
            except Exception as e:
                print(f"\n  ⚠ 跳过文件 {file_path.name}: {e}")
            if on_progress:
                on_progress(i + 1, total)
        return columns

    def _parse_single_htm(self, file_path: Path) -> list[RollerColumn]:
        """
        解析单个 HTM 文件。

        HTM 文件结构：
        - 总共 3N 个表格（N = 滚子列数）
        - 前 N 个表格：载荷分布（雷达图数据）
        - 后 2N 个表格：内/外圈接触应力交替排列

        Returns
        -------
        list[RollerColumn]
            该文件解析出的所有列数据。
        """
        filename = file_path.stem
        pattern = (
            r"(滚子轮廓与内圈接触结果|滚子轮廓与外圈接触结果"
            r"|滚子与滚道接触载荷表|滚子载荷分配)"
        )
        try:
            df_list = pd.read_html(str(file_path), match=pattern)
        except ValueError:
            raise ValueError(f"未找到应力数据表格，该文件可能不是应力分析结果文件")

        if len(df_list) < 3:
            raise ValueError(f"表格数量不足 ({len(df_list)}个)，无法解析完整的滚子列数据")

        num_cols = len(df_list) // 3  # 每列有 3 个表格

        # --- 解析雷达图数据 (前 num_cols 个表格) ---
        polars: list[pd.DataFrame] = []
        for df_raw in df_list[:num_cols]:
            df_polar = df_raw.iloc[:, 0:3]
            df_polar.columns = df_polar.columns.droplevel(0)
            df_polar.set_index(df_polar.columns[0], inplace=True)
            polars.append(df_polar)

        # --- 解析接触应力数据 (后 2*num_cols 个表格, 内外圈交替) ---
        inner_origins: list[pd.DataFrame] = []
        outer_origins: list[pd.DataFrame] = []
        for index, df_raw in enumerate(df_list[num_cols:]):
            df_raw.set_index(df_raw.columns.tolist()[0:2], inplace=True)
            if (index + 1) % 2 == 1:  # 奇数 → 内圈
                inner_origins.append(df_raw)
            else:  # 偶数 → 外圈
                outer_origins.append(df_raw)

        # --- 组装 RollerColumn ---
        columns: list[RollerColumn] = []
        for col_idx in range(num_cols):
            rc = RollerColumn(
                filename=filename,
                col_index=col_idx + 1,
                inner_stress=StressData(origin=inner_origins[col_idx]),
                outer_stress=StressData(origin=outer_origins[col_idx]),
                load_distribution=polars[col_idx] if col_idx < len(polars) else None,
            )
            columns.append(rc)
        return columns

    # ----- Excel -----

    def _load_excel_files(
        self, files: list[Path], on_progress: ProgressCallback
    ) -> list[RollerColumn]:
        """
        加载 Excel 文件。

        Excel 文件通常是 HTM 处理后的汇总数据，
        包含 "内滚道接触应力" 和 "外滚道接触应力" 列。
        """
        columns: list[RollerColumn] = []
        total = len(files)
        for i, file_path in enumerate(files):
            try:
                rc = self._parse_single_excel(file_path)
                columns.append(rc)
            except Exception as e:
                print(f"\n  ⚠ 跳过文件 {file_path.name}: {e}")
            if on_progress:
                on_progress(i + 1, total)
        return columns

    def _parse_single_excel(self, file_path: Path) -> RollerColumn:
        """解析单个 Excel 文件"""
        filename = file_path.stem
        df = pd.read_excel(str(file_path), index_col=[0, 1])

        # 提取内/外圈数据列
        inner_df = (
            df[["内滚道接触应力"]].rename(columns={"内滚道接触应力": "接触应力 (MPa)"})
            if "内滚道接触应力" in df.columns
            else pd.DataFrame()
        )
        outer_df = (
            df[["外滚道接触应力"]].rename(columns={"外滚道接触应力": "接触应力 (MPa)"})
            if "外滚道接触应力" in df.columns
            else pd.DataFrame()
        )

        col_index = self._extract_col_index(filename)

        # Excel 数据视为已处理的数据
        return RollerColumn(
            filename=filename,
            col_index=col_index,
            inner_stress=StressData(origin=inner_df, processed=inner_df),
            outer_stress=StressData(origin=outer_df, processed=outer_df),
            load_distribution=None,
        )

    @staticmethod
    def _extract_col_index(filename: str) -> int:
        """从文件名中提取列号，失败返回 1"""
        try:
            return int(filename.split("-")[-1][1])
        except (IndexError, ValueError):
            return 1


# ============================================================
# 数据处理器
# ============================================================

class EdgeStressProcessor:
    """
    边缘应力数据处理器。

    对加载后的原始数据逐条曲线（每个角度一条）补缺值，再去掉两端的边缘尖峰。
    """

    # 应力恰好等于这个值的点当无效值，和缺失值一起补
    INVALID_STRESS = 4000.0
    # 接触区两端各留出接触长度的这一比例作边缘区：主体峰值在边缘区以内找，免得把边缘尖峰当成峰值；
    # 凹口落在边缘区里才处理，主体数据不动
    EDGE_RATIO = 0.1
    # 拟合弧线用凹口内侧的点数
    FIT_POINTS = 5

    def process(
        self,
        columns: list[RollerColumn],
        on_progress: ProgressCallback = None,
    ) -> None:
        """
        对所有 RollerColumn 执行去峰处理。

        处理结果写入 StressData.processed 字段。

        Parameters
        ----------
        columns : list[RollerColumn]
            待处理的数据列表。
        on_progress : ProgressCallback
            进度回调 (current, total)。
        """
        total = len(columns)
        for i, col in enumerate(columns):
            # 跳过已处理的（如 Excel 加载的数据）
            if col.inner_stress.is_processed and col.outer_stress.is_processed:
                continue
            col.inner_stress.processed = self._remove_peaks(col.inner_stress.origin)
            col.outer_stress.processed = self._remove_peaks(col.outer_stress.origin)
            if on_progress:
                on_progress(i + 1, total)

    def _remove_peaks(self, df: pd.DataFrame) -> pd.DataFrame:
        """逐条曲线补缺值、去边缘尖峰。

        Args:
            df: 原始接触应力，多层索引（角位置, 沿滚子距离），同一角度内按距离升序。

        Returns:
            处理后的接触应力，只保留「接触应力 (MPa)」一列，索引同输入。
        """
        df = df[["接触应力 (MPa)"]].astype(float)
        curves = df.groupby(level=0, sort=False)["接触应力 (MPa)"]
        df["接触应力 (MPa)"] = curves.transform(self._process_curve)
        return df

    @classmethod
    def _process_curve(cls, curve: pd.Series) -> np.ndarray:
        """处理一个角度的应力曲线：先补缺值，再去两端的边缘尖峰。"""
        x = curve.index.get_level_values(1).astype(float).to_numpy()
        y = cls._fill_invalid(x, curve.to_numpy(dtype=float))
        return cls._smooth_edges(x, y)

    @classmethod
    def _fill_invalid(cls, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """缺失值和无效值在本角度内按沿滚子距离线性插值补上。

        两头缺的取最近的有效值；整条都没有有效值时原样返回。

        Args:
            x: 沿滚子距离（mm），升序。
            y: 接触应力（MPa）。

        Returns:
            补好的接触应力。
        """
        bad = np.isnan(y) | (y == cls.INVALID_STRESS)
        if not bad.any() or bad.all():
            return y
        y = y.copy()
        y[bad] = np.interp(x[bad], x[~bad], y[~bad])
        return y

    @classmethod
    def _smooth_edges(cls, x: np.ndarray, y: np.ndarray) -> np.ndarray:
        """把一条应力曲线两端的边缘尖峰换成弧线的延长线，处理后只剩一个峰。

        滚子沿长度的接触应力应是一条单峰的弧。受载大的角度上，Romax 结果在接触端 2 mm 左右以内常有边缘效应：
        弧线先压平出个凹口，再冲出尖峰（可能比主体峰值还高），然后落到 0。

        Args:
            x: 沿滚子距离（mm），升序。
            y: 接触应力（MPa）。

        Returns:
            处理后的接触应力；没有边缘尖峰时和 y 相同。
        """
        y = y.copy()
        contact = np.flatnonzero(y > 0)
        if contact.size == 0:
            return y
        first, last = int(contact[0]), int(contact[-1])
        margin = cls.EDGE_RATIO * (x[last] - x[first])
        body = np.flatnonzero((x >= x[first] + margin) & (x <= x[last] - margin))
        if body.size == 0:
            return y
        peak = int(body[np.argmax(y[body])])
        cls._smooth_edge(x, y, peak, last, 1, body)
        cls._smooth_edge(x, y, peak, first, -1, body)
        return y

    @classmethod
    def _smooth_edge(
        cls, x: np.ndarray, y: np.ndarray, peak: int, end: int, step: int, body: np.ndarray
    ) -> None:
        """处理峰值往一端的这一侧，原地修改 y。

        从峰值往外走，应力应一路下降：第一次升高之前的最低点是凹口，凹口往外比它高的点是尖峰。
        凹口在主体里不算边缘效应，不处理。用凹口内侧的点按沿滚子距离拟合二次曲线并向外延长，
        替换凹口到尖峰这一段，且往外只降不升；尖峰外侧是接触端的落差点和 0，保持原样，接触长度不变。
        按真实距离拟合是因为 Romax 在接触端切片很密，按点的序号均分会把延长线画成一道悬崖。

        Args:
            x: 沿滚子距离（mm），升序。
            y: 接触应力（MPa），原地修改。
            peak: 主体峰值的下标。
            end: 这一侧最外一个接触点（应力大于 0）的下标。
            step: 往外走的方向，右侧 1，左侧 -1。
            body: 主体（两端边缘区以内）的下标。
        """
        rise = next((i for i in range(peak + step, end + step, step) if y[i] > y[i - step]), None)
        if rise is None:
            return
        valley = rise - step
        if valley in body:
            return
        outward = np.arange(valley, end + step, step)
        spike_end = int(outward[y[outward] > y[valley]][-1])

        # 延长线从凹口内侧最近的点接上，拟合点不越过峰值
        anchor = valley - step
        fit = np.arange(anchor, anchor - step * cls.FIT_POINTS, -step)
        fit = fit[(fit - peak) * step >= 0]
        if fit.size < 3:
            return
        coef = np.polyfit(x[fit], y[fit], 2)
        if coef[0] > 0:
            # 拟合出来下凸，不成弧，改用最靠近凹口的三个点连直线
            coef = np.r_[0.0, np.polyfit(x[fit[:3]], y[fit[:3]], 1)]
        offset = y[anchor] - np.polyval(coef, x[anchor])

        level = y[anchor]
        for i in range(valley, spike_end + step, step):
            level = max(min(np.polyval(coef, x[i]) + offset, level), 0.0)
            y[i] = level
        for i in range(spike_end + step, end + step, step):
            y[i] = min(y[i], y[i - step])
