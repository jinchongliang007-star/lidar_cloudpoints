"""
主窗口 - 整合OpenGL控件、控制面板和处理流程面板
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QStatusBar, QSplitter, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from opengl.gl_widget import GLWidget
from ui.control_panel import ControlPanel
from ui.pipeline_panel import PipelinePanel


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("点云处理仿真系统 - Point Cloud Processing Simulation")
        self.setMinimumSize(1400, 900)

        self._setup_ui()
        self._connect_signals()

        # 状态栏更新定时器
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(100)

        # 初始化点云数据
        QTimer.singleShot(500, self._initialize_point_cloud)

    def _setup_ui(self):
        """设置UI"""
        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # OpenGL控件
        self.gl_widget = GLWidget()

        # 右侧面板容器
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # 扫描参数控制面板
        self.control_panel = ControlPanel()

        # 处理流程面板
        self.pipeline_panel = PipelinePanel()

        # 将两个面板添加到右侧布局
        right_layout.addWidget(self.control_panel)
        right_layout.addWidget(self.pipeline_panel)
        right_layout.addStretch()

        # 创建可滚动的右侧面板
        scroll_area = QScrollArea()
        scroll_area.setWidget(right_panel)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(280)
        scroll_area.setMaximumWidth(320)

        # 使用Splitter实现可调整布局
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.gl_widget)
        splitter.addWidget(scroll_area)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        main_layout.addWidget(splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 状态标签
        self.fps_label = QLabel("FPS: 0")
        self.angle_label = QLabel("角度: 0°")
        self.points_label = QLabel("点数: 0")
        self.stage_label = QLabel("阶段: 原始")

        self.status_bar.addPermanentWidget(self.fps_label)
        self.status_bar.addPermanentWidget(self.angle_label)
        self.status_bar.addPermanentWidget(self.points_label)
        self.status_bar.addPermanentWidget(self.stage_label)
        self.status_bar.showMessage("就绪 - 拖拽鼠标旋转视角，滚轮缩放")

        # 设置样式
        self._set_style()

    def _set_style(self):
        """设置窗口样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QWidget {
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QStatusBar {
                color: #000000;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #000000;
            }
            QPushButton {
                padding: 5px 10px;
                border: 1px solid #aaa;
                border-radius: 3px;
                background-color: #f8f8f8;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #e8e8e8;
            }
            QPushButton:pressed {
                background-color: #d8d8d8;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #ddd;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 16px;
                margin: -5px 0;
                background: #3498db;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
            QCheckBox {
                spacing: 8px;
                color: #000000;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton {
                spacing: 8px;
                color: #000000;
            }
            QScrollArea {
                border: none;
            }
        """)

    def _connect_signals(self):
        """连接信号"""
        # 扫描参数
        self.control_panel.rotation_speed_changed.connect(
            self.gl_widget.set_rotation_speed
        )
        self.control_panel.laser_lines_changed.connect(
            self.gl_widget.set_laser_lines
        )
        self.control_panel.vertical_fov_changed.connect(
            self.gl_widget.set_vertical_fov
        )

        # 可见性控制
        self.control_panel.component_visibility_changed.connect(
            self.gl_widget.set_component_visible
        )

        # 视角控制
        self.control_panel.preset_view_requested.connect(
            self.gl_widget.set_preset_view
        )
        self.control_panel.reset_view_requested.connect(
            self.gl_widget.reset_view
        )

        # 处理流程面板信号
        self.pipeline_panel.stage_changed.connect(
            self._on_stage_changed
        )
        self.pipeline_panel.voxel_size_changed.connect(
            self.gl_widget.set_voxel_size
        )
        self.pipeline_panel.eps_changed.connect(
            self.gl_widget.set_eps
        )
        self.pipeline_panel.min_samples_changed.connect(
            self.gl_widget.set_min_samples
        )
        self.pipeline_panel.reprocess_requested.connect(
            self._on_reprocess
        )

    def _initialize_point_cloud(self):
        """初始化点云数据"""
        self.gl_widget.update_point_cloud_data()
        self._on_stage_changed('raw')

    def _on_stage_changed(self, stage: str):
        """处理阶段改变"""
        self.gl_widget.set_processing_stage(stage)
        self._update_pipeline_stats()
        self._update_stage_label(stage)

    def _on_reprocess(self):
        """重新处理点云"""
        self.gl_widget.reprocess()
        self._update_pipeline_stats()

    def _update_pipeline_stats(self):
        """更新处理统计信息"""
        pipeline = self.gl_widget.get_pipeline()
        result = pipeline.get_current_result()

        if result:
            stats = result.statistics
            self.pipeline_panel.update_statistics(stats)
            self.points_label.setText(f"点数: {stats.get('num_points', 0)}")

    def _update_stage_label(self, stage: str):
        """更新阶段标签"""
        stage_names = {
            'raw': '原始',
            'downsampled': '下采样后',
            'clustered': '聚类后',
        }
        self.stage_label.setText(f"阶段: {stage_names.get(stage, stage)}")

    def _update_status(self):
        """更新状态栏"""
        fps = self.gl_widget.get_fps()
        angle = self.gl_widget.get_rotation_angle()

        self.fps_label.setText(f"FPS: {fps:.1f}")
        self.angle_label.setText(f"角度: {angle:.1f}°")

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_R:
            self.gl_widget.reset_view()
        elif event.key() == Qt.Key_1:
            self.gl_widget.set_preset_view('top')
        elif event.key() == Qt.Key_2:
            self.gl_widget.set_preset_view('front')
        elif event.key() == Qt.Key_3:
            self.gl_widget.set_preset_view('side')
        elif event.key() == Qt.Key_4:
            self.gl_widget.set_preset_view('perspective')
        elif event.key() == Qt.Key_5:
            self.gl_widget.set_preset_view('isometric')
