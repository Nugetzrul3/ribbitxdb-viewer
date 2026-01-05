import json

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QLabel,
    QTabWidget, QPlainTextEdit, QMessageBox
)
from src.utils import parse_timestamp
from typing import List, Dict, Any
from PySide6.QtCore import Qt


class SchemaViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(400)

    def display_table_schema_dialog(self, table_name: str, columns: List[Dict[str, Any]]):
        self.setWindowTitle(f"Schema: {table_name}")
        tab_widget = QTabWidget()

        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.itemDoubleClicked.connect(self.on_item_double_clicked)
        table.setColumnCount(8)
        table.setRowCount(len(columns))
        table.setHorizontalHeaderLabels([
            "Column", "Type", "Nullable", "Default", "PK", "AI", "UQ", "FK"
        ])

        for row_idx, col in enumerate(columns):
            table.setItem(row_idx, 0, QTableWidgetItem(col['column_name']))
            table.setItem(row_idx, 1, QTableWidgetItem(col['column_type']))

            nullable_item = QTableWidgetItem("✓" if col['not_null'] else "")
            nullable_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 2, nullable_item)

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

            fk_item = QTableWidgetItem("✓" if col.get('foreign_key', False) else "")
            fk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if col.get('foreign_key', False):
                fk_item.setData(Qt.ItemDataRole.UserRole, {
                    "column": col['column_name'],
                    "fk_def": col['foreign_key']
                })

            table.setItem(row_idx, 7, fk_item)

        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        tab_widget.addTab(table, 'Column Information')
        create_script = self._build_create_script(table_name, columns)
        text_edit = QPlainTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(create_script)
        tab_widget.addTab(text_edit, 'Create Script')
        layout.addWidget(tab_widget)

        table.resizeColumnsToContents()
        total_width = table.verticalHeader().width()

        for i in range(table.columnCount()):
            total_width += table.columnWidth(i)

        total_width += 50
        self.setMinimumWidth(min(total_width, 1000))

        header.setStretchLastSection(True)

        self.exec()

    def display_view_schema_dialog(self, view_name: str, data: Dict[str, Any]):
        self.setWindowTitle(f"View: {view_name}")

        layout = QVBoxLayout(self)
        text_view = QTextEdit()
        text_view.setReadOnly(True)
        text_view.setText(data.get("sql"))
        layout.addWidget(text_view)

        datetime_label = QLabel()
        datetime_label.setText(f"Created at: {parse_timestamp(data.get("created_at"))}")
        datetime_label.setWordWrap(True)
        layout.addWidget(datetime_label)

        self.exec()

    def on_item_double_clicked(self, item: QTableWidgetItem):
        # possibly add other cases?
        column_idx = item.column()

        # foreign key
        if column_idx == 7:
            data = item.data(Qt.ItemDataRole.UserRole)
            if not data:
                return

            column_name = data.get("column")
            fk_def = json.loads(data.get("fk_def"))

            # makes a silent message box
            QMessageBox.about(self, "Foreign key", f"{column_name} references column {fk_def.get('column')} on table {fk_def.get("table")}")

    @classmethod
    def _build_create_script(cls, table_name: str, columns: List[Dict[str, Any]]):
        script = f"CREATE TABLE {table_name} (\n"
        foreign_keys = []
        for idx, col in enumerate(columns):
            col_def = f"\t{col['column_name']} {col['column_type']}"

            if col['primary_key']:
                col_def += " PRIMARY KEY"

            if col['auto_increment']:
                col_def += " AUTOINCREMENT"

            if col['not_null']:
                col_def += " NOT NULL"

            if col['unique_constraint']:
                col_def += " UNIQUE"

            if col['default_value']:
                col_def += f" DEFAULT {col['default_value']}"

            if col['check_expression']:
                col_def += f" CHECK ({col['check_expression']})"

            if col['foreign_key']:
                foreign_keys.append({
                    "column": col['column_name'],
                    "fk_def": col['foreign_key']
                })

            # need to add foreign key, having issues with creating
            # table with foreign key though

            script += col_def + (",\n" if (idx < len(columns) - 1 or len(foreign_keys) > 0) else "\n")

        if len(foreign_keys) > 0:
            for idx, fk in enumerate(foreign_keys):
                fk_def: dict = json.loads(fk.get('fk_def'))
                script += f"\tFOREIGN KEY ({fk.get('column')}) REFERENCES {fk_def.get('table')} ({fk_def.get('column')})"
                script += ',\n' if idx < len(foreign_keys) - 1 else "\n"

        script += ");"

        return script


