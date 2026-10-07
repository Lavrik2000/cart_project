from hardware.motor_driver import MotorDriver

class CartController:
    def __init__(self, driver: MotorDriver):
        self.driver = driver

    def forward(self):
        self.driver.set_left(1)
        self.driver.set_right(1)

    def backward(self):
        self.driver.set_left(-1)
        self.driver.set_right(-1)

    def turn_left(self):
        self.driver.set_left(-1)
        self.driver.set_right(1)

    def turn_right(self):
        self.driver.set_left(1)
        self.driver.set_right(-1)

    def steer_left(self):
        self.driver.set_left(0);
        self.driver.set_right(1)

    def steer_right(self):
        self.driver.set_left(1);
        self.driver.set_right(0)

    def stop(self):
        self.driver.stop()