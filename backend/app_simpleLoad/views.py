"""载荷简化接口：预览载荷文件夹、加载数据、载荷缩减、清空数据

加载和缩减各走一条 WebSocket：连上后前端发一条参数，后端边算边推 progress，最后推 done 或 error，
再关掉连接。加载完的实例存在 LoadedDataCache，改了区间、坐标映射或缩减参数可以直接再缩减。
"""

import asyncio
import json
import os
import re
from pathlib import Path

from fastapi import HTTPException, WebSocket, WebSocketDisconnect
from loguru import logger
from pydantic import ValidationError

from app_simpleLoad.module.cache import LoadedDataCache
from app_simpleLoad.module.cal_simpleLoad import CalSimpleLoad
from app_simpleLoad.module.config import FileParseError
from app_simpleLoad.module.file_reader import list_txt_files, read_head_lines
from app_simpleLoad.module.progress import ProgressReporter
from app_simpleLoad.serializers import (
    ComponentStats,
    ErrorMessage,
    LoadDoneMessage,
    LoadRequest,
    PreviewRequest,
    PreviewResponse,
    ReduceDoneMessage,
    ReduceRequest,
)
from common.constants import LoadColumn

#: 预览读第一个 txt 的前几行，够看清列名、END_OF_HEADER 和头几行数据
PREVIEW_LINES = 20

#: 分布图的六个分量，顺序同区间表
HISTOGRAM_COLUMNS = (
    LoadColumn.FX,
    LoadColumn.FY,
    LoadColumn.FZ,
    LoadColumn.MX,
    LoadColumn.MY,
    LoadColumn.MZ,
)

#: savePic 给的柱用 pandas 区间的写法作键，如 "(-1000, -990]"
INTERVAL_LABEL = re.compile(r"^\(\s*([^,\s]+)\s*,\s*([^\]\s]+)\s*\]$")


# ─── HTTP ────────────────────────────────────────────────────


async def preview(req: PreviewRequest) -> PreviewResponse:
    """列出载荷文件夹里的 txt，读第一个的开头几行，给前端对列。"""
    folder = Path(req.loadDir)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail=f"载荷文件夹不存在：{req.loadDir}")

    paths = await asyncio.to_thread(list_txt_files, str(folder))
    if not paths:
        raise HTTPException(status_code=400, detail=f"载荷文件夹里没有 txt 文件：{req.loadDir}")

    try:
        lines = await asyncio.to_thread(read_head_lines, paths[0], PREVIEW_LINES)
        total_size = await asyncio.to_thread(lambda: sum(os.path.getsize(p) for p in paths))
    except OSError as e:
        raise HTTPException(
            status_code=400, detail=f"读取 {os.path.basename(paths[0])} 失败：{e}"
        ) from e

    return PreviewResponse(
        fileCount=len(paths),
        totalSize=total_size,
        sampleFile=os.path.relpath(paths[0], folder),
        lines=lines,
    )


async def clear() -> None:
    """丢掉加载过的数据，把内存还回去。"""
    LoadedDataCache.clear()


# ─── WebSocket ───────────────────────────────────────────────


async def ws_load(ws: WebSocket):
    """加载数据：读频次表和全部 txt，再统计六个分量的最值和时间占比分布。"""
    await ws.accept()
    try:
        req = LoadRequest.model_validate_json(await ws.receive_text())
        if not os.path.isdir(req.loadDir):
            await send_error(ws, f"载荷文件夹不存在：{req.loadDir}")
            return
        if not os.path.isfile(req.freqTablePath):
            await send_error(ws, f"频次表不存在：{req.freqTablePath}")
            return

        # 先放掉上一次的数据，不然新旧两份同时在内存里
        LoadedDataCache.clear()
        instance = CalSimpleLoad()
        instance.progress = ProgressReporter(ws.send_json)
        instance.setInit(paths=req.path_config(), header=req.header, config=req.conversion_config())

        # 读文件占大头，统计最值和分布占最后一截
        instance.progress.span(0, 90)
        await instance.simple_Pre_processing()
        instance.progress.span(90, 100)
        await instance.progress.send_text("正在统计各分量的最值...")
        min_max = json.loads(await instance.simple_load1([]))
        histograms = await instance.savePic()

        LoadedDataCache.save(instance)
        done = LoadDoneMessage(
            fileCount=instance.df_ref.height,
            rowCount=instance.df_all.height,
            components=component_stats(min_max, histograms),
        )
        await ws.send_json(done.model_dump(mode="json"))
    except WebSocketDisconnect:
        logger.info("加载数据时前端断开了连接")
    except ValidationError as e:
        await send_error(ws, describe_validation_error(e))
    except (ValueError, FileParseError) as e:
        logger.error(str(e))
        await send_error(ws, str(e))
    except Exception as e:
        logger.exception("加载数据出错")
        await send_error(ws, f"加载失败：{e}")
    finally:
        await close(ws)


