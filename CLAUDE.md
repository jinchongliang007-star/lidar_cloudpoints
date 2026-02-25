# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Point Cloud Processing Simulation System** - a Python desktop application for demonstrating LiDAR point cloud generation, downsampling, and clustering algorithms. The system builds upon the LiDAR architecture from `../lidar_architecture/` and extends it with point cloud processing capabilities.

## Running the Application

```bash
python main.py
```

## Dependencies

```
PyQt5>=5.15
PyOpenGL>=3.1.5
numpy>=1.21
scipy>=1.7.0
```

Install with: `pip install -r requirements.txt`

## Architecture

The codebase follows a layered architecture:

### UI Layer (`ui/`)
- `main_window.py`: QMainWindow with QSplitter layout (OpenGL view + control panels)
- `control_panel.py`: LiDAR scan parameter controls (RPM, laser lines, FOV)
- `pipeline_panel.py`: Processing pipeline controls (stage selection, downsampling, clustering parameters)

### OpenGL Rendering Layer (`opengl/`)
- `gl_widget.py`: QOpenGLWidget managing OpenGL context, 60fps animation, integrates ProcessingPipeline
- `camera.py`: Spherical coordinate camera with smooth transitions and preset views
- `scene.py`: Scene manager with multi-stage point cloud rendering and bounding box visualization
- `environment.py`: Extended environment with Vehicle×2, Wall×2, Tree, Pole, Obstacle objects

### Processing Layer (`processing/`)
- `downsampling.py`: Voxel grid downsampling and random sampling algorithms
- `clustering.py`: DBSCAN clustering with KDTree acceleration, bounding box computation
- `pipeline.py`: Processing pipeline managing stage transitions and result caching

### Data Layer (`data/`)
- `point_cloud.py`: NumPy-based point cloud class with labels and statistics

## Key Algorithms

### Point Cloud Generation
- 360° horizontal scan at 1° resolution
- Ray-AABB intersection (Slab method)
- Ray-Cylinder intersection (Quadratic equation)

### Downsampling
- **Voxel Grid**: Space partitioning with centroid aggregation
- **Random**: Uniform random point selection

### Clustering
- **DBSCAN**: Density-based clustering with cKDTree neighbor search
- **Bounding Box**: AABB computation per cluster

## Data Flow

1. Scene generates raw point cloud via ray casting
2. ProcessingPipeline receives raw data
3. User selects processing stage (raw/downsampled/clustered)
4. Pipeline processes and caches results
5. Scene renders current stage with appropriate coloring
6. UI panels display statistics

## Adjustable Parameters

### LiDAR Parameters
- `rotation_speed`: 1-20 RPM
- `laser_lines`: 1-64
- `vertical_fov`: 10-45°

### Processing Parameters
- `voxel_size`: 0.05-1.0m
- `eps`: 0.1-2.0m (DBSCAN neighborhood radius)
- `min_samples`: 1-20 (DBSCAN minimum neighbors)

## Keyboard Shortcuts

- `R`: Reset view
- `1-5`: Preset views (top, front, side, perspective, isometric)
- `ESC`: Exit

## Code Conventions

- Chinese comments throughout
- PyQt signals/slots for UI-to-renderer communication
- QTimer for 60fps animation loop
- Immediate mode OpenGL (glBegin/glEnd style)
- NumPy for efficient array operations
- scipy.cKDTree for spatial queries
