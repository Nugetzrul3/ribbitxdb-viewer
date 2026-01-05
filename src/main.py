from src.ui.main_window import MainWindow
from PySide6.QtWidgets import QApplication
from platformdirs import user_data_dir
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

    data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
    try:
        conn = ribbitxdb.connect(f'{data_dir}/viewer.rbx')
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS databases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                path TEXT UNIQUE
            );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                database TEXT,
                execution_timestamp TEXT,
                execution_time REAL,
                query TEXT
            );
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        raise RuntimeError(f'Could not connect to viewer database: {str(e)}')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()


