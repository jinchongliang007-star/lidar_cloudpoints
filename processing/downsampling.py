"""
下采样算法 - 体素网格下采样和随机采样
"""

import numpy as np
from typing import Optional
from data.point_cloud import PointCloud


def voxel_grid_downsample(cloud: PointCloud, voxel_size: float) -> PointCloud:
    """
    体素网格下采样

    将点云划分为指定大小的体素网格，每个体素内的点取质心

    Args:
        cloud: 输入点云
        voxel_size: 体素大小（米）

    Returns:
        下采样后的点云
    """
    if len(cloud) == 0:
        return PointCloud()

    points = cloud.points
    labels = cloud.labels

    # 计算点云边界
    min_bound = np.min(points, axis=0)
    max_bound = np.max(points, axis=0)

    # 计算每个点的体素索引
    # 使用 floor 来确保正数和负数都被正确处理
    voxel_indices = np.floor((points - min_bound) / voxel_size).astype(np.int32)

    # 为每个体素创建唯一键
    # 使用位运算来创建唯一的体素ID
    # 假设索引范围在合理范围内（比如 ±10000）
    shift = 20000  # 偏移量确保负数变正
    voxel_keys = ((voxel_indices[:, 0] + shift) * 40001 * 40001 +
                  (voxel_indices[:, 1] + shift) * 40001 +
                  (voxel_indices[:, 2] + shift))

    # 找出唯一的体素
    unique_keys, inverse_indices = np.unique(voxel_keys, return_inverse=True)

    # 对于每个体素，计算质心
    num_voxels = len(unique_keys)
    downsampled_points = np.zeros((num_voxels, 3), dtype=np.float64)
    downsampled_labels = np.zeros(num_voxels, dtype=np.int32)

    # 使用bincount和求和来高效计算质心
    for i in range(3):
        downsampled_points[:, i] = np.bincount(inverse_indices, weights=points[:, i]) / np.bincount(inverse_indices)

    # 对于标签，取每个体素内最常见的标签
    for i, key in enumerate(unique_keys):
        mask = voxel_keys == key
        labels_in_voxel = labels[mask]
        # 取最常见的标签
        if len(labels_in_voxel) > 0:
            unique_labels, counts = np.unique(labels_in_voxel, return_counts=True)
            downsampled_labels[i] = unique_labels[np.argmax(counts)]

    # 创建新的点云
    result = PointCloud()
    result._points = downsampled_points
    result._labels = downsampled_labels

    return result


def random_downsample(cloud: PointCloud, target_count: int, seed: Optional[int] = None) -> PointCloud:
    """
    随机下采样

    从点云中均匀随机选取指定数量的点

    Args:
        cloud: 输入点云
        target_count: 目标点数
        seed: 随机种子（可选，用于可重复性）

    Returns:
        下采样后的点云
    """
    if len(cloud) == 0:
        return PointCloud()

    num_points = len(cloud)

    if target_count >= num_points:
        # 如果目标数量大于等于当前点数，返回副本
        return cloud.copy()

    if seed is not None:
        np.random.seed(seed)

    # 随机选择点的索引
    indices = np.random.choice(num_points, size=target_count, replace=False)

    # 创建新的点云
    result = PointCloud()
    result._points = cloud.points[indices].copy()
    result._labels = cloud.labels[indices].copy()

    return result


def compute_downsample_ratio(cloud: PointCloud, target_count: int) -> float:
    """
    计算达到目标点数所需的下采样比例

    Args:
        cloud: 输入点云
        target_count: 目标点数

    Returns:
        下采样比例 (0.0 - 1.0)
    """
    if len(cloud) == 0:
        return 0.0

    return min(1.0, target_count / len(cloud))


def estimate_voxel_size_for_target(cloud: PointCloud, target_count: int) -> float:
    """
    估算达到目标点数所需的体素大小

    Args:
        cloud: 输入点云
        target_count: 目标点数

    Returns:
        估算的体素大小
    """
    if len(cloud) == 0 or target_count <= 0:
        return 1.0

    points = cloud.points
    min_bound = np.min(points, axis=0)
    max_bound = np.max(points, axis=0)

    # 计算边界框体积
    bbox_size = max_bound - min_bound
    bbox_volume = np.prod(bbox_size)

    # 估算体素大小：使得体素数量约等于目标点数
    # volume / voxel_size^3 ≈ target_count
    # voxel_size ≈ (volume / target_count)^(1/3)
    if target_count > 0:
        voxel_size = (bbox_volume / target_count) ** (1/3)
    else:
        voxel_size = 1.0

    # 限制在合理范围内
    return max(0.05, min(voxel_size, 5.0))
