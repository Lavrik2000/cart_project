from .motor_driver import MotorDriver

class MockMotorDriver(MotorDriver):
    def __init__(self):
        self.left = 0
        self.right = 0

    def set_left(self, direction: int) -> None:
        self.left = direction
        print(f"[Mock] Левый мотор: {self._dir_name(direction)}")

    def set_right(self, direction: int) -> None:
        self.right = direction
        print(f"[Mock] Правый мотор: {self._dir_name(direction)}")

    def stop(self) -> None:
        self.left = 0
        self.right = 0
        print("[Mock] Стоп")

    @staticmethod
    def _dir_name(d: int) -> str:
        return {1: "вперёд", -1: "назад", 0: "стоп"}.get(d, "?")