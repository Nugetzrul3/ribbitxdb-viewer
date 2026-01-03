from PyQt6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QAction, QCursor
from .dialogs import SchemaViewerDialog
from .. import APP_NAME, APP_AUTHOR
from platformdirs import user_data_dir
from ..core import DatabaseManager
from ..utils import trim_string
from typing import Optional
from pathlib import Path


class DatabaseTree(QTreeWidget):
    """Widget to display database structure"""

    # Signals
    table_selected = pyqtSignal(str, str)
    view_selected = pyqtSignal(str, str)
    database_disconnected = pyqtSignal(str)
    database_refreshed = pyqtSignal(str)
    query_copied = pyqtSignal(str, str)
    views_refreshed = pyqtSignal(str)
    view_deleted = pyqtSignal(str, str)
    tables_refreshed = pyqtSignal(str)
    table_deleted = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.setup_ui()
        self.setup_connections()
        self.data_dir = user_data_dir(APP_NAME, APP_AUTHOR)

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

    def load_database(self, db_manager: DatabaseManager):
        try:
            db_name = db_manager.db_path
            db_path = db_manager.db_path
            if db_name:
                db_name = db_name.split("/")[-1]

            root = QTreeWidgetItem(self, [(db_name or "Database") + f' ({trim_string(db_path)})'])
            root.setToolTip(0, db_path)
            root.setData(0, Qt.ItemDataRole.UserRole, {
                'type': 'database',
                'name': db_name,
                'path': db_path,
                'db_manager': db_manager
            })
            root.setExpanded(True)

            # Load tables
            self._load_tables(root, db_manager)
            # Load views
            self._load_views(root, db_manager)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database structure: {str(e)}")

    def disconnect_database(self):
        """Disconnect a specific database and remove from tree"""
        item = self.currentItem()

        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data or data.get('type') != 'database':
            return

        db_path = data.get('path', '')

        # Remove the item from the tree
        index = self.indexOfTopLevelItem(item)
        if index != -1:
            self.takeTopLevelItem(index)

        # Emit signal with database path so main_window can close the connection
        self.database_disconnected.emit(db_path)

    def refresh_views(self, parent: QTreeWidgetItem, is_deleting: bool = False):
        """Refresh views for database"""
        item = self.currentItem()
        item.setExpanded(False)

        data = item.data(0, Qt.ItemDataRole.UserRole)
        db_manager: DatabaseManager = data.get('db_manager')

        # check if db still exists
        if not Path(db_manager.db_path).exists():
            self.disconnect_database()
            return

        # Refresh the connection to see external changes
        try:
            db_manager.refresh_connection()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh: {str(e)}")
            return

        parent.takeChildren()
        self._load_views(parent, db_manager, is_refresh=True)

        if not is_deleting:
            self.views_refreshed.emit(db_manager.db_path)

    def refresh_tables(self, parent: QTreeWidgetItem, is_deleting: bool = False):
        """Refresh tables for database"""
        item = self.currentItem()
        item.setExpanded(False)

        data = item.data(0, Qt.ItemDataRole.UserRole)
        db_manager: DatabaseManager = data.get('db_manager')

        # check if db still exists
        if not Path(db_manager.db_path).exists():
            self.disconnect_database()
            return

        # Refresh the connection to see external changes
        try:
            db_manager.refresh_connection()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh: {str(e)}")
            return

        parent.takeChildren()
        self._load_tables(parent, db_manager, is_refresh=True)

        if not is_deleting:
            self.tables_refreshed.emit(db_manager.db_path)

    def refresh_database(self):
        """Refresh database tables and views"""
        item = self.currentItem()
        item.setExpanded(False)

        data = item.data(0, Qt.ItemDataRole.UserRole)
        db_path = data.get('path', '')

        # check if db still exists
        if not Path(db_path).exists():
            self.disconnect_database()
            return

        db_manager: DatabaseManager = data.get('db_manager')

        # Refresh the connection to see external changes
        try:
            db_manager.refresh_connection()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh: {str(e)}")
            return

        # load tables and views again
        item.takeChildren()
        self._load_tables(item, db_manager)
        self._load_views(item, db_manager)
        item.setExpanded(True)
        self.database_refreshed.emit(db_path)

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click"""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        item_type = data.get("type", "")
        db_manager: DatabaseManager = data.get('db_manager')

        if db_manager:
            db_path = db_manager.db_path
            if item_type == "table":
                table_name = data.get("name")
                self.table_selected.emit(db_path, table_name)
            elif item_type == "view":
                view_name = data.get("name")
                self.view_selected.emit(db_path, view_name)

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double click. If item selected is table, the load columns"""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if not data:
            return

        item_type = data.get("type", "")
        if item_type == "table":
            table_name = data.get("name")
            table_db_manager: DatabaseManager = data.get('db_manager')
            self._load_table_columns(item, table_name, table_db_manager)

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
            table_db_manager: DatabaseManager = data.get('db_manager')
            actions = []

            view_action = QAction("View Data", self)
            view_action.triggered.connect(
                lambda: self.table_selected.emit(table_db_manager.db_path, table_name)
            )
            actions.append(view_action)

            schema_action = QAction("View Schema", self)
            schema_action.triggered.connect(
                lambda: self.show_table_schema(table_name, table_db_manager)
            )
            actions.append(schema_action)

            actions.append(menu.addSeparator())

            copy_action = QAction("Copy Table Name", self)
            copy_action.triggered.connect(
                lambda: self.copy_to_clipboard(table_name)
            )
            actions.append(copy_action)

            query_menu = QMenu(self)
            query_menu.setTitle("Generate query")
            query_actions = []

            select_action = QAction("Generate SELECT Query", self)
            select_action.triggered.connect(
                lambda: self.generate_select_query(table_name, table_db_manager)
            )
            query_actions.append(select_action)

            insert_action = QAction("Generate INSERT Query", self)
            insert_action.triggered.connect(
                lambda: self.generate_insert_query(table_name, table_db_manager)
            )
            query_actions.append(insert_action)

            update_action = QAction("Generate UPDATE Query", self)
            update_action.triggered.connect(
                lambda: self.generate_update_query(table_name, table_db_manager))
            query_actions.append(update_action)

            delete_action = QAction("Generate DELETE Query", self)
            delete_action.triggered.connect(
                lambda: self.generate_delete_query(table_name, table_db_manager)
            )
            query_actions.append(delete_action)

            menu.addActions(actions)
            query_menu.addActions(query_actions)
            menu.addMenu(query_menu)

            actions = [menu.addSeparator()]

            delete_table_action = QAction("Delete Table", self)
            delete_table_action.triggered.connect(
                lambda: self.delete_table(table_name, table_db_manager)
            )
            actions.append(delete_table_action)

            menu.addActions(actions)

        elif item_type == 'tables':
            refresh_tables_action = QAction("Refresh Tables", self)
            refresh_tables_action.triggered.connect(
                lambda: self.refresh_tables(item)
            )
            menu.addAction(refresh_tables_action)

        elif item_type == 'view':
            view_name = data.get('name')
            view_db_manager: DatabaseManager = data.get('db_manager')

            actions = []
            view_action = QAction("View Data", self)
            view_action.triggered.connect(
                lambda: self.view_selected.emit(view_db_manager.db_path, view_name)
            )
            actions.append(view_action)

            schema_action = QAction("View Schema", self)
            schema_action.triggered.connect(
                lambda: self.show_view_schema(view_name, view_db_manager)
            )
            actions.append(schema_action)

            actions.append(menu.addSeparator())

            delete_action = QAction("Delete View", self)
            delete_action.triggered.connect(
                lambda: self.delete_view(view_name, view_db_manager)
            )
            actions.append(delete_action)

            menu.addActions(actions)

        elif item_type == 'views':
            refresh_views_action = QAction("Refresh Tables", self)
            refresh_views_action.triggered.connect(
                lambda: self.refresh_views(item)
            )
            menu.addAction(refresh_views_action)

        elif item_type == 'column':
            column_info = data.get('column')
            col_name = column_info['column_name']

            copy_action = QAction("Copy Column Name", self)
            copy_action.triggered.connect(
                lambda: self.copy_to_clipboard(col_name)
            )
            menu.addAction(copy_action)

        elif item_type == 'database':
            actions = []
            disconnect_action = QAction("Disconnect Database", self)
            disconnect_action.triggered.connect(self.disconnect_database)
            actions.append(disconnect_action)

            refresh_action = QAction("Refresh Database", self)
            refresh_action.triggered.connect(self.refresh_database)
            actions.append(refresh_action)

            menu.addActions(actions)

        menu.exec(QCursor.pos())

    @classmethod
    def copy_to_clipboard(cls, text: str):
        """Copy text to clipboard"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def generate_select_query(self, table_name: str, db_manager: DatabaseManager):
        """Generate and copy SELECT query to clipboard"""
        query = "SELECT \n"
        schema = db_manager.get_table_schema(table_name)
        columns = [x.get('column_name') for x in schema]
        for idx, column in enumerate(columns):
            query += f"\t{column}" + (",\n" if idx < len(columns) - 1 else "\n")
        query += "WHERE \n"
        for idx, column in enumerate(columns):
            query += f"\t{column} = '{column}'" + (" AND\n" if idx < len(columns) - 1 else ";")

        self.copy_to_clipboard(query)
        self.query_copied.emit(table_name, "SELECT")

    def generate_insert_query(self, table_name: str, db_manager: DatabaseManager):
        """Generate and copy INSERT query to clipboard"""
        schema = db_manager.get_table_schema(table_name)
        columns = [x.get('column_name') for x in schema]
        columns_seperated = ", ".join(columns)
        columns_stringified = [f"'{x}'" for x in columns]
        columns_stringified_seperated = ", ".join(columns_stringified)
        query = (f"INSERT INTO {table_name}"
                 f"\n\t({columns_seperated})"
                 f"\nVALUES \n\t({columns_stringified_seperated});")
        self.copy_to_clipboard(query)
        self.query_copied.emit(table_name, "INSERT")

    def generate_update_query(self, table_name: str, db_manager: DatabaseManager):
        """Generate and copy UPDATE query to clipboard"""
        schema = db_manager.get_table_schema(table_name)
        columns = [x.get('column_name') for x in schema]
        query = f"UPDATE {table_name} SET\n"
        for idx, column in enumerate(columns):
            query += f"\t{column} = '{column}'" + (",\n" if idx < len(columns) - 1 else "\n")

        query += "WHERE\n"

        for idx, column in enumerate(columns):
            query += f"\t{column} = '{column}'" + (" AND\n" if idx < len(columns) - 1 else "\n;")

        self.copy_to_clipboard(query)
        self.query_copied.emit(table_name, "UPDATE")

    def generate_delete_query(self, table_name: str, db_manager: DatabaseManager):
        """Generate and copy DELETE query to clipboard"""
        schema = db_manager.get_table_schema(table_name)
        columns = [x.get('column_name') for x in schema]
        query = f"DELETE FROM {table_name} WHERE\n"
        for idx, column in enumerate(columns):
            query += f"\t{column} = '{column}'" + (" AND\n" if idx < len(columns) - 1 else ";")

        self.copy_to_clipboard(query)
        self.query_copied.emit(table_name, "DELETE")

    def delete_view(self, view_name: str, db_manager: DatabaseManager):
        """Drop the view selected"""
        try:
            db_manager.delete_view(view_name)
            parent = self.currentItem().parent()
            self.refresh_views(parent, is_deleting=True)
            self.view_deleted.emit(view_name, db_manager.db_path)
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))

    def delete_table(self, table_name: str, db_manager: DatabaseManager):
        """Drop the table selected"""
        try:
            db_manager.delete_table(table_name)
            parent = self.currentItem().parent()
            self.refresh_tables(parent, is_deleting=True)
            self.table_deleted.emit(table_name, db_manager.db_path)
        except Exception as e:
            QMessageBox.warning(self, "Database Error", str(e))

    def show_table_schema(self, table_name: str, db_manager: DatabaseManager):
        """Show detailed schema information for a table"""
        try:
            column_names = db_manager.get_table_schema(table_name)
            schema_viewer = SchemaViewerDialog(self)
            schema_viewer.display_table_schema_dialog(table_name, column_names)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to retrieve schema: {str(e)}"
            )

    def show_view_schema(self, view_name: str, db_manager: DatabaseManager):
        """Show detailed schema information for a view"""
        try:
            view_data = db_manager.get_view_schema(view_name)
            schema_viewer = SchemaViewerDialog(self)
            schema_viewer.display_view_schema_dialog(view_name, view_data)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to retrieve schema: {str(e)}"
            )


    def _load_tables(self, parent: QTreeWidgetItem, db_manager: DatabaseManager, is_refresh: bool = False):
        """Load tables from database"""
        try:
            tables = db_manager.get_tables()

            if not tables:
                return

            if not is_refresh:
                tables_category = QTreeWidgetItem(parent, ["Tables"])
                tables_category.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'tables',
                    'db_manager': db_manager
                })
            else:
                tables_category = parent

            for table_name in tables:
                table_item = QTreeWidgetItem(tables_category, [table_name])
                table_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'table',
                    'name': table_name,
                    'db_manager': db_manager
                })

            tables_category.setExpanded(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database tables: {str(e)}")

    def _load_views(self, parent: QTreeWidgetItem, db_manager: DatabaseManager, is_refresh: bool = False):
        """Load views from database"""
        try:
            views = db_manager.get_views()

            if not views:
                return

            if not is_refresh:
                views_category = QTreeWidgetItem(parent, ["Views"])
                views_category.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'views',
                    'db_manager': db_manager
                })
            else:
                views_category = parent

            for view_name in views:
                view_item = QTreeWidgetItem(views_category, [view_name])
                view_item.setData(0, Qt.ItemDataRole.UserRole, {
                    'type': 'view',
                    'name': view_name,
                    'db_manager': db_manager
                })

            views_category.setExpanded(True)

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load database views: {str(e)}")

    def _load_table_columns(self, table_item: QTreeWidgetItem, table_name: str, db_manager: DatabaseManager):
        """Load columns from table"""
        try:
            table_item.takeChildren()

            # retrieve table columns
            columns = db_manager.get_table_schema(table_name)

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

    # to be utilised
    # @classmethod
    # def _get_dummy_data_for_col_type(cls, col_type: str):
    #     pass

