"""
边缘应力数据处理器

负责文件解析和数据处理，无 UI 依赖。
核心算法保持与原 calEdgeStress.py 一致。

Author: gu lei
Date: 2026-02-11
"""
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from scipy import signal

from app_edgeStress.module.dataset import (
    FileType,
    InputConfig,
    ProcessConfig,
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
        df_list = pd.read_html(str(file_path), match=pattern)

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

    负责对加载后的原始数据执行去峰处理。
    算法与原 calEdgeStress.MainPro.remove_Peaks 保持一致。
    """

    def __init__(self, config: ProcessConfig):
        self.config = config

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
        """
        去除接触应力中的异常峰值。

        算法步骤:
        1. 提取 "接触应力 (MPa)" 列
        2. 替换 4000 为 NaN 并插值
        3. 使用 scipy.signal.find_peaks 检测异常谷值
        4. 将异常区间设为 NaN 并插值

        Parameters
        ----------
        df : pd.DataFrame
            原始接触应力数据，多层索引。

        Returns
        -------
        pd.DataFrame
            去峰后的接触应力数据。
        """
        df = df[["接触应力 (MPa)"]].copy()

        # 获取角度位置列表
        level1_index = df.index.get_level_values(0)
        level_unique = list(level1_index.unique())

        # 替换 4000 为 NaN 并插值
        df = df.replace(4000, np.nan)
        df = df.interpolate()

        # 逐角度检测并去除异常峰值
        for angle in level_unique:
            # 提取该角度的数据为 numpy 数组（避免链式赋值）
            sub_df = df.loc[angle]
            arr: np.ndarray = sub_df["接触应力 (MPa)"].values.copy()

            valleys, _ = signal.find_peaks(
                -arr,
                threshold=self.config.peak_threshold,
            )
            if len(valleys) == 0:
                continue

            # 逐个异常谷值处理
            mid = len(arr) // 2
            for v in valleys:
                bound = arr[v]
                if v < mid:
                    # 异常点在左侧
                    idx = np.flatnonzero(arr[:v] > bound)
                    if idx.size > 0:
                        if idx[0] > 0 and arr[idx[0] - 1] != 0:
                            idx = np.insert(idx, 0, idx[0] - 1)
                        arr[idx] = np.nan
                elif v > mid:
                    # 异常点在右侧
                    idx = np.flatnonzero(arr[v:] > bound) + v
                    if idx.size > 0:
                        if idx[-1] + 1 < len(arr) and arr[idx[-1] + 1] != 0:
                            idx = np.append(idx, idx[-1] + 1)
                        arr[idx] = np.nan

            # 写回（单次赋值，无链式操作）
            df.loc[angle, "接触应力 (MPa)"] = arr

        return df.interpolate()
