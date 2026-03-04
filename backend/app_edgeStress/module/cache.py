"""
EdgeStressDataset 内存缓存管理器

提供 save / load / update 三个操作，供 views 层调用。

Author: gu lei
Date: 2026-03-03
"""

from loguru import logger

from app_edgeStress.module.dataset import EdgeStressDataset, RollerColumn


class DatasetCache:
    """EdgeStressDataset 单例缓存。"""

    _dataset: EdgeStressDataset | None = None

    @classmethod
    def save(cls, dataset: EdgeStressDataset) -> None:
        """保存（覆盖）缓存的 dataset。"""
        cls._dataset = dataset

    @classmethod
    def load(cls) -> EdgeStressDataset | None:
        """读取缓存的 dataset，无缓存返回 None。"""
        return cls._dataset

    @classmethod
    def get_column(cls, file_stem: str, col_index: int) -> RollerColumn | None:
        """便捷方法：从缓存中获取指定 RollerColumn。"""
        if cls._dataset is None:
            return None
        return cls._dataset.get_column(file_stem, col_index)

    @classmethod
    def update(cls, file_stem: str, col_index: int, column: RollerColumn) -> bool:
        """
        替换缓存中指定的 RollerColumn。

        Parameters
        ----------
        file_stem : str
            文件名 stem。
        col_index : int
            列号。
        column : RollerColumn
            新的列数据。

        Returns
        -------
        bool
            替换成功返回 True，未找到目标返回 False。
        """
        if cls._dataset is None:
            return False
        for i, c in enumerate(cls._dataset.columns):
            if c.filename == file_stem and c.col_index == col_index:
                cls._dataset.columns[i] = column
                return True
        return False
