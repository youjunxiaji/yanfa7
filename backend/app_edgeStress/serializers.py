"""边缘应力 Pydantic 序列化模型（对应 Django DRF 的 Serializer）"""

from pydantic import BaseModel


class ReportConfigSerializer(BaseModel):
    """报告配置（默认值由前端维护）"""
    picWidth: float
    picHeight: float
    loadPolarMin: float = 0.0
    pressPolarMin: float = 0.0


class ParseRequestSerializer(BaseModel):
    """解析请求"""
    filePaths: list[str]
    fileType: str = "htm"
    peakThreshold: float = 10.0
    outputDir: str
    reportConfig: ReportConfigSerializer


class ProgressResponseSerializer(BaseModel):
    """进度推送：开始处理第 current 个文件"""
    type: str = "progress"
    current: int
    total: int
    filename: str


class PreviewItemSerializer(BaseModel):
    """预览图项"""
    colIndex: int
    path: str


class FileDoneResponseSerializer(BaseModel):
    """单个文件处理完：解析出的列号和每列的缩略图；index 是文件在 filePaths 里的下标"""
    type: str = "fileDone"
    index: int
    columns: list[int]
    previewItems: list[PreviewItemSerializer]


class FileSkippedResponseSerializer(BaseModel):
    """单个文件没能解析，跳过；index 同上"""
    type: str = "fileSkipped"
    index: int
    reason: str


class DoneResponseSerializer(BaseModel):
    """完成响应"""
    type: str = "done"
    generatedFiles: list[str]


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
