from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QBrush, QPainterPath
from PySide6.QtWidgets import QGraphicsItem

EXTENT = 1500


def _pen(color, width):
    pen = QPen(color, width)
    pen.setCosmetic(True)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    return pen


class ContourRenderer:
    def __init__(self, scene, n):
        self.scene = scene
        self.n = n

        self.item_contour = scene.addPath(QPainterPath(), _pen(QColor(0, 0, 0), 2))
        self.item_selected = scene.addPath(QPainterPath(), _pen(QColor(230, 60, 60), 3))
        self.item_skeleton = scene.addPath(QPainterPath(), _pen(QColor(150, 150, 150), 1))
        self.item_contour.setZValue(5)
        self.item_selected.setZValue(6)
        self.item_skeleton.setZValue(1)

        thin = _pen(QColor(0, 0, 0), 1)
        self.brush_knot = QBrush(QColor(0, 0, 0))
        self.brush_smooth = QBrush(QColor(220, 0, 0))
        green = QBrush(QColor(0, 205, 0))
        self.items_p = [self._dot(3.5, thin, self.brush_knot, 8) for _ in range(n)]
        self.items_q = [self._dot(4.0, thin, green, 9) for _ in range(n)]
        self.item_rotate = self._dot(6, _pen(QColor(30, 80, 220), 2), QBrush(Qt.BrushStyle.NoBrush), 10)

    def _dot(self, r, pen, brush, z):
        item = self.scene.addEllipse(-r, -r, 2 * r, 2 * r, pen, brush)
        item.setZValue(z)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        return item

    def render(self, model):
        n = model.n
        arcs = model.arc_polylines()

        path = QPainterPath()
        for pts in arcs:
            path.moveTo(pts[0][0], pts[0][1])
            for x, y in pts[1:]:
                path.lineTo(x, y)
        self.item_contour.setPath(path)

        sp, sq = model.scene_p(), model.scene_q()
        show = model.skeleton

        sk = QPainterPath()
        for s, e, *_ in model.comps:
            sk.moveTo(sp[s][0], sp[s][1])
            for i in range(s, e):
                sk.lineTo(sq[i][0], sq[i][1])
                nxt = sp[model.next[i]]
                sk.lineTo(nxt[0], nxt[1])
        self.item_skeleton.setPath(sk)
        self.item_skeleton.setVisible(show)

        for i in range(n):
            self.items_p[i].setPos(sp[i][0], sp[i][1])
            self.items_q[i].setPos(sq[i][0], sq[i][1])
            self.items_p[i].setBrush(self.brush_smooth if model.smooth[i] else self.brush_knot)
            self.items_p[i].setVisible(show)
            self.items_q[i].setVisible(show)

        sel = QPainterPath()
        if show and not model.all_arcs and model.selected is not None:
            pts = arcs[model.selected]
            sel.moveTo(pts[0][0], pts[0][1])
            for x, y in pts[1:]:
                sel.lineTo(x, y)
        self.item_selected.setPath(sel)

        self.item_rotate.setPos(model.rx, model.ry)
        self.item_rotate.setVisible(show)
