import math


class TransformMatrix:
    @staticmethod
    def get_identity():
        return [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]

    @staticmethod
    def get_translation(dx, dy):
        return [
            [1.0, 0.0, dx],
            [0.0, 1.0, dy],
            [0.0, 0.0, 1.0]
        ]

    @staticmethod
    def get_rotation(angle_deg):
        rad = math.radians(angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return [
            [cos_a, -sin_a, 0.0],
            [sin_a,  cos_a, 0.0],
            [0.0,    0.0,   1.0]
        ]

    @staticmethod
    def get_rotation_about_point(angle_deg, px, py):
        rad = math.radians(angle_deg)
        c = math.cos(rad)
        s = math.sin(rad)
        return [
            [c, -s, px - px * c + py * s],
            [s,  c, py - px * s - py * c],
            [0.0, 0.0, 1.0]
        ]

    @staticmethod
    def multiply_matrices(m1, m2):
        result = [[0.0] * 3 for _ in range(3)]
        for i in range(3):
            for j in range(3):
                result[i][j] = m1[i][0] * m2[0][j] + m1[i][1] * m2[1][j] + m1[i][2] * m2[2][j]
        return result

    @staticmethod
    def apply_to_point(x, y, matrix):
        new_x = x * matrix[0][0] + y * matrix[0][1] + matrix[0][2]
        new_y = x * matrix[1][0] + y * matrix[1][1] + matrix[1][2]
        w = x * matrix[2][0] + y * matrix[2][1] + matrix[2][2]

        if abs(w) < 1e-6:
            w = 1e-6

        return new_x / w, new_y / w

    @staticmethod
    def get_inverse(matrix):
        a, b, tx = matrix[0]
        c, d, ty = matrix[1]
        det = a * d - b * c
        ia, ib = d / det, -b / det
        ic, id_ = -c / det, a / det
        return [
            [ia, ib, -(ia * tx + ib * ty)],
            [ic, id_, -(ic * tx + id_ * ty)],
            [0.0, 0.0, 1.0]
        ]
