from abc import ABC, abstractmethod

class MotorDriver(ABC):
    """Абстрактный драйвер для двух моторов."""

    @abstractmethod
    def set_left(self, direction: int) -> None:
        """
        Управление левым мотором.
        direction: 1 — вперёд, -1 — назад, 0 — стоп.
        """
        ...

    @abstractmethod
    def set_right(self, direction: int) -> None:
        """Управление правым мотором (аналогично)."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Остановить оба мотора."""
        ...