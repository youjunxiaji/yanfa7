"""边缘应力 WebSocket 视图 & REST API"""

from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import JSONResponse
from loguru import logger

from app_edgeStress.module.dataset import (
    EdgeStressDataset,
    FileType,
    InputConfig,
    ProcessConfig,
    ReportConfig,
    StressPosition,
)
from app_edgeStress.module.cache import DatasetCache
from app_edgeStress.module.processor import EdgeStressLoader, EdgeStressProcessor
from app_edgeStress.module.reporter import EdgeStressReporter
from app_edgeStress.serializers import ParseRequestSerializer, UpdateStressPointRequest, RegeneratePolarRequest


def _get_group_name(filename: str) -> str:
    """从文件名中提取分组名：取第一个 '(' 之前的部分并去除末尾空格。"""
    idx = filename.find("(")
    if idx > 0:
        return filename[:idx].rstrip()
    return filename


async def ws_parse(ws: WebSocket):
    """逐文件处理并通过 WebSocket 推送实时进度。"""
    await ws.accept()
    try:
        raw = await ws.receive_text()
        req = ParseRequestSerializer.model_validate_json(raw)

        file_type = FileType.HTM if req.fileType == "htm" else FileType.EXCEL
        files = [Path(p) for p in req.filePaths]
        total_files = len(files)

        missing = [str(f) for f in files if not f.exists()]
        if missing:
            await ws.send_json({"type": "error", "message": f"文件不存在: {', '.join(missing)}"})
            await ws.close()
            return

        base_output = Path(req.outputDir)
        if not base_output.exists():
            await ws.send_json({"type": "error", "message": f"输出目录不存在: {req.outputDir}"})
            await ws.close()
            return

        output_dir = base_output / "res-output"
        output_dir.mkdir(exist_ok=True)

        rc = req.reportConfig
        process_config = ProcessConfig(peak_threshold=req.peakThreshold)
        report_config = ReportConfig(
            pic_width=rc.picWidth,
            pic_height=rc.picHeight,
            load_polar_min=rc.loadPolarMin,
            press_polar_min=rc.pressPolarMin,
        )

        loader = EdgeStressLoader()
        processor = EdgeStressProcessor(process_config)

        group_reporters: dict[str, EdgeStressReporter] = {}

        all_columns = []
        all_generated: list[str] = []

        for i, file_path in enumerate(files):
            await ws.send_json({
                "type": "progress",
                "current": i,
                "total": total_files,
                "filename": file_path.name,
            })

            try:
                file_columns = loader.load_single_file(file_path, file_type)
                processor.process(file_columns)

                group_name = _get_group_name(file_path.stem)
                if group_name not in group_reporters:
                    group_dir = output_dir / group_name
                    group_dir.mkdir(exist_ok=True)
                    group_reporters[group_name] = EdgeStressReporter(report_config, group_dir)

                reporter = group_reporters[group_name]
                for col in file_columns:
                    paths = reporter.generate_for_column(col)
                    all_generated.extend(str(p) for p in paths)
                all_columns.extend(file_columns)
            except Exception as e:
                logger.warning(f"跳过文件 {file_path.name}: {e}")

        input_config = InputConfig(files=files, file_type=file_type, output_dir=output_dir)
        dataset = EdgeStressDataset(
            process_config=process_config,
            input_config=input_config,
            report_config=report_config,
            columns=all_columns,
        )
        DatasetCache.save(dataset)

        max_summary = dataset.get_max_summary()
        if not max_summary.empty:
            summary_path = output_dir / "最大应力汇总.xlsx"
            max_summary.to_excel(str(summary_path))
            all_generated.append(str(summary_path))

        result_columns: dict[str, list[int]] = {}
        for fn in dataset.filenames:
            result_columns[fn] = [c.col_index for c in dataset.get_columns_by_file(fn)]

        preview_map: dict[str, list[dict]] = {}
        for col in all_columns:
            src_name = col.filename
            group_name = _get_group_name(src_name)
            candidate = output_dir / group_name / f"{src_name}-{StressPosition.INNER.value}-第{col.col_index}列-中.png"
            if candidate.exists():
                preview_map.setdefault(src_name, []).append({
                    "colIndex": col.col_index,
                    "path": str(candidate),
                })

        await ws.send_json({
            "type": "done",
            "fileNames": dataset.filenames,
            "columns": result_columns,
            "generatedFiles": all_generated,
            "previewMap": preview_map,
        })
    except WebSocketDisconnect:
        logger.info("WebSocket 客户端断开")
    except Exception as e:
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        logger.error(f"WebSocket 解析异常: {e}")
    finally:
        try:
            await ws.close()
        except Exception:
            pass


