from PySide6.QtWidgets import QTableView, QHeaderView, QVBoxLayout, QWidget, QMessageBox
from ..models.database_table_model import DatabaseTableModel
from PySide6.QtCore import QSortFilterProxyModel, Qt
from .pagination_widget import PaginationWidget
from typing import Dict, Any, List


class QueryResultViewer(QWidget):
    """Widget to display query results with client-side pagination"""

    def __init__(self):
        super().__init__()

        # Store all data in memory for client-side pagination
        self.all_columns: List[str] = []
        self.all_rows: List[tuple] = []

        self.setup_ui()

    def setup_ui(self):
        """Create UI with table and pagination"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table_view = QTableView()
        self.data_model = DatabaseTableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.data_model)
        self.table_view.setModel(self.proxy_model)

        self.setup_table_view()
        layout.addWidget(self.table_view)

        # Pagination
        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)
        layout.addWidget(self.pagination)

    def setup_table_view(self):
        """Initialize table settings"""
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setSortingEnabled(True)
        self.table_view.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.table_view.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)

        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        v_header = self.table_view.verticalHeader()
        v_header.setVisible(True)

    def display_results(self, result: Dict[str, Any]):
        """
        Display query results with client-side pagination
        """
        self.all_columns = result.get('columns', [])
        self.all_rows = result.get('rows', [])

        self.pagination.set_total_rows(len(self.all_rows))
        self._display_page(page=1)

    def _display_page(self, page: int):
        """Display a specific page of results (client-side pagination)"""
        page_size = self.pagination.page_size
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_rows = self.all_rows[start_idx:end_idx]

        page_data = {
            'columns': self.all_columns,
            'rows': page_rows,
            'total_rows': len(self.all_rows),
            'page': page,
            'page_size': page_size,
            'displayed_rows': len(page_rows)
        }

        # Display the page
        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table_view.setSortingEnabled(False)
        self.data_model.set_data(page_data)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)

    def on_page_changed(self, page: int):
        """Handle page change - paginate through in-memory data"""
        if not self.all_rows:
            return

        self._display_page(page)

    def on_page_size_changed(self, page_size: int):
        """Handle page size change - recalculate and show current page"""
        if not self.all_rows:
            return

        current_page = self.pagination.current_page
        self._display_page(current_page)

    def clear_results(self):
        """Clear all results"""
        empty_data = {
            'columns': [],
            'rows': [],
            'total_rows': 0
        }
        self.data_model.set_data(empty_data)
        self.all_columns = []
        self.all_rows = []
        self.pagination.reset()