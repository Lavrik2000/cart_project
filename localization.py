from __future__ import annotations
import math


def trilaterate(anchors: dict[str, tuple[float, float]],
                distances: dict[str, float]) -> tuple[float, float] | None:
    """
    anchors: {id: (x, y)}
    distances: {id: distance}
    Возвращает (x, y) в метрах или None, если якорей < 3.
    """
    pts = [(anchors[i][0], anchors[i][1], d)
           for i, d in distances.items() if i in anchors]
    if len(pts) < 3:
        return None

    x0, y0, d0 = pts[0]

    # Для каждой следующей точки — линеаризованное уравнение
    A, C = [], []
    for (xi, yi, di) in pts[1:]:
        A.append((2 * (xi - x0), 2 * (yi - y0)))
        C.append(d0**2 - di**2 + xi**2 - x0**2 + yi**2 - y0**2)

    # Нормальные уравнения AᵀA·[x, y] = AᵀC (2×2 — считаем вручную)
    ata00 = ata01 = ata11 = 0.0
    atc0 = atc1 = 0.0
    for (a0, a1), c in zip(A, C):
        ata00 += a0 * a0
        ata01 += a0 * a1
        ata11 += a1 * a1
        atc0 += a0 * c
        atc1 += a1 * c

    det = ata00 * ata11 - ata01 * ata01
    if abs(det) < 1e-9:
        return None
    x = (atc0 * ata11 - atc1 * ata01) / det
    y = (ata00 * atc1 - ata01 * atc0) / det
    return x, y