async def get_chart_data(
    file_stem: str = Query(..., description="文件名 stem（不含扩展名）"),
    col_index: int = Query(..., description="列号（从 1 开始）"),
    position: str = Query(..., description="inner 或 outer"),
) -> JSONResponse:
    """返回指定滚子列的 Plotly 图表数据（原始 + 去峰后）。"""
    col = DatasetCache.get_column(file_stem, col_index)
    if col is None:
        raise HTTPException(
            status_code=400,
            detail="缓存数据不存在，请重新解析文件后再预览",
        )

    pos = StressPosition.INNER if position == "inner" else StressPosition.OUTER
    charts = EdgeStressReporter.build_chart_data(col, pos)
    return JSONResponse(content=charts)


async def update_stress_point(req: UpdateStressPointRequest) -> JSONResponse:
    """修改去峰后数据中的单个应力值，更新内存缓存并重新生成相关 PNG。"""
    dataset = DatasetCache.load()
    if dataset is None:
        raise HTTPException(status_code=400, detail="缓存数据不存在，请重新解析文件")

    col = DatasetCache.get_column(req.file_stem, req.col_index)
    if col is None:
        raise HTTPException(status_code=400, detail="缓存数据不存在，请重新解析文件")

    summary_path = dataset.input_config.output_dir / "最大应力汇总.xlsx"
    try:
        summary_path.touch(exist_ok=True)
        with open(summary_path, "a"):
            pass
    except (PermissionError, OSError):
        raise HTTPException(
            status_code=400,
            detail="最大应力汇总.xlsx 正被其他程序占用，请关闭后重试",
        )

    pos = StressPosition.INNER if req.position == "inner" else StressPosition.OUTER
    stress = col.get_stress(pos)
    if stress.processed is None:
        raise HTTPException(status_code=400, detail="去峰数据不存在")

    df = stress.processed
    shifted = df.copy()
    new_level_0 = ((shifted.index.levels[0].astype(float) + 180) % 360).round(3)  # type: ignore[union-attr]
    shifted.index = shifted.index.set_levels(new_level_0, level=0)  # type: ignore[union-attr]
    shifted = shifted.sort_index()

    level_unique = shifted.index.get_level_values(0).unique()
    visible_idx = 0
    target_angle = None
    for angle in level_unique:
        values = shifted.loc[angle, "接触应力 (MPa)"]
        if (values == 0).all():  # type: ignore[union-attr]
            continue
        if visible_idx == req.trace_index:
            target_angle = angle
            break
        visible_idx += 1

    if target_angle is None:
        raise HTTPException(status_code=400, detail=f"trace_index={req.trace_index} 无法映射到有效角度")

    angle_rows = shifted.loc[target_angle]
    if req.point_index < 0 or req.point_index >= len(angle_rows):
        raise HTTPException(
            status_code=400,
            detail=f"point_index={req.point_index} 超出范围 (0~{len(angle_rows)-1})",
        )

    distance = angle_rows.index[req.point_index]
    original_angle = round((float(target_angle) - 180) % 360, 3)

    df.loc[(original_angle, distance), "接触应力 (MPa)"] = req.new_value

    regenerated: list[str] = []

    max_summary = dataset.get_max_summary()
    if not max_summary.empty:
        max_summary.to_excel(str(summary_path))
        regenerated.append(str(summary_path))

    group_name = _get_group_name(req.file_stem)
    output_dir = dataset.input_config.output_dir / group_name
    reporter = EdgeStressReporter(dataset.report_config, output_dir)

    regenerated.append(str(reporter.generate_stress_chart(col, pos, is_cn=True)))
    regenerated.append(str(reporter.generate_stress_chart(col, pos, is_cn=False)))
    polar = reporter.generate_polar_chart(col, is_load=False)
    if polar:
        regenerated.append(str(polar))

    return JSONResponse(content={"ok": True, "regenerated": regenerated})


async def regenerate_polar(req: RegeneratePolarRequest) -> JSONResponse:
    """使用自定义最小值重新生成雷达图 PNG。"""
    dataset = DatasetCache.load()
    if dataset is None:
        raise HTTPException(status_code=400, detail="缓存数据不存在，请重新解析文件")

    col = DatasetCache.get_column(req.file_stem, req.col_index)
    if col is None:
        raise HTTPException(status_code=400, detail="缓存数据不存在，请重新解析文件")

    group_name = _get_group_name(req.file_stem)
    output_dir = dataset.input_config.output_dir / group_name

    polar_config = ReportConfig(
        pic_width=dataset.report_config.pic_width,
        pic_height=dataset.report_config.pic_height,
        load_polar_min=req.load_polar_min,
        press_polar_min=req.press_polar_min,
    )
    reporter = EdgeStressReporter(polar_config, output_dir)

    regenerated: list[str] = []
    load_path = reporter.generate_polar_chart(col, is_load=True)
    if load_path:
        regenerated.append(str(load_path))
    stress_path = reporter.generate_polar_chart(col, is_load=False)
    if stress_path:
        regenerated.append(str(stress_path))

    return JSONResponse(content={"ok": True, "regenerated": regenerated})
