import argparse
import signal

from threedont import Controller

def main():
    parser = argparse.ArgumentParser(description='3Dont')
    parser.add_argument('--test', action='store_true', help='Test the viewer')
    args = parser.parse_args()

    controller = Controller()

    def signal_handler(sig, frame):
        controller.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    controller.run()

if __name__ == '__main__':
    main()