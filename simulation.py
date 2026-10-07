from __future__ import annotations
import math
from dataclasses import dataclass

from cart_controller import CartController
from hardware.mock_motor_driver import MockMotorDriver
from mesh import Mesh, default_mesh
from localization import trilaterate



LINEAR_SPEED = 1.5   # м/с при скорости мотора 1
WHEEL_BASE   = 0.8   # м между колёсами


@dataclass
class CartState:
    x: float = 5.0
    y: float = 4.0
    angle: float = 0.0            # 0 = +X
    left_speed: int = 0
    right_speed: int = 0
    target: tuple[float, float] | None = None


def _wrap(a: float) -> float:
    while a >  math.pi: a -= 2 * math.pi
    while a <= -math.pi: a += 2 * math.pi
    return a


class Simulation:
    def __init__(self, mesh: Mesh | None = None):
        self.mesh = mesh or default_mesh()
        self.driver = MockMotorDriver()
        self.cart = CartController(self.driver)
        self.state = CartState()
        self.last_distances: dict[str, float] = {}
        self.last_estimate: tuple[float, float] | None = None
        self._turn_bias: int = 0
        self._nav = "idle"  # "idle" | "behind_L" | "behind_R" | "turn_L" | "turn_R" | "steer_L" | "steer_R" | "forward"

    # ---------- API управления ----------
    def set_command(self, cmd: str) -> None:
        if cmd in ("forward", "backward", "left", "right"):
            self.state.target = None       # ручное — выключает автопилот
            self._nav = "idle"
        self._apply(cmd)

    def _apply(self, cmd: str) -> None:
        if   cmd == "forward":  self.cart.forward()
        elif cmd == "backward": self.cart.backward()
        elif cmd == "left":     self.cart.turn_left()
        elif cmd == "right":    self.cart.turn_right()
        elif cmd == "stop":     self.cart.stop()

    def set_target(self, x: float, y: float) -> None:
        self.state.target = (x, y)
        self._nav = "idle"

    def clear_target(self) -> None:
        self.state.target = None
        self._nav = "idle"
        self.cart.stop()

    def set_noise(self, std: float) -> None:
        self.mesh.noise_std = max(0.0, float(std))

    # ---------- Тик симуляции ----------
    def tick(self, dt: float) -> None:
        if self.state.target is not None:
            self._autopilot()

        s = self.state
        s.left_speed = self.driver.left
        s.right_speed = self.driver.right

        v_l = s.left_speed * LINEAR_SPEED
        v_r = s.right_speed * LINEAR_SPEED

        v     = (v_l + v_r) / 2.0
        omega = (v_r - v_l) / WHEEL_BASE

        s.angle = _wrap(s.angle + omega * dt)
        s.x += v * math.cos(s.angle) * dt
        s.y += v * math.sin(s.angle) * dt

        # Якоря измеряют, локализатор считает
        self.last_distances = self.mesh.measure_all(s.x, s.y)
        anchors_xy = {a.id: (a.x, a.y) for a in self.mesh.anchors.values()}
        self.last_estimate = trilaterate(anchors_xy, self.last_distances)

    # ---------- Автопилот ----------
    def _autopilot(self) -> None:
        s = self.state
        tx, ty = s.target
        dx, dy = tx - s.x, ty - s.y
        dist = math.hypot(dx, dy)

        if dist < 0.12:
            self.cart.stop()
            s.target = None
            self._nav = "idle"
            return

        hx, hy = math.cos(s.angle), math.sin(s.angle)
        dot = hx * dx + hy * dy
        cross = hx * dy - hy * dx
        err = math.atan2(cross, dot)  # в (-π, π]

        print(f"[nav] d={dist:5.2f}  "
              f"ang={math.degrees(s.angle):+6.1f}°  "
              f"dot={dot:+5.2f}  cross={cross:+5.2f}  "
              f"err={math.degrees(err):+6.1f}°")

        # -------- BEHIND: цель за спиной (dot < 0) --------
        # При входе ОДИН РАЗ выбираем сторону и держим её до выхода из сектора.
        if dot < 0:
            if self._nav not in ("behind_L", "behind_R"):
                self._nav = "behind_L" if cross >= 0 else "behind_R"

            if self._nav == "behind_L":
                self.cart.turn_left()
            else:
                self.cart.turn_right()
            return

        # -------- FRONT: цель впереди --------
        # Выход из behind — сбрасываем состояние в «нейтральное».
        if self._nav in ("behind_L", "behind_R"):
            self._nav = "idle"

        # Гистерезис: пороги для входа и выхода из каждого состояния разные.
        # Это не даёт «дёргаться» на границе.
        if self._nav == "turn_L":
            if err < 0.20: self._nav = "idle"  # выходим из крутого доворота
        elif self._nav == "turn_R":
            if err > -0.20: self._nav = "idle"
        elif self._nav == "steer_L":
            if err < 0.05: self._nav = "idle"
        elif self._nav == "steer_R":
            if err > -0.05: self._nav = "idle"
        elif self._nav == "forward":
            if abs(err) > 0.18: self._nav = "idle"

        # Принятие решения только если состояние «idle».
        if self._nav == "idle":
            if err > 0.60:
                self._nav = "turn_L"
            elif err < -0.60:
                self._nav = "turn_R"
            elif err > 0.15:
                self._nav = "steer_L"
            elif err < -0.15:
                self._nav = "steer_R"
            else:
                self._nav = "forward"

        # Исполнение
        if self._nav == "turn_L":
            self.cart.turn_left()
        elif self._nav == "turn_R":
            self.cart.turn_right()
        elif self._nav == "steer_L":
            self.cart.steer_left()
        elif self._nav == "steer_R":
            self.cart.steer_right()
        else:
            self.cart.forward()





