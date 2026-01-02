from PyQt6.QtWidgets import QTableView, QHeaderView, QMessageBox
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from ..models import DatabaseTableModel
from typing import Dict, Any


class TableViewer(QTableView):
    """Widget to display table data"""

    def __init__(self):
        super().__init__()
        self.model = DatabaseTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.setModel(self.proxy_model)
        self.setup_ui()

    def setup_ui(self):
        """Initialise table settings"""
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QTableView.EditTrigger.DoubleClicked)

        h_header = self.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.verticalHeader()
        v_header.setVisible(True)

    def display_data(self, data: Dict[str, Any]):
        """Display query results"""
        if data.get('total_rows') == 0:
            QMessageBox.warning(self, 'No results', 'No results')
            return

        self.setSortingEnabled(False)
        self.model.set_data(data)
        self.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.horizontalHeader().setSortIndicatorShown(True)
        self.setSortingEnabled(True)

    def clear_data(self):
        """Clear all data from the table"""
        empty_data = {
            'columns': [],
            'rows': []
        }
        self.model.set_data(empty_data)



