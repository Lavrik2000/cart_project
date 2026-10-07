import OPi.GPIO as GPIO
from .motor_driver import MotorDriver

class OrangePiMotorDriver(MotorDriver):
    def __init__(self, left_in1, left_in2, right_in1, right_in2):
        self.left_in1 = left_in1
        self.left_in2 = left_in2
        self.right_in1 = right_in1
        self.right_in2 = right_in2

        GPIO.setmode(GPIO.SUNXI)
        GPIO.setwarnings(False)
        for pin in (left_in1, left_in2, right_in1, right_in2):
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def _set_motor(self, in1, in2, direction: int):
        if direction == 1:
            GPIO.output(in1, GPIO.HIGH)
            GPIO.output(in2, GPIO.LOW)
        elif direction == -1:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.HIGH)
        else:
            GPIO.output(in1, GPIO.LOW)
            GPIO.output(in2, GPIO.LOW)

    def set_left(self, direction: int) -> None:
        self._set_motor(self.left_in1, self.left_in2, direction)

    def set_right(self, direction: int) -> None:
        self._set_motor(self.right_in1, self.right_in2, direction)

    def stop(self) -> None:
        self.set_left(0)
        self.set_right(0)