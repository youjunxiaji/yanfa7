"""Pmax 时间占比视图"""

from fastapi import HTTPException

from app_pmax.serializers import AnalyzeRequest, AnalyzeResponse, BearingResult, BinItem
from app_pmax.module.calculator import compute_time_ratio
from app_pmax.module.chart import generate_bar_chart, cleanup_temp_files


async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """接收表格数据 + 参数，生成前/后轴承柱状图和分箱统计。"""
    times_front: list[float] = []
    pmax_front: list[float] = []
    times_rear: list[float] = []
    pmax_rear: list[float] = []

    for row in req.data:
        if len(row) < 4:
            continue
        try:
            tf = float(row[0])
            pf = float(row[1])
            times_front.append(tf)
            pmax_front.append(pf)
        except (ValueError, TypeError):
            pass
        try:
            tr = float(row[2])
            pr = float(row[3])
            times_rear.append(tr)
            pmax_rear.append(pr)
        except (ValueError, TypeError):
            pass

    if not pmax_front and not pmax_rear:
        raise HTTPException(status_code=400, detail="未找到有效的数值数据")

    cleanup_temp_files()
    cc = req.chartConfig

    def _process(times, pmax_vals, bin_params, label):
        bins = compute_time_ratio(times, pmax_vals, bin_params.min, bin_params.max, bin_params.step)
        chart_path = generate_bar_chart(
            bins, label, req.language,
            cc.titleFontSize, cc.labelFontSize, cc.tickFontSize, cc.textFontSize,
            cc.width, cc.height,
        )
        return BearingResult(
            chartPath=chart_path,
            bins=[BinItem(**b) for b in bins],
        )

    front_result = _process(times_front, pmax_front, req.binConfig.front, "前轴承")
    rear_result = _process(times_rear, pmax_rear, req.binConfig.rear, "后轴承")

    return AnalyzeResponse(front=front_result, rear=rear_result)
