from PySide6.QtWidgets import (
    QWidget, QToolBar,
    QPlainTextEdit, QVBoxLayout, QTabWidget, QTableView, QHeaderView, QComboBox, QSplitter, QMessageBox, QLabel,
    QFileDialog, QMenu, QApplication, QHBoxLayout, QPushButton
)

from .dialogs.accept_action_dialog import AcceptActionDialog
from .query_table_viewer import QueryResultViewer
from ..models.history_table_model import HistoryTableModel
from PySide6.QtGui import QAction, QFont, QKeySequence
from ..utils.sql_highlighter import SQLHighlighter
from platformdirs import user_data_dir
from PySide6.QtCore import Qt, QPoint
from .. import APP_NAME, APP_AUTHOR
from ..core import DatabaseManager
from typing import Optional, Dict
from datetime import datetime
import ribbitxdb

class QueryEditor(QWidget):
    ok_style = """
        color: #02a661;
        padding: 5px;
        border: 1px solid #00FF94
    """
    error_style = """
        color: #db0235;
        padding: 5px;
        border: 1px solid #f7003a
    """

    def __init__(self):
        super().__init__()
        self.current_db_manager: Optional[DatabaseManager] = None
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.query_result_viewer = QueryResultViewer()
        self.data_model = HistoryTableModel()
        self.data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Query Editor")
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self._create_toolbar()
        self._create_editor()
        self._create_history_table()

        self.v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.v_splitter.setWindowTitle('Query Editor')
        self.v_splitter.setChildrenCollapsible(False)
        self.v_splitter.addWidget(self.tab_widget)
        self.v_splitter.addWidget(self.query_result_viewer)
        self.main_layout.addWidget(self.v_splitter)

    def on_tab_changed(self, index: int):
        current_tab = self.tab_widget.tabText(index)

        if current_tab == 'History':
            # populate history table
            try:
                connection = ribbitxdb.connect(f'{self.data_dir}/viewer.rbx')

                cursor = connection.cursor()
                query = cursor.execute('SELECT database, execution_timestamp, execution_time, row_count, query, id FROM history ORDER BY id DESC')
                rows = query.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []

                if len(rows) > 0:
                    columns.pop()

                cursor.close()
                connection.close()

                h_header = self.history_table.horizontalHeader()
                h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

                self.history_table.setSortingEnabled(False)

                self.data_model.set_data(rows)

                self.history_table.setSortingEnabled(True)
                self.history_table.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

                h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
                h_header.setStretchLastSection(True)

            except Exception as e:
                raise RuntimeError(f"Failed to fetch data: {str(e)}")

    def populate_db_list(self, db_dict: Dict[str, DatabaseManager]):
        if self.db_list_cmb.count() > 0:
            self.db_list_cmb.clear()

        if len(db_dict.items()) == 0:
            self.db_list_cmb.addItem('Empty list')
            return

        for idx, db_path in enumerate(db_dict):
            db_name = db_dict[db_path].db_name
            self.db_list_cmb.addItem(db_name, {
                'db_manager': db_dict[db_path],
                'db_path': db_path
            })
            self.db_list_cmb.setItemData(idx, db_path, Qt.ItemDataRole.ToolTipRole)

    def add_db(self, db_manager: DatabaseManager):
        # since empty list won't have any data, we can pop it from the
        # combo box
        first_item_data = self.db_list_cmb.itemData(0, Qt.ItemDataRole.UserRole)
        if not first_item_data:
            self.db_list_cmb.removeItem(0)

        db_name = db_manager.db_name
        self.db_list_cmb.addItem(db_name, {
            'db_manager': db_manager,
            'db_path': db_manager.db_path,
        })
        self.db_list_cmb.setItemData(self.db_list_cmb.count() - 1, db_manager.db_path, Qt.ItemDataRole.ToolTipRole)

    def remove_db(self, db_path: str):
        for i in range(self.db_list_cmb.count()):
            data = self.db_list_cmb.itemData(i, Qt.ItemDataRole.UserRole)
            data_db_path = data.get('db_path')
            if data_db_path == db_path:
                self.db_list_cmb.removeItem(i)
                break

        if self.db_list_cmb.count() == 0:
            self.db_list_cmb.addItem('Empty list')

    def change_db(self, index):
        if index < 0:
            return

        data = self.db_list_cmb.itemData(index, Qt.ItemDataRole.UserRole)
        if not data:
            return

        db_manager: DatabaseManager = data.get('db_manager', None)
        if db_manager:
            self.current_db_manager = db_manager

    def execute_query(self):
        try:
            sql: str
            if self.sql_input.textCursor().hasSelection():
                sql = self.sql_input.textCursor().selectedText()
            else:
                sql = self.sql_input.toPlainText()

            data = self.current_db_manager.execute_query(sql)
            self.query_result_viewer.display_results(data)

            execution_time = data.get('execution_time', 0)
            execution_timestamp = data.get('execution_timestamp', 0)
            rows_affected = data.get('rows_affected', 0)

            connection = ribbitxdb.connect(f'{self.data_dir}/viewer.rbx')
            cursor = connection.cursor()

            cursor.execute(
                "INSERT INTO history (database, query, row_count, execution_time, execution_timestamp) VALUES (?, ?, ?, ?)",
               (
                   self.current_db_manager.db_name,
                   sql.strip(),
                   rows_affected,
                   execution_time,
                   datetime.fromtimestamp(execution_timestamp).strftime('%Y-%m-%d %H:%M:%S')
               )
            )
            cursor.close()
            connection.commit()
            connection.close()

            if rows_affected > 0:
                self._show_okay_status(f"Query executed successfully in {execution_time:.3f} seconds. {rows_affected} rows affected.")
            else:
                self._show_okay_status(f"Query executed successfully in {execution_time:.3f} seconds.")
        except Exception as e:
            self._show_error_status("Failed to execute query: " + str(e))
            self.query_result_viewer.clear_results()

    def save_sql(self):
        if self.sql_input.toPlainText().strip() == '':
            return

        file_name, _ = QFileDialog.getSaveFileName(self, 'Save Query', "", "SQL files (*.sql);;All Files (*.*)")
        if file_name:
            f = open(file_name, 'w')
            text = self.sql_input.toPlainText().strip()
            f.write(text)
            f.close()
            QMessageBox.information(self, f'SQL saved', f'SQL saved to {file_name}')

    def load_sql(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open SQL File", "", f"SQL files (*.sql);;All Files (*.*)")
        if file_name:
            f = open(file_name, 'r')
            text = f.read()
            f.close()
            self.sql_input.setPlainText(text)
            self._show_okay_status(f"Query loaded from {file_name}")

    def on_column_right_click(self, position: QPoint):
        index = self.history_table.indexAt(position)
        if not index.isValid():
            return

        if index.column() != 3:
            return

        value = index.data(Qt.ItemDataRole.DisplayRole)

        menu = QMenu(self.history_table)
        copy_action = menu.addAction("Copy")
        menu.addSeparator()
        load_into_editor = menu.addAction("Load query into editor")

        action = menu.exec(self.history_table.viewport().mapToGlobal(position))
        if action == copy_action:
            QApplication.clipboard().setText(str(value))
        elif action == load_into_editor:
            self.sql_input.setPlainText(str(value))
            self.tab_widget.setCurrentIndex(0)

    def clear_history(self):
        clear_history_dialog = AcceptActionDialog(
            self,
            "Clear history",
            "Are you sure you want to clear the history?",
        )

        if clear_history_dialog.exec():
            try:
                connection = ribbitxdb.connect(f'{self.data_dir}/viewer.rbx')
                cursor = connection.cursor()
                cursor.execute('DELETE FROM history')
                cursor.close()
                connection.commit()
                connection.close()

                self.data_model.set_data([])

            except Exception as e:
                self._show_error_status("Failed to clear history: " + str(e))


    def _create_toolbar(self):
        toolbar = QToolBar()

        self.db_list_cmb = QComboBox()
        self.db_list_cmb.currentIndexChanged.connect(self.change_db)
        toolbar.addWidget(self.db_list_cmb)

        actions = []

        execute_action = QAction("Execute", self)
        execute_action.triggered.connect(self.execute_query)
        execute_key_sequence = QKeySequence(QKeySequence.StandardKey.Refresh)
        execute_action.setShortcut(execute_key_sequence)
        execute_action.setToolTip(f"Execute ({execute_key_sequence.toString()})")
        actions.append(execute_action)

        export_action = QAction("Export", self)
        actions.append(export_action)

        format_action = QAction("Format", self)
        actions.append(format_action)

        save_action = QAction("Save", self)
        save_action_sequence = QKeySequence(QKeySequence.StandardKey.Save)
        save_action.setShortcut(save_action_sequence)
        save_action.setToolTip(f"Save ({save_action_sequence.toString()})")
        save_action.triggered.connect(self.save_sql)
        actions.append(save_action)

        load_action = QAction("Load", self)
        load_action.setShortcut(QKeySequence("Ctrl+L"))
        load_action.setToolTip(f"Load (Ctrl+L)")
        load_action.triggered.connect(self.load_sql)
        actions.append(load_action)

        toolbar.addActions(actions)

        self.main_layout.addWidget(toolbar)

    def _create_editor(self):
        self.editor = QWidget()
        layout = QVBoxLayout(self.editor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sql_input = QPlainTextEdit()

        SQLHighlighter(self.sql_input.document())

        sql_font = QFont()
        sql_font.setFamily("Consolas")
        sql_font.setPointSize(15)
        self.sql_input .setFont(sql_font)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self._show_okay_status("Ready")

        layout.addWidget(self.sql_input )
        layout.addWidget(self.status_label)
        self.tab_widget.addTab(self.editor, "Query")

    def _create_history_table(self):
        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)
        layout.setContentsMargins(0,0,0,0)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        reset_button = QPushButton("Clear history")
        reset_button.clicked.connect(self.clear_history)
        button_layout.addWidget(reset_button)

        self.history_table = QTableView()
        self.history_table.setModel(self.data_model)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.on_column_right_click)
        self.history_table.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.history_table.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)

        layout.addLayout(button_layout)
        layout.addWidget(self.history_table)
        self.tab_widget.addTab(history_widget, "History")

    def _show_okay_status(self, message):
        self.status_label.setStyleSheet(self.ok_style)
        self.status_label.setText(message)

    def _show_error_status(self, message):
        self.status_label.setStyleSheet(self.error_style)
        self.status_label.setText(message)
