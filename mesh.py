import math
import random
from dataclasses import dataclass


@dataclass
class Anchor:
    id: str
    x: float   # метры, mesh-координаты
    y: float

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(x - self.x, y - self.y)

    def measure(self, x: float, y: float, noise_std: float = 0.0) -> float:
        """«Радиоизмерение» дистанции до точки. С шумом канала."""
        d = self.distance_to(x, y)
        if noise_std > 0:
            d = max(0.0, d + random.gauss(0, noise_std))
        return d


class Mesh:
    """
    Набор якорей — «мэш-роутеров». Именно их взаимное расположение
    задаёт систему координат: метр, начало отсчёта, ориентацию.
    """

    def __init__(self,
                 anchors: list[Anchor],
                 noise_std: float = 0.05,
                 max_range: float = 15.0):
        self.anchors = {a.id: a for a in anchors}
        self.noise_std = noise_std
        self.max_range = max_range

    def measure_all(self, x: float, y: float) -> dict[str, float]:
        """Все якоря измеряют расстояние до точки. Дальние отбрасываются."""
        out = {}
        for a in self.anchors.values():
            d = a.measure(x, y, self.noise_std)
            if d <= self.max_range:
                out[a.id] = d
        return out

    @property
    def extent(self) -> tuple[float, float, float, float]:
        """Границы мэша: (min_x, min_y, max_x, max_y) в метрах."""
        xs = [a.x for a in self.anchors.values()]
        ys = [a.y for a in self.anchors.values()]
        return min(xs), min(ys), max(xs), max(ys)


def default_mesh() -> Mesh:
    """4 якоря по углам помещения 10 × 8 м."""
    return Mesh([
        Anchor("A", 0.0,  0.0),
        Anchor("B", 10.0, 0.0),
        Anchor("C", 10.0, 8.0),
        Anchor("D", 0.0,  8.0),
    ], noise_std=0.05, max_range=20.0)