"""最近一次加载完的数据"""

import gc

from app_simpleLoad.module.cal_simpleLoad import CalSimpleLoad


class LoadedDataCache:
    """后端进程里只留最近一次加载完的计算实例，改了区间可以直接再缩减。

    全量载荷表常有几个 GB：新的加载开始前先清掉旧的，免得两份同时占着内存。
    """

    _instance: CalSimpleLoad | None = None

    @classmethod
    def save(cls, instance: CalSimpleLoad) -> None:
        """存下加载完的实例，覆盖上一次的。"""
        cls._instance = instance

    @classmethod
    def load(cls) -> CalSimpleLoad | None:
        """取最近一次加载完的实例，没加载过或已清空时返回 None。"""
        return cls._instance

    @classmethod
    def clear(cls) -> None:
        """丢掉缓存的实例，把内存还回去。"""
        if cls._instance is None:
            return
        cls._instance = None
        gc.collect()
