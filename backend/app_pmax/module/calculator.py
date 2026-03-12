"""Pmax 分箱计算：pd.cut + groupby 时间占比"""

import numpy as np
import pandas as pd


def compute_time_ratio(
    times: list[float],
    pmax_values: list[float],
    min_val: float,
    max_val: float,
    step: float,
) -> list[dict]:
    """对 Pmax 序列按分箱参数分组，计算各区间的时间占比百分比。

    Returns: [{"label": "<800", "percentage": 5.23}, ...]
    """
    df = pd.DataFrame({"time": times, "pmax": pmax_values})

    bin_edges = list(np.arange(min_val, max_val + 1, step))
    bin_edges.insert(0, -np.inf)
    bin_edges.append(np.inf)

    labels = [f"<{bin_edges[1]:.0f}"]
    for i in range(1, len(bin_edges) - 2):
        labels.append(f"({bin_edges[i]:.0f}, {bin_edges[i + 1]:.0f}]")
    labels.append(f">{bin_edges[-2]:.0f}")

    df["bins"] = pd.cut(df["pmax"], bin_edges, include_lowest=False, labels=labels)
    result = df.groupby("bins", observed=False)["time"].sum()
    total = result.sum()
    if total > 0:
        result = result / total * 100

    return [{"label": lbl, "percentage": round(pct, 4)} for lbl, pct in zip(result.index.astype(str), result.values)]
