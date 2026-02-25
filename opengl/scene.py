"""
场景管理类 - 管理和渲染所有3D对象，支持多阶段渲染
"""

from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
from typing import List, Tuple, Optional

from opengl.environment import Environment
from processing.pipeline import ProcessingResult


class Scene:
    """场景管理类"""

    def __init__(self):
        # 场景参数
        self.rotation_angle = 0.0  # 当前旋转角度
        self.rotation_speed = 10.0  # 转速 (RPM)
        self.laser_lines = 16  # 激光线数
        self.vertical_fov = 30.0  # 垂直视场角

        # 可见性控制
        self.visible_components = {
            'body': True,
            'laser_unit': True,
            'laser_beam': True,
            'environment': True,
            'point_cloud': True,
        }

        # 环境模型
        self.environment = Environment()

        # 点云数据（原始场景点云）
        self.point_cloud_data = []
        self.point_cloud_update_counter = 0
        self.point_cloud_update_interval = 5  # 每5帧更新一次点云（减少更新频率）
        self.generate_point_cloud()

        # 处理结果
        self.processing_result: Optional[ProcessingResult] = None
        self.current_stage = 'raw'

        # 聚类颜色
        self.cluster_colors = []

        # 颜色定义
        self.colors = {
            'body': (0.3, 0.3, 0.35, 1.0),
            'laser_emitter': (0.8, 0.2, 0.2, 1.0),
            'laser_receiver': (0.2, 0.6, 0.2, 1.0),
            'laser_beam': (1.0, 0.0, 0.0, 1.0),
        }

        # 物体类型颜色
        self.object_type_colors = {
            'vehicle': (0.2, 0.5, 1.0, 0.9),    # 蓝色
            'wall': (1.0, 0.8, 0.2, 0.9),       # 黄色
            'ground': (0.2, 0.8, 0.3, 0.9),     # 绿色
            'tree': (0.3, 0.6, 0.2, 0.9),       # 深绿色
            'pole': (0.5, 0.5, 0.5, 0.9),       # 灰色
            'obstacle': (0.9, 0.5, 0.1, 0.9),   # 橙色
            'unknown': (0.7, 0.7, 0.7, 0.8),    # 默认灰色
        }

    def generate_point_cloud(self):
        """
        根据LiDAR参数和环境碰撞生成更真实的点云数据（优化版）

        模拟真实激光雷达的特性:
        1. 距离相关的测量噪声 - 远处点误差更大
        2. 入射角影响检测概率 - 斜入射可能丢失
        3. 边缘效应 - 物体边缘点不稳定
        4. 反射率差异 - 某些点可能丢失
        """
        self.point_cloud_data = []

        # LiDAR位置（在原点上方）
        lidar_origin = np.array([0.35, 0.4, 0])

        # 水平扫描分辨率（度）
        horizontal_resolution = 1.0

        # 真实LiDAR参数模拟
        distance_noise_base = 0.02
        distance_noise_factor = 0.005
        dropout_probability = 0.02

        # 预生成随机数用于dropout判断（向量化）
        num_h_angles = int(360 / horizontal_resolution)
        total_rays = num_h_angles * self.laser_lines
        random_values = np.random.random(total_rays)

        ray_idx = 0
        # 一次遍历完成所有处理
        for h_angle in np.arange(0, 360, horizontal_resolution):
            h_rad = math.radians(h_angle)

            for i in range(self.laser_lines):
                v_angle = -self.vertical_fov / 2 + self.vertical_fov * i / max(1, self.laser_lines - 1)
                v_rad = math.radians(v_angle)

                # 计算射线方向
                dx = math.cos(v_rad) * math.cos(h_rad)
                dy = math.sin(v_rad)
                dz = math.cos(v_rad) * math.sin(h_rad)
                direction = np.array([dx, dy, dz])

                # 发射射线
                hit_point, distance, hit_object = self.environment.ray_cast(lidar_origin, direction)

                if hit_point is None:
                    ray_idx += 1
                    continue

                # 简化的入射角检测
                if hit_object == 'ground':
                    cos_incidence = abs(dy)  # 地面法向量是(0,1,0)
                else:
                    cos_incidence = 0.8  # 其他物体假设入射角较好

                # 入射角导致的dropout（简化）
                if cos_incidence < 0.3 and random_values[ray_idx] < 0.3:
                    ray_idx += 1
                    continue

                # 距离相关的dropout
                if distance > 10 and random_values[ray_idx] < 0.1:
                    ray_idx += 1
                    continue

                # 基础随机dropout
                if random_values[ray_idx] < dropout_probability:
                    ray_idx += 1
                    continue

                # 添加距离相关的测量噪声
                noise_std = distance_noise_base + distance * distance_noise_factor
                noisy_point = hit_point + np.random.normal(0, noise_std, 3)

                # 角度抖动（简化版）
                jitter = np.random.normal(0, noise_std * 0.5, 3)
                noisy_point += jitter

                self.point_cloud_data.append((
                    float(noisy_point[0]),
                    float(noisy_point[1]),
                    float(noisy_point[2]),
                    hit_object
                ))

                ray_idx += 1

    def set_processing_result(self, result: ProcessingResult):
        """设置处理结果"""
        self.processing_result = result
        self.current_stage = result.stage

    def set_cluster_colors(self, colors: List[Tuple[float, float, float]]):
        """设置聚类颜色"""
        self.cluster_colors = colors

    def get_raw_point_cloud(self) -> List[Tuple]:
        """获取原始点云数据"""
        return self.point_cloud_data

    def update(self, dt):
        """更新场景状态"""
        # 计算旋转角度增量
        angle_per_second = self.rotation_speed * 6.0
        self.rotation_angle += angle_per_second * dt
        self.rotation_angle %= 360.0

        # 定期更新点云（为了性能，不是每帧都更新）
        self.point_cloud_update_counter += 1
        if self.point_cloud_update_counter >= self.point_cloud_update_interval:
            self.point_cloud_update_counter = 0
            self.generate_point_cloud()

    def render(self):
        """渲染整个场景"""
        # 绘制地面网格
        self._draw_ground_grid()

        # 绘制坐标轴
        self._draw_axes()

        # 渲染环境模型
        if self.visible_components.get('environment', True):
            self.environment.render()

        # 绘制LiDAR主体
        if self.visible_components['body']:
            self._draw_lidar_body()

        # 旋转部分
        glPushMatrix()
        glRotatef(self.rotation_angle, 0, 1, 0)

        # 绘制旋转头
        if self.visible_components['body']:
            self._draw_rotating_head()

        # 绘制激光单元
        if self.visible_components['laser_unit']:
            self._draw_laser_unit()

        # 绘制激光束
        if self.visible_components['laser_beam']:
            self._draw_laser_beams()

        glPopMatrix()

        # 绘制点云
        if self.visible_components['point_cloud']:
            self._draw_point_cloud()

    def _draw_ground_grid(self):
        """绘制地面网格"""
        glDisable(GL_LIGHTING)
        glColor4f(0.3, 0.3, 0.3, 0.5)
        glLineWidth(1.0)

        glBegin(GL_LINES)
        grid_size = 10
        for i in range(-grid_size, grid_size + 1):
            glVertex3f(i, -2.0, -grid_size)
            glVertex3f(i, -2.0, grid_size)
            glVertex3f(-grid_size, -2.0, i)
            glVertex3f(grid_size, -2.0, i)
        glEnd()

        glEnable(GL_LIGHTING)

    def _draw_axes(self):
        """绘制坐标轴"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)

        glBegin(GL_LINES)
        # X轴 - 红色
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(2, 0, 0)
        # Y轴 - 绿色
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 2, 0)
        # Z轴 - 蓝色
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 2)
        glEnd()

        glEnable(GL_LIGHTING)
        glLineWidth(1.0)

    def _draw_lidar_body(self):
        """绘制LiDAR外壳"""
        glColor4fv(self.colors['body'])

        # 底座圆柱
        glPushMatrix()
        glTranslatef(0, -1.5, 0)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.6, 0.6, 0.3, 32, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

        # 底座圆盘
        glPushMatrix()
        glTranslatef(0, -1.2, 0)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glRotatef(-90, 1, 0, 0)
        gluDisk(quadric, 0, 0.6, 32, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

        # 主体圆柱
        glPushMatrix()
        glTranslatef(0, -1.2, 0)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.5, 0.5, 1.2, 32, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

    def _draw_rotating_head(self):
        """绘制旋转头"""
        glColor4fv(self.colors['body'])

        # 旋转头圆柱
        glPushMatrix()
        glTranslatef(0, 0.2, 0)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(quadric, 0.4, 0.4, 0.4, 32, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

        # 旋转头顶部圆盘
        glPushMatrix()
        glTranslatef(0, 0.6, 0)
        quadric = gluNewQuadric()
        gluQuadricNormals(quadric, GLU_SMOOTH)
        glRotatef(-90, 1, 0, 0)
        gluDisk(quadric, 0, 0.4, 32, 1)
        gluDeleteQuadric(quadric)
        glPopMatrix()

    def _draw_laser_unit(self):
        """绘制激光发射/接收单元"""
        # 发射器阵列（红色）
        glColor4fv(self.colors['laser_emitter'])
        for i in range(self.laser_lines):
            angle = -self.vertical_fov / 2 + self.vertical_fov * i / max(1, self.laser_lines - 1)

            glPushMatrix()
            glTranslatef(0.35, 0.4, 0)
            glRotatef(angle, 0, 0, 1)

            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quadric, 0.02, 0.02, 0.1, 8, 1)
            gluDeleteQuadric(quadric)
            glPopMatrix()

        # 接收器阵列（绿色）
        glColor4fv(self.colors['laser_receiver'])
        for i in range(self.laser_lines):
            angle = -self.vertical_fov / 2 + self.vertical_fov * i / max(1, self.laser_lines - 1)

            glPushMatrix()
            glTranslatef(-0.35, 0.4, 0)
            glRotatef(angle, 0, 0, 1)

            quadric = gluNewQuadric()
            gluQuadricNormals(quadric, GLU_SMOOTH)
            glRotatef(-90, 1, 0, 0)
            gluCylinder(quadric, 0.025, 0.025, 0.08, 8, 1)
            gluDeleteQuadric(quadric)
            glPopMatrix()

    def _draw_laser_beams(self):
        """绘制激光束"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)

        beam_length = 5.0

        for i in range(self.laser_lines):
            t = i / max(1, self.laser_lines - 1)
            r = 1.0
            g = 0.2 + t * 0.3
            b = 0.0
            glColor4f(r, g, b, 0.8)

            angle = -self.vertical_fov / 2 + self.vertical_fov * i / max(1, self.laser_lines - 1)
            angle_rad = math.radians(angle)

            start_x = 0.35 + 0.1 * math.cos(angle_rad)
            start_y = 0.4 + 0.1 * math.sin(angle_rad)
            start_z = 0

            end_x = start_x + beam_length * math.cos(angle_rad)
            end_y = start_y + beam_length * math.sin(angle_rad)
            end_z = start_z

            glBegin(GL_LINES)
            glVertex3f(start_x, start_y, start_z)
            glVertex3f(end_x, end_y, end_z)
            glEnd()

        glEnable(GL_LIGHTING)
        glLineWidth(1.0)

    def _draw_point_cloud(self):
        """绘制点云（根据当前阶段）"""
        if self.processing_result is not None:
            # 使用处理后的点云
            self._draw_processed_point_cloud()
        else:
            # 绘制原始点云
            self._draw_raw_point_cloud()

    def _draw_raw_point_cloud(self):
        """绘制原始点云（按物体类型着色）"""
        glDisable(GL_LIGHTING)
        glPointSize(3.0)

        glBegin(GL_POINTS)

        for point in self.point_cloud_data:
            x, y, z = point[0], point[1], point[2]
            hit_type = point[3] if len(point) > 3 else 'unknown'

            color = self.object_type_colors.get(hit_type, self.object_type_colors['unknown'])
            glColor4fv(color)
            glVertex3f(x, y, z)

        glEnd()
        glEnable(GL_LIGHTING)
        glPointSize(1.0)

    def _draw_processed_point_cloud(self):
        """绘制处理后的点云"""
        result = self.processing_result
        points = result.point_cloud.points

        glDisable(GL_LIGHTING)
        glPointSize(3.0)

        if result.stage == 'clustered' and result.cluster_labels is not None:
            # 聚类阶段：每个簇不同颜色
            labels = result.cluster_labels

            glBegin(GL_POINTS)
            for i, (point, label) in enumerate(zip(points, labels)):
                if label < 0:
                    # 噪声点 - 灰色
                    glColor4f(0.5, 0.5, 0.5, 0.7)
                else:
                    # 获取簇颜色
                    if label < len(self.cluster_colors):
                        color = self.cluster_colors[label]
                    else:
                        # 如果颜色不够，生成一个
                        color = (0.7, 0.7, 0.7)
                    glColor4f(color[0], color[1], color[2], 0.9)

                glVertex3f(point[0], point[1], point[2])
            glEnd()

            # 绘制边界框
            if result.bounding_boxes:
                self._draw_bounding_boxes(result.bounding_boxes)
        else:
            # 原始或下采样阶段：按物体类型着色
            glBegin(GL_POINTS)
            for i, point in enumerate(points):
                # 使用默认颜色渐变
                dist = np.linalg.norm(point)
                max_dist = 15.0
                t = min(1.0, dist / max_dist)

                r = 0.2 + t * 0.3
                g = 0.6 - t * 0.2
                b = 0.9 - t * 0.4
                glColor4f(r, g, b, 0.9)
                glVertex3f(point[0], point[1], point[2])
            glEnd()

        glEnable(GL_LIGHTING)
        glPointSize(1.0)

    def _draw_bounding_boxes(self, bounding_boxes: List[dict]):
        """绘制边界框"""
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)

        for i, bbox in enumerate(bounding_boxes):
            # 获取边界框颜色
            if i < len(self.cluster_colors):
                color = self.cluster_colors[i]
            else:
                color = (1.0, 1.0, 1.0)

            glColor4f(color[0], color[1], color[2], 1.0)

            min_b = bbox['min_bound']
            max_b = bbox['max_bound']

            # 绘制边界框的12条边
            self._draw_box_edges(min_b, max_b)

        glEnable(GL_LIGHTING)
        glLineWidth(1.0)

    def _draw_box_edges(self, min_b: np.ndarray, max_b: np.ndarray):
        """绘制边界框的边"""
        x0, y0, z0 = min_b
        x1, y1, z1 = max_b

        glBegin(GL_LINES)
        # 底面
        glVertex3f(x0, y0, z0); glVertex3f(x1, y0, z0)
        glVertex3f(x1, y0, z0); glVertex3f(x1, y0, z1)
        glVertex3f(x1, y0, z1); glVertex3f(x0, y0, z1)
        glVertex3f(x0, y0, z1); glVertex3f(x0, y0, z0)
        # 顶面
        glVertex3f(x0, y1, z0); glVertex3f(x1, y1, z0)
        glVertex3f(x1, y1, z0); glVertex3f(x1, y1, z1)
        glVertex3f(x1, y1, z1); glVertex3f(x0, y1, z1)
        glVertex3f(x0, y1, z1); glVertex3f(x0, y1, z0)
        # 垂直边
        glVertex3f(x0, y0, z0); glVertex3f(x0, y1, z0)
        glVertex3f(x1, y0, z0); glVertex3f(x1, y1, z0)
        glVertex3f(x1, y0, z1); glVertex3f(x1, y1, z1)
        glVertex3f(x0, y0, z1); glVertex3f(x0, y1, z1)
        glEnd()
