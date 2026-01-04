from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout,
    QSplitter, QToolBar, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QActionGroup
from .database_tree import DatabaseTree
from .dialogs import OpenDatabaseDialog
from PyQt6.QtCore import Qt, QSettings
from platformdirs import user_data_dir
from .table_viewer import TableViewer
from .. import APP_NAME, APP_AUTHOR
from ..core import DatabaseManager
from pathlib import Path
from typing import Dict
import csv
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_managers: Dict[str, DatabaseManager] = {}

        self.setWindowTitle("RibbitXDB Viewer")
        self.setGeometry(100, 100, 1400, 900)

        try:
            base_path = Path(sys._MEIPASS)
        except Exception:
            base_path = Path(__file__).parent.parent

        icon_path = base_path / 'resources' / 'logo.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowIcon(QIcon(icon_path.as_posix()))

        self._init_ui()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._load_dbs()
        self._restore_settings()

    def _init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Horizontal splitter: sidebar | content
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setChildrenCollapsible(False)

        # Left: Database tree
        self.db_tree = DatabaseTree()
        self.db_tree.table_selected.connect(self.on_table_selected)
        # Since views are tables, we can call same function
        self.db_tree.view_selected.connect(self.on_table_selected)
        self.db_tree.database_disconnected.connect(self.on_database_disconnected)
        self.db_tree.database_refreshed.connect(self.on_database_refreshed)
        self.db_tree.query_copied.connect(self.on_query_copied)
        self.db_tree.views_refreshed.connect(self.on_views_refreshed)
        self.db_tree.view_deleted.connect(self.on_view_deleted)
        self.db_tree.tables_refreshed.connect(self.on_tables_refreshed)
        self.db_tree.table_deleted.connect(self.on_table_deleted)
        self.db_tree.setMinimumWidth(200)

        # Will use this for query editor
        # v_splitter = QSplitter(Qt.Orientation.Vertical)

        self.db_table_viewer = TableViewer()
        self.query_table_viewer = TableViewer()
        # self.query_editor = QueryEditor()
        # self.query_editor.query_executed.connect(self.execute_query)

        # v_splitter.addWidget(self.table_viewer)
        # # v_splitter.addWidget(self.query_editor)
        # v_splitter.setStretchFactor(0, 2)
        # v_splitter.setStretchFactor(1, 1)

        h_splitter.addWidget(self.db_tree)
        h_splitter.addWidget(self.db_table_viewer)
        h_splitter.setStretchFactor(0, 2)
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
        open_database_viewer_action = QAction("Database Viewer", self)
        open_database_viewer_action.triggered.connect(self.open_database_viewer)
        toolbar.addAction(open_database_viewer_action)

        toolbar.addSeparator()

        open_execute_query_action = QAction("Query Editor", self)
        open_execute_query_action.triggered.connect(self.open_query_editor)
        toolbar.addAction(open_execute_query_action)

    def _create_statusbar(self):
        """Create status bar"""
        self.statusBar().showMessage("Ready")

    def open_database_viewer(self):
        """Hide query editor and open database viewer"""
        # self.query_editor.hide()
        self.db_table_viewer.show()

    def open_query_editor(self):
        self.db_table_viewer.hide()
        # self.query_editor.show()

    def open_database(self):
        """Open database dialog"""
        dialog = OpenDatabaseDialog(self)
        if dialog.exec():
            filepath = dialog.get_filepath()
            filepath = Path(filepath).as_posix()
            self.open_database_viewer()

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
                db_manager = DatabaseManager(filepath)

                self.db_managers[db_manager.db_path] = db_manager

                # Load tree with this manager
                self.db_tree.load_database(db_manager)

                self.statusBar().showMessage(f"Opened: {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open database: {str(e)}")

    def on_table_selected(self, db_path: str, table_name: str):
        """Handle table selection from tree"""
        if db_path not in self.db_managers:
            return

        try:
            db_manager = self.db_managers[db_path]
            page_size = self.db_table_viewer.pagination.page_size

            data = db_manager.get_table_data_paginated(table_name, page=1, page_size=page_size)
            self.db_table_viewer.display_data(data, db_manager, table_name)

            total_pages = self.db_table_viewer.pagination.total_pages
            self.open_database_viewer()
            self.statusBar().showMessage(
                f"Viewing: {table_name} (Page 1 of {total_pages})"
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load table: {str(e)}")

    def on_database_disconnected(self, db_path: str):
        """Handle database disconnection"""
        try:
            # Get and close the specific database manager
            if db_path in self.db_managers:
                del self.db_managers[db_path]

            self.db_table_viewer.clear_data()
            self.statusBar().showMessage(f"{db_path} disconnected")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to disconnect database: {str(e)}")

    def on_database_refreshed(self, db_path: str):
        """Handle database refreshed"""
        try:
            self.db_table_viewer.clear_data()
            self.statusBar().showMessage(f"{db_path} refreshed")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh database: {str(e)}")

    def on_query_copied(self, table_name: str, query_type: str):
        self.statusBar().showMessage(f"{query_type} query for {table_name} copied to clipboard")

    def on_views_refreshed(self, db_name: str):
        self.statusBar().showMessage(f"Views for {db_name} refreshed")

    def on_view_deleted(self, view_name: str, db_name: str):
        self.statusBar().showMessage(f"View {view_name} deleted from {db_name}")

    def on_tables_refreshed(self, db_name: str):
        self.statusBar().showMessage(f"Tables for {db_name} refreshed")

    def on_table_deleted(self, table_name: str, db_name: str):
        self.statusBar().showMessage(f"Table {table_name} deleted from {db_name}")

    def _load_dbs(self):
        """Load databases saved in csv"""
        data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
        data_dir_path = Path(data_dir)
        db_list = []

        with open(data_dir_path / "databases.csv", 'r', newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                db_list.append(row[0])

        # I have plans to make it so that we don't load all the dbs immediately, but for now
        # I will keep it this way
        for db_path in db_list:
            db_manager = DatabaseManager(db_path)
            self.db_tree.load_database(db_manager)
            self.db_managers[db_path] = db_manager


    def closeEvent(self, event):
        """On window close, save open dbs to datadir file"""
        data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
        data_dir_path = Path(data_dir)
        db_list = [x for x in self.db_managers.keys()]

        with open(data_dir_path / 'databases.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows([path] for path in db_list)


    def _restore_settings(self):
        """Restore window settings"""
        settings = QSettings()
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
