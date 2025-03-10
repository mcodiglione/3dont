import argparse
import signal

from threedont import Controller

def main():
    parser = argparse.ArgumentParser(description='3Dont')
    parser.add_argument('--test', action='store_true', help='Test the viewer')
    args = parser.parse_args()

    controller = Controller()

    controller.run()
    print("Application stopped gracefully")

if __name__ == '__main__':
    main()