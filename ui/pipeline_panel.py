"""
处理流程面板 - 控制点云处理参数和阶段切换
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QSlider, QLabel, QPushButton, QFrame, QButtonGroup, QRadioButton
)
from PyQt5.QtCore import Qt, pyqtSignal


class PipelinePanel(QWidget):
    """处理流程控制面板"""

    # 信号
    stage_changed = pyqtSignal(str)  # 阶段改变
    voxel_size_changed = pyqtSignal(float)  # 体素大小改变
    eps_changed = pyqtSignal(float)  # DBSCAN eps改变
    min_samples_changed = pyqtSignal(int)  # DBSCAN min_samples改变
    reprocess_requested = pyqtSignal()  # 请求重新处理

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        self.setStyleSheet("""
            QWidget {
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QGroupBox {
                color: #000000;
            }
            QRadioButton {
                color: #000000;
            }
            QPushButton {
                color: #000000;
            }
            QSlider {
                color: #000000;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 标题
        title = QLabel("点云处理")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 处理阶段选择
        stage_group = self._create_stage_group()
        layout.addWidget(stage_group)

        # 下采样参数组
        downsample_group = self._create_downsample_group()
        layout.addWidget(downsample_group)

        # 聚类参数组
        cluster_group = self._create_cluster_group()
        layout.addWidget(cluster_group)

        # 统计信息组
        stats_group = self._create_stats_group()
        layout.addWidget(stats_group)

        # 弹性空间
        layout.addStretch()

    def _create_stage_group(self):
        """创建处理阶段选择组"""
        group = QGroupBox("处理阶段")
        layout = QVBoxLayout(group)

        # 阶段按钮组
        self.stage_buttons = QButtonGroup(self)

        stages = [
            ('raw', '原始点云'),
            ('downsampled', '下采样后'),
            ('clustered', '聚类后'),
        ]

        for i, (key, label) in enumerate(stages):
            rb = QRadioButton(label)
            rb.setChecked(i == 0)
            rb.clicked.connect(lambda checked, k=key: self._on_stage_changed(k))
            self.stage_buttons.addButton(rb, i)
            layout.addWidget(rb)

        return group

    def _create_downsample_group(self):
        """创建下采样参数组"""
        group = QGroupBox("下采样参数")
        layout = QVBoxLayout(group)

        # 体素大小
        voxel_layout = QHBoxLayout()
        voxel_label = QLabel("体素大小(m):")
        self.voxel_slider = QSlider(Qt.Horizontal)
        self.voxel_slider.setRange(5, 100)  # 0.05m - 1.0m
        self.voxel_slider.setValue(20)  # 默认0.2m
        self.voxel_slider.setTickPosition(QSlider.TicksBelow)
        self.voxel_slider.setTickInterval(10)
        self.voxel_value = QLabel("0.20")
        self.voxel_value.setMinimumWidth(40)

        self.voxel_slider.valueChanged.connect(self._on_voxel_changed)

        voxel_layout.addWidget(voxel_label)
        voxel_layout.addWidget(self.voxel_slider)
        voxel_layout.addWidget(self.voxel_value)
        layout.addLayout(voxel_layout)

        return group

    def _create_cluster_group(self):
        """创建聚类参数组"""
        group = QGroupBox("聚类参数 (DBSCAN)")
        layout = QVBoxLayout(group)

        # EPS 邻域半径
        eps_layout = QHBoxLayout()
        eps_label = QLabel("邻域半径(m):")
        self.eps_slider = QSlider(Qt.Horizontal)
        self.eps_slider.setRange(1, 20)  # 0.1m - 2.0m
        self.eps_slider.setValue(5)  # 默认0.5m
        self.eps_slider.setTickPosition(QSlider.TicksBelow)
        self.eps_slider.setTickInterval(5)
        self.eps_value = QLabel("0.50")
        self.eps_value.setMinimumWidth(40)

        self.eps_slider.valueChanged.connect(self._on_eps_changed)

        eps_layout.addWidget(eps_label)
        eps_layout.addWidget(self.eps_slider)
        eps_layout.addWidget(self.eps_value)
        layout.addLayout(eps_layout)

        # min_samples 最小邻居数
        min_layout = QHBoxLayout()
        min_label = QLabel("最小邻居数:")
        self.min_slider = QSlider(Qt.Horizontal)
        self.min_slider.setRange(1, 20)
        self.min_slider.setValue(5)
        self.min_slider.setTickPosition(QSlider.TicksBelow)
        self.min_slider.setTickInterval(5)
        self.min_value = QLabel("5")
        self.min_value.setMinimumWidth(40)

        self.min_slider.valueChanged.connect(self._on_min_samples_changed)

        min_layout.addWidget(min_label)
        min_layout.addWidget(self.min_slider)
        min_layout.addWidget(self.min_value)
        layout.addLayout(min_layout)

        return group

    def _create_stats_group(self):
        """创建统计信息组"""
        group = QGroupBox("统计信息")
        layout = QVBoxLayout(group)

        self.stats_points_label = QLabel("点数: 0")
        self.stats_clusters_label = QLabel("簇数: 0")
        self.stats_noise_label = QLabel("噪声点: 0")

        self.stats_points_label.setStyleSheet("color: #333;")
        self.stats_clusters_label.setStyleSheet("color: #333;")
        self.stats_noise_label.setStyleSheet("color: #333;")

        layout.addWidget(self.stats_points_label)
        layout.addWidget(self.stats_clusters_label)
        layout.addWidget(self.stats_noise_label)

        # 重新处理按钮
        self.reprocess_btn = QPushButton("重新处理")
        self.reprocess_btn.clicked.connect(self._on_reprocess)
        self.reprocess_btn.setStyleSheet("background-color: #3498db; color: white;")
        layout.addWidget(self.reprocess_btn)

        return group

    def _on_stage_changed(self, stage):
        """处理阶段改变"""
        self.stage_changed.emit(stage)

    def _on_voxel_changed(self, value):
        """体素大小改变"""
        voxel_size = value / 100.0  # 转换为米
        self.voxel_value.setText(f"{voxel_size:.2f}")
        self.voxel_size_changed.emit(voxel_size)

    def _on_eps_changed(self, value):
        """EPS改变"""
        eps = value / 10.0  # 转换为米
        self.eps_value.setText(f"{eps:.2f}")
        self.eps_changed.emit(eps)

    def _on_min_samples_changed(self, value):
        """min_samples改变"""
        self.min_value.setText(str(value))
        self.min_samples_changed.emit(value)

    def _on_reprocess(self):
        """重新处理请求"""
        self.reprocess_requested.emit()

    def update_statistics(self, stats: dict):
        """
        更新统计信息显示

        Args:
            stats: 统计信息字典
        """
        num_points = stats.get('num_points', 0)
        num_clusters = stats.get('num_clusters', 0)
        num_noise = stats.get('num_noise_points', 0)

        self.stats_points_label.setText(f"点数: {num_points}")
        self.stats_clusters_label.setText(f"簇数: {num_clusters}")
        self.stats_noise_label.setText(f"噪声点: {num_noise}")

    def set_stage(self, stage: str):
        """
        设置当前阶段（用于外部更新UI）

        Args:
            stage: 'raw', 'downsampled', 或 'clustered'
        """
        stage_map = {'raw': 0, 'downsampled': 1, 'clustered': 2}
        if stage in stage_map:
            button = self.stage_buttons.button(stage_map[stage])
            if button:
                button.setChecked(True)
