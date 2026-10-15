"""齿轮载荷接口：计算、导出 Excel，查和存网页版的历史记录

照搬网页版（tmb_web_v1 的 shanghai_yanfa7/views.py 里 GearCalculationView 这几个），算法在
module/cal_gearLoads.py。网页版在浏览器里生成 Excel 下载，这边由前端选好保存位置，后端写文件。
历史记录还存在 TMB 服务器上，经 common/tmb_web.py 转发。
"""

import os
from typing import Annotated

from fastapi import Header, HTTPException
from loguru import logger

from app_gearLoad.module.cal_gearLoads import CalGearLoads
from app_gearLoad.module.workbook import write_workbook
from app_gearLoad.serializers import (
    CalculateRequest,
    ExportRequest,
    ExportResponse,
    HistoryDetail,
    HistoryItem,
    HistorySaveRequest,
    HistorySaveResponse,
    StageResult,
)
from common import tmb_web

#: 网页版齿轮计算历史的接口：查和存是同一个地址，取一条在后面接 `<id>/detail/`
TMB_HISTORIES = "/shanghai_yanfa7/gearCalculation/history/"


async def calculate(req: CalculateRequest) -> dict[str, StageResult]:
    """有几列 16 行都填了，就算 Stage I 起的前几级；下一级的扭矩、转速取上一级的输出。"""
    return CalGearLoads(req.input_frame()).cal()


async def export_excel(req: ExportRequest) -> ExportResponse:
    """多工况逐个算，每级一张表写进 xlsx。"""
    if not req.selectedData:
        raise HTTPException(status_code=400, detail="请先编辑多工况：导出按其中每一组扭矩、转速算")
    tables = CalGearLoads(req.input_frame(), req.condition_frame()).getExportData()
    if not tables:
        raise HTTPException(status_code=400, detail="Stage I 还有参数没填，没有能导出的结果")
    try:
        write_workbook(tables, req.path)
    except PermissionError as e:
        name = os.path.basename(req.path)
        raise HTTPException(status_code=400, detail=f"{name} 正被其他程序占用，请关闭后重试") from e
    except OSError as e:
        raise HTTPException(status_code=400, detail=f"保存 Excel 失败：{e}") from e
    logger.info(f"已导出齿轮载荷：{req.path}")
    return ExportResponse(path=req.path)


async def histories(
    query: str = "", authorization: Annotated[str | None, Header()] = None
) -> list[HistoryItem]:
    """查网页版的齿轮计算历史：只给自己存的，齿轮单元、风机、载荷谱任一项模糊匹配，新存的在前，不限条数。"""
    token = tmb_web.bearer_token(authorization)
    data = await tmb_web.request("GET", TMB_HISTORIES, token=token, params={"query": query})
    return [HistoryItem.model_validate(item) for item in data["results"]]


async def history(
    record_id: int, authorization: Annotated[str | None, Header()] = None
) -> HistoryDetail:
    """取一条历史记录回填页面。"""
    token = tmb_web.bearer_token(authorization)
    record = await tmb_web.request("GET", f"{TMB_HISTORIES}{record_id}/detail/", token=token)
    return HistoryDetail.from_tmb(record)


async def save_history(
    req: HistorySaveRequest, authorization: Annotated[str | None, Header()] = None
) -> HistorySaveResponse:
    """把页面现在的输入存成网页版的一条历史记录，网页版和这边都查得到。

    网页版按「登录的人 + 齿轮单元 + 风机 + 载荷谱」存：没存过就新建，存过就把输入表和多工况整个换成这次的。
    """
    token = tmb_web.bearer_token(authorization)
    form = req.formData
    if not (form.gearUnit and form.windTurbine and form.loadSpectrum):
        raise HTTPException(status_code=400, detail="请填写完整的基本信息")
    data = await tmb_web.request("POST", TMB_HISTORIES, token=token, json=req.model_dump())
    created = bool(data.get("created"))
    logger.info(f"已{'新建' if created else '覆盖'}齿轮载荷历史记录：{req.label}")
    return HistorySaveResponse(created=created)
