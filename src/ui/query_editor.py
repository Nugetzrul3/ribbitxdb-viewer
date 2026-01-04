from PyQt6.QtWidgets import (
    QWidget, QToolBar,
    QPlainTextEdit, QVBoxLayout, QTabWidget, QTableView, QHeaderView
)
from ..models.history_table_model import HistoryTableModel
from PyQt6.QtGui import QAction, QFont, QKeySequence
from ..core import DatabaseManager
from typing import Optional
from PyQt6.QtCore import Qt
import ribbitxdb



class QueryEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.current_db_manager: Optional[DatabaseManager] = None
        self.db_list: list = []
        self.main_layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        self.data_model = HistoryTableModel()
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
            print("populating table!")
            test_data = {
                'columns': ['DB Name', 'Execution Timestamp', 'Execution Time', 'Rows affected', 'SQL'],
                'rows': [
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                    ['hello', '12/12/12', '12ms', 1, 'SELECT * FROM fuck_this_shit'],
                ]
            }
            self.data_model.set_data(test_data)

    def _create_toolbar(self):
        toolbar = QToolBar()
        actions = []

        execute_action = QAction("Execute", self)
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
