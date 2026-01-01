from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QToolBar, QMessageBox
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from .database_tree import DatabaseTree
from .dialogs import OpenDatabaseDialog
from PyQt6.QtCore import Qt, QSettings
from .table_viewer import TableViewer
from ..core import DatabaseManager
from pathlib import Path
from typing import Dict


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_managers: Dict[str, DatabaseManager] = {}

        self.setWindowTitle("RibbitXDB Viewer")
        self.setGeometry(100, 100, 1400, 900)

        icon_path = Path(__file__).parent.parent / 'resources' / 'logo.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowIcon(QIcon(icon_path.as_posix()))

        self._init_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._restore_settings()

    def _init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Horizontal splitter: sidebar | content
        h_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Database tree
        self.db_tree = DatabaseTree()
        self.db_tree.table_selected.connect(self.on_table_selected)
        # Since views are tables, we can call same function
        self.db_tree.view_selected.connect(self.on_table_selected)
        self.db_tree.database_disconnected.connect(self.on_database_disconnected)

        # Right: Vertical splitter for table view and query editor
        v_splitter = QSplitter(Qt.Orientation.Vertical)

        self.table_viewer = TableViewer()
        # self.query_editor = QueryEditor()
        # self.query_editor.query_executed.connect(self.execute_query)

        v_splitter.addWidget(self.table_viewer)
        # v_splitter.addWidget(self.query_editor)
        v_splitter.setStretchFactor(0, 2)
        v_splitter.setStretchFactor(1, 1)

        h_splitter.addWidget(self.db_tree)
        h_splitter.addWidget(v_splitter)
        h_splitter.setStretchFactor(0, 1)
        h_splitter.setStretchFactor(1, 4)

        main_layout.addWidget(h_splitter)

    def _create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Database...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_database)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        # View menu
        view_menu = menubar.addMenu("&View")

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        export_action = QAction("&Export Data...", self)
        # export_action.triggered.connect(self.export_data)
        tools_menu.addAction(export_action)

    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        # Add common actions
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_database)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        execute_action = QAction("Execute", self)
        execute_action.setShortcut("F5")
        # execute_action.triggered.connect(self.query_editor.execute)
        toolbar.addAction(execute_action)

    def _create_statusbar(self):
        """Create status bar"""
        self.statusBar().showMessage("Ready")

    def open_database(self):
        """Open database dialog"""
        dialog = OpenDatabaseDialog(self)
        if dialog.exec():
            filepath = dialog.get_filepath()
            filepath = Path(filepath).as_posix()

            # Check if already open
            if filepath in self.db_managers:
                QMessageBox.information(
                    self,
                    "Already Open",
                    f"Database '{filepath}' is already open."
                )
                return

            try:
                # Create new database manager for this connection and store
                db_manager = DatabaseManager()
                db_manager.open(filepath)

                self.db_managers[db_manager.db_path] = db_manager

                # Load tree with this manager
                self.db_tree.load_database(db_manager)

                self.statusBar().showMessage(f"Opened: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open database: {str(e)}")

    def on_table_selected(self, db_path: str, table_name: str):
        """Handle table selection from tree"""
        try:
            db_manager = self.db_managers[db_path]
            data = db_manager.get_table_data(table_name)
            self.table_viewer.display_data(data)
            self.statusBar().showMessage(f"Viewing: {table_name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open table: {str(e)}")

    def on_database_disconnected(self, db_path: str):
        """Handle database disconnection"""
        try:
            # Get and close the specific database manager
            if db_path in self.db_managers:
                db_manager = self.db_managers[db_path]
                db_manager.close()
                del self.db_managers[db_path]

            db_name = db_path.split('/')[-1]
            self.table_viewer.clearContents()
            self.table_viewer.setRowCount(0)
            self.table_viewer.setColumnCount(0)
            self.statusBar().showMessage(f"{db_name} disconnected")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to disconnect database: {str(e)}")

    def _restore_settings(self):
        """Restore window settings"""
        settings = QSettings()
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
