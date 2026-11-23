import math

F_MIN = 0.05
F_MAX = 0.49
F_DEFAULT = 0.35
ARC_STEPS = 32


def weight_from_f(f):
    return f / (1.0 - f)


def clamp_f(f):
    return max(F_MIN, min(F_MAX, f))


def arc_kind(f):
    if f < 0.5 - 1e-9:
        return "ellipse"
    if f > 0.5 + 1e-9:
        return "hyperbola"
    return "parabola"


def arc_point(a, b, c, f, u):
    w = weight_from_f(f)
    k_a = (1.0 - u) ** 2
    k_b = 2.0 * w * u * (1.0 - u)
    k_c = u * u
    den = k_a + k_b + k_c
    return ((k_a * a[0] + k_b * b[0] + k_c * c[0]) / den,
            (k_a * a[1] + k_b * b[1] + k_c * c[1]) / den)


def sample_arc(a, b, c, f, steps=ARC_STEPS):
    return [arc_point(a, b, c, f, i / steps) for i in range(steps + 1)]


IMG_CX, IMG_CY = 530.0, 380.0


def img(x, y):
    return x - IMG_CX, IMG_CY - y


def outline_component(points_img, f=F_DEFAULT):
    n = len(points_img)
    pts = [img(x, y) for x, y, _ in points_img][::-1]
    ks = [points_img[(n - 2 - j) % n][2] for j in range(n)]
    points_img = [(0, 0, k) for k in ks]
    p = [[x, y] for x, y in pts]
    q = []
    for i, (_, _, k) in enumerate(points_img):
        a, c = p[i], p[(i + 1) % n]
        dx, dy = c[0] - a[0], c[1] - a[1]
        q.append([(a[0] + c[0]) / 2.0 + k * dy, (a[1] + c[1]) / 2.0 - k * dx])
    return p, q, [f] * n


def ellipse_component(cx, cy, a, b, rot_deg, n=6):
    cx, cy = img(cx, cy)
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    half = math.pi / n
    w = math.cos(half)

    def at(theta, scale=1.0):
        x, y = a * math.cos(theta) * scale, b * math.sin(theta) * scale
        return [cx + x * cr - y * sr, cy + x * sr + y * cr]

    p = [at(2 * half * j) for j in range(n)]
    q = [at(2 * half * j + half, 1.0 / w) for j in range(n)]
    return p, q, [w / (1.0 + w)] * n


def open_component(points_img, f=F_DEFAULT):
    p = [list(img(x, y)) for x, y, _ in points_img]
    n = len(p)
    q = []
    for i in range(n - 1):
        k = points_img[i][2]
        a, c = p[i], p[i + 1]
        dx, dy = c[0] - a[0], c[1] - a[1]
        q.append([(a[0] + c[0]) / 2.0 + k * dy, (a[1] + c[1]) / 2.0 - k * dx])
    q.append(p[-1][:])
    return p, q, [f] * n, False


def spiral_component(c0, c1, a0, b0, scale_end, rot_deg,
                     turns=3, per_turn=6, start_deg=180):
    rot = math.radians(rot_deg)
    cr, sr = math.cos(rot), math.sin(rot)
    n = turns * per_turn
    half = math.pi / per_turn
    w = math.cos(half)

    def at(j, mid=False):
        jj = j + (0.5 if mid else 0.0)
        t = jj / n
        th = math.radians(start_deg) + 2 * half * jj
        s = scale_end ** t
        k = 1.0 / w if mid else 1.0
        cx, cy = img(c0[0] + (c1[0] - c0[0]) * t, c0[1] + (c1[1] - c0[1]) * t)
        x, y = a0 * s * k * math.cos(th), b0 * s * k * math.sin(th)
        return [cx + x * cr - y * sr, cy + x * sr + y * cr]

    p = [at(j) for j in range(n + 1)]
    q = [at(j, True) for j in range(n)] + [at(n)]
    return p, q, [w / (1.0 + w)] * (n + 1), False


