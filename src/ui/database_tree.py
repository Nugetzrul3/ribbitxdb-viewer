from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QCursor
from ..core import DatabaseManager
from typing import Optional

class DatabaseTree(QTreeWidget):
    """Widget to display database structure"""

    # Signals
    table_selected = pyqtSignal(str)
    view_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Initialise widget settings"""
        self.setHeaderLabel("Database Objects")
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setAnimated(True)
        self.setIndentation(20)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

    def setup_connections(self):
        """Connect signals and slots"""
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def load_database(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.clear()

        try:
            db_name = self.db_manager.db_path
            if db_name:
                db_name = db_name.split("/")[-1]

            root = QTreeWidgetItem(self, [db_name or "Database"])
            root.setExpanded(True)

            # Load tables
            self._load_tables(root)
            # Load views
            self._load_views(root)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database structure: {str(e)}")

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click"""
        pass

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click. If item selected is table, the load columns"""
        pass

    def show_context_menu(self, position: QPoint):
        pass

    def _load_tables(self, parent: QTreeWidgetItem):
        """Load tables from database"""
        if not self.db_manager:
            return

        try:
            tables = self.db_manager.get_tables()

            if not tables:
                return

            tables_category = QTreeWidgetItem(parent, ["Tables"])
            tables_category.setExpanded(True)

            for table_name in tables:
                table_item = QTreeWidgetItem(tables_category, [table_name])
                table_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'table',
                    'name': table_name,
                })

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database tables: {str(e)}")

    def _load_views(self, parent: QTreeWidgetItem):
        """Load views from database"""
        if not self.db_manager:
            return

        try:
            views = self.db_manager.get_views()

            if not views:
                return

            views_category = QTreeWidgetItem(parent, ["Views"])
            views_category.setExpanded(False)

            for view_name in views:
                view_item = QTreeWidgetItem(views_category, [view_name])
                view_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'view',
                    'name': view_name
                })

        except Exception as e:
            print(f"Error loading views: {e}")