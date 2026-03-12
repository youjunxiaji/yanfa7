"""Pmax 时间占比 Pydantic 序列化模型"""

from pydantic import BaseModel

from common.constants import Language


class BinParams(BaseModel):
    min: float
    max: float
    step: float


class BinConfig(BaseModel):
    front: BinParams
    rear: BinParams


class ChartConfig(BaseModel):
    titleFontSize: int = 25
    labelFontSize: int = 20
    tickFontSize: int = 20
    textFontSize: int = 25
    width: int = 20
    height: int = 15


class AnalyzeRequest(BaseModel):
    data: list[list[str]]
    binConfig: BinConfig
    chartConfig: ChartConfig
    language: Language = Language.ZH


class BinItem(BaseModel):
    label: str
    percentage: float


class BearingResult(BaseModel):
    chartPath: str
    bins: list[BinItem]


class AnalyzeResponse(BaseModel):
    front: BearingResult
    rear: BearingResult
