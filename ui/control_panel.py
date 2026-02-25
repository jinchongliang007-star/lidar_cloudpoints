"""
控制面板 - 用户交互控件
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QSlider, QLabel, QCheckBox, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal


class ControlPanel(QWidget):
    """控制面板"""

    # 信号
    rotation_speed_changed = pyqtSignal(float)
    laser_lines_changed = pyqtSignal(int)
    vertical_fov_changed = pyqtSignal(float)
    component_visibility_changed = pyqtSignal(str, bool)
    preset_view_requested = pyqtSignal(str)
    reset_view_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI"""
        # 设置全局样式 - 所有文字为黑色
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
            QCheckBox {
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
        title = QLabel("扫描参数控制")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # 扫描参数组
        scan_group = self._create_scan_group()
        layout.addWidget(scan_group)

        # 可见性控制组
        visibility_group = self._create_visibility_group()
        layout.addWidget(visibility_group)

        # 视角预设组
        view_group = self._create_view_group()
        layout.addWidget(view_group)

        # 使用说明
        help_group = self._create_help_group()
        layout.addWidget(help_group)

        # 弹性空间
        layout.addStretch()

    def _create_scan_group(self):
        """创建扫描参数组"""
        group = QGroupBox("扫描参数")
        layout = QVBoxLayout(group)

        # 转速控制
        speed_layout = QHBoxLayout()
        speed_label = QLabel("转速 (RPM):")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 20)
        self.speed_slider.setValue(10)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(5)
        self.speed_value = QLabel("10")
        self.speed_value.setMinimumWidth(30)

        self.speed_slider.valueChanged.connect(
            lambda v: self._on_speed_changed(v)
        )

        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value)
        layout.addLayout(speed_layout)

        # 激光线数
        lines_layout = QHBoxLayout()
        lines_label = QLabel("激光线数:")
        self.lines_slider = QSlider(Qt.Horizontal)
        self.lines_slider.setRange(1, 64)
        self.lines_slider.setValue(16)
        self.lines_slider.setTickPosition(QSlider.TicksBelow)
        self.lines_slider.setTickInterval(16)
        self.lines_value = QLabel("16")
        self.lines_value.setMinimumWidth(30)

        self.lines_slider.valueChanged.connect(
            lambda v: self._on_lines_changed(v)
        )

        lines_layout.addWidget(lines_label)
        lines_layout.addWidget(self.lines_slider)
        lines_layout.addWidget(self.lines_value)
        layout.addLayout(lines_layout)

        # 垂直视场角
        fov_layout = QHBoxLayout()
        fov_label = QLabel("垂直FOV (°):")
        self.fov_slider = QSlider(Qt.Horizontal)
        self.fov_slider.setRange(10, 45)
        self.fov_slider.setValue(30)
        self.fov_slider.setTickPosition(QSlider.TicksBelow)
        self.fov_slider.setTickInterval(10)
        self.fov_value = QLabel("30")
        self.fov_value.setMinimumWidth(30)

        self.fov_slider.valueChanged.connect(
            lambda v: self._on_fov_changed(v)
        )

        fov_layout.addWidget(fov_label)
        fov_layout.addWidget(self.fov_slider)
        fov_layout.addWidget(self.fov_value)
        layout.addLayout(fov_layout)

        return group

    def _create_visibility_group(self):
        """创建可见性控制组"""
        group = QGroupBox("显示控制")
        layout = QVBoxLayout(group)

        # 复选框
        self.checkboxes = {}
        components = [
            ('body', 'LiDAR外壳', True),
            ('laser_unit', '激光单元', True),
            ('laser_beam', '激光束', True),
            ('environment', '环境模型', True),
        ]

        for key, label, default in components:
            cb = QCheckBox(label)
            cb.setChecked(default)
            cb.stateChanged.connect(
                lambda state, k=key: self._on_visibility_changed(k, state == Qt.Checked)
            )
            self.checkboxes[key] = cb
            layout.addWidget(cb)

        return group

    def _create_view_group(self):
        """创建视角预设组"""
        group = QGroupBox("视角预设")
        layout = QVBoxLayout(group)

        # 预设按钮
        presets = [
            ('top', '俯视图'),
            ('front', '正视图'),
            ('side', '侧视图'),
            ('perspective', '透视图'),
            ('isometric', '等轴视图'),
        ]

        # 第一行
        row1 = QHBoxLayout()
        for key, label in presets[:3]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, k=key: self.preset_view_requested.emit(k))
            row1.addWidget(btn)
        layout.addLayout(row1)

        # 第二行
        row2 = QHBoxLayout()
        for key, label in presets[3:]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, k=key: self.preset_view_requested.emit(k))
            row2.addWidget(btn)
        # 重置按钮
        reset_btn = QPushButton("重置视角")
        reset_btn.clicked.connect(lambda: self.reset_view_requested.emit())
        reset_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        row2.addWidget(reset_btn)
        layout.addLayout(row2)

        return group

    def _create_help_group(self):
        """创建使用说明组"""
        group = QGroupBox("使用说明")
        layout = QVBoxLayout(group)

        help_text = QLabel(
            "• 鼠标左键拖拽: 旋转视角\n"
            "• 鼠标滚轮: 缩放\n"
            "• 调节滑块改变参数\n"
            "• 复选框控制显示\n"
            "• 点击按钮切换视角"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(help_text)

        return group

    def _on_speed_changed(self, value):
        """转速改变"""
        self.speed_value.setText(str(value))
        self.rotation_speed_changed.emit(float(value))

    def _on_lines_changed(self, value):
        """激光线数改变"""
        self.lines_value.setText(str(value))
        self.laser_lines_changed.emit(value)

    def _on_fov_changed(self, value):
        """垂直视场角改变"""
        self.fov_value.setText(str(value))
        self.vertical_fov_changed.emit(float(value))

    def _on_visibility_changed(self, component, visible):
        """可见性改变"""
        self.component_visibility_changed.emit(component, visible)
