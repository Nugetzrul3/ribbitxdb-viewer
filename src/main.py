from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import sys


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName('RibbitXDB Viewer')
    app.setOrganizationName('Nugetzrul3')

    try:
        with open('resources/theme.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()


