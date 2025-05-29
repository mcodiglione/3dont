import argparse

from threedont import Controller
from .app.state import Config, AppState


def main():
    parser = argparse.ArgumentParser(description='3Dont')
    parser.add_argument('--test', action='store_true', help='Test the viewer')
    args = parser.parse_args()

    app_state = AppState("threedont")
    config = Config("threedont")

    controller = Controller()

    controller.run()
    print("Application stopped gracefully")


if __name__ == '__main__':
    main()
