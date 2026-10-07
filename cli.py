from hardware.mock_motor_driver import MockMotorDriver
from cart_controller import CartController
import curses

def main():
    driver = MockMotorDriver()
    cart = CartController(driver)


    print("Управление тележкой (симуляция)")
    print("W — вперёд, S — назад, A — влево, D — вправо, Q — выход")

    while True:
        cmd = input("> ").strip().lower()
        if cmd == 'w' or cmd == 'w':
            cart.forward()
        elif cmd == 's':
            cart.backward()
        elif cmd == 'a':
            cart.turn_left()
        elif cmd == 'd':
            cart.turn_right()
        elif cmd == 'q':
            cart.stop()
            break
        else:
            cart.stop()

if __name__ == "__main__":
    main()