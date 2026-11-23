import math

import lab3.contour as cn
from lab3.transformations import TransformMatrix

ANIM_MOVE_TIME = 2.5
ANIM_HOLD_TIME = 0.4
EPS = 1e-9


class ContourModel:
    def __init__(self):
        (self.initial_p, self.initial_q, self.initial_f,
         self.next, self.comps) = cn.default_contour()
        self.n = len(self.initial_p)
        self._build_topology()
        self.reset()

    def _build_topology(self):
        self.prev = [None] * self.n
        self.can_smooth = [False] * self.n
        for s, e, closed in self.comps:
            for i in range(s, e):
                if closed or i != e - 1:
                    self.prev[self.next[i]] = i
            for j in range(s, e):
                if closed or s < j < e - 1:
                    self.can_smooth[j] = True

    def reset(self):
        self.p = [pt[:] for pt in self.initial_p]
        self.q = [pt[:] for pt in self.initial_q]
        self.f = list(self.initial_f)
        self.smooth = [False] * self.n
        self.all_arcs = True
        self.selected = None
        self.fx = self.fy = 0.0
        self.rx = self.ry = 0.0
        self.angle = 0.0
        self.skeleton = True
        self.animating = False
        self._tau = 0.0
        self._base = None
        self._target = None

    def matrix(self):
        t = TransformMatrix.get_translation(self.fx, self.fy)
        r = TransformMatrix.get_rotation_about_point(self.angle, self.rx, self.ry)
        return TransformMatrix.multiply_matrices(r, t)

    def to_scene(self, pts, m=None):
        m = m or self.matrix()
        return [list(TransformMatrix.apply_to_point(x, y, m)) for x, y in pts]

    def scene_p(self):
        return self.to_scene(self.p)

    def scene_q(self):
        return self.to_scene(self.q)

    def arc_polylines(self):
        m = self.matrix()
        sp, sq = self.to_scene(self.p, m), self.to_scene(self.q, m)
        return [cn.sample_arc(sp[i], sq[i], sp[self.next[i]], self.f[i])
                for i in range(self.n)]

    def set_f(self, value):
        value = cn.clamp_f(value)
        if self.all_arcs or self.selected is None:
            self.f = [value] * self.n
        else:
            self.f[self.selected] = value

    def current_f(self):
        return self.f[self.selected] if self.selected is not None else self.f[0]

    def hit_test(self, x, y, tol):
        best, best_d = None, tol * tol
        for kind, pts in (("q", self.scene_q()), ("p", self.scene_p())):
            for i, (px, py) in enumerate(pts):
                d = (px - x) ** 2 + (py - y) ** 2
                if d <= best_d:
                    best, best_d = (kind, i), d
        return best

    def toggle_smooth(self, j):
        if self.can_smooth[j]:
            self.smooth[j] = not self.smooth[j]

    def _align_outgoing(self, j, k):
        px, py = self.p[j]
        vx, vy = px - self.q[k][0], py - self.q[k][1]
        length = math.hypot(vx, vy)
        if length < EPS:
            return False
        d = math.hypot(self.q[j][0] - px, self.q[j][1] - py)
        self.q[j] = [px + vx / length * d, py + vy / length * d]
        return True

    def _align_incoming(self, j, k):
        px, py = self.p[j]
        vx, vy = self.q[j][0] - px, self.q[j][1] - py
        length = math.hypot(vx, vy)
        if length < EPS:
            return False
        d = math.hypot(px - self.q[k][0], py - self.q[k][1])
        self.q[k] = [px - vx / length * d, py - vy / length * d]
        return True

    def _propagate(self, start, visited):
        stack = [start]
        while stack:
            i = stack.pop()
            j = self.next[i]
            if self.smooth[j] and j not in visited:
                if self._align_outgoing(j, i):
                    visited.add(j)
                    stack.append(j)
            if self.smooth[i]:
                k = self.prev[i]
                if k is not None and k not in visited:
                    if self._align_incoming(i, k):
                        visited.add(k)
                        stack.append(k)

    def move_point(self, kind, i, x, y):
        inv = TransformMatrix.get_inverse(self.matrix())
        nx, ny = TransformMatrix.apply_to_point(x, y, inv)
        if kind == "q":
            self.q[i] = [nx, ny]
            self._propagate(i, {i})
            return
        self.p[i] = [nx, ny]
        if self.smooth[i]:
            k = self.prev[i]
            self._align_outgoing(i, k)
            self._propagate(i, {i, k})

    def start_animation(self):
        self._base = ([pt[:] for pt in self.p], [pt[:] for pt in self.q])
        tp, tq = cn.target_triangle(self.p, self.comps)
        dist = sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a, b in zip(self.p, tp))
        self._target = (tp, tq) if dist > 1.0 else (
            [pt[:] for pt in self.initial_p], [pt[:] for pt in self.initial_q])
        self._tau = 0.0
        self.animating = True

    def stop_animation(self):
        self.animating = False

    def toggle_animation(self):
        if self.animating:
            self.stop_animation()
        else:
            self.start_animation()

    def tick(self, dt):
        if not self.animating:
            return
        move, hold = ANIM_MOVE_TIME, ANIM_HOLD_TIME
        self._tau = (self._tau + dt) % (2 * (move + hold))
        tau = self._tau
        if tau < move:
            s = tau / move
        elif tau < move + hold:
            s = 1.0
        elif tau < 2 * move + hold:
            s = 1.0 - (tau - move - hold) / move
        else:
            s = 0.0
        t = cn.ease(s)
        self.p = cn.lerp_points(self._base[0], self._target[0], t)
        self.q = cn.lerp_points(self._base[1], self._target[1], t)
