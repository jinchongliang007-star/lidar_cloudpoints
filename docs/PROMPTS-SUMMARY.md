# 点云处理仿真系统 - 复现提示词

本文档包含复现整个项目所需的关键提示词和技术要点。

---

## 项目概述

### 一句话描述
创建一个 Python 桌面应用程序，用于演示激光雷达点云的生成、下采样和聚类处理过程。

### 核心功能
1. LiDAR 点云生成（射线碰撞检测）
2. 体素网格下采样
3. DBSCAN 密度聚类
4. 边界框计算与显示
5. 多阶段可视化（原始→下采样→聚类）

---

## 技术栈

```
- GUI 框架: PyQt5
- 3D 渲染: PyOpenGL
- 数学计算: NumPy
- 空间索引: scipy.spatial.cKDTree
- 动画计时: QTimer
```

---

## 项目结构提示词

```
创建以下项目结构：

lidar_cloudpoints/
├── main.py                      # 程序入口
├── requirements.txt             # PyQt5, PyOpenGL, numpy, scipy
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # 主窗口，左侧OpenGL+右侧控制面板
│   ├── control_panel.py         # 扫描参数控制
│   └── pipeline_panel.py        # 处理流程控制面板
├── opengl/
│   ├── __init__.py
│   ├── gl_widget.py             # QOpenGLWidget，渲染循环60fps
│   ├── scene.py                 # 场景管理，多阶段点云渲染
│   ├── camera.py                # 球坐标系相机，预设视角
│   └── environment.py           # 环境、射线碰撞检测
├── processing/
│   ├── __init__.py
│   ├── downsampling.py          # 体素网格、随机采样
│   ├── clustering.py            # DBSCAN聚类、边界框
│   └── pipeline.py              # 处理流水线
└── data/
    ├── __init__.py
    └── point_cloud.py           # 点云数据结构
```

---

## 模块实现提示词

### 1. 数据结构 (data/point_cloud.py)

```
创建 NumPy 点云类：

属性：
- _points: Nx3 的 np.ndarray (x, y, z)
- _labels: N 的 np.ndarray (标签)

方法：
- from_scene_data(): 从场景数据创建
- get_bounds(): 获取边界框
- select_by_index(): 按索引选择
- select_by_label(): 按标签选择
- get_statistics(): 获取统计信息
```

### 2. 下采样算法 (processing/downsampling.py)

```python
# 体素网格下采样
def voxel_grid_downsample(cloud, voxel_size):
    """
    1. 计算每个点的体素索引
    2. 为每个体素创建唯一键
    3. 同一体素内的点取质心
    4. 返回降采样后的点云
    """
    # 体素索引计算
    voxel_indices = np.floor((points - min_bound) / voxel_size).astype(np.int32)

    # 创建唯一键
    voxel_keys = (voxel_indices[:, 0] + shift) * 40001 * 40001 + ...

    # 计算质心
    downsampled_points = np.bincount(inverse_indices, weights=points[:, i]) / count

# 随机下采样
def random_downsample(cloud, target_count, seed=None):
    """均匀随机选取指定数量的点"""
    indices = np.random.choice(num_points, size=target_count, replace=False)
```

### 3. DBSCAN 聚类 (processing/clustering.py)

```python
def dbscan_clustering(cloud, eps, min_samples):
    """
    使用 KDTree 加速的 DBSCAN 聚类

    参数：
    - eps: 邻域半径（米）
    - min_samples: 核心点的最小邻居数

    返回：聚类标签数组，-1 表示噪声
    """
    # 使用 KDTree 加速邻域搜索
    tree = cKDTree(points)
    neighbors_list = tree.query_ball_point(points, eps)

    # 遍历所有点
    for i in range(num_points):
        if labels[i] != -2:  # 已处理
            continue

        neighbors = neighbors_list[i]

        if len(neighbors) < min_samples:
            labels[i] = -1  # 噪声
            continue

        # 开始新聚类
        labels[i] = cluster_id

        # 扩展聚类（使用队列避免递归）
        seed_set = list(neighbors)
        ...

def compute_bounding_boxes(cloud, labels):
    """为每个聚类计算轴对齐包围盒 (AABB)"""
    for cluster_id in unique_labels:
        mask = labels == cluster_id
        cluster_points = points[mask]
        min_bound = np.min(cluster_points, axis=0)
        max_bound = np.max(cluster_points, axis=0)
```

### 4. 处理流水线 (processing/pipeline.py)

```
创建 ProcessingPipeline 类：

参数：
- voxel_size: 体素大小（米）
- eps: DBSCAN 邻域半径
- min_samples: DBSCAN 最小邻居数

方法：
- set_raw_point_cloud(): 设置原始点云
- process_downsampling(): 执行下采样
- process_clustering(): 执行聚类
- set_stage(): 设置当前阶段 ('raw', 'downsampled', 'clustered')
- get_current_result(): 获取当前阶段结果
- reprocess_current_stage(): 重新处理当前阶段
```

