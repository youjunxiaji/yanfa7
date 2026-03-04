from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pandas as pd


# ============================================================
# 枚举
# ============================================================

class FileType(Enum):
    """输入文件类型"""
    HTM = "htm"
    EXCEL = "xlsx"


class StressPosition(Enum):
    """应力位置（内圈/外圈）"""
    INNER = "内滚道接触应力"
    OUTER = "外滚道接触应力"


# ============================================================
# 数据模型
# ============================================================

@dataclass
class StressData:
    """
    单列滚子的应力数据（内圈或外圈）。

    Attributes
    ----------
    origin : pd.DataFrame
        原始接触应力，多层索引 (角度位置, 沿滚子距离)，列为 "接触应力 (MPa)"。
    processed : pd.DataFrame | None
        去峰后的接触应力，结构同 origin。未处理时为 None。
    """
    origin: pd.DataFrame
    processed: pd.DataFrame | None = None

    @property
    def is_processed(self) -> bool:
        """是否已完成去峰处理"""
        return self.processed is not None

    @property
    def level_unique(self) -> list:
        """获取角度位置列表（level_0 的唯一值）"""
        df = self.processed if self.processed is not None else self.origin
        return list(df.index.get_level_values(0).unique())


@dataclass
class RollerColumn:
    """
    单个文件中单列滚子的完整数据。

    一个轴承文件可能包含多列滚子，每列滚子有内圈应力、外圈应力和载荷分布。

    Attributes
    ----------
    filename : str
        来源文件名（不含扩展名）。
    col_index : int
        列号（从 1 开始）。
    inner_stress : StressData
        内圈接触应力数据。
    outer_stress : StressData
        外圈接触应力数据。
    load_distribution : pd.DataFrame | None
        载荷分布数据（用于雷达图），索引为角度，列为载荷/应力值。
    """
    filename: str
    col_index: int
    inner_stress: StressData
    outer_stress: StressData
    load_distribution: pd.DataFrame | None = None

    def get_stress(self, position: StressPosition) -> StressData:
        """根据位置获取对应的应力数据"""
        if position == StressPosition.INNER:
            return self.inner_stress
        return self.outer_stress

    def get_max_stress(self, position: StressPosition) -> float:
        """获取指定位置的最大应力值"""
        stress = self.get_stress(position)
        df = stress.processed if stress.processed is not None else stress.origin
        return float(df.max().iloc[0])

    def get_min_stress(self, position: StressPosition) -> float:
        """获取指定位置的最小应力值"""
        stress = self.get_stress(position)
        df = stress.processed if stress.processed is not None else stress.origin
        return float(df.min().iloc[0])


# ============================================================
# 配置
# ============================================================

@dataclass
class ProcessConfig:
    """
    数据处理配置。

    Attributes
    ----------
    peak_threshold : float
        峰值去除阈值，用于 scipy.signal.find_peaks 的 threshold 参数。
        值越大，去除的峰越少。默认 10.0。
    """
    peak_threshold: float = 10.0


@dataclass
class ReportConfig:
    """
    报告生成配置。

    Attributes
    ----------
    pic_width : float
        图片宽度（英寸），默认 8.0。
    pic_height : float
        图片高度（英寸），默认 6.0。
    load_polar_min : float
        载荷雷达图径向最小值，默认 0.0。
    press_polar_min : float
        应力雷达图径向最小值，默认 0.0。
    """
    pic_width: float = 8.0
    pic_height: float = 6.0
    load_polar_min: float = 0.0
    press_polar_min: float = 0.0


@dataclass
class InputConfig:
    """
    输入配置。

    Attributes
    ----------
    files : list[Path]
        待处理的文件路径列表。
    file_type : FileType
        文件类型 (HTM / EXCEL)。
    output_dir : Path
        输出目录路径。
    """
    files: list[Path] = field(default_factory=list)
    file_type: FileType = FileType.HTM
    output_dir: Path = field(default_factory=lambda: Path.home() / "Desktop")

    def validate(self) -> list[str]:
        """
        校验输入配置，返回错误信息列表。空列表表示通过。
        """
        errors: list[str] = []
        if not self.files:
            errors.append("未指定输入文件")
        for f in self.files:
            if not f.exists():
                errors.append(f"文件不存在: {f}")
            elif f.suffix.lstrip(".") != self.file_type.value:
                errors.append(
                    f"文件类型不匹配: {f.name} (期望 .{self.file_type.value})"
                )
        if not self.output_dir.exists():
            errors.append(f"输出目录不存在: {self.output_dir}")
        return errors


# ============================================================
# 数据集
# ============================================================

@dataclass
class EdgeStressDataset:
    """
    边缘应力数据集 — 整个分析流程的核心数据容器。

    职责：
    - 持有所有配置 (input / process / report)
    - 持有解析后的标准化数据 (columns)
    - 提供查询和汇总接口

    Attributes
    ----------
    process_config : ProcessConfig
        处理配置。
    input_config : InputConfig
        输入配置。
    report_config : ReportConfig
        报告配置。
    columns : list[RollerColumn]
        所有文件所有列的滚子数据。
    """
    process_config: ProcessConfig = field(default_factory=ProcessConfig)
    input_config: InputConfig = field(default_factory=InputConfig)
    report_config: ReportConfig = field(default_factory=ReportConfig)
    columns: list[RollerColumn] = field(default_factory=list)

    # ----- 查询 -----

    @property
    def filenames(self) -> list[str]:
        """获取所有文件名（去重、排序）"""
        return sorted(set(c.filename for c in self.columns))

    def get_columns_by_file(self, filename: str) -> list[RollerColumn]:
        """获取指定文件名下的所有列"""
        return [c for c in self.columns if c.filename == filename]

    def get_column(self, filename: str, col_index: int) -> RollerColumn | None:
        """获取指定文件名、指定列号的 RollerColumn"""
        for c in self.columns:
            if c.filename == filename and c.col_index == col_index:
                return c
        return None

    # ----- 汇总 -----

    def get_max_summary(self) -> pd.DataFrame:
        """
        获取所有文件所有列的最大应力汇总表。

        Returns
        -------
        pd.DataFrame
            索引为 (文件名, 应力位置)，列为各列的列号和最大应力值。
        """
        rows: list[dict] = []
        for filename in self.filenames:
            file_columns = self.get_columns_by_file(filename)
            for position in StressPosition:
                row: dict = {"文件名": filename, "应力位置": position.value}
                for rc in file_columns:
                    row[f"列{rc.col_index}"] = rc.get_max_stress(position)
                rows.append(row)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df.set_index(["文件名", "应力位置"], inplace=True)
        return df

    # ----- 状态 -----

    @property
    def is_loaded(self) -> bool:
        """数据是否已加载"""
        return len(self.columns) > 0

    @property
    def is_processed(self) -> bool:
        """数据是否已全部完成去峰处理"""
        return self.is_loaded and all(
            c.inner_stress.is_processed and c.outer_stress.is_processed
            for c in self.columns
        )

    def __repr__(self) -> str:
        return (
            f"EdgeStressDataset("
            f"files={len(self.input_config.files)}, "
            f"columns={len(self.columns)}, "
            f"loaded={self.is_loaded}, "
            f"processed={self.is_processed})"
        )
