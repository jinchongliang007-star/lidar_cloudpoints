"""
处理流水线 - 管理点云处理的各个阶段
"""

import numpy as np
from typing import Optional, List, Tuple, Callable
from dataclasses import dataclass, field

from data.point_cloud import PointCloud
from processing.downsampling import voxel_grid_downsample, random_downsample
from processing.clustering import (
    dbscan_clustering,
    compute_bounding_boxes,
    get_cluster_colors,
    get_clustering_statistics,
)


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    stage: str  # 'raw', 'downsampled', 'clustered'
    point_cloud: PointCloud
    cluster_labels: Optional[np.ndarray] = None
    bounding_boxes: Optional[List[dict]] = None
    statistics: dict = field(default_factory=dict)


class ProcessingPipeline:
    """
    点云处理流水线

    管理从原始点云到下采样到聚类的整个处理流程
    """

    def __init__(self):
        # 处理参数
        self.downsample_method = 'voxel'  # 'voxel' 或 'random'
        self.voxel_size = 0.2  # 体素大小（米）
        self.random_sample_count = 1000  # 随机采样目标点数

        self.eps = 0.5  # DBSCAN邻域半径
        self.min_samples = 5  # DBSCAN最小邻居数

        # 当前处理阶段
        self.current_stage = 'raw'

        # 处理结果
        self.raw_result: Optional[ProcessingResult] = None
        self.downsampled_result: Optional[ProcessingResult] = None
        self.clustered_result: Optional[ProcessingResult] = None

        # 回调函数
        self._on_result_updated: Optional[Callable[[ProcessingResult], None]] = None

    def set_on_result_updated(self, callback: Callable[[ProcessingResult], None]):
        """设置结果更新回调函数"""
        self._on_result_updated = callback

    def set_raw_point_cloud(self, points: List[Tuple]):
        """
        设置原始点云数据

        Args:
            points: 场景点云数据列表，每个元素为 (x, y, z, object_type)
        """
        cloud = PointCloud.from_scene_data(points)

        self.raw_result = ProcessingResult(
            stage='raw',
            point_cloud=cloud,
            statistics={
                'num_points': len(cloud),
                'stage': 'raw',
            }
        )

        # 重置后续结果
        self.downsampled_result = None
        self.clustered_result = None

        self._notify_update()

    def process_downsampling(self) -> ProcessingResult:
        """
        执行下采样处理

        Returns:
            下采样结果
        """
        if self.raw_result is None:
            raise ValueError("没有原始点云数据，请先调用 set_raw_point_cloud")

        cloud = self.raw_result.point_cloud

        # 根据方法选择下采样算法
        if self.downsample_method == 'voxel':
            downsampled = voxel_grid_downsample(cloud, self.voxel_size)
        else:
            downsampled = random_downsample(cloud, self.random_sample_count)

        self.downsampled_result = ProcessingResult(
            stage='downsampled',
            point_cloud=downsampled,
            statistics={
                'num_points': len(downsampled),
                'original_points': len(cloud),
                'reduction_ratio': len(downsampled) / len(cloud) if len(cloud) > 0 else 0,
                'voxel_size': self.voxel_size if self.downsample_method == 'voxel' else None,
                'method': self.downsample_method,
                'stage': 'downsampled',
            }
        )

        # 重置聚类结果
        self.clustered_result = None

        self._notify_update()
        return self.downsampled_result

    def process_clustering(self) -> ProcessingResult:
        """
        执行聚类处理

        Returns:
            聚类结果
        """
        # 使用下采样后的点云（如果存在），否则使用原始点云
        if self.downsampled_result is not None:
            cloud = self.downsampled_result.point_cloud
        elif self.raw_result is not None:
            cloud = self.raw_result.point_cloud
        else:
            raise ValueError("没有点云数据")

        # 执行DBSCAN聚类
        labels = dbscan_clustering(cloud, self.eps, self.min_samples)

        # 计算边界框
        bounding_boxes = compute_bounding_boxes(cloud, labels)

        # 获取聚类统计
        cluster_stats = get_clustering_statistics(labels)

        self.clustered_result = ProcessingResult(
            stage='clustered',
            point_cloud=cloud,
            cluster_labels=labels,
            bounding_boxes=bounding_boxes,
            statistics={
                'num_points': len(cloud),
                'num_clusters': cluster_stats['num_clusters'],
                'num_noise_points': cluster_stats['num_noise_points'],
                'cluster_sizes': cluster_stats['cluster_sizes'],
                'eps': self.eps,
                'min_samples': self.min_samples,
                'stage': 'clustered',
            }
        )

        self._notify_update()
        return self.clustered_result

    def get_current_result(self) -> Optional[ProcessingResult]:
        """
        获取当前阶段的处理结果

        Returns:
            当前阶段的处理结果
        """
        stage = self.current_stage

        if stage == 'raw':
            return self.raw_result
        elif stage == 'downsampled':
            if self.downsampled_result is None and self.raw_result is not None:
                self.process_downsampling()
            return self.downsampled_result
        elif stage == 'clustered':
            if self.clustered_result is None:
                if self.downsampled_result is None and self.raw_result is not None:
                    self.process_downsampling()
                if self.downsampled_result is not None:
                    self.process_clustering()
            return self.clustered_result

        return None

    def set_stage(self, stage: str):
        """
        设置当前处理阶段

        Args:
            stage: 'raw', 'downsampled', 或 'clustered'
        """
        if stage not in ['raw', 'downsampled', 'clustered']:
            raise ValueError(f"无效的阶段: {stage}")

        self.current_stage = stage
        self._notify_update()

    def set_voxel_size(self, size: float):
        """设置体素大小"""
        self.voxel_size = size
        # 使下采样结果失效
        self.downsampled_result = None
        self.clustered_result = None

    def set_eps(self, eps: float):
        """设置DBSCAN邻域半径"""
        self.eps = eps
        # 使聚类结果失效
        self.clustered_result = None

    def set_min_samples(self, min_samples: int):
        """设置DBSCAN最小邻居数"""
        self.min_samples = min_samples
        # 使聚类结果失效
        self.clustered_result = None

    def set_downsample_method(self, method: str):
        """设置下采样方法"""
        if method not in ['voxel', 'random']:
            raise ValueError(f"无效的下采样方法: {method}")
        self.downsample_method = method
        # 使下采样结果失效
        self.downsampled_result = None
        self.clustered_result = None

    def _notify_update(self):
        """通知结果更新"""
        if self._on_result_updated is not None:
            result = self.get_current_result()
            if result is not None:
                self._on_result_updated(result)

    def reprocess_current_stage(self):
        """重新处理当前阶段"""
        if self.current_stage == 'raw':
            # 原始数据不需要重新处理
            self._notify_update()
        elif self.current_stage == 'downsampled':
            self.process_downsampling()
        elif self.current_stage == 'clustered':
            self.process_clustering()

    def get_cluster_colors(self) -> List[Tuple[float, float, float]]:
        """
        获取聚类的颜色列表

        Returns:
            颜色列表
        """
        if self.clustered_result is None:
            return []

        num_clusters = self.clustered_result.statistics.get('num_clusters', 0)
        return get_cluster_colors(num_clusters)
