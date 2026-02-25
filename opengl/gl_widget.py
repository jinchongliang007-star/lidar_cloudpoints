"""
OpenGL渲染控件 - 核心渲染逻辑，支持点云处理
"""

import time
from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *

from opengl.camera import Camera
from opengl.scene import Scene
from processing.pipeline import ProcessingPipeline, ProcessingResult


class GLWidget(QOpenGLWidget):
    """OpenGL渲染控件"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 相机和场景
        self.camera = Camera()
        self.scene = Scene()

        # 处理流水线
        self.pipeline = ProcessingPipeline()
        self.pipeline.set_on_result_updated(self._on_processing_result_updated)

        # 鼠标交互
        self.last_mouse_pos = None
        self.mouse_button = None

        # 动画计时
        self.last_time = time.time()
        self.fps = 0.0
        self.frame_count = 0
        self.fps_update_time = time.time()

        # 动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(16)  # ~60 FPS

        # 设置焦点策略
        self.setFocusPolicy(Qt.StrongFocus)

    def initializeGL(self):
        """初始化OpenGL"""
        # 背景颜色
        glClearColor(0.15, 0.15, 0.18, 1.0)

        # 启用深度测试
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        # 启用混合
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # 启用光照
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # 设置光源
        glLightfv(GL_LIGHT0, GL_POSITION, [5.0, 10.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

        # 启用平滑
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)

    def resizeGL(self, width, height):
        """调整视口大小"""
        if height == 0:
            height = 1
        glViewport(0, 0, width, height)
        self.camera.apply_projection(width, height)

    def paintGL(self):
        """渲染场景"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # 应用相机视图
        self.camera.apply_view()

        # 渲染场景
        self.scene.render()

    def update_animation(self):
        """更新动画"""
        # 计算时间增量
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time

        # 更新场景
        self.scene.update(dt)

        # 更新相机平滑过渡
        self.camera.update_smooth()

        # 计算FPS
        self.frame_count += 1
        if current_time - self.fps_update_time >= 1.0:
            self.fps = self.frame_count / (current_time - self.fps_update_time)
            self.frame_count = 0
            self.fps_update_time = current_time

        # 请求重绘
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        self.last_mouse_pos = event.pos()
        self.mouse_button = event.button()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.last_mouse_pos is None:
            return

        dx = event.x() - self.last_mouse_pos.x()
        dy = event.y() - self.last_mouse_pos.y()

        if self.mouse_button == Qt.LeftButton:
            # 左键旋转视角
            self.camera.rotate(dx * 0.5, -dy * 0.5)

        self.last_mouse_pos = event.pos()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        self.last_mouse_pos = None
        self.mouse_button = None

    def wheelEvent(self, event):
        """鼠标滚轮事件"""
        delta = event.angleDelta().y() / 120.0
        self.camera.zoom(-delta * 0.5)

    def _on_processing_result_updated(self, result: ProcessingResult):
        """处理结果更新回调"""
        self.scene.set_processing_result(result)
        self.scene.set_cluster_colors(self.pipeline.get_cluster_colors())

    def set_rotation_speed(self, speed):
        """设置旋转速度 (RPM)"""
        self.scene.rotation_speed = speed

    def set_laser_lines(self, lines):
        """设置激光线数"""
        self.scene.laser_lines = lines

    def set_vertical_fov(self, fov):
        """设置垂直视场角"""
        self.scene.vertical_fov = fov

    def set_component_visible(self, component, visible):
        """设置组件可见性"""
        if component in self.scene.visible_components:
            self.scene.visible_components[component] = visible

    def set_preset_view(self, view_name):
        """设置预设视角"""
        self.camera.set_preset_view(view_name)

    def reset_view(self):
        """重置视角"""
        self.camera.reset()

    def get_fps(self):
        """获取当前帧率"""
        return self.fps

    def get_rotation_angle(self):
        """获取当前旋转角度"""
        return self.scene.rotation_angle

    # 点云处理相关方法
    def set_processing_stage(self, stage: str):
        """设置处理阶段"""
        self.pipeline.set_stage(stage)

    def set_voxel_size(self, size: float):
        """设置体素大小"""
        self.pipeline.set_voxel_size(size)

    def set_eps(self, eps: float):
        """设置DBSCAN eps参数"""
        self.pipeline.set_eps(eps)

    def set_min_samples(self, min_samples: int):
        """设置DBSCAN min_samples参数"""
        self.pipeline.set_min_samples(min_samples)

    def reprocess(self):
        """重新处理点云"""
        # 更新原始点云数据
        raw_points = self.scene.get_raw_point_cloud()
        self.pipeline.set_raw_point_cloud(raw_points)

        # 重新处理当前阶段
        self.pipeline.reprocess_current_stage()

    def update_point_cloud_data(self):
        """更新点云数据到处理流水线"""
        raw_points = self.scene.get_raw_point_cloud()
        self.pipeline.set_raw_point_cloud(raw_points)

    def get_pipeline(self) -> ProcessingPipeline:
        """获取处理流水线"""
        return self.pipeline

    def get_scene(self) -> Scene:
        """获取场景"""
        return self.scene
