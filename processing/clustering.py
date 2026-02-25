"""
聚类算法 - DBSCAN密度聚类和边界框计算
"""

import numpy as np
from scipy.spatial import cKDTree
from typing import List, Tuple, Optional
from data.point_cloud import PointCloud


def dbscan_clustering(cloud: PointCloud, eps: float, min_samples: int) -> np.ndarray:
    """
    DBSCAN密度聚类算法

    Args:
        cloud: 输入点云
        eps: 邻域半径（米）
        min_samples: 核心点的最小邻居数

    Returns:
        聚类标签数组，-1表示噪声点
    """
    if len(cloud) == 0:
        return np.array([], dtype=np.int32)

    points = cloud.points
    num_points = len(points)

    # 使用KDTree加速邻域搜索
    tree = cKDTree(points)

    # 查询每个点的邻域
    # 返回每个点在eps半径内的邻居数量
    neighbors_list = tree.query_ball_point(points, eps)

    # 初始化标签（-2表示未访问）
    labels = np.full(num_points, -2, dtype=np.int32)

    # 当前聚类ID
    cluster_id = 0

    for i in range(num_points):
        # 如果点已经被处理过，跳过
        if labels[i] != -2:
            continue

        # 获取邻居
        neighbors = neighbors_list[i]

        # 如果邻居数量不足，标记为噪声
        if len(neighbors) < min_samples:
            labels[i] = -1  # 噪声
            continue

        # 开始新的聚类
        labels[i] = cluster_id

        # 使用列表作为队列（避免递归）
        seed_set = list(neighbors)
        seed_set.remove(i)  # 移除自己

        j = 0
        while j < len(seed_set):
            q = seed_set[j]

            if labels[q] == -1:
                # 噪声点转为边界点
                labels[q] = cluster_id
            elif labels[q] == -2:
                # 未访问的点
                labels[q] = cluster_id

                q_neighbors = neighbors_list[q]
                if len(q_neighbors) >= min_samples:
                    # q是核心点，添加其邻居到种子集
                    for n in q_neighbors:
                        if n not in seed_set and labels[n] != cluster_id:
                            seed_set.append(n)

            j += 1

        cluster_id += 1

    return labels


def compute_bounding_box(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    计算点集的轴对齐包围盒 (AABB)

    Args:
        points: Nx3的点坐标数组

    Returns:
        (min_bound, max_bound): 包围盒的最小和最大角点
    """
    if len(points) == 0:
        return np.zeros(3), np.zeros(3)

    min_bound = np.min(points, axis=0)
    max_bound = np.max(points, axis=0)

    return min_bound, max_bound


def compute_bounding_boxes(cloud: PointCloud, labels: np.ndarray) -> List[dict]:
    """
    为每个聚类计算边界框

    Args:
        cloud: 点云数据
        labels: 聚类标签

    Returns:
        边界框信息列表，每个元素包含：
        - cluster_id: 聚类ID
        - min_bound: 最小角点
        - max_bound: 最大角点
        - center: 中心点
        - size: 尺寸
        - num_points: 点数
    """
    bounding_boxes = []
    points = cloud.points

    # 获取唯一的聚类ID（排除噪声 -1）
    unique_labels = np.unique(labels)
    unique_labels = unique_labels[unique_labels >= 0]

    for cluster_id in unique_labels:
        # 获取该聚类的所有点
        mask = labels == cluster_id
        cluster_points = points[mask]

        if len(cluster_points) == 0:
            continue

        # 计算边界框
        min_bound, max_bound = compute_bounding_box(cluster_points)
        center = (min_bound + max_bound) / 2
        size = max_bound - min_bound

        bounding_boxes.append({
            'cluster_id': int(cluster_id),
            'min_bound': min_bound,
            'max_bound': max_bound,
            'center': center,
            'size': size,
            'num_points': int(np.sum(mask)),
        })

    return bounding_boxes


def get_cluster_colors(num_clusters: int) -> List[Tuple[float, float, float]]:
    """
    为聚类生成不同的颜色

    Args:
        num_clusters: 聚类数量

    Returns:
        颜色列表，每个颜色为 (r, g, b) 元组
    """
    # 预定义的区分度高的颜色
    base_colors = [
        (0.0, 0.6, 1.0),    # 天蓝色
        (1.0, 0.4, 0.4),    # 红色
        (0.2, 0.8, 0.2),    # 绿色
        (1.0, 0.8, 0.0),    # 黄色
        (0.8, 0.4, 0.8),    # 紫色
        (1.0, 0.6, 0.2),    # 橙色
        (0.4, 0.8, 0.8),    # 青色
        (0.8, 0.2, 0.6),    # 粉色
        (0.6, 0.6, 0.2),    # 橄榄色
        (0.4, 0.4, 0.8),    # 靛蓝色
    ]

    if num_clusters <= len(base_colors):
        return base_colors[:num_clusters]

    # 如果需要更多颜色，使用HSV色彩空间均匀分布
    import colorsys
    colors = list(base_colors)
    for i in range(len(base_colors), num_clusters):
        hue = (i * 0.618033988749895) % 1.0  # 黄金比例分布
        rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
        colors.append(rgb)

    return colors


def apply_clustering_to_cloud(cloud: PointCloud, labels: np.ndarray) -> PointCloud:
    """
    将聚类标签应用到点云，创建新的点云对象

    Args:
        cloud: 原始点云
        labels: 聚类标签

    Returns:
        新的点云，标签被聚类ID替换
    """
    result = PointCloud()
    result._points = cloud.points.copy()
    # 将标签平移+1，使得噪声点(-1)变成0，第一个聚类(0)变成1
    # 这样可以保留噪声点的信息
    result._labels = labels.copy()

    return result


def get_clustering_statistics(labels: np.ndarray) -> dict:
    """
    获取聚类统计信息

    Args:
        labels: 聚类标签

    Returns:
        统计信息字典
    """
    unique_labels = np.unique(labels)
    num_noise = np.sum(labels == -1)
    num_clusters = len(unique_labels[unique_labels >= 0])

    # 每个聚类的点数
    cluster_sizes = {}
    for label in unique_labels:
        if label >= 0:
            cluster_sizes[int(label)] = int(np.sum(labels == label))

    return {
        'num_clusters': num_clusters,
        'num_noise_points': num_noise,
        'total_points': len(labels),
        'cluster_sizes': cluster_sizes,
    }
