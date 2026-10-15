"""齿轮载荷 Pydantic 序列化模型：计算、导出 Excel 的请求，以及网页版历史记录的查和存

页面照搬网页版（tmb_web_v1 的 gearLoadsView.vue），数据也沿用网页版的写法：输入表一行一个参数，`parameter`
是英文参数名，4 级的值是输入框里的字符串，`CalGearLoads` 按参数名取值；多工况一行一组扭矩、转速。
历史记录存的就是这两张表，网页版和这边存的互相能回填。
"""

from typing import Any, Self

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class InputRow(BaseModel):
    """输入表的一行：参数名和 4 级的值，同网页版的 inputData

    空串是没填。网页版历史记录里的值都是字符串，万一有数字、null，也换成字符串、空串。
    """

    model_config = ConfigDict(coerce_numbers_to_str=True)

    parameter: str
    stageI: str = ""
    stageII: str = ""
    stageIII: str = ""
    stageIIII: str = ""
    editable: bool = False  # 网页版页面用的标记，CalGearLoads 算之前会丢掉

    @field_validator("stageI", "stageII", "stageIII", "stageIIII", mode="before")
    @classmethod
    def blank_if_none(cls, value: Any) -> Any:
        return "" if value is None else value


class ConditionRow(BaseModel):
    """多工况的一行：扭矩 T (kNm)、转速 n (rpm)，同网页版的 selectedData"""

    model_config = ConfigDict(coerce_numbers_to_str=True)

    torque: str = ""
    rpm: str = ""


class CalculateRequest(BaseModel):
    """POST /api/gear-load/calculate"""

    inputData: list[InputRow] = Field(min_length=1)

    def input_frame(self) -> pd.DataFrame:
        """换成 `CalGearLoads` 收的输入表：行是参数名，列是 4 级。"""
        return pd.DataFrame([row.model_dump() for row in self.inputData]).set_index("parameter")


class ExportRequest(CalculateRequest):
    """POST /api/gear-load/export：多工况逐个算，写到 `path`"""

    selectedData: list[ConditionRow]
    path: str = Field(min_length=1)

    def condition_frame(self) -> pd.DataFrame:
        """换成 `getExportData` 收的多工况表。

        `getExportData` 算第一级时按位置取：第 0 列当转速、第 1 列当扭矩，所以列顺序在这里定死。网页版直接拿请求里的
        字典建表，列顺序跟着键的顺序走，新录入的工况扭矩在前，导出的扭矩、转速就对调了。
        """
        return pd.DataFrame(
            [[row.rpm, row.torque] for row in self.selectedData], columns=["rpm", "torque"]
        )


# 结果里的一格：数值（已四舍五入到 3 位小数），算不出来是空串，除以 0 是 "Infinity" / "-Infinity"
StageValue = float | str


class StageResult(BaseModel):
    """一级的计算结果，各列表的顺序同网页版的结果表"""

    input_data: list[StageValue]  # 功率、输出扭矩、输出转速，前端填到下一级的输入
    gear_loads: list[StageValue]  # 齿轮载荷 9 项
    speed_of_components: list[StageValue]  # 部件转速 3 项
    equivalent_diameter: list[StageValue]  # 等效直径 3 项


class ExportResponse(BaseModel):
    path: str


class HistoryItem(BaseModel):
    """历史记录列表的一条：网页版的记录 id 和「齿轮单元/风机/载荷谱」"""

    id: int
    label: str


class HistoryForm(BaseModel):
    """基础设置：网页版按「登录的人 + 这三项」存历史记录"""

    gearUnit: str = ""
    windTurbine: str = ""
    loadSpectrum: str = ""


class HistoryDetail(BaseModel):
    """一条历史记录，回填页面用；网页版的记录里输入表、多工况可能是空的"""

    formData: HistoryForm
    inputData: list[InputRow] | None
    selectedData: list[ConditionRow] | None

    @classmethod
    def from_tmb(cls, record: dict[str, Any]) -> Self:
        """把网页版的一条记录（tmb_web_v1 的 `GearCalculationHistorySerializer`）换成回填用的字段。

        Args:
            record: 网页版历史详情接口给的记录。

        Returns:
            回填用的基础设置、输入表和多工况。
        """
        return cls(
            formData=HistoryForm(
                gearUnit=record.get("gear_unit") or "",
                windTurbine=record.get("wind_turbine") or "",
                loadSpectrum=record.get("load_spectrum") or "",
            ),
            inputData=record.get("vars_json"),
            selectedData=record.get("selected_data_json"),
        )


class HistorySaveRequest(BaseModel):
    """POST /api/gear-load/histories：报文同网页版 Ctrl+S 发的，原样转给网页版"""

    formData: HistoryForm
    inputData: list[InputRow]
    selectedData: list[ConditionRow]

    @property
    def label(self) -> str:
        """网页版历史记录列表里显示的名字。"""
        form = self.formData
        return f"{form.gearUnit}/{form.windTurbine}/{form.loadSpectrum}"


class HistorySaveResponse(BaseModel):
    """存好了：新建了一条，还是覆盖了自己存过的同名记录"""

    created: bool
