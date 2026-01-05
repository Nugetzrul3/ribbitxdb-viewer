from PyQt6.QtWidgets import (
    QWidget, QToolBar,
    QPlainTextEdit, QVBoxLayout, QTabWidget, QTableView, QHeaderView, QComboBox
)
from ..models.history_table_model import HistoryTableModel
from PyQt6.QtGui import QAction, QFont, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from platformdirs import user_data_dir
from .. import APP_NAME, APP_AUTHOR
from ..core import DatabaseManager
from typing import Optional, Dict
import ribbitxdb



class QueryEditor(QWidget):
    query_executed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_db_manager: Optional[DatabaseManager] = None
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.data_model = HistoryTableModel()
        self.data_dir = user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=True)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Query Editor")
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self._create_toolbar()
        self.main_layout.addWidget(self.tab_widget)
        self._create_editor()
        self._create_history_table()

    def on_tab_changed(self, index: int):
        current_tab = self.tab_widget.tabText(index)

        if current_tab == 'History':
            # populate history table
            try:
                connection = ribbitxdb.connect(f'{self.data_dir}/viewer.rbx')

                cursor = connection.cursor()
                query = cursor.execute('SELECT database, execution_timestamp, execution_time, query FROM history')
                rows = query.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                cursor.close()
                connection.close()

                self.data_model.set_data({
                    'rows': rows,
                    'columns': columns
                })
            except Exception as e:
                raise RuntimeError(f"Failed to fetch data: {str(e)}")

    def populate_db_list(self, db_dict: Dict[str, DatabaseManager]):
        if self.db_list_cmb.count() > 0:
            self.db_list_cmb.clear()

        if len(db_dict.items()) == 0:
            self.db_list_cmb.addItem('Empty list')
            return

        for db_path in db_dict:
            db_name = db_dict[db_path].db_name
            self.db_list_cmb.addItem(db_name, {
                'db_manager': db_dict[db_path],
            })

    def add_db(self, db_manager: DatabaseManager):
        db_name = db_manager.db_name
        self.db_list_cmb.addItem(db_name, {
            'db_manager': db_manager,
            'db_path': db_manager.db_path,
        })

    def remove_db(self, db_path: str):
        for i in range(self.db_list_cmb.count()):
            data = self.db_list_cmb.itemData(i, Qt.ItemDataRole.UserRole)
            data_db_path = data.get('db_path')
            if data_db_path == db_path:
                self.db_list_cmb.removeItem(i)
                break

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
            connection = ribbitxdb.connect(f'{self.data_dir}/viewer.rbx')
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO history (database, query) VALUES (?, ?)
            """, (self.current_db_manager.db_name, self.editor.toPlainText()))
            cursor.close()
            connection.commit()
            connection.close()
        except Exception as e:
            raise RuntimeError(f"Failed to execute query: {str(e)}")


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
        actions.append(save_action)

        load_action = QAction("Load", self)
        load_action.setShortcut(QKeySequence("Ctrl+L"))
        load_action.setToolTip(f"Load (Ctrl+L)")
        actions.append(load_action)

        toolbar.addActions(actions)

        self.main_layout.addWidget(toolbar)

    def _create_editor(self):
        self.editor = QPlainTextEdit()
        sql_font = QFont()
        sql_font.setFamily("Consolas")
        sql_font.setPointSize(15)
        self.editor.setFont(sql_font)
        self.tab_widget.addTab(self.editor, "Query")

    def _create_history_table(self):
        self.history_table = QTableView()
        self.history_table.setModel(self.data_model)
        self.history_table.setAlternatingRowColors(True)

        h_header = self.history_table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.history_table.verticalHeader()
        v_header.setVisible(True)

        self.tab_widget.addTab(self.history_table, "History")
