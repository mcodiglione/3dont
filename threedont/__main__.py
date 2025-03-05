import argparse

from threedont import Controller

def main():
    parser = argparse.ArgumentParser(description='3Dont')
    parser.add_argument('--test', action='store_true', help='Test the viewer')
    args = parser.parse_args()

    controller = Controller()

    try:
        controller.run()
    except KeyboardInterrupt:
        controller.stop()

    controller.stop()

if __name__ == '__main__':
    main()