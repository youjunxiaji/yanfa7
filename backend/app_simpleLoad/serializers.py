"""载荷简化 Pydantic 序列化模型：预览、加载、缩减的请求，WebSocket 推送的报文，以及历史记录的查和存

字段名用 camelCase，和前端 `api/simpleLoad.ts` 一致。请求模型负责换成计算层收的 dataclass
（PathConfig、ConversionConfig、AxisMapping），`cal_simpleLoad` 不依赖 Pydantic。
"""

import math
from itertools import count
from typing import Any, ClassVar, Literal, Self

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

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


class HistoryConfig(BaseModel):
    """一套载荷简化配置：从历史记录查回来回填的、存成历史记录的都是它

    TMB 服务器上存的是网页版页面的写法（tmb_web_v1 的 `SimpleLoadCalculationHistoryModel`）：列对应是带
    「占位符」的列名列表，区间表一行一个分量、11 格里数字和字符串都有。查的时候 `HistoryRecord.from_tmb`
    换过来，存的时候 `HistorySaveRequest.to_tmb` 换回去，网页版照样能回填这边存的。
    """

    INTERVAL_SLOTS: ClassVar[int] = 11  # 区间表每行：下界、9 个分段点、上界

    loadDir: str
    freqTablePath: str
    outputDir: str
    skipRows: int
    columns: list[LoadColumn | None]  # txt 每一列是什么，None 是不用的列（网页版的「占位符」）
    unitForce: float
    unitMoment: float
    unitSpeed: float
    axisMapping: list[AxisMappingPayload]
    keepTorque: bool
    slope: float  # 网页版叫转换系数（translate_factor）
    temperature: float
    tol: float
    intervals: dict[LoadColumn, list[float | None]]  # 分量 → 11 格，没填的是 None


class HistoryRecord(HistoryConfig):
    """TMB 服务器上存的一条载荷简化配置，换成这边的字段，前端拿到直接回填。缺的字段按网页版的默认值补。"""

    DEFAULT_AXIS_MAPPING: ClassVar[list[dict[str, str]]] = [
        {"romax": "x", "origin": "-y"},
        {"romax": "y", "origin": "-z"},
        {"romax": "z", "origin": "x"},
    ]

    projName: str  # 保存时取输出目录的最后一级

    @classmethod
    def from_tmb(cls, record: dict[str, Any]) -> Self:
        """把 TMB 服务器返回的一条记录换成回填用的字段。

        Args:
            record: tmb_web_v1 的 `SimpleLoadCalculationHistorySerializer` 给的一条记录。

        Returns:
            回填用的配置。
        """
        paths = record.get("file_path_json") or {}
        factors = record.get("conversion_factors_json") or {}
        title_row = cls.number(factors.get("title_row"))
        return cls(
            projName=record.get("proj_name") or "",
            loadDir=paths.get("load_file_folder_path") or "",
            freqTablePath=paths.get("freq_table_path") or "",
            outputDir=paths.get("result_folder_save_path") or "",
            # 网页版存的是标题行的行号，它和它前面的行都跳过；没有标题行时是 None
            skipRows=int(title_row) + 1 if title_row is not None and title_row >= 0 else 0,
            columns=[cls.column(item) for item in record.get("draggable_elements_json") or []],
            unitForce=cls.number_or(factors.get("unit_force"), 1000),
            unitMoment=cls.number_or(factors.get("unit_moment"), 1000),
            unitSpeed=cls.number_or(factors.get("unit_speed"), 1),
            axisMapping=cls.axis_mapping(record.get("romax_origin_json")),
            keepTorque=bool(paths.get("keep_torque_component", False)),
            slope=cls.number_or(factors.get("translate_factor"), 4.05),
            temperature=cls.number_or(factors.get("temperature"), 60),
            tol=cls.number_or(factors.get("tol"), 1e-4),
            intervals=cls.interval_rows(record.get("table_data_json")),
        )

    @staticmethod
    def number(value: Any) -> float | None:
        """网页版的数值有数字也有字符串（区间表的格子），空串和认不出的当作没填。"""
        if isinstance(value, bool):
            return None
        if isinstance(value, str):
            try:
                value = float(value.strip())
            except ValueError:
                return None
        if isinstance(value, int | float) and math.isfinite(value):
            return float(value)
        return None

    @classmethod
    def number_or(cls, value: Any, default: float) -> float:
        """没填时用网页版的默认值；填了 0 就是 0。"""
        number = cls.number(value)
        return default if number is None else number

    @staticmethod
    def column(item: Any) -> LoadColumn | None:
        """列名换成分量；「占位符」和认不出的列名是不用的列。"""
        name = item.get("name") if isinstance(item, dict) else item
        try:
            return LoadColumn(name)
        except ValueError:
            return None

    @classmethod
    def axis_mapping(cls, value: Any) -> list[AxisMappingPayload]:
        """坐标映射要依次是 Romax 的 x、y、z，对不上就用网页版的默认映射。"""
        try:
            mapping = [AxisMappingPayload.model_validate(item) for item in value]
        except (TypeError, ValidationError):
            mapping = []
        if [item.romax for item in mapping] != ["x", "y", "z"]:
            mapping = [AxisMappingPayload.model_validate(item) for item in cls.DEFAULT_AXIS_MAPPING]
        return mapping

    @classmethod
    def interval_rows(cls, rows: Any) -> dict[LoadColumn, list[float | None]]:
        """区间表按分量名取，每行 11 格；不是力或力矩的行跳过。"""
        intervals: dict[LoadColumn, list[float | None]] = {}
        for row in rows if isinstance(rows, list) else []:
            component = cls.column(row.get("component")) if isinstance(row, dict) else None
            if component is None or component in (LoadColumn.TIME, LoadColumn.SPEED):
                continue
            intervals[component] = [cls.number(row.get(str(i))) for i in range(cls.INTERVAL_SLOTS)]
        return intervals