async def ws_reduce(ws: WebSocket):
    """载荷缩减：用最近一次加载的数据按区间表分组缩减，写出 GL 和 Romax 两个 Excel。"""
    await ws.accept()
    try:
        req = ReduceRequest.model_validate_json(await ws.receive_text())
        instance = LoadedDataCache.load()
        if instance is None:
            await send_error(ws, "请先加载数据")
            return

        output_dir = os.path.normpath(req.outputDir)
        if not os.path.isdir(output_dir):
            await send_error(ws, f"输出目录不存在：{req.outputDir}")
            return
        files = CalSimpleLoad.output_files(output_dir)
        busy = [os.path.basename(path) for path in files if is_locked(path)]
        if busy:
            await send_error(ws, f"{'、'.join(busy)} 正被其他程序占用，请关闭后重试")
            return

        # 加载时只给了读文件要的参数，缩减用的这里补上
        instance.paths.result_folder_save_path = output_dir
        instance.paths.keep_torque_component = req.keepTorque
        instance.config.translate_factor = req.slope
        instance.config.temperature = req.temperature
        instance.config.tol = req.tol
        instance.progress = ProgressReporter(ws.send_json)

        result = await instance.simple_load2(req.table_data(), req.axis_mappings())
        if isinstance(result, dict):
            await send_error(ws, result["message"])
            return
        done = ReduceDoneMessage(cellCount=result, files=list(files))
        await ws.send_json(done.model_dump(mode="json"))
    except WebSocketDisconnect:
        logger.info("载荷缩减时前端断开了连接")
    except ValidationError as e:
        await send_error(ws, describe_validation_error(e))
    except Exception as e:
        logger.exception("载荷缩减出错")
        await send_error(ws, f"载荷缩减失败：{e}")
    finally:
        await close(ws)


# ─── 工具 ────────────────────────────────────────────────────


def component_stats(min_max: dict, histograms: dict[str, str]) -> list[ComponentStats]:
    """把 simple_load1 的最值和 savePic 的直方图换成按分量排开的数组。

    Args:
        min_max: simple_load1 返回的 JSON 解析后的样子，`{"min": {列名: 值}, "max": {列名: 值}}`。
        histograms: savePic 的返回值，列名 → 以区间写法作键的 JSON 字符串。

    Returns:
        六个分量各一项，顺序同区间表。
    """
    stats = []
    for column in HISTOGRAM_COLUMNS:
        left, right, share = [], [], []
        for label, value in json.loads(histograms[column.value]).items():
            match = INTERVAL_LABEL.match(label)
            if match is None:
                raise ValueError(f"{column.value} 的分布区间无法识别：{label}")
            left.append(float(match.group(1)))
            right.append(float(match.group(2)))
            share.append(float(value))
        stats.append(
            ComponentStats(
                component=column,
                min=min_max["min"][column.value],
                max=min_max["max"][column.value],
                binLeft=left,
                binRight=right,
                share=share,
            )
        )
    return stats


def is_locked(path: str) -> bool:
    """文件在，却打不开来写：Windows 上被 Excel 开着就是这样，这时写结果会失败。"""
    if not os.path.exists(path):
        return False
    try:
        with open(path, "a"):
            pass
    except OSError:
        return True
    return False


def describe_validation_error(error: ValidationError) -> str:
    """Pydantic 的校验错误拼成一句话；模型校验抛的提示原样给出，字段错误带上字段名。"""
    parts = []
    for item in error.errors():
        message = item["msg"].removeprefix("Value error, ")
        location = ".".join(str(part) for part in item["loc"])
        parts.append(f"{location}：{message}" if location else message)
    return "；".join(parts)


async def send_error(ws: WebSocket, message: str):
    """推一条 error；连接已经断了就算了，前端会按连接关闭处理。"""
    try:
        await ws.send_json(ErrorMessage(message=message).model_dump(mode="json"))
    except Exception as e:
        logger.warning(f"错误消息没能发出去：{e}")


async def close(ws: WebSocket):
    """关掉连接；已经关了就不管。"""
    try:
        await ws.close()
    except Exception:
        pass
