"""载荷简化 HTTP 接口与 WebSocket 视图"""

import asyncio
import json

from fastapi import Depends, Request, WebSocket, WebSocketDisconnect
from loguru import logger

from app_simpleLoad.module.cal_simpleLoad import CalSimpleLoad
from app_simpleLoad.module.config import FileParseError
from app_simpleLoad.module.global_ws import ws
from app_simpleLoad.module.socket_manager import ConnectionManager
from app_simpleLoad.serializers import (
    DivideIntervalRequest,
    LoadFileRequest,
    ReduceLoadRequest,
)


async def load_file(request: Request, data_: LoadFileRequest):
    """加载文件：读频次表和全部载荷 txt，完成预处理。"""
    manager = request.app.state.websocket_manager
    instance: CalSimpleLoad | None = manager.cal_instance

    # 检查实例是否存在，如果不存在则创建新实例
    if instance is None:
        # 检查WebSocket连接状态，如果断开则等待重连
        if not ws.is_connection_active('simple_load'):
            logger.info("WebSocket连接断开，等待前端重连...")

            # 等待前端重连，最多等待10秒
            for i in range(20):  # 20次 * 0.5秒 = 10秒
                await asyncio.sleep(0.5)
                if ws.is_connection_active('simple_load'):
                    logger.info(f"WebSocket重连成功，等待了 {(i+1)*0.5} 秒")
                    break
            else:
                # 10秒后仍未重连成功
                return {
                    "message": "WebSocket连接已断开，请刷新页面重新连接",
                    "status": "error",
                    "need_reconnect": True
                }

        instance = CalSimpleLoad()
        manager.cal_instance = instance
        logger.info("创建新的 CalSimpleLoad 实例，WebSocket连接正常")

    try:
        instance.setInit(
            paths=data_.file_path,
            header=data_.header,
            config=data_.conversion_factors,
        )
    except ValueError as e:
        # 捕获header配置错误
        error_msg = str(e)
        logger.error(error_msg)
        return {"message": error_msg, "status": "error"}

    try:
        await instance.simple_Pre_processing()
    except ValueError as e:
        logger.error(str(e))
        return {"message": str(e), "status": "error"}
    except FileParseError as e:
        logger.error(str(e))
        return {"message": str(e), "status": "error"}
    except Exception as e:
        logger.error(f"文件加载过程中发生未知错误: {e}")
        return {"message": f"文件加载失败: {e}", "status": "error"}

    return {"message": "读取文件完成", "status": "success"}


async def simple_pre_processing(request: Request, data: DivideIntervalRequest):
    """划分区间：算各分量的最值和加权直方图数据。"""
    manager = request.app.state.websocket_manager
    instance: CalSimpleLoad | None = manager.cal_instance

    # 检查实例是否存在
    if instance is None:
        return {"message": "请先加载文件", "status": "error"}

    try:
        min_max = await instance.simple_load1(data.romax_origin)
        echarts_data = await instance.savePic()
    except AttributeError:
        return {"message": "请先加载文件", "status": "error"}
    return {
        "message": "划分区间完成",
        "min_max": min_max,
        "echarts_data": echarts_data,
        "status": "success",
    }


async def simple_load(request: Request, data: ReduceLoadRequest):
    """载荷缩减：按区间表分组缩减，写出 GL 和 Romax 两个 Excel。"""
    manager = request.app.state.websocket_manager
    instance: CalSimpleLoad | None = manager.cal_instance

    # 检查实例是否存在
    if instance is None:
        return {"message": "请先加载文件", "status": "error"}

    try:
        msg = await instance.simple_load2(data.tableData, data.romax_origin)
    except Exception as e:
        logger.error(f"载荷缩减过程中发生错误: {e}")
        return {"message": f"载荷缩减失败: {e}", "status": "error"}

    if isinstance(msg, dict):
        return {**msg, "status": "error"}
    return {"message": "载荷简化处理全部完成", "count": msg}


# ─── WebSocket ───────────────────────────────────────────────

async def get_manager(websocket: WebSocket):
    """取应用上挂着的连接管理器。"""
    return websocket.app.state.websocket_manager


async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    manager: ConnectionManager = Depends(get_manager)
):
    """客户端连上后收命令和广播消息；断开时清掉计算实例。"""
    try:
        await manager.connect(websocket, client_id)
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"收到客户端 {client_id} 的消息: {data}")

                try:
                    message = json.loads(data)
                    if message.get("type") == "command":
                        await manager.handle_command(message, client_id)
                    elif message.get("type") == "broadcast":
                        await manager.broadcast(json.dumps({
                            "type": "broadcast",
                            "message": message.get("message")
                        }))
                except json.JSONDecodeError:
                    logger.error(f"无效的 JSON 消息: {data}")

            except WebSocketDisconnect:
                manager.disconnect(client_id)
                break

    except Exception as e:
        logger.error(f"WebSocket 错误: {str(e)}")
        manager.disconnect(client_id)
