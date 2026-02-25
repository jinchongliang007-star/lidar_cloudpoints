# 点云处理仿真系统 - 设计文档

## 1. 项目概述

### 1.1 目标
创建一个教学演示系统，展示激光雷达点云的生成、下采样和聚类处理过程。

### 1.2 功能需求
- LiDAR 点云生成与可视化
- 体素网格下采样
- DBSCAN 密度聚类
- 边界框计算与显示
- 多阶段切换展示

## 2. 系统架构

### 2.1 模块划分

| 模块 | 职责 |
|------|------|
| `ui/` | 用户界面（主窗口、控制面板、处理面板） |
| `opengl/` | 3D 渲染（场景、相机、环境、OpenGL 控件） |
| `processing/` | 点云处理（下采样、聚类、流水线） |
| `data/` | 数据结构（点云类） |

### 2.2 数据流

```
用户输入 → 控制面板 → GLWidget → Scene
                           ↓
                      ProcessingPipeline
                           ↓
                    ProcessingResult → Scene 渲染
```

## 3. 核心算法

### 3.1 体素网格下采样
- 输入: Nx3 点云，体素大小 v
- 输出: 降采样后的点云
- 复杂度: O(N)

### 3.2 DBSCAN 聚群
- 输入: Nx3 点云，eps，min_samples
- 输出: 聚类标签，边界框
- 复杂度: O(N log N) 使用 KDTree

## 4. 环境物体

| 物体 | 位置 | 尺寸 | 类型 |
|------|------|------|------|
| Vehicle 1 | (4, 0, 0) | 4×1.8×1.2m | Box 组合 |
| Vehicle 2 | (-3, 0, 5) | 4×1.8×1.2m | Box 组合 |
| Wall 1 | (7, 2, 0) | 0.2×4×10m | Box |
| Wall 2 | (0, 2, -8) | 10×4×0.2m | Box |
| Tree | (-5, 0, -3) | r=0.3, h=3m | Cylinder |
| Pole | (6, 0, 5) | r=0.15, h=4m | Cylinder |
| Obstacle | (-2, 0, 7) | 1×1×1m | Box |

## 5. UI 设计

### 5.1 布局
```
┌─────────────────────────────────────────┬──────────────┐
│                                         │ 扫描参数控制  │
│           3D 渲染区域                    ├──────────────┤
│                                         │ 点云处理控制  │
│                                         │ - 阶段选择    │
│                                         │ - 下采样参数  │
│                                         │ - 聚类参数    │
│                                         │ - 统计信息    │
└─────────────────────────────────────────┴──────────────┘
```

### 5.2 交互
- 鼠标拖拽旋转视角
- 滚轮缩放
- 滑块调参数
- 按钮切换阶段

## 6. 技术选型

| 组件 | 技术 | 版本 |
|------|------|------|
| GUI | PyQt5 | ≥5.15 |
| 3D 渲染 | PyOpenGL | ≥3.1.5 |
| 数学计算 | NumPy | ≥1.21 |
| 空间索引 | scipy.cKDTree | ≥1.7.0 |

## 7. 文件清单

```
lidar_cloudpoints/
├── main.py
├── requirements.txt
├── CLAUDE.md
├── README.md
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── control_panel.py
│   └── pipeline_panel.py
├── opengl/
│   ├── __init__.py
│   ├── gl_widget.py
│   ├── camera.py
│   ├── scene.py
│   └── environment.py
├── processing/
│   ├── __init__.py
│   ├── downsampling.py
│   ├── clustering.py
│   └── pipeline.py
├── data/
│   ├── __init__.py
│   └── point_cloud.py
└── docs/
    ├── DOCUMENTATION-GUIDE.md
    ├── PROMPTS-SUMMARY.md
    ├── plans/
    └── textbook/
        └── point-cloud-processing-material.md
```

## 8. 实现状态

- [x] 项目结构
- [x] 数据结构 (PointCloud)
- [x] 下采样算法
- [x] 聚类算法
- [x] 处理流水线
- [x] 环境物体扩展
- [x] 多阶段渲染
- [x] UI 面板
- [x] 文档

---

*设计日期：2026年2月24日*
