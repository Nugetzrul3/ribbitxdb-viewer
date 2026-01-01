from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox,
    QTreeWidgetItemIterator
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QCursor
from ..core import DatabaseManager
from typing import Optional, List
from pathlib import Path


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
        self.setIndentation(10)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

    def setup_connections(self):
        """Connect signals and slots"""
        self.itemClicked.connect(self.on_item_clicked)
        self.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def load_database(self, db_manager: DatabaseManager) -> bool:
        self.db_manager = db_manager

        try:
            db_name = self.db_manager.db_path
            if db_name:
                db_name = db_name.split("/")[-1]

            if self._check_duplicate_items(db_name):
                QMessageBox.critical(self, "Error", "Database already exists")
                return False

            root = QTreeWidgetItem(self, [db_name or "Database"])
            root.setData(0, Qt.ItemDataRole.UserRole, {
                'name': db_name or "Database",
                'type': 'DBName'
            })
            root.setExpanded(True)

            # Load tables
            self._load_tables(root)
            # Load views
            self._load_views(root)

            return True

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database structure: {str(e)}")

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click"""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        item_type = data.get("type", "")

        if item_type == "table":
            table_name = data.get("name")
            self.table_selected.emit(table_name)
        elif item_type == "view":
            view_name = data.get("name")
            self.view_selected.emit(view_name)

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click. If item selected is table, the load columns"""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        item_type = data.get("type", "")
        if item_type == "table":
            table_name = data.get("name")
            self._load_table_columns(item, table_name)

    def show_context_menu(self, position: QPoint):
        """Display context menu for different items"""
        item = self.itemAt(position)

        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        menu = QMenu(self)
        item_type = data.get("type", "")

        if item_type == 'table':
            table_name = data.get('name')

            view_action = QAction("View Data", self)
            view_action.triggered.connect(
                lambda: self.table_selected.emit(table_name)
            )
            menu.addAction(view_action)

            schema_action = QAction("View Schema", self)
            schema_action.triggered.connect(
                lambda: self.show_table_schema(table_name)
            )
            menu.addAction(schema_action)

            menu.addSeparator()

            copy_action = QAction("Copy Table Name", self)
            copy_action.triggered.connect(
                lambda: self.copy_to_clipboard(table_name)
            )
            menu.addAction(copy_action)

            select_action = QAction("Generate SELECT Query", self)
            select_action.triggered.connect(
                lambda: self.generate_select_query(table_name)
            )
            menu.addAction(select_action)

        elif item_type == 'view':
            view_name = data.get('name')

            view_action = QAction("View Data", self)
            view_action.triggered.connect(
                lambda: self.view_selected.emit(view_name)
            )
            menu.addAction(view_action)

        elif item_type == 'column':
            column_info = data.get('column')
            col_name = column_info['column_name']

            copy_action = QAction("Copy Column Name", self)
            copy_action.triggered.connect(
                lambda: self.copy_to_clipboard(col_name)
            )
            menu.addAction(copy_action)

        menu.exec(QCursor.pos())

    @classmethod
    def copy_to_clipboard(cls, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def generate_select_query(self, table_name: str):
        """Generate and copy SELECT query to clipboard"""
        query = f"SELECT * FROM {table_name};"
        self.copy_to_clipboard(query)

        QMessageBox.information(
            self,
            "Query Copied",
            f"SELECT query for '{table_name}' copied to clipboard!"
        )

    def show_table_schema(self, table_name: str):
        """Show detailed schema information for a table"""
        if not self.db_manager:
            return

        try:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
            from PyQt6.QtCore import Qt

            columns = self.db_manager.get_table_schema(table_name)

            dialog = QDialog(self)
            dialog.setWindowTitle(f"Schema: {table_name}")
            dialog.setMinimumSize(700, 400)

            layout = QVBoxLayout(dialog)

            table = QTableWidget()
            table.setColumnCount(7)
            table.setRowCount(len(columns))
            table.setHorizontalHeaderLabels([
                "Column", "Type", "Nullable", "Default", "PK", "AI", "UQ"
            ])

            for row_idx, col in enumerate(columns):
                table.setItem(row_idx, 0, QTableWidgetItem(col['column_name']))
                table.setItem(row_idx, 1, QTableWidgetItem(col['column_type']))

                nullable = "NULL" if not col['not_null'] else "NOT NULL"
                table.setItem(row_idx, 2, QTableWidgetItem(nullable))

                default = str(col['default_value']) if col['default_value'] else ""
                table.setItem(row_idx, 3, QTableWidgetItem(default))

                pk_item = QTableWidgetItem("✓" if col['primary_key'] else "")
                pk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, 4, pk_item)

                ai_item = QTableWidgetItem("✓" if col.get('auto_increment', False) else "")
                ai_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, 5, ai_item)

                uq_item = QTableWidgetItem("✓" if col.get('unique_constraint', False) else "")
                uq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_idx, 6, uq_item)

            table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setAlternatingRowColors(True)

            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            header.setStretchLastSection(True)

            layout.addWidget(table)
            dialog.exec()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to retrieve schema: {str(e)}"
            )

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
            QMessageBox.warning(self, "Error", f"Failed to load database views: {str(e)}")

    def _load_table_columns(self, table_item: QTreeWidgetItem, table_name: str):
        """Load columns from table"""
        if not self.db_manager:
            return

        try:
            table_item.takeChildren()

            # retrieve table columns
            columns = self.db_manager.get_table_schema(table_name)

            columns_category = QTreeWidgetItem(table_item, ["Columns"])
            columns_category.setExpanded(True)

            for col in columns:
                col_name = col["column_name"]
                col_type = col["column_type"]
                col_info = f"{col_name}: ({col_type})"

                if col["primary_key"]:
                    col_info += " 🔑"

                if col["not_null"]:
                    col_info += " 🚫"

                if col["unique_constraint"]:
                    col_info += " 🔒"

                if col["auto_increment"]:
                    col_info += " ⬆️"

                column_item = QTreeWidgetItem(columns_category, [col_info])
                column_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'column',
                    'table': table_name,
                    'column': col
                })

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load columns for {table_name}: {str(e)}")

    def _check_duplicate_items(self, db_name: str) -> bool:
        """Check if database name already exists"""
        iterator = QTreeWidgetItemIterator(self)

        while iterator.value():
            item: QTreeWidgetItem = iterator.value()
            data = item.data(0, Qt.ItemDataRole.UserRole)
            name = data.get("name", None)

            if not name:
                return False

            if name == db_name:
                return True

            iterator += 1

        return False

