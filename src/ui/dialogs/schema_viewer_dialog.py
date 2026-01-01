from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from typing import List, Dict, Any
from PyQt6.QtCore import Qt


class SchemaViewerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

    def display_schema_dialog(self, table_name: str, columns: List[Dict[str, Any]]):
        self.setWindowTitle(f"Schema: {table_name}")
        self.setMinimumSize(700, 400)

        layout = QVBoxLayout(self)

        table = QTableWidget()
        table.setColumnCount(7)
        table.setRowCount(len(columns))
        table.setHorizontalHeaderLabels([
            "Column", "Type", "Nullable", "Default", "PK", "AI", "UQ"
        ])

        for row_idx, col in enumerate(columns):
            table.setItem(row_idx, 0, QTableWidgetItem(col['column_name']))
            table.setItem(row_idx, 1, QTableWidgetItem(col['column_type']))

            nullable_item = QTableWidgetItem("✓" if col['not_null'] else "")
            nullable_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row_idx, 2, QTableWidgetItem(nullable_item))

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

        self.exec()

