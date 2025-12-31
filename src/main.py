from PyQt6.QtWidgets import QApplication
from src.core import DatabaseManager
from PyQt6.QtCore import Qt
import sys

from src.ui.main_window import MainWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName('RibbitXDB Viewer')
    app.setOrganizationName('Nugetzrul3')

    try:
        with open('src/resources/theme.qss', 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()


