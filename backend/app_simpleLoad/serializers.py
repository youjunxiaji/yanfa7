"""载荷简化 Pydantic 序列化模型：预览、加载、缩减的请求，以及 WebSocket 推送的报文

字段名用 camelCase，和前端 `api/simpleLoad.ts` 一致。请求模型负责换成计算层收的 dataclass
（PathConfig、ConversionConfig、AxisMapping），`cal_simpleLoad` 不依赖 Pydantic。
"""

from typing import ClassVar, Literal, Self

from pydantic import BaseModel, Field, model_validator

from app_simpleLoad.module.config import AxisMapping, ConversionConfig, PathConfig
from common.constants import LoadColumn


class PreviewRequest(BaseModel):
    """POST /api/simple-load/preview"""

    loadDir: str = Field(min_length=1)


class PreviewResponse(BaseModel):
    """载荷文件夹里 txt 的个数和总大小，以及第一个 txt 开头几行的原文（空行不算）"""

    fileCount: int
    totalSize: int
    sampleFile: str  # 第一个 txt 相对载荷文件夹的路径
    lines: list[str]


class LoadRequest(BaseModel):
    """WS /ws/simple-load/load：连上后发的第一条消息"""

    REQUIRED_COLUMNS: ClassVar[tuple[LoadColumn, ...]] = (
        LoadColumn.SPEED,
        LoadColumn.FX,
        LoadColumn.FY,
        LoadColumn.FZ,
        LoadColumn.MX,
        LoadColumn.MY,
        LoadColumn.MZ,
    )

    loadDir: str = Field(min_length=1)
    freqTablePath: str = Field(min_length=1)
    columns: list[LoadColumn | None] = Field(min_length=1)  # txt 每一列是什么，None 是不用的列
    skipRows: int = Field(ge=0)  # 数据行前面跳过几行（列名、END_OF_HEADER 这类）
    unitForce: float = Field(gt=0)  # 力除以它换成 KN
    unitMoment: float = Field(gt=0)  # 力矩除以它换成 KNm
    unitSpeed: float = Field(gt=0)  # 转速乘以它换成 rpm

    @model_validator(mode="after")
    def check_columns(self) -> Self:
        """每个分量最多对一列，转速和六个力 / 力矩必须有，Time 可以没有。"""
        used = [column for column in self.columns if column is not None]
        repeated = [column.value for column in LoadColumn if used.count(column) > 1]
        if repeated:
            raise ValueError(f"列对应里 {'、'.join(repeated)} 选了不止一列")
        missing = [column.value for column in self.REQUIRED_COLUMNS if column not in used]
        if missing:
            raise ValueError(f"列对应缺少 {'、'.join(missing)}")
        return self

    @property
    def header(self) -> list[str]:
        """按 txt 列顺序展开的列名，直接喂给 `CalSimpleLoad.setInit`。

        不用的列起「占位符」开头的名字，读文件时跳过。
        """
        return [
            column.value if column is not None else f"占位符{index}"
            for index, column in enumerate(self.columns)
        ]

    def path_config(self) -> PathConfig:
        """加载只用到载荷文件夹和频次表，结果目录等缩减时再给。"""
        return PathConfig(
            result_folder_save_path="",
            load_file_folder_path=self.loadDir,
            freq_table_path=self.freqTablePath,
        )

    def conversion_config(self) -> ConversionConfig:
        """`title_row` 是标题行的行号：跳过的最后一行当标题行，一行都不跳就是没有标题行。

        S-N 斜率、温度、占比阈值只有缩减用得到，随缩减请求给。
        """
        return ConversionConfig(
            title_row=self.skipRows - 1 if self.skipRows > 0 else None,
            unit_moment=self.unitMoment,
            unit_force=self.unitForce,
            unit_speed=self.unitSpeed,
        )


class AxisMappingPayload(BaseModel):
    """Romax 的轴取载荷文件里的哪个轴，origin 带负号表示取反"""

    romax: Literal["x", "y", "z"]
    origin: Literal["x", "y", "z", "-x", "-y", "-z"]


class ReduceRequest(BaseModel):
    """WS /ws/simple-load/reduce：连上后发的第一条消息"""

    intervals: dict[LoadColumn, list[float]] = Field(min_length=1)  # 参与分组的分量 → 区间边界
    axisMapping: list[AxisMappingPayload]  # 依次是 Romax 的 x、y、z
    keepTorque: bool = False  # 绕 Romax z 轴的力矩也参与分组
    slope: float = Field(gt=0)  # S-N 曲线斜率，幂等效变换的指数
    temperature: float  # 写进 Romax 的工况表
    tol: float = Field(ge=0)  # 时间占比不超过它的格子丢掉
    outputDir: str = Field(min_length=1)

    @model_validator(mode="after")
    def check_axis_mapping(self) -> Self:
        """Romax 的 x、y、z 依次给出，载荷文件的三个轴各用一次。"""
        if [mapping.romax for mapping in self.axisMapping] != ["x", "y", "z"]:
            raise ValueError("坐标映射要依次给出 Romax 的 x、y、z")
        if len({mapping.origin.lstrip("-") for mapping in self.axisMapping}) != 3:
            raise ValueError("坐标映射里载荷文件的 x、y、z 要各用一次")
        return self

    def table_data(self) -> list[dict[str, str | float]]:
        """换成 `simple_load2` 收的区间表：每行带分量名，边界按「列序号: 值」排开。"""
        return [
            {"component": column.value, **{str(index): edge for index, edge in enumerate(edges)}}
            for column, edges in self.intervals.items()
        ]

    def axis_mappings(self) -> list[AxisMapping]:
        """换成计算层收的 AxisMapping。"""
        return [AxisMapping(romax=item.romax, origin=item.origin) for item in self.axisMapping]


class ComponentStats(BaseModel):
    """一个分量的最值和加权时间占比分布，分布只含占比不小于 1e-4 的柱"""

    component: LoadColumn
    min: float
    max: float
    binLeft: list[float]
    binRight: list[float]
    share: list[float]  # 每根柱的时间占比，0~1


class LoadDoneMessage(BaseModel):
    """加载完成"""

    type: Literal["done"] = "done"
    fileCount: int
    rowCount: int
    components: list[ComponentStats]


class ReduceDoneMessage(BaseModel):
    """缩减完成"""

    type: Literal["done"] = "done"
    cellCount: int  # 有载荷的格子数
    files: list[str]


class ErrorMessage(BaseModel):
    """出错，连接随后关闭"""

    type: Literal["error"] = "error"
    message: str
