"""
Control panel for 3D Galaxy Viewer.

Provides UI controls for:
- Component selection (disk, bulge, all)
- Rendering mode (surface, volume, isosurface)
- View presets (top, side, front, iso)
- Visual options (spiral arms, halo, axes)
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QComboBox, QSlider,
    QCheckBox, QButtonGroup, QRadioButton,
    QFrame, QSpacerItem, QSizePolicy,
)


class Galaxy3DControlPanel(QWidget):
    """Control panel for 3D galaxy visualization."""

    # Signals
    options_changed = pyqtSignal(dict)
    view_preset_requested = pyqtSignal(str)
    screenshot_requested = pyqtSignal()
    auto_rotate_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Build the control panel UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Component Selection
        component_group = QGroupBox("구성 성분")
        component_layout = QVBoxLayout(component_group)

        self.component_combo = QComboBox()
        self.component_combo.addItems(["전체 (Disk + Bulge)", "Disk만", "Bulge만"])
        component_layout.addWidget(self.component_combo)

        layout.addWidget(component_group)

        # Render Mode
        render_group = QGroupBox("렌더링 방식")
        render_layout = QVBoxLayout(render_group)

        self.render_combo = QComboBox()
        self.render_combo.addItems(["표면", "볼륨", "등밀도면"])
        render_layout.addWidget(self.render_combo)

        # Resolution
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("해상도:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["낮음", "보통", "높음"])
        self.resolution_combo.setCurrentIndex(1)  # Default: Medium
        res_layout.addWidget(self.resolution_combo)
        render_layout.addLayout(res_layout)

        # Opacity slider
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("투명도:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        self.opacity_label = QLabel("90%")
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        render_layout.addLayout(opacity_layout)

        layout.addWidget(render_group)

        # Visual Options
        options_group = QGroupBox("시각화 옵션")
        options_layout = QVBoxLayout(options_group)

        self.check_axes = QCheckBox("축 표시")
        self.check_axes.setChecked(True)
        options_layout.addWidget(self.check_axes)

        self.check_spiral = QCheckBox("나선팔 표시")
        self.check_spiral.setChecked(False)
        self.check_spiral.setToolTip("로그 나선 형태를 시각적으로 덧씌웁니다.")
        options_layout.addWidget(self.check_spiral)

        self.check_halo = QCheckBox("암흑물질 헤일로 표시")
        self.check_halo.setChecked(False)
        self.check_halo.setToolTip("헤일로를 와이어프레임 구 형태로 표시합니다.")
        options_layout.addWidget(self.check_halo)

        layout.addWidget(options_group)

        # View Presets
        view_group = QGroupBox("카메라 시점")
        view_layout = QVBoxLayout(view_group)

        btn_row1 = QHBoxLayout()
        self.btn_iso = QPushButton("등각")
        self.btn_iso.setToolTip("3D 등각 시점 (R)")
        self.btn_top = QPushButton("위")
        self.btn_top.setToolTip("위에서 내려다보는 시점 (T)")
        btn_row1.addWidget(self.btn_iso)
        btn_row1.addWidget(self.btn_top)
        view_layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        self.btn_side = QPushButton("옆")
        self.btn_side.setToolTip("옆면 시점 (S)")
        self.btn_front = QPushButton("앞")
        self.btn_front.setToolTip("정면 시점")
        btn_row2.addWidget(self.btn_side)
        btn_row2.addWidget(self.btn_front)
        view_layout.addLayout(btn_row2)

        # Auto-rotate
        self.check_auto_rotate = QCheckBox("자동 회전")
        view_layout.addWidget(self.check_auto_rotate)

        layout.addWidget(view_group)

        # Screenshot
        action_group = QGroupBox("작업")
        action_layout = QVBoxLayout(action_group)

        self.btn_screenshot = QPushButton("스크린샷 저장")
        self.btn_screenshot.setToolTip("현재 보기를 PNG로 저장합니다.")
        action_layout.addWidget(self.btn_screenshot)

        layout.addWidget(action_group)

        # Help text
        help_frame = QFrame()
        help_frame.setObjectName("helpFrame")
        help_layout = QVBoxLayout(help_frame)
        help_layout.setContentsMargins(8, 8, 8, 8)

        help_text = QLabel(
            "<b>탐구 포인트</b><br>"
            "- 왼쪽 드래그: 회전<br>"
            "- 오른쪽 드래그: 이동<br>"
            "- 휠 스크롤: 확대/축소<br>"
            "- R: 시점 초기화<br>"
            "- T: 위에서 보기<br>"
            "- S: 옆에서 보기<br><br>"
            "2D 회전곡선에서 본 질량 분포를 3D 구조와 연결해 해석해 보세요."
        )
        help_text.setObjectName("subtitle")
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)

        layout.addWidget(help_frame)

        # Spacer
        layout.addSpacerItem(QSpacerItem(
            20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding
        ))

    def _connect_signals(self):
        """Connect internal signals."""
        # Component and render changes
        self.component_combo.currentIndexChanged.connect(self._emit_options)
        self.render_combo.currentIndexChanged.connect(self._emit_options)
        self.resolution_combo.currentIndexChanged.connect(self._emit_options)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)

        # Checkboxes
        self.check_axes.stateChanged.connect(self._emit_options)
        self.check_spiral.stateChanged.connect(self._emit_options)
        self.check_halo.stateChanged.connect(self._emit_options)

        # View buttons
        self.btn_iso.clicked.connect(lambda: self.view_preset_requested.emit("iso"))
        self.btn_top.clicked.connect(lambda: self.view_preset_requested.emit("top"))
        self.btn_side.clicked.connect(lambda: self.view_preset_requested.emit("side"))
        self.btn_front.clicked.connect(lambda: self.view_preset_requested.emit("front"))

        # Auto rotate
        self.check_auto_rotate.stateChanged.connect(
            lambda state: self.auto_rotate_toggled.emit(state == Qt.Checked)
        )

        # Screenshot
        self.btn_screenshot.clicked.connect(self.screenshot_requested.emit)

    def _on_opacity_changed(self, value: int):
        """Handle opacity slider change."""
        self.opacity_label.setText(f"{value}%")
        self._emit_options()

    def _emit_options(self):
        """Emit current options as signal."""
        self.options_changed.emit(self.get_options())

    def get_options(self) -> dict:
        """
        Get current control values as options dict.

        Returns
        -------
        dict
            Options dictionary for Galaxy3DViewer
        """
        # Component mapping
        component_map = {0: "all", 1: "disk", 2: "bulge"}
        component = component_map.get(self.component_combo.currentIndex(), "all")

        # Render mode mapping
        render_map = {0: "surface", 1: "volume", 2: "isosurface"}
        render_mode = render_map.get(self.render_combo.currentIndex(), "surface")

        # Resolution mapping
        res_map = {0: "low", 1: "medium", 2: "high"}
        resolution = res_map.get(self.resolution_combo.currentIndex(), "medium")

        return {
            "component": component,
            "render_mode": render_mode,
            "resolution": resolution,
            "opacity": self.opacity_slider.value() / 100.0,
            "show_axes": self.check_axes.isChecked(),
            "show_spiral": self.check_spiral.isChecked(),
            "show_halo": self.check_halo.isChecked(),
        }

    def set_options(self, options: dict):
        """
        Set control values from options dict.

        Parameters
        ----------
        options : dict
            Options dictionary
        """
        # Block signals during update
        self.blockSignals(True)

        component = options.get("component", "all")
        component_idx = {"all": 0, "disk": 1, "bulge": 2}.get(component, 0)
        self.component_combo.setCurrentIndex(component_idx)

        render_mode = options.get("render_mode", "surface")
        render_idx = {"surface": 0, "volume": 1, "isosurface": 2}.get(render_mode, 0)
        self.render_combo.setCurrentIndex(render_idx)

        resolution = options.get("resolution", "medium")
        res_idx = {"low": 0, "medium": 1, "high": 2}.get(resolution, 1)
        self.resolution_combo.setCurrentIndex(res_idx)

        opacity = options.get("opacity", 0.9)
        self.opacity_slider.setValue(int(opacity * 100))
        self.opacity_label.setText(f"{int(opacity * 100)}%")

        self.check_axes.setChecked(options.get("show_axes", True))
        self.check_spiral.setChecked(options.get("show_spiral", False))
        self.check_halo.setChecked(options.get("show_halo", False))

        self.blockSignals(False)