### 5. 扩展环境 (opengl/environment.py)

```
扩展环境模型，添加更多物体：

物体列表：
- Vehicle 1: (4, 0, 0), 4m×1.8m×1.2m, 蓝色
- Vehicle 2: (-3, 0, 5), 4m×1.8m×1.2m, 蓝色
- Wall 1: (7, 2, 0), 0.2m×4m×10m, 黄色
- Wall 2: (0, 2, -8), 10m×4m×0.2m, 黄色
- Tree: (-5, 0, -3), r=0.3m, h=3m, 深绿色
- Pole: (6, 0, 5), r=0.15m, h=4m, 灰色
- Obstacle: (-2, 0, 7), 1m×1m×1m, 橙色

类设计：
- Box: 长方体，Slab 方法射线相交
- Cylinder: 圆柱，二次方程法射线相交
- Vehicle: 组合几何体
- Wall: 包含 Box
- Tree/Pole: 包含 Cylinder
- Environment: 管理所有物体
```

### 6. 多阶段场景渲染 (opengl/scene.py)

```
创建 Scene 类：

处理结果：
- processing_result: ProcessingResult 实例
- current_stage: 当前阶段
- cluster_colors: 聚类颜色列表

渲染方法：
- _draw_raw_point_cloud(): 按物体类型着色
- _draw_processed_point_cloud(): 根据阶段着色
  - 原始/下采样: 按物体类型着色
  - 聚类: 每个簇不同颜色，噪声灰色
- _draw_bounding_boxes(): 绘制边界框

真实感效果：
- 距离相关的测量噪声
- 入射角影响检测概率
- 随机 dropout
```

### 7. 处理流程面板 (ui/pipeline_panel.py)

```
创建 PipelinePanel 类：

阶段选择：
- [ ] 原始点云
- [ ] 下采样后
- [ ] 聚类后

下采样参数：
- 体素大小滑块 (0.05m - 1.0m)

聚类参数：
- 邻域半径滑块 (0.1m - 2.0m)
- 最小邻居数滑块 (1 - 20)

统计信息：
- 点数、簇数、噪声点数

信号：
- stage_changed(str)
- voxel_size_changed(float)
- eps_changed(float)
- min_samples_changed(int)
- reprocess_requested()
```

---

## 关键算法提示词

### 体素网格下采样

```
算法原理：
1. 将空间划分为指定大小的立方体（体素）
2. 计算每个点所属的体素索引
3. 同一体素内的点取质心作为代表点

优点：
- 均匀降采样
- 保持点云空间分布特征
- 体素大小可控
```

### DBSCAN 聚类

```
算法原理：
1. 对每个点，找出 eps 半径内的所有邻居
2. 如果邻居数 >= min_samples，该点为核心点
3. 核心点及其密度可达的点组成一个簇
4. 不属于任何簇的点为噪声

优点：
- 不需要预设簇数量
- 能发现任意形状的簇
- 能识别噪声点

参数选择：
- eps: 通常取 k-distance 图的拐点
- min_samples: 通常为维度+1或更大
```

### 边界框 (AABB)

```
轴对齐包围盒计算：
- min_bound = np.min(cluster_points, axis=0)
- max_bound = np.max(cluster_points, axis=0)
- center = (min_bound + max_bound) / 2
- size = max_bound - min_bound
```

---

## 运行和测试

### 安装依赖

```bash
pip install PyQt5 PyOpenGL numpy scipy
```

### 运行程序

```bash
python main.py
```

### 验证清单

- [ ] 窗口正常显示，左侧 3D 视图，右侧双面板
- [ ] LiDAR 模型正确渲染
- [ ] 多个环境物体正确显示
- [ ] 原始点云按物体类型着色
- [ ] 切换到下采样阶段，点数减少
- [ ] 切换到聚类阶段，显示不同颜色簇
- [ ] 边界框正确显示在每个簇周围
- [ ] 参数调整后"重新处理"生效

---

## 快捷键

| 键 | 功能 |
|----|------|
| R | 重置视角 |
| 1 | 俯视图 |
| 2 | 正视图 |
| 3 | 侧视图 |
| 4 | 透视图 |
| 5 | 等轴视图 |
| ESC | 退出 |

---

## 完整复现流程

```
1. 创建项目结构和 requirements.txt
2. 实现 data/point_cloud.py 点云类
3. 实现 processing/downsampling.py 下采样
4. 实现 processing/clustering.py 聚类
5. 实现 processing/pipeline.py 流水线
6. 实现 opengl/environment.py 扩展环境
7. 实现 opengl/scene.py 多阶段渲染
8. 实现 opengl/gl_widget.py OpenGL 控件
9. 实现 ui/control_panel.py 扫描控制
10. 实现 ui/pipeline_panel.py 处理控制
11. 实现 ui/main_window.py 主窗口
12. 实现 main.py 入口
13. 运行测试
14. 生成文档
```

---

*本文档可用于指导 AI 助手复现整个项目*
