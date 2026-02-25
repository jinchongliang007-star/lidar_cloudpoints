"""
点云数据结构 - 基于NumPy的点云类
"""

import numpy as np
from typing import Optional, Tuple, List


class PointCloud:
    """
    点云数据类

    存储点云的位置数据和元数据（如物体类型标签）
    """

    def __init__(self, points: Optional[np.ndarray] = None, labels: Optional[np.ndarray] = None):
        """
        初始化点云

        Args:
            points: Nx3 或 Nx4 的NumPy数组 (x, y, z) 或 (x, y, z, label)
            labels: N 的标签数组（可选，如果points包含标签则不需要）
        """
        self._points = np.empty((0, 3), dtype=np.float64)
        self._labels = np.empty((0,), dtype=np.int32)
        self._object_types = []  # 存储原始物体类型字符串

        if points is not None:
            if points.shape[1] == 4:
                # points包含标签
                self._points = points[:, :3].astype(np.float64)
                self._labels = points[:, 3].astype(np.int32)
            elif points.shape[1] == 3:
                self._points = points.astype(np.float64)
                if labels is not None:
                    self._labels = labels.astype(np.int32)
                else:
                    self._labels = np.zeros(len(points), dtype=np.int32)

    @classmethod
    def from_scene_data(cls, scene_points: List[Tuple]) -> 'PointCloud':
        """
        从场景点云数据创建点云对象

        Args:
            scene_points: 场景点云数据列表，每个元素为 (x, y, z, object_type) 或 (x, y, z)

        Returns:
            PointCloud 实例
        """
        if not scene_points:
            return cls()

        # 解析点云数据
        points_list = []
        types_list = []

        # 物体类型到标签的映射
        type_to_label = {}
        current_label = 0

        for point in scene_points:
            if len(point) >= 4:
                x, y, z = point[0], point[1], point[2]
                obj_type = point[3]

                if obj_type not in type_to_label:
                    type_to_label[obj_type] = current_label
                    current_label += 1

                points_list.append([x, y, z])
                types_list.append(type_to_label[obj_type])
            else:
                points_list.append([point[0], point[1], point[2]])
                types_list.append(0)

        cloud = cls()
        cloud._points = np.array(points_list, dtype=np.float64)
        cloud._labels = np.array(types_list, dtype=np.int32)
        cloud._type_to_label = type_to_label
        cloud._label_to_type = {v: k for k, v in type_to_label.items()}

        return cloud

    @property
    def points(self) -> np.ndarray:
        """获取点坐标 (Nx3)"""
        return self._points

    @property
    def labels(self) -> np.ndarray:
        """获取点标签 (N,)"""
        return self._labels

    @property
    def xyz(self) -> np.ndarray:
        """获取点坐标的别名"""
        return self._points

    @property
    def x(self) -> np.ndarray:
        """获取X坐标"""
        return self._points[:, 0]

    @property
    def y(self) -> np.ndarray:
        """获取Y坐标"""
        return self._points[:, 1]

    @property
    def z(self) -> np.ndarray:
        """获取Z坐标"""
        return self._points[:, 2]

    def __len__(self) -> int:
        """返回点云中的点数"""
        return len(self._points)

    def size(self) -> int:
        """返回点云中的点数"""
        return len(self._points)

    def get_bounds(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        获取点云的边界框

        Returns:
            (min_bound, max_bound): 边界框的最小和最大角点
        """
        if len(self._points) == 0:
            return np.zeros(3), np.zeros(3)

        min_bound = np.min(self._points, axis=0)
        max_bound = np.max(self._points, axis=0)
        return min_bound, max_bound

    def get_center(self) -> np.ndarray:
        """获取点云中心点"""
        if len(self._points) == 0:
            return np.zeros(3)
        return np.mean(self._points, axis=0)

    def select_by_index(self, indices: np.ndarray) -> 'PointCloud':
        """
        根据索引选择点

        Args:
            indices: 点索引数组

        Returns:
            新的点云对象
        """
        cloud = PointCloud()
        cloud._points = self._points[indices]
        cloud._labels = self._labels[indices]
        return cloud

    def select_by_label(self, label: int) -> 'PointCloud':
        """
        根据标签选择点

        Args:
            label: 标签值

        Returns:
            新的点云对象
        """
        mask = self._labels == label
        return self.select_by_index(mask)

    def get_unique_labels(self) -> np.ndarray:
        """获取所有唯一标签"""
        return np.unique(self._labels)

    def get_points_by_label(self, label: int) -> np.ndarray:
        """根据标签获取点坐标"""
        mask = self._labels == label
        return self._points[mask]

    def to_array(self) -> np.ndarray:
        """转换为NumPy数组 (Nx3)"""
        return self._points.copy()

    def copy(self) -> 'PointCloud':
        """创建点云的副本"""
        cloud = PointCloud()
        cloud._points = self._points.copy()
        cloud._labels = self._labels.copy()
        return cloud

    def get_statistics(self) -> dict:
        """
        获取点云统计信息

        Returns:
            包含统计信息的字典
        """
        if len(self._points) == 0:
            return {
                'num_points': 0,
                'bounds': (np.zeros(3), np.zeros(3)),
                'center': np.zeros(3),
                'unique_labels': [],
            }

        min_bound, max_bound = self.get_bounds()

        return {
            'num_points': len(self._points),
            'bounds': (min_bound, max_bound),
            'center': self.get_center(),
            'unique_labels': list(self.get_unique_labels()),
        }

    def __repr__(self) -> str:
        return f"PointCloud(points={len(self._points)}, labels={len(self._labels)})"
