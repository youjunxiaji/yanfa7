"""Pmax 柱状图生成（matplotlib → PNG 文件）"""

import os
import tempfile

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from common.constants import Language

TEMP_DIR = os.path.join(tempfile.gettempdir(), "yanfa7_pmax")
print(TEMP_DIR)

def _ensure_temp_dir() -> str:
    os.makedirs(TEMP_DIR, exist_ok=True)
    return TEMP_DIR


def cleanup_temp_files() -> None:
    if not os.path.exists(TEMP_DIR):
        return
    for f in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, f))
        except OSError:
            pass


def generate_bar_chart(
    bins: list[dict],
    bearing_label: str,
    language: str,
    title_fs: int,
    label_fs: int,
    tick_fs: int,
    text_fs: int,
    width: int,
    height: int,
) -> str:
    """生成柱状图 PNG 并返回文件绝对路径。"""
    labels = [b["label"] for b in bins]
    values = [b["percentage"] for b in bins]

    fig, ax = plt.subplots(figsize=(width, height))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", zorder=0, linestyle=":")

    ax.bar(labels, values, width=0.5, zorder=10)

    y_max = int(np.ceil(max(values) / 10) * 10) if values and max(values) > 0 else 10
    ax.set_yticks(np.arange(0, y_max + 1, 10))
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=100, decimals=0))

    if language == Language.ZH:
        ax.set_xlabel("\n最大接触应力 (MPa)", fontsize=label_fs)
        ax.set_ylabel("时间占比\n", fontsize=label_fs)
        ax.set_title(f"{bearing_label}\n", fontsize=title_fs)
    else:
        ax.set_xlabel("\nMax. Contact Pressure (MPa)", fontsize=label_fs)
        ax.set_ylabel("Time Proportion\n", fontsize=label_fs)
        en_title = "Front Bearing" if bearing_label == "前轴承" else "Rear Bearing"
        ax.set_title(f"{en_title}\n", fontsize=title_fs)

    ax.tick_params(axis="x", labelrotation=45, labelsize=tick_fs)
    ax.tick_params(axis="y", labelsize=tick_fs)

    for lbl, val in zip(labels, values):
        if val == 0:
            prec = 0
        elif abs(val) < 0.01:
            prec = max(2, abs(int(np.log10(val))) + 1)
        else:
            prec = 2
        ax.text(lbl, val, f"{val:.{prec}f}%", ha="center", va="bottom", fontsize=text_fs)

    fig.tight_layout()

    out_dir = _ensure_temp_dir()
    filename = "front.png" if bearing_label == "前轴承" else "rear.png"
    filepath = os.path.join(out_dir, filename)
    fig.savefig(filepath, format="png", bbox_inches="tight", dpi=150)
    plt.close(fig)

    return filepath
