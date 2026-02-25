"""
相机类 - 控制视角和投影
"""

import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *


class Camera:
    """相机类，处理视角变换和投影"""

    def __init__(self):
        # 相机参数
        self.distance = 8.0  # 到目标点的距离
        self.azimuth = 45.0  # 水平角度（度）
        self.elevation = 30.0  # 垂直角度（度）
        self.target = [0.0, 0.0, 0.0]  # 观察目标点

        # 投影参数
        self.fov = 45.0  # 视场角
        self.aspect = 1.0  # 宽高比
        self.near_plane = 0.1  # 近裁剪面
        self.far_plane = 100.0  # 远裁剪面

        # 平滑过渡
        self.target_distance = self.distance
        self.target_azimuth = self.azimuth
        self.target_elevation = self.elevation
        self.smooth_factor = 0.1

    def update_smooth(self):
        """平滑过渡到目标位置"""
        self.distance += (self.target_distance - self.distance) * self.smooth_factor
        self.azimuth += (self.target_azimuth - self.azimuth) * self.smooth_factor
        self.elevation += (self.target_elevation - self.elevation) * self.smooth_factor

    def get_position(self):
        """计算相机位置"""
        az_rad = math.radians(self.azimuth)
        el_rad = math.radians(self.elevation)

        x = self.distance * math.cos(el_rad) * math.sin(az_rad)
        y = self.distance * math.sin(el_rad)
        z = self.distance * math.cos(el_rad) * math.cos(az_rad)

        return [x + self.target[0], y + self.target[1], z + self.target[2]]

    def apply_view(self):
        """应用视图变换"""
        pos = self.get_position()
        gluLookAt(
            pos[0], pos[1], pos[2],
            self.target[0], self.target[1], self.target[2],
            0, 1, 0
        )

    def apply_projection(self, width, height):
        """应用投影变换"""
        self.aspect = width / height if height > 0 else 1.0
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, self.aspect, self.near_plane, self.far_plane)
        glMatrixMode(GL_MODELVIEW)

    def rotate(self, delta_azimuth, delta_elevation):
        """旋转相机（鼠标拖拽）"""
        self.target_azimuth += delta_azimuth
        self.target_elevation += delta_elevation
        # 限制垂直角度
        self.target_elevation = max(-89.0, min(89.0, self.target_elevation))

    def zoom(self, delta):
        """缩放（鼠标滚轮）"""
        self.target_distance += delta
        self.target_distance = max(2.0, min(20.0, self.target_distance))

    def set_preset_view(self, view_name):
        """设置预设视角"""
        presets = {
            'top': (90.0, 0.0, 6.0),
            'front': (0.0, 0.0, 8.0),
            'side': (90.0, 0.0, 8.0),
            'perspective': (45.0, 30.0, 8.0),
            'isometric': (45.0, 35.0, 10.0),
        }
        if view_name in presets:
            az, el, dist = presets[view_name]
            self.target_azimuth = az
            self.target_elevation = el
            self.target_distance = dist

    def reset(self):
        """重置相机"""
        self.target_distance = 8.0
        self.target_azimuth = 45.0
        self.target_elevation = 30.0