class HistorySaveRequest(HistoryConfig):
    """POST /api/simple-load/histories：把现在的配置存成网页版的一条历史记录

    网页版的规则不改，照着用：按「登录的人 + 项目名」存，项目名是输出目录的最后一级，没存过就新建，
    存过同名的就整条覆盖。区间表前端只给参与分组的分量，和网页版存的一样。
    """

    PLACEHOLDER: ClassVar[str] = "占位符"  # 网页版不用的列叫「占位符1」「占位符2」……

    @field_validator("outputDir")
    @classmethod
    def strip_trailing_separator(cls, value: str) -> str:
        """去掉首尾空白和末尾的斜杠：网页版取最后一段当项目名，末尾带斜杠就取成了空串。"""
        return value.strip().rstrip("\\/")

    @property
    def proj_name(self) -> str:
        """网页版存的项目名，和 tmb_web_v1 一样取输出目录的最后一段。"""
        return self.outputDir.replace("\\", "/").split("/")[-1]

    def to_tmb(self) -> dict[str, Any]:
        """换成网页版「存储」发的报文。

        Returns:
            tmb_web_v1 的 `SimpleLoadCalculationHistoryView.post` 收的五块：路径、列对应、转换系数、坐标映射、区间表。
        """
        placeholders = count(1)
        return {
            "file_path": {
                "result_folder_save_path": self.outputDir,
                "load_file_folder_path": self.loadDir,
                "freq_table_path": self.freqTablePath,
                "keep_torque_component": self.keepTorque,
            },
            "draggable_elements": [
                {"name": column.value if column is not None else f"{self.PLACEHOLDER}{next(placeholders)}"}
                for column in self.columns
            ],
            "conversion_factors": {
                "unit_moment": self.unitMoment,
                "unit_force": self.unitForce,
                "unit_speed": self.unitSpeed,
                # 网页版存标题行的行号：跳过的最后一行是标题行，一行都不跳就是没有标题行
                "title_row": self.skipRows - 1 if self.skipRows > 0 else None,
                "temperature": self.temperature,
                "translate_factor": self.slope,
                "tol": self.tol,
            },
            "romax_origin": [mapping.model_dump() for mapping in self.axisMapping],
            # 行的顺序同网页版：Fx、Fy、Fz、Mx、My、Mz
            "table_data": [
                {"component": column.value, **self.interval_cells(self.intervals[column])}
                for column in LoadColumn
                if column in self.intervals
            ],
        }

    @classmethod
    def interval_cells(cls, edges: list[float | None]) -> dict[str, float | str]:
        """一行区间按「列序号: 值」排开，补齐 11 格，没填的写空串，和网页版的空格子一样。"""
        cells = (edges + [None] * cls.INTERVAL_SLOTS)[: cls.INTERVAL_SLOTS]
        return {str(index): "" if edge is None else edge for index, edge in enumerate(cells)}


class HistorySaveResponse(BaseModel):
    """存好了：存成的项目名，同一个人同名的记录只留这一条"""

    projName: str
