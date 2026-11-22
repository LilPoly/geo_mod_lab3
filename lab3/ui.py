# ui.py
import math

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPainter, QBrush, QColor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QGraphicsView, QGraphicsScene, QDockWidget, QScrollArea,
    QGridLayout, QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton,
    QCheckBox, QSlider, QAbstractSpinBox, QFrame,
)

import lab3.contour as cn
from lab3.model import ContourModel
from lab3.renderer import ContourRenderer, EXTENT

ANIM_INTERVAL_MS = 16
HIT_RADIUS_PX = 9

STYLE = """
QLineEdit#flat, QComboBox#flat {
    background: white;
    border: none;
    border-bottom: 1px solid #9a9a9a;
    padding: 1px 3px;
}
QPushButton {
    background: #fdfdfd;
    border: 1px solid #adadad;
    border-radius: 3px;
    padding: 3px 10px;
}
QPushButton:hover { background: #e6effa; }
QPushButton:pressed { background: #cfe0f5; }
"""


class CanvasView(QGraphicsView):
    leftPressed = Signal(float, float)
    leftMoved = Signal(float, float)
    leftReleased = Signal()
    rotatePointSet = Signal(float, float)

    def __init__(self, scene):
        super().__init__(scene)
        self.scale(1, -1)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor(255, 255, 255)))
        self._pan_last = None

    def zoom(self):
        return self.transform().m11()

    def _world(self, event):
        p = self.mapToScene(event.position().toPoint())
        return p.x(), p.y()

    def mousePressEvent(self, event):
        btn = event.button()
        if btn == Qt.MouseButton.LeftButton:
            self.leftPressed.emit(*self._world(event))
        elif btn == Qt.MouseButton.RightButton:
            self.rotatePointSet.emit(*self._world(event))
        elif btn == Qt.MouseButton.MiddleButton:
            self._pan_last = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.leftMoved.emit(*self._world(event))
        elif self._pan_last is not None:
            pos = event.position().toPoint()
            delta = pos - self._pan_last
            self._pan_last = pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.leftReleased.emit()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._pan_last = None
            self.unsetCursor()

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        if 0.25 < self.zoom() * factor < 8:
            self.scale(factor, factor)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Криволінійний контур (дуги еліпсів) - Лабораторна 3")
        self.resize(1300, 820)
        self.setStyleSheet(STYLE)

        self.model = ContourModel()
        self._drag = None

        self.scene = QGraphicsScene(-EXTENT, -EXTENT, 2 * EXTENT, 2 * EXTENT)
        self.view = CanvasView(self.scene)
        self.setCentralWidget(self.view)
        self.renderer = ContourRenderer(self.scene, self.model.n)

        self._build_panel()

        self.timer = QTimer(self)
        self.timer.setInterval(ANIM_INTERVAL_MS)
        self.timer.timeout.connect(self.on_anim_tick)

        self.view.leftPressed.connect(self.on_left_pressed)
        self.view.leftMoved.connect(self.on_left_moved)
        self.view.leftReleased.connect(self.on_left_released)
        self.view.rotatePointSet.connect(self.on_rotate_point_set)

        self.refresh()

    def _label(self, text, right=False):
        lb = QLabel(text)
        if right:
            lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return lb

    def _pos_spin(self):
        sp = QDoubleSpinBox()
        sp.setObjectName("flat")
        sp.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        sp.setRange(-5000, 5000)
        sp.setDecimals(2)
        sp.setKeyboardTracking(False)
        sp.setFixedWidth(80)
        sp.valueChanged.connect(self.on_transform_changed)
        return sp

    def _readout(self, width=80):
        le = QLineEdit()
        le.setObjectName("flat")
        le.setReadOnly(True)
        le.setFixedWidth(width)
        return le

    def _build_panel(self):
        panel = QWidget()
        g = QGridLayout(panel)
        g.setHorizontalSpacing(8)
        g.setVerticalSpacing(6)
        g.setContentsMargins(14, 14, 14, 14)
        r = 0

        self.chk_skeleton = QCheckBox("Skeleton")
        self.chk_skeleton.setChecked(True)
        self.chk_skeleton.toggled.connect(self.on_skeleton_toggled)
        g.addWidget(self.chk_skeleton, r, 0, 1, 4); r += 1

        self.btn_anim = QPushButton("Start/Stop Animation")
        self.btn_anim.clicked.connect(self.toggle_animation)
        g.addWidget(self.btn_anim, r, 0, 1, 4); r += 1

        self.btn_reset = QPushButton("Reset")
        self.btn_reset.clicked.connect(self.reset_all)
        g.addWidget(self.btn_reset, r, 0, 1, 4); r += 1

        g.setRowMinimumHeight(r, 14); r += 1

        g.addWidget(QLabel("Arc parameter f (0 < f < 1)"), r, 0, 1, 4); r += 1
        self.slider_f = QSlider(Qt.Orientation.Horizontal)
        self.slider_f.setRange(round(cn.F_MIN * 100), round(cn.F_MAX * 100))
        self.slider_f.valueChanged.connect(self.on_slider_f)
        self.spin_f = QDoubleSpinBox()
        self.spin_f.setObjectName("flat")
        self.spin_f.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_f.setRange(cn.F_MIN, cn.F_MAX)
        self.spin_f.setDecimals(2)
        self.spin_f.setSingleStep(0.01)
        self.spin_f.setKeyboardTracking(False)
        self.spin_f.setFixedWidth(50)
        self.spin_f.valueChanged.connect(self.on_spin_f)
        g.addWidget(self.slider_f, r, 0, 1, 3); g.addWidget(self.spin_f, r, 3); r += 1

        self.chk_all = QCheckBox("All arcs")
        self.chk_all.setChecked(True)
        self.chk_all.toggled.connect(self.on_all_arcs_toggled)
        self.lbl_arc = QLabel("")
        g.addWidget(self.chk_all, r, 0, 1, 2); g.addWidget(self.lbl_arc, r, 2, 1, 2); r += 1

        self.edit_w = self._readout()
        self.edit_kind = self._readout()
        g.addWidget(self._label("wB", True), r, 0); g.addWidget(self.edit_w, r, 1)
        g.addWidget(self.edit_kind, r, 2, 1, 2); r += 1

        g.setRowMinimumHeight(r, 14); r += 1

        g.addWidget(QLabel("Figure position"), r, 0, 1, 4); r += 1
        self.spin_fx = self._pos_spin()
        self.spin_fy = self._pos_spin()
        g.addWidget(self._label("X", True), r, 0); g.addWidget(self.spin_fx, r, 1)
        g.addWidget(self._label("Y", True), r, 2); g.addWidget(self.spin_fy, r, 3); r += 1

        g.addWidget(QLabel("Rotate point position"), r, 0, 1, 4); r += 1
        self.spin_rx = self._pos_spin()
        self.spin_ry = self._pos_spin()
        g.addWidget(self._label("X", True), r, 0); g.addWidget(self.spin_rx, r, 1)
        g.addWidget(self._label("Y", True), r, 2); g.addWidget(self.spin_ry, r, 3); r += 1

        # ---- angle
        self.spin_angle = QSpinBox()
        self.spin_angle.setObjectName("flat")
        self.spin_angle.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.spin_angle.setRange(-360, 360)
        self.spin_angle.setWrapping(True)
        self.spin_angle.setFixedWidth(70)
        self.spin_angle.valueChanged.connect(self.on_transform_changed)
        g.addWidget(self._label("angle", True), r, 0); g.addWidget(self.spin_angle, r, 1); r += 1
        
        g.setRowStretch(r, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(panel)

        self.dock = QDockWidget("", self)
        self.dock.setWidget(scroll)
        self.dock.setMinimumWidth(290)
        self.dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                              QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)

    def refresh(self, *_):
        self.renderer.render(self.model)
        self.update_arc_panel()

    def update_arc_panel(self):
        m = self.model
        f = m.current_f()
        for w in (self.slider_f, self.spin_f):
            w.blockSignals(True)
        self.slider_f.setValue(round(f * 100))
        self.spin_f.setValue(f)
        for w in (self.slider_f, self.spin_f):
            w.blockSignals(False)
        self.edit_w.setText(f"{cn.weight_from_f(f):.3f}")
        self.edit_kind.setText(cn.arc_kind(f))
        if m.all_arcs:
            self.lbl_arc.setText("")
        elif m.selected is None:
            self.lbl_arc.setText("click a point")
        else:
            self.lbl_arc.setText(f"arc {m.selected + 1} / {m.n}")

    def _set_spin(self, spin, value):
        spin.blockSignals(True)
        spin.setValue(value)
        spin.blockSignals(False)

    def on_skeleton_toggled(self, checked):
        self.model.skeleton = checked
        self.refresh()

    def on_transform_changed(self, *_):
        m = self.model
        m.fx, m.fy = self.spin_fx.value(), self.spin_fy.value()
        m.rx, m.ry = self.spin_rx.value(), self.spin_ry.value()
        m.angle = float(self.spin_angle.value())
        self.refresh()

    def on_slider_f(self, value):
        self.model.set_f(value / 100.0)
        self.refresh()

    def on_spin_f(self, value):
        self.model.set_f(value)
        self.refresh()

    def on_all_arcs_toggled(self, checked):
        self.model.all_arcs = checked
        if checked:
            self.model.set_f(self.model.current_f())
        self.refresh()

    def on_left_pressed(self, x, y):
        m = self.model
        self._drag = None
        if m.skeleton and not m.animating:
            tol = HIT_RADIUS_PX / self.view.zoom()
            hit = m.hit_test(x, y, tol)
            if hit is not None:
                kind, i = hit
                m.selected = i
                self._drag = ("point", kind, i)
                self.refresh()
                return
        self._drag = ("figure", x, y, m.fx, m.fy)

    def on_left_moved(self, x, y):
        if self._drag is None:
            return
        m = self.model
        if self._drag[0] == "point":
            _, kind, i = self._drag
            m.move_point(kind, i, x, y)
        else:
            _, x0, y0, fx0, fy0 = self._drag
            m.fx, m.fy = fx0 + (x - x0), fy0 + (y - y0)
            self._set_spin(self.spin_fx, m.fx)
            self._set_spin(self.spin_fy, m.fy)
        self.refresh()

    def on_left_released(self):
        self._drag = None

    def on_rotate_point_set(self, x, y):
        self.model.rx, self.model.ry = x, y
        self._set_spin(self.spin_rx, x)
        self._set_spin(self.spin_ry, y)
        self.refresh()

    def toggle_animation(self):
        self._drag = None
        self.model.toggle_animation()
        if self.model.animating:
            self.timer.start()
        else:
            self.timer.stop()

    def on_anim_tick(self):
        self.model.tick(ANIM_INTERVAL_MS / 1000.0)
        self.refresh()

    def reset_all(self):
        self.timer.stop()
        self._drag = None
        self.model.reset()
        widgets = (self.spin_fx, self.spin_fy, self.spin_rx, self.spin_ry,
                   self.spin_angle, self.chk_skeleton, self.chk_all)
        for w in widgets:
            w.blockSignals(True)
        self.spin_fx.setValue(0.0); self.spin_fy.setValue(0.0)
        self.spin_rx.setValue(0.0); self.spin_ry.setValue(0.0)
        self.spin_angle.setValue(0)
        self.chk_skeleton.setChecked(True)
        self.chk_all.setChecked(True)
        for w in widgets:
            w.blockSignals(False)
        self.view.resetTransform()
        self.view.scale(1, -1)
        self.view.centerOn(0, 0)
        self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, lambda: self.view.centerOn(0, 0))
