"""全局共享常量"""

from enum import Enum


class Language(str, Enum):
    ZH = "中文"
    EN = "English"


class LoadColumn(str, Enum):
    """载荷简化里 txt 各列的含义，值就是计算时用的列名。"""

    TIME = "Time[s]"
    SPEED = "speed[rpm]"
    FX = "Fx[KN]"
    FY = "Fy[KN]"
    FZ = "Fz[KN]"
    MX = "Mx[KNm]"
    MY = "My[KNm]"
    MZ = "Mz[KNm]"
