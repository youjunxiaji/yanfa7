"""全局共享常量"""

from enum import Enum


class Language(str, Enum):
    ZH = "中文"
    EN = "English"


class LogLevel(str, Enum):
    """「日志」页的级别，取值同 loguru 的级别名；DEBUG 不进日志页，ERROR 含 CRITICAL。"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class LogSource(str, Enum):
    """一条日志从哪来"""

    BACKEND = "后端"  # 后端代码和第三方库写的
    REQUEST = "请求"  # 访问记录和请求出错的原因
    UI = "界面"  # 渲染层报上来的


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
