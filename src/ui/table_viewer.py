from PyQt6.QtWidgets import QTableView, QHeaderView, QMessageBox, QVBoxLayout, QWidget
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from .pagination_widget import PaginationWidget
from ..core import DatabaseManager
from ..models import DatabaseTableModel
from typing import Dict, Any, Optional


class TableViewer(QWidget):
    """Widget to display table data"""

    def __init__(self):
        super().__init__()
        self.current_table: Optional[str] = None
        self.current_db_manager: Optional[DatabaseManager] = None
        self.table_view = QTableView()
        self.data_model = DatabaseTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.data_model)
        self.table_view.setModel(self.proxy_model)
        self.setup_ui()

    def setup_ui(self):
        """Create UI with table and pagination"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.setup_table_view()
        layout.addWidget(self.table_view)

        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)
        layout.addWidget(self.pagination)

    def setup_table_view(self):
        """Initialise table settings"""
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableView.EditTrigger.DoubleClicked)

        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.table_view.verticalHeader()
        v_header.setVisible(True)

    def display_data(self, data: Dict[str, Any], db_manager: Optional[DatabaseManager] = None, table_name: Optional[str] = None):
        """Display query results"""
        if data.get('total_rows') == 0:
            self.clear_data()
            QMessageBox.warning(self, 'No results', 'No results')
            return
        self.current_db_manager = db_manager
        self.current_table = table_name

        self.table_view.setSortingEnabled(False)
        self.data_model.set_data(data)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

        total_rows = data.get('total_rows', len(data.get('rows', [])))
        self.pagination.set_total_rows(total_rows)

    def on_page_changed(self, page: int):
        if not self.current_table or not self.current_db_manager:
            return

        try:
            page_size = self.pagination.page_size
            data = self.current_db_manager.get_table_data_paginated(
                self.current_table, page, page_size
            )

            self.table_view.setSortingEnabled(False)
            self.data_model.set_data(data)
            self.table_view.setSortingEnabled(True)
            self.table_view.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load page: {str(e)}")

    def on_page_size_changed(self, page_size: int):
        current_page = self.pagination.current_page
        self.on_page_changed(current_page)

    def clear_data(self):
        """Clear all data from the table"""
        empty_data = {
            'columns': [],
            'rows': [],
            'total_rows': 0
        }
        self.data_model.set_data(empty_data)
        self.pagination.reset()
        self.current_table = None
        self.current_db_manager = None



