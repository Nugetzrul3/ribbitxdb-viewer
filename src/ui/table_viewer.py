from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from typing import Dict, Any
from PyQt6.QtCore import Qt

class TableViewer(QTableWidget):
    """Widget to display table data"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """Initialise table settings"""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

    def display_data(self, data: Dict[str, Any]):
        """Display query results"""
        columns = data.get("columns")
        rows = data.get("rows", [])

        # Reset
        self.clear()
        self.setRowCount(len(rows))
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)

        if len(rows) == 0:
            QMessageBox.information(self, "No data found", "No data found")
            return

        for row_idx, row in enumerate(rows):
            for col_idx, col in enumerate(row):
                item = QTableWidgetItem(str(col) if col is not None else "NULL")

                if col is None:
                    item.setForeground(Qt.GlobalColor.gray)

                self.setItem(row_idx, col_idx, item)

        self.resizeColumnsToContents()



