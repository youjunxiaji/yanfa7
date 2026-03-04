"""边缘应力 Pydantic 序列化模型（对应 Django DRF 的 Serializer）"""

from pydantic import BaseModel


class ReportConfigSerializer(BaseModel):
    """报告配置"""
    picWidth: float = 8.0
    picHeight: float = 6.0
    loadPolarMin: float = 0.0
    pressPolarMin: float = 0.0


class ParseRequestSerializer(BaseModel):
    """解析请求"""
    filePaths: list[str]
    fileType: str = "htm"
    peakThreshold: float = 10.0
    outputDir: str
    reportConfig: ReportConfigSerializer = ReportConfigSerializer()


class ProgressResponseSerializer(BaseModel):
    """进度推送"""
    type: str = "progress"
    current: int
    total: int
    filename: str


class PreviewItemSerializer(BaseModel):
    """预览图项"""
    colIndex: int
    path: str


class DoneResponseSerializer(BaseModel):
    """完成响应"""
    type: str = "done"
    fileNames: list[str]
    columns: dict[str, list[int]]
    generatedFiles: list[str]
    previewMap: dict[str, list[PreviewItemSerializer]]


class ErrorResponseSerializer(BaseModel):
    """错误响应"""
    type: str = "error"
    message: str


class UpdateStressPointRequest(BaseModel):
    """单点应力修改请求"""
    file_stem: str
    col_index: int
    position: str  # "inner" | "outer"
    trace_index: int
    point_index: int
    new_value: float


class RegeneratePolarRequest(BaseModel):
    """雷达图重新生成请求"""
    file_stem: str
    col_index: int
    load_polar_min: float = 0.0
    press_polar_min: float = 0.0