def build_components():
    comps = [
        spiral_component((595, 160), (572, 176), 262, 68, 0.26, -12.7),

        outline_component([
            (222, 187, 0.04),
            (248, 247, -0.02),
            (380, 285, -0.05),
            (495, 303, -0.10),
            (545, 285, 0.10),
            (610, 290, 0.14),
            (690, 325, 0.12),
            (775, 400, 0.28),
            (775, 455, 0.10),
            (690, 462, 0.05),
            (580, 450, 0.05),
            (500, 410, 0.04),
            (400, 350, 0.02),
            (290, 285, 0.02),
            (220, 245, 0.10),
        ], 0.35),

        ellipse_component(598, 372, 64, 44, 82),
        outline_component([
            (582, 319, 0.12),
            (636, 326, 0.12),
            (643, 376, 0.12),
            (578, 374, 0.12),
        ], 0.35),
        outline_component([
            (648, 331, 0.12),
            (682, 341, 0.12),
            (686, 383, 0.12),
            (648, 378, 0.12),
        ], 0.35),

        open_component([
            (378, 441, 0.03),
            (488, 458, 0.03),
            (598, 486, 0.03),
            (683, 510, 0.03),
            (738, 507, -0.10),
            (748, 502, 0.00),
        ], 0.35),
        open_component([(465, 452, 0.0), (501, 413, 0.0)], 0.35),
        open_component([(650, 458, 0.0), (654, 500, 0.0)], 0.35),

        open_component([
            (228, 540, -0.29),
            (249, 511, -0.29),
            (303, 488, -0.29),
            (357, 511, -0.29),
            (380, 565, -0.16),
            (379, 598, -0.05),
            (373, 624, -0.05),
            (400, 640, -0.45),
            (445, 645, -0.30),
            (486, 676, 0.00),
        ], 0.35),
    ]
    return comps


def default_contour():
    p, q, f, nxt, comps = [], [], [], [], []
    for comp in build_components():
        cp, cq, cf = comp[:3]
        closed = comp[3] if len(comp) > 3 else True
        s = len(p)
        n = len(cp)
        p += cp
        q += cq
        f += cf
        if closed:
            nxt += [s + (i + 1) % n for i in range(n)]
        else:
            nxt += [s + i + 1 for i in range(n - 1)] + [s + n - 1]
        comps.append((s, s + n, closed))
    return p, q, f, nxt, comps


def _triangle_for(points, count, source):
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    verts = [(x0, y0), (x1, y0), ((x0 + x1) / 2.0, y1)]
    counts = [count // 3 + (1 if i < count % 3 else 0) for i in range(3)]
    p = []
    for s in range(3):
        a, b = verts[s], verts[(s + 1) % 3]
        for j in range(counts[s]):
            t = j / counts[s]
            p.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])

    def cost(shift):
        return sum((source[i][0] - p[(i + shift) % count][0]) ** 2 +
                   (source[i][1] - p[(i + shift) % count][1]) ** 2 for i in range(count))
    best = min(range(count), key=cost)
    return [p[(i + best) % count] for i in range(count)]


def _open_triangle(points, m):
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    verts = [(x0, y0), (x1, y0), ((x0 + x1) / 2.0, y1)]
    seg = m - 1
    counts = [seg // 3 + (1 if i < seg % 3 else 0) for i in range(3)]
    p = []
    for s in range(3):
        a, b = verts[s], verts[(s + 1) % 3]
        for j in range(counts[s]):
            t = j / counts[s]
            p.append([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t])
    p.append([verts[0][0], verts[0][1]])
    return p


def target_triangle(p_src, comps):
    tp = [None] * len(p_src)
    tq = [None] * len(p_src)
    for s, e, closed in comps:
        m = e - s
        if closed:
            tri = _triangle_for(p_src[s:e], m, p_src[s:e])
        elif m < 4:
            tri = [pt[:] for pt in p_src[s:e]]
        else:
            tri = _open_triangle(p_src[s:e], m)
        for j in range(m):
            tp[s + j] = tri[j]
        for j in range(m):
            a = tri[j]
            if not closed and j == m - 1:
                tq[s + j] = [a[0], a[1]]
                continue
            c = tri[(j + 1) % m]
            tq[s + j] = [(a[0] + c[0]) / 2.0, (a[1] + c[1]) / 2.0]
    return tp, tq


def lerp_points(src, dst, t):
    return [[a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
            for a, b in zip(src, dst)]


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)
