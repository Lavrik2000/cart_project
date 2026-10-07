import pytest
from hardware.mock_motor_driver import MockMotorDriver
from cart_controller import CartController

@pytest.fixture
def cart():
    driver = MockMotorDriver()
    return CartController(driver), driver

def test_forward(cart):
    ctrl, drv = cart
    ctrl.forward()
    assert drv.left == 1
    assert drv.right == 1

def test_backward(cart):
    ctrl, drv = cart
    ctrl.backward()
    assert drv.left == -1
    assert drv.right == -1

def test_turn_left(cart):
    ctrl, drv = cart
    ctrl.turn_left()
    assert drv.left == -1
    assert drv.right == 1

def test_stop(cart):
    ctrl, drv = cart
    ctrl.forward()
    ctrl.stop()
    assert drv.left == 0
    assert drv.right == 0