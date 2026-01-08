from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils import query_viewer_db
from src import APP_NAME, APP_AUTHOR
from PySide6.QtCore import Qt
from pathlib import Path
import ribbitxdb
import sys

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_AUTHOR)

    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(__file__).parent

    qss_path = base_path / 'resources' / 'theme.qss'

    try:
        with open(qss_path, 'r') as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass

    try:
        queries = [
            """
                        CREATE TABLE IF NOT EXISTS databases (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            path TEXT UNIQUE
                        );
                    """,
            """
                    CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            database TEXT,
                            execution_timestamp TEXT,
                            execution_time REAL,
                            row_count INTEGER,
                            query TEXT
                        );
                    """
        ]

        query_viewer_db(queries)
    except Exception as e:
        raise RuntimeError(f'Could not connect to viewer database: {str(e)}')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()


