"""Pmax 时间占比视图"""

import pandas as pd
from fastapi import HTTPException

from app_pmax.serializers import AnalyzeRequest, AnalyzeResponse, BearingResult, BinItem, StatsInfo
from app_pmax.module.calculator import compute_time_ratio
from app_pmax.module.chart import generate_bar_chart, cleanup_temp_files


async def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    """接收表格数据 + 参数，生成前/后轴承柱状图和分箱统计。"""
    df = pd.DataFrame(req.data, columns=["time_front", "pmax_front", "time_rear", "pmax_rear"])
    df = df.apply(pd.to_numeric, errors="coerce")

    df_front = df[["time_front", "pmax_front"]].dropna()
    df_rear = df[["time_rear", "pmax_rear"]].dropna()

    if df_front["pmax_front"].empty and df_rear["pmax_rear"].empty:
        raise HTTPException(status_code=400, detail="未找到有效的数值数据")

    cleanup_temp_files()
    cc = req.chartConfig

    def _process(df_bearing: pd.DataFrame, time_col: str, pmax_col: str, bin_params, label: str):
        times = df_bearing[time_col].tolist()
        pmax_vals = df_bearing[pmax_col].tolist()

        bins = compute_time_ratio(times, pmax_vals, bin_params.min, bin_params.max, bin_params.step)
        chart_path = generate_bar_chart(
            bins, label, req.language,
            cc.titleFontSize, cc.labelFontSize, cc.tickFontSize, cc.textFontSize,
            cc.width, cc.height,
        )
        stats = StatsInfo(
            timeMin=float(df_bearing[time_col].min()) if not df_bearing.empty else 0,
            timeMax=float(df_bearing[time_col].max()) if not df_bearing.empty else 0,
            pmaxMin=float(df_bearing[pmax_col].min()) if not df_bearing.empty else 0,
            pmaxMax=float(df_bearing[pmax_col].max()) if not df_bearing.empty else 0,
        )
        return BearingResult(
            chartPath=chart_path,
            bins=[BinItem(**b) for b in bins],
            stats=stats,
        )

    front_result = _process(df_front, "time_front", "pmax_front", req.binConfig.front, "前轴承")
    rear_result = _process(df_rear, "time_rear", "pmax_rear", req.binConfig.rear, "后轴承")

    return AnalyzeResponse(front=front_result, rear=rear_result)
